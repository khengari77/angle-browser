# Preservation feasibility: initial static assessment

Reference: macOS Arc 1.170.0 / 89123, acquired October 29, 2026. This is an initial assessment, not a completed reconstruction. Linux is the first new native platform; macOS defines the reference experience and Windows remains a compatibility target.

## Evidence and findings

| ID | Observation | Evidence | Implication and limit |
| --- | --- | --- | --- |
| F01 | Main executable contains x86_64 and arm64 Mach-O slices | `evidence/macos-main-load-commands.json` | These are macOS executables, not Linux builds. |
| F02 | Main executable loads AppKit, SwiftUI, Security, CloudKit, CoreData and many other system frameworks | Same file; load-command offsets recorded per architecture | Native Linux support requires platform replacements. A load declaration does not prove a particular feature uses that library at runtime. |
| F03 | Main executable loads bundled ArcCore through `@executable_path/../Frameworks/ArcCore.framework/Versions/A/ArcCore` | Same file | An actual application-to-core binary dependency exists. Its public/private API boundary and stability remain unresolved. |
| F04 | ArcCore declares version 156.0.8078.48 | `evidence/macos-inventory.json`, ArcCore `Resources/Info.plist` | A declared framework version; not independently verified as an upstream Chromium source revision. |
| F05 | Copied bundle inventory contains 1,135 file/link records | `evidence/macos-inventory.json` | Hashes, relative paths and selected plist metadata are recorded. Extraction does not validate Apple signatures or reproduce all filesystem metadata. |
| F06 | Intel slice contains `StorableSidebar.json` and related resource/module strings | `evidence/workspace-string-seeds.json`, exact slice offsets | Useful seeds for workspace persistence tracing. Storage schema, actual path and serialization behavior are not established. |
| F07 | REA Ghidra adapter rejects universal Mach-O input | Local `artifacts/rea-arc-inspect.json` | Analyze a byte-identical thin slice; preserve original and slice hashes. This is a provider limitation, not an Arc defect. |

The inventory includes signature-related files and Mach-O signature commands. Their presence is not signature validation. The shipped credits are retained locally at `Contents/Resources/ARC_AboutWindow.bundle/Contents/Resources/Credits.html`; listing a dependency there is not proof that Arc-specific code is reusable.

## Component maintenance matrix

| Component | Current evidence | Maintenance assessment | Linux work |
| --- | --- | --- | --- |
| Native UI and workflows | Main executable, Apple load commands, packaged resources | Original maintainable source not established; behavior specification incomplete | Independently implement platform layer and preserve measured workflows; no redesign |
| ArcCore / engine integration | Bundled binary and direct load dependency | No verified source match, reproducible build, or stable replacement ABI yet | Establish engine boundary before selecting integration |
| ADK-specific behavior | ADK resource directory; broader private infrastructure described by vendor | Resource name alone does not identify executable ownership or callable interfaces | Trace function boundaries and determine replacement scope |
| Workspace persistence | Filename seeds plus 14 resolved workspace declarations and internal type-reference links | Model relationships are established by compiler metadata; serialization behavior and file samples remain unverified | Preserve the observed hierarchy; validate actual storage before implementing import/export |
| Account and cloud features | CloudKit load and bundled Firebase-related framework | Mandatory service dependencies and post-shutdown behavior unverified | Local operation is a requirement; replacement service design deferred |
| Credentials / desktop integration | Security, AppKit, IOKit and other platform imports | Feature-specific call paths unresolved | Linux keyring, desktop and accessibility adapters need design after interface tracing |
| Chromium updates | ArcCore version metadata | Swapping a binary is not a demonstrated upgrade path | Require buildable, maintained engine integration and regression validation |

## Decision

There is no demonstrated path yet to maintain the original app as an open-source browser or to run its existing macOS binaries natively on Linux. There is concrete evidence of a substantial Apple-specific dependency surface. Native Linux support will require platform implementation work; the scope of reusable Arc components remains unknown.

Continue reverse engineering the existing app before choosing a browser stack. Prioritize workspace serialization and the UI-to-ArcCore boundary. If original-component maintenance cannot be demonstrated, use independently authored implementations based on documented behavior, with source provenance recorded. Do not treat decompiler output as a recovered buildable source tree.

## Persistence research milestone

The [bounded persistence dossier](WORKSPACE_PERSISTENCE.md) now records workspace declarations, internal type links and candidate filename-reference locations. Read/write entry points and serialization dependencies remain unresolved. The next step is targeted analysis of the two declared function spans surrounding the candidates, followed by serialization tests against a synthetic original-app workspace. No production profile is needed for static tracing. A read-only exporter follows only after synthetic file samples validate the schema.

In parallel with future platform access, prepare macOS tests for startup with/without network, restart persistence, Space/Profile assignment, pins/folders, split views, keyboard focus, and archive/restore. No Mac is available now, so these are pending rather than passed. Preserve the same distinction for account/service dependencies and visual parity.

## Verification status

The small synthetic `add` function was analyzed successfully with REA/Ghidra 12.1.4 after permitting the local bridge socket. Provider identity and Evidence ID are recorded in `evidence/toolchain-verification.json`. Main Arc Intel-slice analysis exceeded the 330-second startup deadline; Objective-C type-encoding diagnostics were present and output was incomplete. No complete main-app function map or call-path reconstruction is claimed. A subsequent focused import with an increased deadline and sufficient available memory is needed before that milestone can pass.

The Intel slice of Arc’s shipped DockTilePlugIn completed Ghidra inspection successfully (identity and Evidence ID in the toolchain verification record). The standalone MCP probe also completed function analysis on the synthetic target. This validates the local analysis pipeline, not main-app behavioral fidelity. The registered REA server is now visible in the live client; a live session check confirmed it.

## Workspace declaration findings

The [workspace dossier](WORKSPACE_PERSISTENCE.md) records concrete sidebar, item and Space declarations with field offsets and type-reference evidence. This advances the model map beyond string searches. It does not yet identify serialization entry points or establish the on-disk schema.

## Main import recovery attempt

A new focused import allowed 900 seconds and disabled the Objective-C Type Metadata Analyzer that had emitted repeated type-encoding errors. It also timed out before REA exposed a completed inventory. The local evidence was exported and the session closed; [the recovery record](evidence/main-import-recovery.json) preserves the changed settings and incomplete coverage. No repeated unchanged import is scheduled. Targeted disassembly and compiler metadata are the supported evidence path for this machine until a more selective analysis profile is established.

## Persistent targeted analysis

The direct Ghidra workflow successfully saved the imported main executable, reopened the database, and analyzed the two selected spans. Bounded jump-target annotations expanded instruction/reference coverage without global auto-analysis. A function referencing `StorableSidebar.json` contains calls to JSON encoding and file writing; its role in normal persistence versus export/diagnostics remains unverified. See [the updated dossier](WORKSPACE_PERSISTENCE.md). Pseudocode remains unreliable: one result escaped its selected span and the other timed out. The persistent database and observed API references are usable starting points for the next pass.
