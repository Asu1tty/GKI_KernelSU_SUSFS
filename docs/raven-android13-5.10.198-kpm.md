# Raven Android 13 GKI 5.10.198 with SukiSU, KPM, and AVC log spoofing

This is the verified build recipe for Pixel 6 Pro (`raven`) running
`AP2A.240605.024` and the SukiSU v4.3.0-r1 manager APK with version code
41140. The successful Action run is
[41954226200](https://github.com/Asu1tty/GKI_KernelSU_SUSFS/actions/runs/41954226200)
at build-script commit `c2588b4`. On 2026-11-05, the resulting kernel booted
to Android (`sys.boot_completed=1`), and the manager displayed KPM.

## Current 41150 / v4.3.0-r2 target

The current target uses the same verified GKI and SukiSU builtin commits, but
aligns the kernel with the
[SukiSU v4.3.0-r2 manager APK](https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases/download/v4.3.0-r2/SukiSU_v4.3.0-r2_41150-release.apk)
(version code `41150`) and enables AVC log spoofing.

| Input | Value |
| --- | --- |
| `android_version` | `android13` |
| `kernel_version` | `5.10` |
| `sub_level` | `198` |
| `os_patch_level` | `2024-01` |
| `kernelsu_version` | `Stable(标准)` |
| `kernelsu_commit` | `1cfa57340590971cba7521ed536da8ebbedc5f0a` |
| `susfs_commit` | `8a120081f2739bc0e4b1f6a389d8236f22944acc` |
| `ksu_version_code` | `41150` |
| `use_kpm` | `true` |
| `avc_log_spoof` | `true` |
| `use_zram`, `BBG`, `supp_op`, `set_defbbr` | `false` |
| `make_release`, `send_telegram` | `false` for a test build |

The build injects the 41150 manager's `avc_spoof` feature id (`10003`) into the
builtin branch and maps it to SUSFS's native AVC audit hook. The SUSFS jump
label is enabled before userspace starts, so the 41150 manager reports the
feature as enabled and can toggle it at runtime.

```bash
gh workflow run kernel-build.yml \
  -R Asu1tty/GKI_KernelSU_SUSFS \
  --ref codex/full-gki-matrix \
  -f android_version=android13 -f kernel_version=5.10 \
  -f sub_level=198 -f os_patch_level=2024-01 \
  -f 'kernelsu_version=Stable(标准)' \
  -f kernelsu_commit=1cfa57340590971cba7521ed536da8ebbedc5f0a \
  -f susfs_commit=8a120081f2739bc0e4b1f6a389d8236f22944acc \
  -f ksu_version_code=41150 -f use_kpm=true -f avc_log_spoof=true \
  -f use_zram=false -f BBG=false -f supp_op=false \
  -f set_defbbr=false -f make_release=false -f send_telegram=false
```

Action [42819486819](https://github.com/Asu1tty/GKI_KernelSU_SUSFS/actions/runs/42819486819)
succeeded on 2026-11-10 at build-script commit `7f3f6ff`. The downloaded
AnyKernel3 package passed its ZIP integrity check. Its embedded kernel config
contains `CONFIG_KSU=y`, `CONFIG_KPM=y`, and `CONFIG_KSU_SUSFS=y`; the Image
contains the AVC spoofing default-enable message, and an independent
`kptools-linux -l -i Image` check reports `patched=true`, `version=0xe00`,
`config=android,release`, and `arch=arm64`.

- AnyKernel3 ZIP SHA-256: `1ef767719f8a1c448bd44e5e5b48608815b9485e14b8d96331656d78fe1bc57a`
- Image SHA-256: `45b61aaedefac507505786c6240814d3d4c344771c22fd1435b0d0c37272c3d4`

The build also isolates the feature subsystem's forced-value bitmaps from
the extension subsystem in the builtin unity build. The 41150 feature ID
expands `KSU_FEATURE_MAX`; leaving both subsystems' static bitmaps under the
same names caused conflicting array declarations during compilation.

This target still needs a device boot check. The 41140 run below remains the
latest device-verified result.

## Build

Run `Kernel Build` on branch `codex/android13-5.10.198-sukisu-41140` in
`Asu1tty/GKI_KernelSU_SUSFS` with these inputs. Keep the commit hashes and
version code explicit; workflow defaults are for other builds.

| Input | Value |
| --- | --- |
| `android_version` | `android13` |
| `kernel_version` | `5.10` |
| `sub_level` | `198` |
| `os_patch_level` | `2024-01` |
| `kernelsu_version` | `Stable(标准)` |
| `kernelsu_commit` | `1cfa57340590971cba7521ed536da8ebbedc5f0a` |
| `susfs_commit` | `8a120081f2739bc0e4b1f6a389d8236f22944acc` |
| `ksu_version_code` | `41140` |
| `use_kpm` | `true` |
| `use_zram`, `BBG`, `supp_op`, `set_defbbr` | `false` |
| `make_release`, `send_telegram` | `false` for a test build |

With GitHub CLI:

```bash
gh workflow run kernel-build.yml \
  -R Asu1tty/GKI_KernelSU_SUSFS \
  --ref codex/android13-5.10.198-sukisu-41140 \
  -f android_version=android13 -f kernel_version=5.10 \
  -f sub_level=198 -f os_patch_level=2024-01 \
  -f 'kernelsu_version=Stable(标准)' \
  -f kernelsu_commit=1cfa57340590971cba7521ed536da8ebbedc5f0a \
  -f susfs_commit=8a120081f2739bc0e4b1f6a389d8236f22944acc \
  -f ksu_version_code=41140 -f use_kpm=true \
  -f use_zram=false -f BBG=false -f supp_op=false \
  -f set_defbbr=false -f make_release=false -f send_telegram=false
```

## Accept the artifact

The build script checks `CONFIG_KPM=y`, downloads pinned `kptools-linux` and
the complete `kpimg`, patches `Image`, verifies `patched=true` and
`version=0xe00`, and regenerates `Image.lz4` in legacy format. Inspect the
Action log for `CONFIG_KPM=y`, `kpimg: ...,0x47df0`, `kpimg version: e00`, and
`avc_log_spoof: enabled by default`.
An `0x10` payload or `kpimg version: 0` is invalid even if the workflow says
it succeeded.

Check the uploaded file independently:

```bash
gh run download RUN_ID -R Asu1tty/GKI_KernelSU_SUSFS \
  -n kernel-android13-5.10-198 -D ./artifact
unzip -p ./artifact/android13-5.10.198-2024-01-AnyKernel3.zip Image > ./Image
curl -fLSs \
  https://raw.githubusercontent.com/SukiSU-Ultra/SukiSU_patch/eec45788c9a115e5498040298133336d6b6071dd/kpm/kptools-linux \
  -o ./kptools-linux
chmod +x ./kptools-linux
./kptools-linux -l -i ./Image
```

Expected fields: `patched=true`, `[kpimg]`, `version=0xe00`,
`config=android,release`, `arch=arm64`. The known successful run's `Image`
SHA-256 is `7cbaef3779261136777fa9168006a3f5fa77a24656e1a98979a896b708f33351`.
Rebuilds can have a different checksum because the kernel banner includes the
build time.

## Device check

The tested raven procedure replaces only the kernel in the **matching
factory `boot.img`** from `image-raven-ap2a.240605.024.zip`, then flashes the
repacked boot partition. Do not flash the generic Action `boot.img` as a
substitute for the device-specific factory boot image. Keep the original boot
image available for recovery.

After boot, check `adb shell getprop sys.boot_completed` is `1`, compare
`adb shell uname -a` with the new Action's kernel banner, and confirm KPM in
the SukiSU manager. The successful run reached Android and the manager issued
KPM list requests. Static artifact checks establish that the payload is
present; the device check establishes that this build boots on raven.

If a future build loops at the Google logo, start ADB capture before the
flash. After restoring the factory boot image, collect
`adb shell dumpsys dropbox --print SYSTEM_LAST_KMSG`. If the device never
reaches ADB or is manually sent to bootloader during the loop, there may be
no kernel stack for that attempt. Keep device logs outside this repository.

## Why the previous build failed

Run [41948739427](https://github.com/Asu1tty/GKI_KernelSU_SUSFS/actions/runs/41948739427)
used `kpm/patch_linux`. Its log reported `kpimg` size `0x10` and version `0`.
The uploaded `Image` reported `patched=false` with `kptools -l -i`, and raven
rebooted at the Google logo. The wrapper's source embeds a `kpimg` resource;
the downloaded wrapper contained only a 16-byte placeholder. The repaired
builder invokes `kptools-linux` with the full pinned `kpimg` and rejects an
unrecognized patched image.
