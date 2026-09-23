# Lisa Android 17 WFD audio AIDL bring-up

## Evidence

- `libwfdservice.so` directly needs `android.media.audio.common.types-V4-cpp.so`.
  The generated prebuilt declaration was correct, not stale. No existing
  extraction fixup injected this dependency.
- The WFD system blobs are pinned under the `from dada` section of
  `device/xiaomi/sm8350-common/proprietary-files.txt`.
- Platform audio dependencies use V5. The prebuilt is already declared as
  `cc_prebuilt_library_shared`; suppressing a static variant would not correct
  the runtime library dependency or shared dependency closure.
- Inspected undefined dynamic symbols with readelf and c++filt. All ten
  directly imported audio-common classes have byte-identical generated C++
  headers between frozen V4 and V5, using the same local AIDL compiler:
  AudioDevice, AudioDeviceAddress, AudioDeviceDescription,
  AudioFormatDescription, AudioGainConfig, AudioIoFlags, AudioPort,
  AudioPortConfig, AudioPortDeviceExt, AudioPortExt.
- The imported AudioSystem::setDeviceConnectionState signature matches the
  current platform declaration.
- V5 adds enum constants, new types, and an AudioChannelLayout acnMask union
  alternative with int32_t payload. Existing tags remain unchanged. This is
  evidence for a targeted bring-up replacement, not proof of complete C++ ABI
  or WFD runtime compatibility. Test wireless display and audio after boot.

## Change

Added a source extraction `replace_needed` fixup, patched the checked-in ELF,
recorded both original and fixed SHA1 hashes, then regenerated Android.bp with
`./extract-files.py --regenerate_makefiles` in the common device directory.
Regeneration changed only the libwfdservice V4 dependency to V5.

Original SHA1: `af0e31f17ed997a5d8bad64cdad486be28cb9f07`

Fixed SHA1: `b8ac918ddd45ae2982b96fe19183b14b32257a5f`

The ELF differs by exactly the single ASCII byte `4` -> `5` in the library
name; file size and all other bytes are unchanged. Source and vendor binary
patches are saved beside this note and apply relative to their respective
repository roots. Previous vendor_available fixes remain intact.

## Validation

- readelf confirms V5 DT_NEEDED and no V4 DT_NEEDED for this blob.
- Device and vendor `git diff --check` pass.
- Build #4 was blocked by the execution sandbox's Unix socket restrictions.
- Build #5 was externally force-killed (reported by the user as
  gnome-settings-daemon). Its log contains memory stalls, no completed graph
  or new source error. Observed host usage approached 29 GiB RAM and 21 GiB
  swap. This attempt does not validate the AIDL fix.
