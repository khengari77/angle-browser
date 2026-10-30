# Workspace persistence dossier

Reference: Arc macOS 1.170.0 / 89123. This is a static declaration dossier, not a verified storage specification or recovered source tree. The original application was not executed.

## Confirmed compiler declarations

The Intel slice contains 11,556 Swift field descriptors. The parser scanned that section without record-layout errors; 3,087 descriptor names remain unresolved by its supported context rules. A selected set of 14 workspace-related declarations resolved successfully. See [the selected evidence](evidence/workspace-declarations.json) for artifact hash, descriptor addresses, field-record offsets, type bytes, symbolic reference targets, and unresolved-coverage information.

| Declaration | Observed properties or enum cases |
| --- | --- |
| `StorableSidebar.StorableSidebar` | `version`, `sidebar`, `sidebarSyncState`, `firebaseSyncState` |
| `SidebarDataStore.AppSidebarReducerState` | `containers` |
| `BaseModels.SidebarContainer` | `items`, `spaces`, `topAppsContainerIDs` |
| `BaseModels.SidebarContainerType` | `incognito`, `littleBrowser`, `standalone`, `global` |
| `BaseModels.SidebarItem` | `id`, `title`, `childrenIds`, `parentID`, `data`, `createdAt`, `isUnread`, `originatingDevice` |
| `BaseModels.SidebarItemData` | `tab`, `list`, `arcDocument`, `easel`, `itemContainer`, `welcomeToArc`, `splitView`, `sharedObject`, `instantLinks`, `tabGroup` |
| `BaseModels.SpaceModel` | `id`, `title`, `containerIDs`, `customInfo`, `profile` |
| `BaseModels.SpaceModel.CustomInfo` | `iconType`, `windowTheme` |
| `BaseModels.SpaceModel.CodingKeys` | `id`, `title`, `customInfo`, `profile`, `containerIDs`, `legacyContainerIDs` |

The `sidebar` property's indirect type reference resolves through an observed internal chained rebase to `SidebarDataStore.AppSidebarReducerState`. The `sidebarSyncState` and `firebaseSyncState` properties reference `SidebarSyncCloudKit.ZoneSyncData` and `FirebaseSidebarSyncCommon.PersistedFirebaseSidebarSyncState`, respectively. Original mangled bytes, including suffixes, are preserved; a named context alone is not the full instantiated type.

The same 14 selected declarations have matching names, descriptor kinds and field names in Intel and Apple Silicon slices; [the comparison](evidence/workspace-cross-architecture.json) records both hashes. This checks the selected declaration shapes, not identical implementations or serialization.

The item IDs and parent/child properties provide a concrete starting point for documenting hierarchical organization. The split-view data case provides a code-tracing target. The coding-key enum is evidence that these names exist in compiler metadata; it does not prove raw string values, which cases are emitted, or whether decoding applies migrations.

## Filename and entry-point status

The main Intel slice contains `StorableSidebar.json`; its exact offsets were recorded in [the initial string evidence](evidence/workspace-string-seeds.json). A bounded Intel code-byte search found two candidate RIP-relative LEA references to its address, `0x103ec9cb0`. GNU objdump independently decodes the candidate instruction bytes. The binary's `LC_FUNCTION_STARTS` stream places them after declared function starts `0x100f41540` and `0x103373b00`, respectively. See [the candidate evidence](evidence/sidebar-filename-code-candidates.json). Linear disassembly from each preceding declared function start confirms an instruction boundary at both candidates. Full disassembly stays in ignored local artifacts; the public report records span hashes and sizes. Control-flow reachability and read/write roles remain unverified. It does not establish the file's directory, whether it is authoritative, or whether all named model fields are stored there.

A bounded scan of the Intel slice's 10,339 Mach-O symbol entries found no symbol name containing `StorableSidebar`. This does not establish absence of the implementation: reflected type names exist, and function names may be stripped. The corresponding symbol-search artifact is local at `artifacts/sidebar-symbols.json`.

## Method and limitations

`scripts/swift_fields.py` reads the Mach-O section layout, relative field descriptors, and symbolic mangled-name references. It resolves direct supported context descriptors and indirect contexts only when an exact pointer slot is present in a format-6 chained internal rebase. It preserves unhandled imports and context kinds as unresolved. It neither loads Arc nor invokes its runtime.

