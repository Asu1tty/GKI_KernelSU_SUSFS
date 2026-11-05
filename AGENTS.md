# Notes for build agents

For the verified Pixel 6 Pro (raven) Android 13 GKI 5.10.198 build with
SukiSU manager version code 41140 and KPM, read
[`docs/raven-android13-5.10.198-kpm.md`](docs/raven-android13-5.10.198-kpm.md)
before changing or running the workflow.

The KPM build has two required parts: `CONFIG_KPM=y` in the compiled kernel
and injection of a complete `kpimg` into the final `Image`. The old
`kpm/patch_linux` wrapper injected a 16-byte placeholder; its Action run
reported success, but `kptools -l -i Image` reported `patched=false` and
the device rebooted at the Google logo. Use the pinned `kptools-linux` and
`kpimg` in `.github/workflows/scripts/config.py`, and keep the post-patch
`patched=true` check in `kernel_builder.py`.

For this configuration, preserve the exact input commits and version code
listed in the guide. Check the uploaded `Image` independently before
suggesting a flash. Do not commit device logs, serial numbers, boot images,
or private credentials to this public repository.
