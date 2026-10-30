# Browser implementation status

The repository now contains a buildable C++/Qt Quick browsing prototype and the existing reverse-engineering tools. Original project code is MPL-2.0. The agreed first-alpha milestone is **not complete**: extension enablement fails its required engine gate, and visual parity has not been validated.

## Verified on this machine

- Builds with the isolated Qt 6.11.3 SDK and CMake/Ninja.
- Workspace tests cover restart persistence, folder cycles, profile selection isolation, pinned-tab closing, and format rejection. Additional corruption and folder-visibility tests are included.
- A temporary-profile smoke run loaded https://example.com with Chromium sandboxing left enabled.
- Rendering passed through native Wayland and X11/XWayland on the Fedora 42 host.
- Existing Python research tests pass.

## Prototype implementation

The C++ workspace service saves its own versioned state in SQLite transactions. It models Profiles, Spaces, Favorites, pinned and temporary tabs, folder hierarchy, selection, ordering, and profile assignments. The QML shell exposes basic navigation, a command bar, lazy page creation, light/dark appearance, folder operations, and profile/Space creation. These features still need broader interactive and visual validation.

The database is ArcReverse's format. Arc-data import is not implemented. No proprietary Arc engine, UI assets, executable code or decompiler output is bundled in the browser.

## Blocking engine result

Enabling a minimal MV3 extension crashes inside Qt WebEngine on this host. The failure reproduces:

- In the QML integration runner.
- In `tests/extension_probe.cpp`, an independent native program with no ArcReverse workspace or QML services.
- With both the Qt 6.11.3 and Qt 6.12.0 prebuilt SDKs.
- With content-script-only and action-popup extensions.
- On Wayland and X11 for Qt 6.11.3.

Installation succeeds; the native probe reports `isLoaded=true`, `isEnabled=false`, then crashes at the enable operation. These observations do not establish the precise upstream defect or prove that every environment is affected. Raw logs are retained locally under `artifacts/`.

Normal browsing keeps extension enablement unavailable to avoid this reproduced crash. `--engine-gate` and the native diagnostic remain explicit test paths. The full engine gate is red. Ubuntu CI is configured but has not been run remotely.

The user selected evaluating prebuilt CEF as the next engine investigation. Qt Quick remains a possible UI layer, subject to embedding feasibility. No CEF compatibility claims have been established yet.

## Build and run

Prerequisites: CMake 3.28+, C++20 compiler, Ninja, an OpenGL development package, and a Qt SDK with Core, Gui, Quick, Quick Controls, SQL, Test, Widgets and WebEngine. The local SDK also includes WebChannel, Positioning, ShaderTools and TaskTree. System Qt 6.9 is insufficient for the extension API used by the diagnostics.

```bash
scripts/build_browser.sh
build/arcreverse
ctest --test-dir build --output-on-failure
python3 -m unittest discover -s tests
```

Override `ARCREVERSE_QT_SDK` to use a compatible installed SDK. The default is `.local-tools/Qt/6.11.3/gcc_64`. The build wrapper recognizes the locally extracted Fedora graphics headers in `.local-tools/sysroot`; other hosts should install their normal development packages.

```bash
# A temporary browsing session that exits after loading a real page:
build/arcreverse --smoke

# Full required engine gate; currently reproduces the blocking failure:
python3 scripts/test_engine.py

# Independent native diagnostic, also currently failing:
build/extension_probe "$PWD/tests/extensions/content-probe"
```

The engine runner hosts a loopback-only fixture site, uses isolated browser data, and attempts a second process to check restart persistence. A first-phase crash means later extension and restart assertions have not passed. No test enables `--no-sandbox`.

## Delivery limits

Packaging scripts produce a local AppDir archive and support installation to a chosen user-local prefix. Packaging and installer validation are still in progress. Local development packages must not be described as the completed alpha or as portable/verified Ubuntu releases. Public distribution requires a checked dependency/attribution inventory.

Remaining milestone work includes a passing extension engine, close visual reproduction against recorded Arc references, download handling, broader browser/permission/crash-recovery tests, Qt Quick interface tests, and installation validation. Split view, automatic archiving, multiple windows, sync and AI remain deferred as agreed.

## Renamed checkout

CMake caches and old executable runtime search paths can retain the former ArcReverse directory. After moving the checkout, configure a fresh build directory with the current SDK path; do not reuse the old cache. Historical executables require the SDK runtime libraries and do not validate current source changes.
