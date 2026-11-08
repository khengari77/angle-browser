# Bounded binary reconstruction pass

Research date: 2026-11-08. Purpose: document local workspace interfaces and UI-state vocabulary needed for an independent implementation and read-only migration tooling. Scope: selected Swift declarations, two Windows PE members, and six exact addresses in the saved macOS database. No application was executed, no authentication or signature mechanism was changed, and no proprietary implementation is included in this report. The supplied official-release copies were acquired by the project; user authorization to investigate is not a legal opinion or a redistribution license. The research policy and applicable terms remain relevant. This pass does not assert legal clearance.

## Artifact and method identity

The [sanitized declaration and package report](../evidence/binary-reconstruction.json) records freshly computed SHA-256 identities. The macOS input is the previously extracted Intel slice of Arc 1.170.0 / 89123, `338e4d317981a7c3c958e606ee1e42ede73f536adcf3478fbe2ee9eeb66d6313`. The cached Swift parser report is bound to that hash and its own report hash is recorded. This reuses the prior complete metadata scan rather than claiming that every declaration was reparsed during this pass.

Windows Arc 1.129.0.288 x64 MSIX has SHA-256 `b45d110aad915c82a042782b0f3dae126787107727bb44e86ad733d2479196b5`. It contains 1,441 members. Two members were inspected without extracting or executing them:

| Member | SHA-256 | Size |
|---|---|---|
| Arc.exe | `27bc7728fd355d9f700e37d80536aeb39c00bb2b9fa6a521efad8de6b56f644a` | 3,409,304 |
| Arc.dll | `719aeb366654c80ba7244b37e145ec6858489e30843aed8f5d02d7604bd058b6` | 82,866,584 |

These hashes identify the inspected files; signature authenticity was not checked. Both PE headers declare AMD64/PE32+. Section ranges were bounds-checked. Resource presence is inventory, not execution evidence.

## Findings and implementation implications

1. **The existing metadata has useful coverage beyond the original 14 selected declarations.** The new report selects 25 exact contexts, including command-bar actions, selection, presentation and typing-state declarations. Every selected context was found; the overall parser still reports 3,087 unresolved names among 11,556 descriptors. Selection success does not establish whole-program completeness.
2. **The container model distinguishes roles.** `SidebarItemContainer.ContainerType` declares `topApps` and `spaceItems`. `SpaceModel.ContainerType` declares `unpinned` and `pinned`; its nested unpinned type declares `desktop` and `shared`. These names provide concrete hypotheses for Favorites and Space-root mappings, but do not specify encoded enum payloads or on-disk key strings.
3. **Dictionary encoding needs separate investigation.** `SidebarItemDictionaryCoding` declares a `dictionary` property. `SpaceModel.CodingKeys` declares `containerIDs` and `legacyContainerIDs`; the declaration does not prove when either is emitted or migrated. Community reports of `newContainerIDs` must remain version-specific hypotheses rather than being silently equated with these declarations.
4. **The command bar exposes multiple actions.** Selected metadata distinguishes `navigateToURL`, `openURL`, and `openTab`; keyboard-up/down, Escape, return, query update, highlighted-result index and scoped-search fields also exist. This supports a research model with separate navigation and selection states. It does not establish ranking weights, keyboard dispatch precedence, wraparound, or exact visual behavior.
5. **Windows application logic deserves inspection in Arc.dll.** Arc.exe has no exact UTF-8 or UTF-16LE occurrences of the eight selected workspace strings. Arc.dll contains UTF-8 occurrences of `StorableSidebar.json` (2), `savedURL` (5), `childrenIds` (2), `parentID` (12), `newContainerIDs` (1), `containerIDs` (2), and `topAppsContainerIDs` (2). Exact `currentURL` was not found by this bounded search. Arc.dll also declares Swift-related sections including `.sw5flmd`, `.sw5rfst`, and `.sw5tymd`. These facts identify a better follow-up target; absence in this search does not prove a field is unsupported or absent at runtime.
6. **The saved database remains reusable.** Ghidra 12.1.4, Java 21.0.11 reopened the existing project in read-only mode, without auto-analysis or decompilation. The [reference query](../evidence/persistence-reference-query.json) confirms the previously recorded encoder, URL-append and write calls in function `0x103373b00`.
7. **Caller roles remain unresolved.** Existing ReferenceManager state reports one DATA reference to each selected function entry: `0x10534064d` to `0x100f41540`, and `0x105371f36` to `0x103373b00`. No code caller was returned by this exact query. Because whole-program analysis is disabled, this is not proof that callers do not exist. The deeper ownership pass below identifies these sources as function-start records, not callers. No argument value-flow was established, so normal persistence versus export/diagnostics remains unresolved.

