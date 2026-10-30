#!/usr/bin/env bash
# SPDX-License-Identifier: MPL-2.0
set -euo pipefail
browser_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
qt_sdk="${ARCREVERSE_QT_SDK:-$browser_root/.local-tools/Qt/6.11.3/gcc_64}"
args=(-S "$browser_root" -B "$browser_root/build" -G Ninja -DCMAKE_PREFIX_PATH="$qt_sdk" -DCMAKE_BUILD_TYPE=Debug)
if [[ -x "$browser_root/.local-tools/qt-tools/bin/ninja" ]]; then args+=(-DCMAKE_MAKE_PROGRAM="$browser_root/.local-tools/qt-tools/bin/ninja"); fi
if [[ -f "$browser_root/.local-tools/sysroot/usr/include/GL/gl.h" && -f /usr/lib64/libGL.so.1 ]]; then
 args+=(-DOPENGL_INCLUDE_DIR="$browser_root/.local-tools/sysroot/usr/include" -DOPENGL_GLX_INCLUDE_DIR="$browser_root/.local-tools/sysroot/usr/include" -DOPENGL_opengl_LIBRARY=/usr/lib64/libOpenGL.so.0 -DOPENGL_glx_LIBRARY=/usr/lib64/libGLX.so.0 -DOPENGL_gl_LIBRARY=/usr/lib64/libGL.so.1 -DOpenGL_GL_PREFERENCE=LEGACY)
fi
cmake "${args[@]}"
cmake --build "$browser_root/build" --parallel "${ARCREVERSE_BUILD_JOBS:-2}"