- Build #6 retries with `GOGC=20 GOMEMLIMIT=22GiB` and `m evolution -j4`.
  A separate opt-in host patch in `build/soong/ui/build/soong.go` forwards
  those two settings to the primary builder, which otherwise runs under
  `env -i` and discards them. Patch: `soong-go-memory-tuning.patch`.
  The memory target is soft, not a hard process/RSS ceiling. See the
  [Go GC guide](https://go.dev/doc/gc-guide) for these controls.
  See `/home/wolverine/android/build_lisa_06.log` for the retry result.
- Build #6 completed Soong graph generation successfully in about 9 minutes:
  the audio AIDL conflict is resolved at build-graph level. Kati then rejected
  duplicate `libMegviiFacepp-0.5.2` modules in hardware/xiaomi/megvii and
  hardware/lineage/compat.
- Removed the old Xiaomi Megvii module declarations in favor of the platform
  compatibility modules. Compared the 27-entry mg_facepp function table:
  identical entries and ordering. Platform libmegface supplies a superset of
  the old empty Xiaomi library's symbols. Camera blobs remain unchanged.
  Saved patch: `xiaomi-use-platform-megvii.patch` (hardware/xiaomi root).
- Build #7 uses the same memory settings and four jobs to validate this next
  fix. Log: `/home/wolverine/android/build_lisa_07.log`.
- Build #7 passed Soong and module parsing, confirming the Megvii fix. Kati
  then rejected duplicate abl.img output rules from the standalone firmware
  repository and vendor/xiaomi/lisa's generated radio packaging rules.
- Both repositories contain exactly 17 firmware images, all byte-identical
  by SHA-256 comparison. Integrated vendor/lisa has SHA1-checked packaging
  and the AB partition list generated from proprietary-firmware.txt.
- Updated the standalone firmware Android.mk and BoardConfigVendor.mk to
  supply only image names absent from vendor/xiaomi/lisa/radio. No firmware
  binaries were changed. A Make check confirms 17 unique firmware partitions
  and zero remaining legacy duplicate images. Saved patch (including the
  earlier handoff's path correction): firmware-use-integrated-radio.patch.
- Build #8 retries with the same memory settings and four jobs.
  Log: `/home/wolverine/android/build_lisa_08.log`.
- No clean, repo sync, or unrelated hardware/Pixel changes were performed.

## Retrying on this 32 GiB host

User preference: do not launch builds or retry commands; the user runs them
in their own terminal. No build process remained at the latest check.

The user's build #10 reached 74,455 completed actions (about 35%) before two
arm compilation failures in libdisplayconfig.qti: device_impl.cpp and
device_interface.cpp. Both include device_impl.h, which declares std::mutex
without including <mutex>. Added that direct include and saved
displayconfig-include-mutex.patch relative to vendor/qcom/opensource/display.
Diff whitespace validation passes; compilation has NOT been retried, per the
user's request. The other inheritance diagnostics in device_impl.cpp may be
secondary to the missing type and should be reassessed after this fix.
Next user-run full build log: build_lisa_11.log. Preserve incremental output.

Keep the Go environment forwarding patch applied when using these settings.
Choose a new log number for each attempt.

```bash
cd /home/wolverine/android
export GOGC=20 GOMEMLIMIT=22GiB
source build/envsetup.sh
lunch lineage_lisa-trunk_staging-userdebug
set -o pipefail
m evolution -j4 2>&1 | tee build_lisa_NEXT.log
```

`-j4` limits the compile scheduler; it does not directly bound the single
Soong analysis process. Keep watching memory and swap during analysis.



## libaudiobase split breaks two more WFD prebuilts (fresh-machine build)

### Evidence

- `frameworks/av/media/libaudioclient/Android.bp` splits `AudioSystem.cpp`
  (and its declared methods: `setDeviceConnectionState`, `setParameters`,
  `addErrorCallback`, `removeErrorCallback`) out of `libaudioclient` into a
  new `libaudiobase` module on this platform. Both WFD prebuilts still only
  declare `libaudioclient` as a dependency and their ELF `DT_NEEDED` tables
  were never updated for the split.
- `libwfdservice.so` needed only the added dependency; its declared
  `AudioSystem::setDeviceConnectionState` signature already matches the
  current platform header exactly.
- `libwfdmmsrc_system.so` needed the same added dependency, plus one symbol
  that cannot be fixed: `SurfaceComposerClient::createVirtualDisplay` gained a
  `uid_t ownerUid` parameter upstream since this blob was compiled. No source
  is available to rebuild the blob against the new signature, so that one
  symbol is left undefined via `allow_undefined_symbols: true`. WFD/screen
  mirroring through this code path may fail or crash at runtime; everything
  else in the module is unaffected. Consistent with this repo's existing
  caveat that WFD runtime behavior is unverified.

### Change

Patched both prebuilts directly:

```bash
prebuilts/extract-tools/linux-x86/bin/patchelf-0_18 --add-needed libaudiobase.so \
    vendor/xiaomi/sm8350-common/proprietary/system_ext/lib64/libwfdservice.so
prebuilts/extract-tools/linux-x86/bin/patchelf-0_18 --add-needed libaudiobase.so \
    vendor/xiaomi/sm8350-common/proprietary/system_ext/lib64/libwfdmmsrc_system.so
```

Recorded the resulting fixed hashes in `device/xiaomi/sm8350-common/proprietary-files.txt`
and the `add_needed` calls in `extract-files.py`, and added `libaudiobase`
(plus `allow_undefined_symbols` for the second module) to the generated
`vendor/xiaomi/sm8350-common/Android.bp` by hand.

**Not captured in `binary_fixups`.** Unlike the existing `libwfdservice.so`
V4→V5 fixup, `patchelf --add-needed` is not a same-length byte substitution —
it grows the file (observed: libwfdservice.so 303216 → 371713 bytes,
libwfdmmsrc_system.so 151520 → 217401 bytes) via patchelf-0_18's own
padding/relocation behavior. `scripts/capture.py`'s binary recipe format
(`original.replace(from, to)`) cannot express that, and `scripts/apply.py`
would silently apply only the old V4→V5 recipe and skip the `libaudiobase`
fix with no error if the stale recipe were left in place. The existing
`libwfdservice.so` recipe in `binary-fixups.json`/`snapshot.json` has been
removed rather than left incorrect. **A fresh checkout must re-run the two
`patchelf --add-needed` commands above by hand** (after `repo sync`, before
building) until this is captured a better way — for example, teaching
`capture.py` to record a rebuild recipe (base hash + shell command) instead
of a text substitution, or getting `extract-files.py --regenerate_makefiles`
working again (it currently exits silently after "Parsing
proprietary-files.txt" without regenerating anything or reporting why).

Final hashes:
- `libwfdservice.so`: `af0e31f1...` → `95dad874ea44b508dc9379ca30b24089fcebda3c`
- `libwfdmmsrc_system.so`: `0cc97095...` → `01f6bfd5c0d25c91321c7880c3354347dee40cbb`
