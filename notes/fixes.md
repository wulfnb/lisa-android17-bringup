# Snapshot contents and evidence

| Repository | Change | Validation |
| --- | --- | --- |
| device/xiaomi/lisa | Declare modern lunch choice; retain firmware BoardConfig integration | Lunch and later compilation passed |
| device/xiaomi/sm8350-common | WFD V4-to-V5 extraction fixup and fixed blob hash | ELF dependency inspected; imported type headers compared; Soong passed |
| vendor/xiaomi/sm8350-common | Regenerated libwfdservice build dependency | Soong passed; binary reproduced by separate recipe |
| external/XMP-Toolkit-SDK | Vendor variants for xmp_toolkit_sdk and zuid_md5 | Earlier missing-variant errors passed |
| external/google-highway | Vendor variant for libhwy | Earlier missing-variant errors passed |
| external/skia | Vendor variant for libskia_skcms | Earlier missing-variant errors passed |
| build/soong | Forward opt-in GOGC and GOMEMLIMIT | Generated command verified; multiple analysis passes completed |
| hardware/xiaomi | Use existing platform Megvii compatibility modules | Stub function table compared; duplicate-module error passed |
| vendor/xiaomi/firmware-lisa | Supply only firmware absent from integrated vendor radio directory | 17 matching SHA-256 comparisons; 17 unique AB partitions; later build reached compilation |
| vendor/qcom/opensource/display | Include mutex directly in device_impl.h | Diff check passed; compilation not retried by assistant |
| bootable/recovery | Include algorithm directly in PublicVolume.cpp for std::replace | Diff check passed; compilation not retried |
| device/xiaomi/sm8350-common | Move inline `LocIpc::getLocIpcQrtrRecver(listener, service, instance)` out of `LocIpc.h` into `LocIpc.cpp`, so its `unique_ptr<LocIpcRecver>` destructor is only instantiated once `LocIpcRecver` is a complete type | Failed compile step re-run standalone via `siso_failed_commands.sh`; exits 0 with no diagnostics. Full `m evolution` not retried by the assistant |
| hardware/qcom/sm7250/gps | Same `LocIpc.h`/`LocIpc.cpp` split (byte-identical upstream file to sm8350-common's) | Not build-verified; `sm7250` is outside the `lisa` (sm8350) target's dependency graph |
| hardware/qcom/sm8150/gps | Same `LocIpc.h`/`LocIpc.cpp` split (byte-identical upstream file to sm8350-common's) | Not build-verified; `sm8150` is outside the `lisa` (sm8350) target's dependency graph |
| system/vold | Include algorithm directly in model/PublicVolume.cpp for std::replace (same missing include as the bootable/recovery copy) | Not build-verified; no generated Soong/Siso command exists yet for this target to re-run standalone |
| hardware/qcom-caf/sm8450/display | Include mutex directly in services/config/src/device_impl.h (same missing include as vendor/qcom/opensource/display's copy) | Not build-verified; not part of the `lisa` target's dependency graph |
| hardware/qcom-caf/sm8550/display | Include mutex directly in services/config/src/device_impl.h | Not build-verified; not part of the `lisa` target's dependency graph |
| hardware/qcom-caf/sm8650/display | Include mutex directly in services/config/src/device_impl.h | Not build-verified; not part of the `lisa` target's dependency graph |
| hardware/qcom-caf/sm8450-6.6/display/hal | Include mutex directly in services/config/src/device_impl.h | Not build-verified; not part of the `lisa` target's dependency graph |
| hardware/qcom-caf/sm8750/display/hal | Include mutex directly in services/config/src/device_impl.h | Not build-verified; not part of the `lisa` target's dependency graph |
| hardware/qcom-caf/sm8850/display/hal | Include mutex directly in services/config/src/device_impl.h | Not build-verified; not part of the `lisa` target's dependency graph |
| device/xiaomi/sm8350-common | Declare missing `type vendor_sysfs_usb_c, sysfs_type, fs_type;` in sepolicy/vendor/batterysecret.te | Regenerated vendor_sepolicy.conf via its rule_builder script, then re-ran the failed checkpolicy step through `siso_failed_commands.sh`: exits 0, `unknown type` error gone, only the pre-existing unrelated hal_vm_capabilities_default neverallow warning remains |

The libjxl and libdng_sdk vendor variants are already in the pinned upstream
source, so no additional source patch is required for them.

For subsequent fixes, record the failing module/error, diagnosis, exact
change, build or test result, and remaining runtime uncertainty here or in a
new dated note. Capture and commit the updated snapshot with each fix.

`bringup-history.md` preserves the earlier chronological notes. Filenames for
old individual patch exports mentioned there are historical; the authoritative
current patch mapping is `snapshot.json` and `patches/`.

## Build #11: recovery header fix

The user's incremental retry scheduled 137,621 actions, compared with 212,206
in build #10. Its displayed 4% is progress through that retry's work, not a
loss of the previously completed compilation. It completed 6,406 more actions
before one failure. The UWB license-metadata line preceding the summary is
not the failed command.

The actual failed target was libvolume_manager's recovery arm64
PublicVolume.o. PublicVolume.cpp:65 calls std::replace but did not directly
include <algorithm>. Added that header. No build, failed-command retry, clean
or source sync was run by the assistant. The user will validate with the next
incremental build; the next log number is 12.

## Build #11 (retry): GPS utils LocIpc incomplete-type fix

The user re-ran the same `build_lisa_11.log` command after the recovery
header fix above. It progressed to 4,353 done actions and failed on
`device/xiaomi/sm8350-common/gps/utils/LocIpc.o`:

```
prebuilts/clang/host/linux-x86/clang-r584948b/include/c++/v1/__memory/unique_ptr.h:75:19:
error: invalid application of 'sizeof' to an incomplete type 'loc_util::LocIpcRecver'
```

`LocIpc.h` forward-declares `class LocIpcRecver;` at line 46 and only defines
it fully at line 175. Between those, an inline 3-argument
`LocIpc::getLocIpcQrtrRecver` (lines 114-119) returns a
`unique_ptr<LocIpcRecver>` built from a call to the 4-argument overload. The
`clang-r584948b` prebuilt now eagerly instantiates that returned
`unique_ptr`'s destructor at the point of the inline function body, before
`LocIpcRecver` is complete, tripping libc++'s `default_delete` completeness
`static_assert`. Older/looser clang releases deferred this and never caught
it; nothing else about the surrounding code changed.

Fix: declare the 3-argument overload in the header (no body) and move its
one-line body to `LocIpc.cpp`, next to the existing 4-argument definition,
where the full `LocIpcRecver` class is already in scope. Verified by
re-running only the failed step through `out/siso_failed_commands.sh`: exit
0, no diagnostics. The assistant did not restart the full `m evolution`.

`hardware/qcom/sm7250/gps/utils/LocIpc.h` and
`hardware/qcom/sm8150/gps/utils/LocIpc.h` are byte-identical copies of the
same vendored file (same line numbers for the forward declaration, the inline
overload, and the full definition). Applied the identical split there so a
future `sm7250` or `sm8150` bring-up on this toolchain doesn't hit the same
error; neither is part of the `lisa` build graph, so neither was compiled to
confirm. Next log number is still 12.

## Sweep for the same missing-include class as the two earlier one-off fixes

The user asked whether the `vendor/qcom/opensource/display` (`<mutex>`) and
`bootable/recovery` (`<algorithm>`) fixes recorded above, made in an earlier
session, might also be needed in other repositories in this manifest that
just haven't been reached by a build yet. `find` for exact duplicate
filenames, followed by grep for the same standard-library usage without the
corresponding include, turned up two more affected sets:

- `system/vold/model/PublicVolume.cpp` calls `std::replace` at line 73 with
  no `<algorithm>` include, identical to the `bootable/recovery` copy of the
  same file. Unlike the display trees below, `system/vold` is a core system
  component that is definitely compiled for this build, not a bundled but
  unused chipset variant, so this is a likely near-term build blocker rather
  than a precaution. Added `#include <algorithm>` in the same position as the
  `bootable/recovery` fix.
- `services/config/src/device_impl.h` is duplicated across eight repos in
  this manifest. `vendor/qcom/opensource/commonsys/display`'s copy is a
  distinct, newer file revision that already includes both `<mutex>` and
  `<shared_mutex>` directly, so it needed no change. The other six —
  `hardware/qcom-caf/sm8450/display`, `hardware/qcom-caf/sm8550/display`,
  `hardware/qcom-caf/sm8650/display`, `hardware/qcom-caf/sm8450-6.6/display/hal`,
  `hardware/qcom-caf/sm8750/display/hal`, and
  `hardware/qcom-caf/sm8850/display/hal` — declare `std::mutex` and
  `std::recursive_mutex` members and include `<shared_mutex>` but not
  `<mutex>` directly, the same shape of bug as the already-fixed
  `vendor/qcom/opensource/display` copy (which has no `<shared_mutex>` use at
  all, so it is not proof `<shared_mutex>` transitively supplies `<mutex>` on
  this toolchain). Added `#include <mutex>` in the same position as the
  existing fix. None of these six chipset trees are reachable from the
  `lisa` (sm8350) lunch target, so none could be compiled to confirm.

No generated Siso/Soong command exists yet for any of these targets (the
build hasn't reached them), so unlike the GPS fix these could not be
re-verified with a standalone recompile; per this repository's convention
the assistant did not start `m` to reach them. `system/vold` in particular
is worth resolving before or during the very next attempted build.

## Build #12: sepolicy unknown type

The user's next incremental build (still logged as `build_lisa_11.log`)
progressed to 48,726 done actions over 1h33m before failing. The `FAILED:`
line sits well before the log's tail — the bionic/libc lines the user pasted
are unrelated in-flight parallel jobs still printing after Siso had already
stopped scheduling new work, not the failing step itself.

The actual failure was `checkpolicy` compiling `vendor_sepolicy.conf`:

```
device/xiaomi/sm8350-common/sepolicy/vendor/batterysecret.te:13:ERROR 'unknown type vendor_sysfs_usb_c' at token ';' on line 69771:
```

`batterysecret.te` references `vendor_sysfs_usb_c` inside its
`batterysecret_sysfs` type-set macro alongside three sibling types
(`vendor_sysfs_battery_supply`, `vendor_sysfs_usb_supply`,
`vendor_sysfs_usbpd_device`). Those three are declared in
`device/qcom/sepolicy_vndr/<chip>/generic/vendor/common/file.te`; lisa
(`lahaina`, sm8350) resolves through `SEPolicy.mk`'s `UM_5_4_FAMILY` branch
to the shared `legacy-um` variant of that file. A tree-wide search for
`vendor_sysfs_usb_c` found exactly one hit in the whole source tree — this
same usage — in every chip family's `sepolicy_vndr` copy, not just
`legacy-um`. It was never declared anywhere; not a version-skew gap, a plain
missing type.

Fix: declared `type vendor_sysfs_usb_c, sysfs_type, fs_type;` directly in
`batterysecret.te`, above its first use, following this device tree's own
existing convention of declaring a locally-needed type inline in the `.te`
file that uses it (see `hal_sensors_default.te`'s `vendor_sysfs_iio` and
`hal_fingerprint_default.te`'s `vendor_sysfs_udfps`). Deliberately not added
to the shared `device/qcom/sepolicy_vndr/legacy-um` repo, which would also
apply to every unrelated `kona`/`lito`/`bengal`/`msmnile`/`sdm845`/`sdm710`
device sharing that family.

No `genfscon`/`file_contexts` labeling rule exists for this type on any chip
family, unlike its three siblings (e.g. `vendor_sysfs_usb_supply` is labeled
in `legacy-um/generic/vendor/common/file_contexts`). The declaration alone
is enough to satisfy `checkpolicy`; at runtime, `batterysecret` simply won't
find any real file carrying this label until (if) a labeling rule is added,
so the `allow ... vendor_sysfs_usb_c:file rw_file_perms` grant is currently a
no-op rather than wrong. Unverified: which sysfs path a genfscon rule should
target, and whether batterysecret needs it at all on this device's hardware.

Verified past the level of the two previous include fixes: regenerated
`vendor_sepolicy.conf` by running its Soong rule_builder script directly
(`out/soong/rule_builder_scripts/52fb5220...sh`, which re-invokes `m4` over
the current `.te` sources), then re-ran the failing `checkpolicy` step via
`out/siso_failed_commands.sh`. Exit 0; the `unknown type` error is gone,
leaving only the pre-existing, unrelated `hal_vm_capabilities_default`
neverallow warning that was already present in the failing run's stderr.
Full `m evolution` was not restarted by the assistant.

| vendor/qcom/opensource/vibrator/aidl/VibratorSelector | Include memory directly in VibratorSelector.h for std::shared_ptr | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| bootable/recovery/volume_manager | Include vector directly in VolumeManager.h for std::vector | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| device/xiaomi/sm8350-common/gps/android/utils | Include mutex directly in battery_listener.cpp for std::mutex/std::lock_guard/std::unique_lock | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| hardware/qcom-caf/sm8350/audio/hal/audio_extn | Include mutex directly in battery_listener.cpp (byte-identical duplicate of the GPS copy, same missing include) | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| hardware/xiaomi/aidl/fingerprint | Include functional directly in Session.cpp for std::function/std::bind | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| vendor/qcom/opensource/audio-hal/st-hal | Declare dbg_trace_max_lab_reads extern in sound_trigger_hw.h instead of defining it directly (was defined per translation unit under the non-LINUX_ENABLED branch); added the one real definition to sound_trigger_hw.c | ld.lld duplicate-symbol error across 6 .o files in the same static link; full m evolution resumed after the fix and passed this step |
| vendor/qcom/opensource/data-ipa-cfg-mgr-legacy-um | Include vector directly in IPACM_OffloadManager.h for std::vector | Failed compile step re-run standalone via siso_failed_commands.sh; exits 0. Full m evolution resumed and passed this step |
| hardware/qcom-caf/wlan/qcwcn | Declare drv and bss extern in driver_cmd_nl80211_common.h instead of defining them directly (shared by 5 .c files); added the one real definition to driver_cmd_nl80211.c | ld.lld duplicate-symbol error for both drv and bss across driver_cmd_nl80211_mlo.o, _oem_data.o, _mon.o, _sr.o; full m evolution resumed after the fix and passed this step |

| kernel/xiaomi/lisa | drivers/staging/qca-wifi-host-cmn hif/src/ce/ce_main.c returned A_ERROR (a legacy A_STATUS enum value) from a function declared to return QDF_STATUS; replaced with the semantically equivalent QDF_STATUS_E_FAILURE | -Werror,-Wimplicit-enum-enum-cast; full m evolution resumed and passed this step, build reached completion |
| vendor/xiaomi/sm8350-common (libwfdservice.so) | AudioSystem::setDeviceConnectionState moved from libaudioclient into a newly-split libaudiobase on this platform; prebuilt's DT_NEEDED table never updated. Added libaudiobase via patchelf --add-needed plus matching extract-files.py/Android.bp entries | ld.lld unresolved-symbol error; declared signature confirmed to match the current platform header exactly (not an ABI break); full m evolution resumed and passed this step |
| vendor/xiaomi/sm8350-common (libwfdmmsrc_system.so) | Same libaudiobase gap as libwfdservice.so above. Additionally SurfaceComposerClient::createVirtualDisplay gained a uid_t ownerUid parameter upstream that this prebuilt does not call; no source to rebuild against, so allow_undefined_symbols: true was set for this one module (WFD/screen-mirroring runtime behavior through this path is therefore unverified, consistent with this repo's existing WFD caveat) | ld.lld unresolved-symbol errors (4 symbols: 3 resolved by the libaudiobase dependency, 1 left undefined); full m evolution resumed and passed this step, build reached completion (EvolutionX-17.0-20260923-lisa-12.2-Unofficial.zip, sha256-verified) |