## Deeper pass: incoming DATA references resolved

Both incoming DATA sources reside in the file-backed `__LINKEDIT` segment, outside named sections. Mapping through the segment's file offset (rather than incorrectly assuming VA minus image base) yields:

| Ghidra source VA | File offset | Declaring record | Decoded target |
|---|---|---|---|
| `0x10534064d` | `0x508b64d` | LC_FUNCTION_STARTS, one-byte ULEB128 delta | `0x100f41540` |
| `0x105371f36` | `0x50bcf36` | LC_FUNCTION_STARTS, one-byte ULEB128 delta | `0x103373b00` |

The `LC_FUNCTION_STARTS` load command identifies table offset `0x5072d40`, size `0x589b0`. Sequentially decoding its address deltas from the `__TEXT` base reproduces both exact target addresses. The new `function_start_reference_ownership` report records the coordinate derivation without raw bytes.

**Conclusion:** these are importer-created references from function-start declarations. They are not call sites, function-pointer dispatch entries, or evidence of a feature caller. This resolves a concrete false lead: further caller tracing must inspect code and callable metadata rather than follow these two references. It does not establish that actual callers are absent. The writer's arguments and operation role remain unresolved.

## Reproduction

Run from the repository root with Python 3.11+ and the archived local inputs:

```bash
python3 scripts/binary_reconstruction.py \
  --macho artifacts/macos/Arc.x86_64 \
  --metadata artifacts/swift-all-fields-cached.json \
  --msix artifacts/windows/ArcReverse-Arc-1.129.0.288-x64.msix \
  > artifacts/binary-reconstruction-reproduced.json
python3 -m unittest discover -s tests -p test_binary_reconstruction.py
```

The report generator validates the cache/input hash match, bounded PE section layout, and Mach-O function-start ownership, records factual names/coordinates and does not output raw bytes. Its synthetic PE tests cover coordinates, unchanged input, truncated headers, out-of-file sections and excessive section counts.

For the Ghidra query, configure task-local user/config/cache directories because the sandbox does not permit writing global Ghidra preferences. The initial launcher attempt failed on that write; changing only these locations resolved it. No provider or global configuration was installed or changed.

```bash
mkdir -p /tmp/angle-ghidra-home /tmp/angle-ghidra-config
XDG_CACHE_HOME=/tmp/angle-ghidra-cache \
XDG_CONFIG_HOME=/tmp/angle-ghidra-config \
JAVA_TOOL_OPTIONS=-Duser.home=/tmp/angle-ghidra-home \
JAVA_HOME=/usr/lib/jvm/java-21-openjdk \
timeout 180 .local-tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless \
  artifacts/ghidra-projects ArcPreservation \
  -process Arc.x86_64 -readOnly -noanalysis -scriptPath scripts/ghidra \
  -postScript ArcPersistenceReferences.java /tmp/angle-persistence-references.json
```

This query is capped at six sites and 128 incoming references per site. It does not decompile, disassemble, or change the stored database. The process finished successfully within its 180-second limit. Raw launcher logs remain local under `/tmp/angle-persistence-query.log` for this session.

## Next bounded questions

- Both incoming DATA sites have now been resolved as LC_FUNCTION_STARTS records; exclude them from caller hypotheses. Search code callers and callable metadata separately.
- Follow the selected function's data arguments and read-path counterparts with explicit function-boundary checks. Do not retry the unchanged failed whole-application analysis.
- Extend the Swift metadata reader to PE sections, using synthetic fixtures and independently reviewed section formats. Arc.dll provides a target; this pass did not decode Windows Swift declarations.
- Corroborate dictionary/enum representation against independently built compatibility fixtures and multiple community parsers. Such tests establish parser behavior, not an Arc-generated fixture or complete migration support.

A local-only PE mapping probe found that `.sw5flmd` begins with an eight-byte prefix that the current Mach-O field scanner rejects. Skipping it experimentally required a broader parse that was stopped rather than turning this bounded ownership pass into a new PE metadata implementation. No Windows declaration recovery result is claimed; the prefix requires format-aware synthetic tests before a production adapter.

The pass improves evidence coverage and identifies follow-up targets. It does not establish full serialization, defaults, migration precedence, account-independent launch, or exact UI equivalence.
