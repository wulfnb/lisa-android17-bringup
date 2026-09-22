# Evolution X Android 17 bring-up for Xiaomi lisa

Private development record for Xiaomi 11 Lite 5G NE (`lisa`). This repository
stores the source differences and revision information needed to reproduce
this workspace, rather than a copy of the entire Android source tree.

## Current status

- Base: Evolution X `cnb`, version 12.2 / Android 17.
- Product: `lineage_lisa-trunk_staging-userdebug`, with Google Apps enabled.
- Kernel: `kernel/xiaomi/lisa`, with `lisa_defconfig vendor/lisa_QGKI.config`.
- Soong graph analysis and the duplicate Megvii/firmware packaging blockers
  have been passed by subsequent compilation.
- The latest build inspected was build #10: approximately 35%, with 74,455
  completed actions. The two failed display-config compilations shared a
  missing `<mutex>` include. That include is patched here; its compilation
  has not been verified by the assistant.
- No completed flashable ROM or successful device boot has been verified.
- The user runs build/retry commands in their own terminal. Snapshot scripts
  never start a build, sync source, clean output, or push to GitHub.

## Contents

| Path | Purpose |
| --- | --- |
| `manifests/default.xml` | Pinned source manifest, including nine manually cloned repositories |
| `repositories.json` | Baseline commit for each of the 1,261 repositories |
| `snapshot.json` | Source patch list, file list, patch hashes and active binary recipes |
| `patches/` | Changes against the pinned baseline, grouped by source repository |
| `binary-fixups.json` | Reviewed, hash-checked binary transformations; no binary payloads |
| `notes/` | Bring-up history, fixes, validation status and upstream information |
| `scripts/capture.py` | Refresh source patches from a local Android checkout |
| `scripts/apply.py` | Check or apply the recorded snapshot |

The two local libjxl revert/reapply commits have zero net source changes.
The manifest pins their upstream parent instead of an unpublished local SHA.
Existing upstream licenses and history remain in the original repositories.

## Save the next fix

After editing source and recording the diagnosis/validation in `notes/`, run
these commands from this repository:

```bash
python3 scripts/capture.py --source ~/android
python3 scripts/apply.py --source ~/android
git diff --stat
git diff
git add README.md notes patches snapshot.json
git commit -m "Describe the specific bring-up fix"
git push
```

The apply command above is a check only. Capture includes tracked source
changes, including local commits, relative to the original pinned baseline.
It refuses untracked files and unreviewed binary changes so new work cannot
silently disappear from a snapshot. Review and stage intended new source
files in their component Git repository before capturing them. Do not stage
build outputs, credentials, or proprietary binary payloads.

If adding repositories or syncing to new upstream versions, deliberately
update the manifest and baseline records first. The snapshot is tied to these
recorded revisions; it is not a general patch set for arbitrary ROM versions.

Each commit in this repository records a new snapshot. Git history shows
what changed between fixes; `notes/` explains why it changed and what passed.

## Recreate on another machine

GitHub access to this private repository and access to every referenced
upstream repository are required. Upstream availability is not guaranteed by
this snapshot; it is not an offline mirror of all source or binaries.

On a configured Android build host, in a **new empty source directory**:

```bash
repo init -u https://github.com/wulfnb/lisa-android17-bringup.git \
  -b main -m manifests/default.xml
repo sync -c -j4 --no-clone-bundle --no-tags
```

Clone this backup repository separately, then run from that backup clone:

```bash
python3 scripts/apply.py --source /path/to/new/android
python3 scripts/apply.py --source /path/to/new/android --apply
```

The first command checks all patches and binary hashes before changing
anything. The second applies pending changes. Already-applied changes are
recognized. Conflicts require review; the script does not reset repositories.

## Build manually

No clean is needed for ordinary incremental fixes. Select a fresh log number.
The next log number after the last inspected build is 11.

```bash
cd ~/android
export GOGC=20 GOMEMLIMIT=22GiB
source build/envsetup.sh
set -o pipefail
lunch lineage_lisa-trunk_staging-userdebug &&
m evolution -j4 2>&1 | tee build_lisa_11.log
```

The Soong patch forwards the Go memory controls through its otherwise empty
environment. The 22 GiB value is a soft Go runtime target, not a hard RSS
limit. `-j4` controls compile scheduling, not the single analysis process.
Watch memory, swap and disk space. Do not run concurrent builds in one tree.

## Scope and licensing

See [LICENSE-NOTICE.md](LICENSE-NOTICE.md). This repository is private by
choice, not a claim that private storage grants additional rights. It contains
no firmware, ROM ZIPs, Google Apps, proprietary shared libraries, signing
keys, credentials, or binary Git patches. Proprietary dependencies are
referenced by upstream location and hash. Their terms still apply.

The WFD runtime behavior, hardware operation and first boot remain untested.
