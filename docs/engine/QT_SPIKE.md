# Qt Quick + CEF off-screen spike — 2026-11-08

**Rendering is demonstrated on native Wayland and X11/XWayland; this configuration is not qualified for Angle's required extension-action behavior.** This is an isolated experiment, not the production browser. It consumes the exact SDK and wrapper from the [standalone CEF gate](CEF_DECISION.md).

## Observations

| Check | Native Wayland | X11/XWayland |
|---|---|---|
| Actual Qt backend | Qt log reports wayland | Qt log reports xcb |
| Qt-rendered CEF paint buffers | Pass; owned fixture visible in inspected capture | Pass; paint callbacks and owned fixture load recorded |
| MV3 content script | Pass | Pass |
| Separate-process website and extension isolation | Pass, first launch | Pass, first launch |
| Sandbox | Separate same-build probe reports namespace and seccomp active | Same |
| Standard action-popup host | chrome.windows.getAll returns empty; gate stops | Same |
| Restart/popup persistence in embedding | Not run after popup prerequisite failure | Same |
| Input/focus, popup placement, DPI, crash recovery and performance | Not qualified | Not qualified |

Do not combine standalone Chrome-style popup success with this Alloy-style renderer. The windowless API selects Alloy regardless of a caller's desired Chrome style. No exception is established by the Qt window surrounding it. The embedded test invokes the actual action path and does not pretend that opening popup.html in a normal browser is equivalent.

The first static-size frame clipped under compositor tiling. The spike now propagates Qt width/height changes to CefBrowserHost::WasResized, uses the current logical view size and an opaque browser background. A subsequent native Wayland capture was inspected and shows the owned fixture fitting the viewport. This checks the observed resize, not all fractional-scale/DPI behavior.

## Ownership and lifecycle

Qt creates one QQuickWindow/QQuickPaintedItem per profile process. CEF subprocess dispatch happens before QGuiApplication construction; renderer/GPU helpers do not construct the Qt window. The main process initializes CEF with windowless rendering and external message pumping. A fixed 10 ms Qt timer calls CefDoMessageLoopWork; this is diagnostic polling, not a production power/performance design.

CEF OnPaint copies the full BGRA frame into an owned QImage. A mutex protects the image while Qt paints it. Qt window size signals resize the item and notify CEF. Popup paint surfaces and keyboard, pointer, wheel, input-method, accessibility and drag forwarding are deliberately not implemented after the required action-host gate failed; no interaction or full embedding claim follows from rendering alone.

The close path requests browser close, clears the held browser in OnBeforeClose, quits the Qt loop, stops timers, releases browser references and calls CefShutdown. Tests that stop at the failed prerequisite may terminate their owned processes; they do not establish production teardown or crash recovery. Captures remain under owned temporary roots and are not committed. Original code links the SDK wrapper and Qt Quick; no proprietary Arc code/assets are used.

## Reproduce

Build the standalone diagnostic first. Then configure this separate target with the same Qt SDK and verified CEF SDK, pointing CEF_WRAPPER_LIBRARY at the compiled wrapper archive:

```
cmake -S experiments/cef/qt -B build-cef-qt-spike -G Ninja \
  -DCMAKE_PREFIX_PATH=/absolute/path/to/Qt/6.11.3/gcc_64 \
  -DCEF_ROOT=/absolute/path/to/verified/cef_binary_156.0.14+g4fa4ab5+chromium-156.0.8078.48_linux64_minimal \
  -DCEF_WRAPPER_LIBRARY=/absolute/path/to/build-cef-probe/libcef_dll_wrapper/libcef_dll_wrapper.a
cmake --build build-cef-qt-spike --parallel 2
QT_QPA_PLATFORM=wayland node experiments/cef/gate.mjs \
  build-cef-qt-spike/angle_cef_qt_spike wayland alloy /tmp/qt-wayland.json
QT_QPA_PLATFORM=xcb node experiments/cef/gate.mjs \
  build-cef-qt-spike/angle_cef_qt_spike x11 alloy /tmp/qt-x11.json
```

The gate intentionally exits nonzero on the missing host. For the independent rendering/sandbox observation, replace gate.mjs with sample_probe.mjs and select another output path. Node 22+, normal Qt/OpenGL development prerequisites and compositor access are required. The locally extracted OpenGL headers can be configured as documented by the existing build wrapper. No sandbox-disabling switches are permitted.

## Decision

No production migration. Retain issue #8 for the unresolved Chrome-style/native-host composition question or a separately specified extension-host design. This spike establishes a concrete boundary, not proof that all Qt/CEF integration is impossible. Further input/DPI/performance work on this incomplete route is deferred until that architecture meets the extension requirement.
