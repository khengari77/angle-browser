# Sidebar and command-bar implementation notes

Basis: ARC-B001, ARC-B002 and ARC-B006 in [CONFIRMED_BEHAVIOR.md](CONFIRMED_BEHAVIOR.md). These are vendor-documented historical behaviors, not current original-app runtime observations.

Implemented in Angle:

- A 6-pixel edge handle resizes the sidebar between 180 and 360 logical pixels. Dragging below a proposed width of 120 pixels and releasing hides it without closing the active page. Ctrl+S reveals it with its prior width. Initial width remains 238. These dimensions, the release-triggered threshold and the Linux shortcut are provisional Angle defaults, not measurements of Arc. Width/visibility remain session state; no workspace schema change.
- The command popup is nonmodal, retains input focus on opening, and closes on Escape/outside press. Sidebar interaction is no longer blocked by a modal overlay. Exact click/focus equivalence remains untested against Arc.
- A current-profile change clears the command query and resets replace-current mode before activating the selected page. Search results already derive from the current profile; the old query is not retained across profile switches. Same-profile Space changes keep the query.
- Folder carets reflect the existing `expanded` state.

Deferred: ARC-B005 collapse/expand-pinned commands and ARC-B003 hidden-section traversal. Angle's model does not identify pinned-section affiliation for folder rows; it permits mixed folder children. Filtering all folders or nested temporary tabs would invent a section policy and could hide unrelated data. Add explicit section ownership and meaningful model/traversal tests before implementing these behaviors. ARC-B004 rename-on-blur is also outside this change.

Validation: `cmake --build build-reconstruction --parallel 2` passed, including QML compilation, and `ctest --test-dir build-reconstruction --output-on-failure` passed (one workspace suite). `qmllint` found no syntax errors; existing context-property/unqualified-access and QWindow `active` override warnings remain, so this is not a warning-clean lint result. No interactive scenario below was executed in this task. The required manual scenarios remain: resize/release-to-hide and Ctrl+S reveal while a page stays loaded; click a sidebar row with command popup open; switch profiles with a typed query; switch same-profile Spaces; expand/collapse folders and inspect caret. A successful rendering smoke run alone does not validate those interactions or establish Arc visual fidelity.

## Review regression validation

The resize coordinate mapping now targets `root.contentItem` (a QQuickItem), not the ApplicationWindow. `tests/qml/tst_sidebar.qml` sends press/move/release events to the real Main.qml handle and verifies width change, drag-to-hide, and Ctrl+S restoration of the retained width. This test reproduced the incompatible-argument TypeError before the fix and passes on Qt 6.11.3 after it. The stacked Favorite pointer-action test also passes. These isolated offscreen tests do not establish original Arc equivalence or validate every desktop backend.
