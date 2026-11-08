# QML interaction regressions

Run from the checkout root with the same Qt SDK used to build the prototype:

```
QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software \
  .local-tools/Qt/6.11.3/gcc_64/bin/qmltestrunner -input tests/qml -o -,txt
```

The tests instantiate the actual Main.qml with synthetic in-memory workspace and profile mocks, send pointer events, and check reachable menu actions. No Arc installation or personal profile is used. The WebEngineProfile is off the record; the saved-URL test substitutes an in-memory page so clicking the action does not navigate the network. Run outside a restricted execution sandbox if Chromium cannot initialize its own sandbox; do not disable Chromium sandboxing. SDK qmltestrunner may emit organization-settings and offscreen Vulkan/profile-deprecation warnings; these are distinct from input-handler TypeErrors and failed assertions. These tests supplement core workspace tests, not full browser integration coverage.
