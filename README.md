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
- Build #10 stopped after 74,455 completed actions with two display-config
  compilation errors; the missing `<mutex>` include was added.
- The latest inspected retry, build #11, completed another 6,406 actions and
  reported one recovery compilation failure: `PublicVolume.cpp` uses
  `std::replace` without including `<algorithm>`. That include is now patched;
  compilation of this newest fix has not been retried by the assistant.
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

Cloning this repository downloads the manifest, patches and documentation;
`repo sync` downloads the full Android source and referenced dependencies.
Run the following steps yourself on the remote machine, in order. Stop if a
step fails instead of proceeding to the build.

This restores our current bring-up state, not a verified working ROM. A fresh
machine restore and complete ROM build have not yet been tested end to end.

### 1. Prepare a Linux build host

Use an x86-64 Linux machine; these package commands target Ubuntu 24.04 or
later. For a new host, follow AOSP's current requirement of 64 GB RAM and at
least 400 GB free disk space. Allow additional space for Evolution X, Google
Apps and ccache. See the [official AOSP host setup guide](https://source.android.com/docs/setup/start/requirements).

Our existing 32 GB machine is below that RAM requirement. It reached partial
compilation using swap and the Go memory settings below, but this is not a
guarantee that every stage will fit. Check resources before downloading:

```bash
uname -m
free -h
df -h "$HOME"
```

Install the base build dependencies and command-line tools:

```bash
sudo apt-get update
sudo apt-get install -y \
  git gnupg flex bison build-essential zip curl unzip \
  zlib1g-dev libc6-dev-i386 lib32z1-dev x11proto-core-dev \
  libx11-dev libgl1-mesa-dev libxml2-utils xsltproc fontconfig \
  python3 ccache bc libssl-dev libelf-dev lz4 rsync tmux gh repo

git --version
python3 --version
repo version
gh --version
```

If `gh` or `repo` is unavailable in your Ubuntu package sources, enable the
Universe repository and retry the installation:

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y universe
sudo apt-get update
sudo apt-get install -y gh repo
```

The Android tree supplies its compiler and JDK prebuilts; do not substitute
an arbitrary system Java version. The package list is the starting setup;
this unfinished bring-up may still expose additional host or source issues.

### 2. Authenticate GitHub and configure Git

Use `wulfnb` or another account granted access to this private repository:

```bash
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git --hostname github.com
gh auth status
gh repo view wulfnb/lisa-android17-bringup
```

On a server without a browser, open the URL shown by `gh auth login` on your
own computer and enter the displayed one-time code. `gh auth setup-git`
allows Git and Repo to use that authentication for HTTPS GitHub requests.
See the [login documentation](https://cli.github.com/manual/gh_auth_login)
and [Git credential setup](https://cli.github.com/manual/gh_auth_setup-git).

If Git identity is not already configured, replace these example values with
your own before running:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Access to every referenced upstream repository is also required. This
snapshot is not an offline mirror and cannot guarantee upstream availability.

### 3. Keep the remote session running

For an SSH session, start tmux before the long sync and build:

```bash
tmux new -s lisa-build
```

Detach with **Ctrl+B**, then **D**. After reconnecting, resume with:

```bash
tmux attach -t lisa-build
```

### 4. Clone the patch repository

```bash
git clone https://github.com/wulfnb/lisa-android17-bringup.git ~/lisa-bringup
cd ~/lisa-bringup
git rev-parse HEAD
```

Keep this clone separate from the Android checkout. Record its commit so you
know which patch snapshot was used. Do not pull a newer snapshot halfway
through restoring or building the source.

### 5. Download the full Android source

Use a **new, empty `~/android` directory** for these instructions. If that
path already contains another checkout, choose a different directory and
replace `~/android` consistently in the remaining steps.

```bash
mkdir -p ~/android
cd ~/android

repo init \
  -u https://github.com/wulfnb/lisa-android17-bringup.git \
  -b "$(git -C ~/lisa-bringup rev-parse HEAD)" \
  --manifest-upstream-branch=refs/heads/main \
  -m manifests/default.xml

repo sync -c -j4 --no-clone-bundle --no-tags
```

The `-b` argument pins the manifest repository to the same commit as your
patch clone, even if `main` advances later. The pinned manifest includes the
lisa/common device trees, correct lisa
kernel, Xiaomi hardware, Dolby, vendor dependencies, camera and firmware.
Do not clone additional repositories over those paths.

If the download is interrupted or rate-limited, retry without deleting
`.repo`. Use a lower sync parallelism to diagnose persistent failures:

```bash
cd ~/android
repo sync -c -j1 --fail-fast --no-clone-bundle --no-tags
```

### 6. Check and apply all saved fixes

Only continue after `repo sync` succeeds:

```bash
cd ~/lisa-bringup

# Check only: this does not modify the Android source.
python3 scripts/apply.py --source ~/android

# Apply pending source patches and the hash-checked WFD binary fixup.
python3 scripts/apply.py --source ~/android --apply

# Verify that the snapshot is now recognized as already applied.
python3 scripts/apply.py --source ~/android
```

If there is a patch conflict or unexpected binary hash, stop and investigate
the revision mismatch. Do not bypass the checks or reset existing work.

### 7. Build on the new machine

Use log `01` for the first attempt on this new machine. The source patches,
including the Soong memory-setting pass-through, must already be applied.

```bash
cd ~/android
export GOGC=20 GOMEMLIMIT=22GiB
source build/envsetup.sh
set -o pipefail

lunch lineage_lisa-trunk_staging-userdebug &&
m evolution -j4 2>&1 | tee build_lisa_01.log
```

Start with four compile jobs. If the host has enough memory, use `-j6` in
place of `-j4`; more jobs can increase peak memory usage. These Go settings
are the existing 32 GB host's workaround, not tuning for every remote host.
Evolution envsetup configures ccache automatically when available.

### 8. Monitor and inspect failures

From another terminal, without starting a second build:

```bash
free -h
df -h ~/android
du -sh ~/android/out
ccache -s
tail -f ~/android/build_lisa_01.log
```

After a failure, inspect the actual errors rather than only the final Ninja
summary. Replace the log number with your current attempt:

```bash
cd ~/android
tail -180 build_lisa_01.log
grep -nE 'FAILED:|error:|fatal:|kati failed|ninja failed' build_lisa_01.log | tail -80
less -R out/siso_output
```

Siso may also write `out/siso_failed_commands.sh`. It contains executable
retry commands: inspect it before deciding whether to run it. Do not delete
`out/` for a normal source fix; the next build reuses completed work. Stop a
foreground build with **Ctrl+C** and wait for it to exit before retrying.

### 9. Retry incrementally and save new fixes

After fixing the specific error, repeat the environment setup and build
command with a new log number, for example `build_lisa_02.log`. In a fresh
shell you must source envsetup and run lunch again before `m` is available.

Use [Save the next fix](#save-the-next-fix) to capture and push a new snapshot
after documenting the change and its validation. Local compilation outputs
are not part of that source snapshot.

## Build manually

For the **existing original checkout**, the next log number after the last
inspected build is 12. This is the requested six-job example; keep `-j4` if
memory pressure is high. Run only after any previous build has stopped.

```bash
cd ~/android
export GOGC=20 GOMEMLIMIT=22GiB
source build/envsetup.sh
set -o pipefail
lunch lineage_lisa-trunk_staging-userdebug &&
m evolution -j6 2>&1 | tee build_lisa_12.log
```

The Soong patch forwards the Go memory controls through its otherwise empty
environment. The 22 GiB value is a soft Go runtime target, not a hard RSS
limit. `-j4` or `-j6` controls compile scheduling, not the single analysis process.
Watch memory, swap and disk space. Do not run concurrent builds in one tree.

## Scope and licensing

See [LICENSE-NOTICE.md](LICENSE-NOTICE.md). This repository is private by
choice, not a claim that private storage grants additional rights. It contains
no firmware, ROM ZIPs, Google Apps, proprietary shared libraries, signing
keys, credentials, or binary Git patches. Proprietary dependencies are
referenced by upstream location and hash. Their terms still apply.

The WFD runtime behavior, hardware operation and first boot remain untested.
