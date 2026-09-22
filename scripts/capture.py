#!/usr/bin/env python3
"""Snapshot changes against the recorded upstream commits; never build or push."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess

BUNDLE = Path(__file__).resolve().parents[1]


def git(root, repo, *args):
    return subprocess.check_output(["git", "-C", str(root / repo), *args])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    root = args.source.resolve()
    repositories = json.loads((BUNDLE / "repositories.json").read_text())
    recipes = json.loads((BUNDLE / "binary-fixups.json").read_text())
    known = {(r["repository"], r["path"]): r for r in recipes}
    expected = {r["path"] for r in repositories if r["managed"]}
    actual = set((root / ".repo/project.list").read_text().splitlines())
    if expected != actual:
        raise SystemExit("Repo project list changed: review and update the pinned manifest first.")

    def capture(repo):
        path, base = repo["path"], repo["base_commit"]
        untracked = git(root, path, "ls-files", "--others", "--exclude-standard", "-z")
        if untracked:
            raise RuntimeError(f"{path}: review/stage untracked files before capture: {untracked!r}")
        stats = git(root, path, "diff", "--no-renames", "--numstat", "-z", base, "--")
        text_paths, transforms = [], []
        for entry in stats.split(b"\0"):
            if not entry:
                continue
            added, removed, raw_path = entry.split(b"\t", 2)
            filename = raw_path.decode()
            if added != b"-" and removed != b"-":
                text_paths.append(filename)
                continue
            recipe = known.get((path, filename))
            if not recipe:
                raise RuntimeError(f"Unreviewed binary change: {path}/{filename}")
            original = git(root, path, "show", f"{base}:{filename}")
            current = (root / path / filename).read_bytes()
            assert hashlib.sha1(original).hexdigest() == recipe["original_sha1"]
            assert current == original.replace(recipe["from"].encode(), recipe["to"].encode())
            assert hashlib.sha1(current).hexdigest() == recipe["fixed_sha1"]
            transforms.append(recipe)
        patch = git(root, path, "diff", "--no-renames", "--full-index", base, "--", *text_paths) if text_paths else b""
        return repo, patch, text_paths, transforms

    # Validate every project before writing any generated snapshot files.
    with ThreadPoolExecutor(max_workers=4) as pool:
        captured = list(pool.map(capture, repositories))
    patch_dir = BUNDLE / "patches"
    patch_dir.mkdir(exist_ok=True)
    snapshot = {"schema": 1, "repository_count": len(repositories), "projects": [], "binary_fixups": []}
    filenames = set()
    for repo, patch, paths, transforms in captured:
        if patch:
            filename = repo["path"].replace("/", "__") + ".patch"
            filenames.add(filename)
            (patch_dir / filename).write_bytes(patch)
            snapshot["projects"].append({
                "path": repo["path"], "base_commit": repo["base_commit"],
                "patch": "patches/" + filename, "files": paths,
                "patch_sha256": hashlib.sha256(patch).hexdigest(),
            })
        snapshot["binary_fixups"].extend(transforms)
    for old in patch_dir.glob("*.patch"):
        if old.name not in filenames:
            old.unlink()
    (BUNDLE / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"Captured {len(snapshot['projects'])} source patches and {len(snapshot['binary_fixups'])} binary recipes; no binary payloads copied.")


if __name__ == "__main__":
    main()
