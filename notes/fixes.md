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
