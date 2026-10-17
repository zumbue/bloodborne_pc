"""Fail unless the player zip has the launcher, DLLs, FSR 4 assets and the DLSS bridge.

The Windows release asset is this zip (Bloodborne-Windows.zip). A package that
only contains the raw build outputs is the failure this check exists for.
"""
import sys
import zipfile

path = sys.argv[1]
with zipfile.ZipFile(path) as archive:
    names = {info.filename.replace("\\", "/") for info in archive.infolist()}
    probe = next(
        (info for info in archive.infolist()
         if info.filename.replace("\\", "/").endswith("bin/bb-probe.exe")),
        None,
    )

need = [
    "bbport-windows/Bloodborne.exe",
    "bbport-windows/Play Bloodborne.exe",
    "bbport-windows/bin/bb-probe.exe",
    "bbport-windows/bin/bb-gpu-capabilities.exe",
    "bbport-windows/bin/bbport_dlss.dll",
    "bbport-windows/bin/nvngx_dlss.dll",
    "bbport-windows/bin/nvngx_dlssg.dll",
    "bbport-windows/run.py",
    "bbport-windows/scripts/prepare.py",
    "bbport-windows/launcher/bloodborne.ico",
    "bbport-windows/fsr4_shaders/rcas.spv",
    "bbport-windows/fsr4_shaders/LICENSE-FSR4-v07.txt",
]
missing = [name for name in need if name not in names]
opt = [name for name in names if name.startswith("bbport-windows/fsr4_shaders/opt/")]
shaders = [name for name in names if name.startswith("bbport-windows/fsr4_shaders/")]
probe_size = probe.file_size if probe is not None else 0
print(f"{len(names)} files, {len(shaders)} fsr4, {len(opt)} optimized passes, probe {probe_size}")
# The unstripped bb-probe.exe from the build tree is about 190 MB. The player zip strips it.
if missing or len(opt) < 20 or len(shaders) < 200 or len(names) < 380 or probe_size == 0 or probe_size > 80 * 1024 * 1024:
    print("MISSING", missing)
    sys.exit(1)
