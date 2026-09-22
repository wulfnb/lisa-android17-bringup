#!/usr/bin/env python3
"""Check a snapshot; apply only with --apply. Never sync, clean, build or push."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BUNDLE = Path(__file__).resolve().parents[1]


def check(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True).returncode == 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = args.source.resolve()
    snapshot = json.loads((BUNDLE / "snapshot.json").read_text())
    pending = []
    for project in snapshot["projects"]:
        repo, patch = root / project["path"], BUNDLE / project["patch"]
        assert hashlib.sha256(patch.read_bytes()).hexdigest() == project["patch_sha256"]
        if check(repo, "apply", "--reverse", "--check", str(patch)):
            print(f"Already applied: {project['path']}")
        elif not check(repo, "diff", "--quiet", project["base_commit"], "HEAD", "--"):
            raise SystemExit(f"{repo}: HEAD differs from recorded base; review before applying.")
        elif check(repo, "apply", "--check", str(patch)):
            pending.append((repo, patch))
            print(f"Ready: {project['path']}")
        else:
            raise SystemExit(f"{repo}: patch conflicts with current source; nothing applied.")
    binaries = []
    for recipe in snapshot["binary_fixups"]:
        path = root / recipe["repository"] / recipe["path"]
        data = path.read_bytes()
        digest = hashlib.sha1(data).hexdigest()
        if digest == recipe["fixed_sha1"]:
            print(f"Already fixed: {recipe['path']}")
        elif digest == recipe["original_sha1"]:
            fixed = data.replace(recipe["from"].encode(), recipe["to"].encode())
            assert hashlib.sha1(fixed).hexdigest() == recipe["fixed_sha1"]
            binaries.append((path, fixed))
            print(f"Ready binary fixup: {recipe['path']}")
        else:
            raise SystemExit(f"{path}: unexpected binary hash; nothing applied.")
    if args.apply:
        for repo, patch in pending:
            subprocess.run(["git", "-C", str(repo), "apply", str(patch)], check=True)
        for path, data in binaries:
            path.write_bytes(data)
        print("Snapshot applied.")
    else:
        print("Check complete; no files changed. Add --apply to apply pending changes.")


if __name__ == "__main__":
    main()
