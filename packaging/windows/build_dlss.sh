#!/usr/bin/env bash
# Builds bbport_dlss.dll (gpu/dlss_bridge, the only code that uses the NVIDIA DLSS SDK) with
# MSVC and puts it with NVIDIA's nvngx_dlss.dll (Super Resolution) and nvngx_dlssg.dll (Frame
# Generation) next to out/bb-probe.exe; package.sh ships them.
# Needs Visual Studio 2022 or 2026 (Build Tools) and a checkout of https://github.com/NVIDIA/DLSS:
#   DLSS_SDK_ROOT=F:/sdk/DLSS bash packaging/windows/build_dlss.sh
set -euo pipefail
cd -- "$(dirname -- "$0")/../.."
sdk=${DLSS_SDK_ROOT:?Set DLSS_SDK_ROOT to a checkout of github.com/NVIDIA/DLSS}
cmake=${CMAKE_EXE:-cmake}
# MSYS2 rewrites cmake's vswhere query "[17.0,18.0)" and then no Visual Studio is found.
export MSYS2_ARG_CONV_EXCL='*'
if [[ -z ${CMAKE_GENERATOR:-} ]]; then
    vswhere="/c/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe"
    ver=""
    if [[ -f $vswhere ]]; then
        ver=$("$vswhere" -latest -prerelease -products '*' \
            -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 \
            -property catalog_productLineVersion | tr -d '\r' || true)
    fi
    # catalog_productLineVersion is the year on VS 2022 ("2022") and the major on VS 2026 ("18").
    case $ver in
        18|2026) CMAKE_GENERATOR="Visual Studio 18 2026" ;;
        17|2022) CMAKE_GENERATOR="Visual Studio 17 2022" ;;
        "") echo "vswhere did not report a Visual Studio with the C++ tools" >&2; exit 1 ;;
        *) echo "Unsupported Visual Studio product line: $ver" >&2; exit 1 ;;
    esac
fi
echo "DLSS bridge generator: $CMAKE_GENERATOR"
# Only the Vulkan headers: MSYS2's C headers must not reach MSVC.
# MINGW_PREFIX is /clang64 in the CLANG64 shell, including CI where MSYS2 is not at C:\msys64.
prefix=${MINGW_PREFIX:-/clang64}
[[ -d $prefix/include/vulkan ]] || { echo "Vulkan headers not in $prefix (use the CLANG64 shell)" >&2; exit 1; }
rm -rf out/vkinclude && mkdir -p out/vkinclude
cp -r "$prefix/include/vulkan" "$prefix/include/vk_video" out/vkinclude/
"$cmake" -S gpu/dlss_bridge -B out/dlss-bridge -G "$CMAKE_GENERATOR" -A x64 \
    -DDLSS_SDK_ROOT="$(cygpath -m "$sdk")" -DVULKAN_INCLUDE="$(cygpath -m "$PWD/out/vkinclude")"
"$cmake" --build out/dlss-bridge --config Release
cp out/dlss-bridge/Release/bbport_dlss.dll "$sdk/lib/Windows_x86_64/rel/nvngx_dlss.dll" \
    "$sdk/lib/Windows_x86_64/rel/nvngx_dlssg.dll" out/
cp "$sdk/LICENSE.txt" out/NVIDIA-DLSS-LICENSE.txt
echo "DLSS bridge ready: out/bbport_dlss.dll, out/nvngx_dlss.dll, out/nvngx_dlssg.dll"