The implementation follows the structure declarations in [Swift reflection records](https://github.com/swiftlang/swift/blob/main/include/swift/RemoteInspection/Records.h), [Swift symbolic mangling](https://github.com/swiftlang/swift/blob/main/docs/ABI/Mangling.rst), and [Apple chained fixup layouts](https://github.com/apple-oss-distributions/dyld/blob/main/include/mach-o/fixup-chains.h). These are format references, not Arc implementation source. Synthetic fixtures test the parser independently of the Arc artifact.

## What remains unknown

- JSON root representation, wrapper keys, identifier encoding and enum payload encoding.
- Actual encoded key strings, default values, omitted fields and schema migrations.
- File location, write atomicity, backup behavior and recovery precedence.
- Read/write entry points and calls into encoder/decoder APIs.
- Which cloud states are required for local operation, particularly after account shutdown.

No exporter is implemented against these unverified assumptions. Next: obtain the filename's code references, trace the containing function to decoding/encoding operations, and validate resulting schema facts against a synthetic workspace produced by the original application when macOS access is available. Native Linux work should preserve this model's observed relationships while keeping the engine/platform boundary separate.

## Reproduce

```bash
python3 scripts/swift_fields.py artifacts/macos/Arc.x86_64 > artifacts/swift-all-fields.json
python3 scripts/workspace_dossier.py artifacts/swift-all-fields.json > artifacts/workspace-declarations.json
python3 scripts/x86_literal_refs.py artifacts/macos/Arc.x86_64 StorableSidebar.json > artifacts/filename-candidates.json
python3 -m unittest discover -s tests
```

The input must be a thin little-endian Mach-O64. The public selection report contains declarations and evidence coordinates, not executable code or proprietary pseudocode.

## Whole-program analysis limit

Ghidra did not complete a focused main-app import within 900 seconds even with Objective-C type metadata analysis disabled. The [recovery record](evidence/main-import-recovery.json) preserves those limits. The declaration results above come from the independent format parser, not a completed Ghidra import. No entry-point or serialization conclusion is inferred from the failed import.

## Persistent targeted analysis results

A persistent Ghidra project was created with whole-program automatic analysis disabled. The program was saved, reopened, annotated, and saved again; the import no longer has to repeat for every pass. [The targeted findings](evidence/targeted-workspace-findings.json) preserve the actual program hash, instruction counts, selected reference addresses, and analysis failures.

Both selected functions contain indirect jump tables. Initial flow-following disassembly stopped at the computed jumps. A second pass applied the [explicit bounded target selections](evidence/workspace-jump-table-selection.json), increasing recorded instructions from 36 to 290 in `0x100f41540` and from 128 to 970 in `0x103373b00`. These selections are analyst annotations and do not prove exhaustive runtime cases.

The stronger lead is now `0x103373b00`:

| Instruction | Observed reference |
| --- | --- |
| `0x103374605` | Imported `Foundation.JSONEncoder.encode` symbol |
| `0x103374692` | `StorableSidebar.json` string at `0x103ec9cb0` |
| `0x1033746c7` | Imported `Foundation.URL.appendingPathComponent` symbol |
| `0x1033746e1` | Imported `Foundation.Data.write(to:options:)` symbol |

The filename address is established by the recorded LEA instruction operands and independent original-byte disassembly. With automatic analysis disabled, Ghidra did not generate a filename data-xref record; that missing record is not treated as absence of the reference.

This is a concrete JSON-writing candidate tied to the workspace filename. The surrounding function also calls temporary-directory and other path-related APIs. Whether it participates in normal persistence, data export, diagnostics, or multiple operations remains unresolved; these static references are not runtime observations and do not establish the encoded model or write options.

Pseudocode is deliberately excluded from the new semantic claims. Ghidra returned pseudocode for `0x100f41540`, but its recovered basic blocks included addresses outside the selected function span. The second function's decompilation still exceeded 45 seconds. Instruction and reference collection completed and the database was saved despite these decompiler limitations. Neighboring function boundaries and callee signatures need refinement before pseudocode can be trusted.

The next focused questions are: what value reaches `JSONEncoder.encode` at `0x103374605`, which path reaches the write at `0x1033746e1`, and which callers invoke that operation. Follow those exact sites in the saved project; no further whole-app analysis is required to begin.
