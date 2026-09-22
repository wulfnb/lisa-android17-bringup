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
