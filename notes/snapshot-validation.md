# Initial snapshot validation

- Inventoried 1,261 component repositories: 1,252 managed by repo plus nine
  manually cloned repositories. Found modifications in 10 component repos.
- Checked for locally unique commits. Only the known libjxl revert/reapply
  pair was found; verified its net source diff is empty and pinned upstream.
- Checked that every manifest path and revision matches repositories.json.
- Checked every text patch against its pinned base using a temporary Git
  index. The source checkout and its real indexes were not changed.
- Ran apply.py in check-only mode against the existing workspace; every
  source patch and the WFD binary fixup were recognized as already applied.
- Tested capture and apply in a disposable fixture: dry-run does not edit,
  apply restores the intended text and binary transformation, a second apply
  is idempotent, committed fixes can be captured, and untracked files and
  unexpected binary contents are rejected.
- Checked the upload for binary payloads, binary Git patches, private-key
  headers and common GitHub token markers; none were found.

These are snapshot-tool and patch checks, not a new ROM build. No build or
retry commands were run during repository preparation. A fresh full upstream
sync and end-to-end rebuild from this repository have not been performed.

## Remote-machine README update

- Syntax-checked all 16 Bash examples without executing their commands.
- Corrected capture's inventory check to accept the original nine manual
  clones and the restored layout where Repo manages those same repositories.
- Exercised both layouts in disposable Git repositories and confirmed they
  produce identical snapshots. Missing required or unknown projects fail.
- Re-captured the existing workspace and confirmed the source patches and
  snapshot were unchanged. No setup, sync, build or retry command was run.
