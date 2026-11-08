# Core workflow specifications for independent implementation

Use stable claims in [CONFIRMED_BEHAVIOR.md](CONFIRMED_BEHAVIOR.md). These are evidence-backed acceptance scenarios, not a claim that all listed changes are implemented. Historical vendor documentation defines the intended compatibility baseline; original-app runtime validation remains pending.

| Scenario | Initial state and actions | Expected behavior | Basis |
|---|---|---|---|
| Collapse sidebar | Visible sidebar; drag its edge left | Enter a hidden-sidebar state; retain current page | ARC-B001; exact threshold is an explicitly provisional Angle default |
| Sidebar while searching | Command bar open; click a sidebar item | Item remains interactable | ARC-B002; final focus behavior needs original-app observation |
| Hidden pinned traversal | Pinned section collapsed; traverse sidebar via keyboard | Do not focus hidden pinned rows | ARC-B003 |
| Commit folder name | Editing a folder title; click outside | Save the typed name | ARC-B004 |
| Section commands | Open command bar and invoke collapse/expand-pinned action | Change pinned-section visibility without mutating tab data | ARC-B005 |
| Cross-profile search | Two empty Spaces on separate profiles; switch while suggestions are open | Clear old profile suggestions before displaying new results | ARC-B006 and ARC-B010 |
| Restore pinned URL | Pin a synthetic page, navigate away, activate return-to-pinned control | Navigate to saved URL while retaining pin identity | ARC-B007; Linux control mapping is an Angle choice |
| Edit pinned URL | Edit saved URL through pin/Favorite context menu, restart | New saved URL survives restart | ARC-B008; no conclusion about Arc's serialization mechanism |
| Profile assignment | Create Spaces sharing one profile plus another separate profile | Group browsing storage by profile; keep Space organization independently selectable | ARC-B009/010; verify isolation in Angle's engine, not merely workspace JSON |
| Nested organization | Create nested folders and rename a pinned tab | Retain hierarchy and custom title independently of document navigation title | ARC-B011; traversal and persistence tests use original synthetic data |
| Read-only recovery | Supply copied supported sidebar JSON | Parse only recognized schema variants and export links without modifying input | ARC-S001/002; explicitly not a round-trip writer or credentials migration |

## Defaults and unresolved behavior

Historical Windows raster measurements are now available in [VISUAL.md](VISUAL.md). They do not establish universal/default dimensions; preserve explicit platform and scale uncertainty when selecting Angle values. Do not infer Arc animation timings from a still image. Keep chosen Linux shortcut mappings visible in implementation documentation; Ctrl substitutions do not prove Windows and macOS behavior is identical.

Test command handling while a page has focus, hidden rows, Unicode folder names, duplicate URLs, profile switches, restart and malformed synthetic workspace input. Runtime engine tests must use isolated owned data and keep the sandbox enabled. Do not implement Arc service calls, authentication bypass, sync, automatic archive, split view or Little Arc as part of these core scenarios.

A report can support part of issues #1–#5, but those original observation tasks remain open until their original-app acceptance criteria are met. Implementation PRs should cite the exact supported rows and document provisional choices.
