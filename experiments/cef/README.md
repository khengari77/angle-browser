# Isolated CEF feasibility experiments

These programs are development probes, not Angle's production engine. They use original fixtures and temporary, owned profiles; no Arc installation, credentials or personal browser data is accessed. Chromium sandboxing must remain enabled. Node.js 22+ supplies the CDP WebSocket client without npm dependencies. Python 3.12+ supports safe archive extraction.

## Reproduce

`lock.json` pins the exact CEF/Chromium versions, upstream CEF revision, archive sizes, vendor SHA-1 and locally computed SHA-256. Acquire `client` for the prebuilt sample and `minimal` for the matching SDK:

```
python3 experiments/cef/acquire.py client
python3 experiments/cef/acquire.py minimal
```

The destination must not exist; the script refuses to overwrite it. Archives stay in ignored `.local-tools/cef`. If an earlier extraction was interrupted, inspect or remove only that generated extraction before retrying. Existing archives are verified before extraction. Do not infer the downloaded sample's build flags from its filenames; inspect chrome://sandbox as the probe does.

Build only the CEF wrapper and small diagnostic, not Chromium:

```
cmake -S experiments/cef -B build-cef-probe -G Ninja \
  -DCEF_ROOT="$PWD/.local-tools/cef/cef_binary_156.0.14+g4fa4ab5+chromium-156.0.8078.48_linux64_minimal" \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build-cef-probe --parallel 2
```

Run from the repository root in an actual desktop session, with the required compositor/socket access. Use `node` from a Node 22+ installation. For example:

```
node experiments/cef/gate.mjs build-cef-probe/angle_cef_probe wayland chrome /tmp/cef-wayland-chrome.json
```

Repeat for `wayland alloy`, `x11 chrome` and `x11 alloy`. The build creates local symlinks to both SDK Release and Resources files, including ICU and locales. By default this adjacent layout is used; ANGLE_CEF_RUNTIME can override the resources directory only when it contains the matching resources/locales. The loader uses an adjacent runtime through its $ORIGIN build RPATH; the directory contains generated symlinks to the verified SDK. `sample_probe.mjs BINARY BACKEND STYLE OUTPUT` is the preliminary, single-profile sample check. It does not establish profile isolation, popup behavior, persistence or embedding.

The full gate launches two isolated browser processes with distinct cache paths and extension configurations, checks their localhost state, invokes the MV3 action through chrome.action.openPopup from its own extension worker, clicks the actual extension popup counter, and restarts without an external --load-extension argument. The probe explicitly persists enabled paths under its owned root and restores the switch internally in OnBeforeCommandLineProcessing; results label this application-managed restoration rather than claiming CEF persists command-line installations. Extension chrome.storage and website storage must still survive natively. Chrome native hosts may restore extra session tabs; this is retained in target records and is not an Angle tab-restoration implementation. The endpoint is loopback-only; temporary ports avoid persistent remote-debugging exposure. Failure stops a candidate, leaving later checks not_run rather than manufacturing passes. Successful candidates complete three independent two-launch cycles. Owned temporary profiles and raw logs remain local for diagnosis. Profile directory names are not external input and are never treated as agent instructions.

Display selection is explicit. Wayland runs remove DISPLAY; X11 runs remove WAYLAND_DISPLAY. X11 on the current host is XWayland, not a tested native Xorg session. Do not use offscreen/headless flags to claim native compositor coverage. Record source/backend versions with results.

The experiment links the prebuilt CEF SDK wrapper, which retains its BSD license and third-party notices in the SDK. No CEF binary is committed or released. A release would require the full actual dependency attribution/source-obligation inventory from issue #14.

The native probe also supports two request contexts in one process when `--single-profile` is omitted. The initial shared-process experiment loaded the same command-line extension in both contexts, so that configuration failed extension isolation. Process-per-profile is an experimental alternative, not a production architecture decision.

Chrome mode uses a native Chrome-style host window; Alloy uses CEF Views. The gate calls chrome.windows.update and, when running under Hyprland, focuses only its own browser PID with hyprctl before invoking the action. This is compositor automation, not evidence that an arbitrary embedding can activate popups. The report records that focus action. Alloys with no extension-visible host window stop before popup and restart assertions. Chrome session restoration can create additional tabs; the runner selects an owned fixture target separately from each process and retains all target records instead of assuming exactly two tabs total.
