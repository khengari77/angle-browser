# Reproducing the research

Run from the repository root. Artifacts and tool installations are ignored by Git. The Python scripts use only the standard library; acquisition uses curl, extraction uses 7z. None execute Arc.

```bash
python3 scripts/acquire.py > artifacts/reference-packages.json
python3 scripts/extract_macos.py artifacts/macos/Arc-1.170.0-89123.dmg artifacts/fresh-extraction
python3 scripts/inventory.py artifacts/fresh-extraction/bundle/Arc/Arc.app > artifacts/inventory.json
python3 scripts/inspect_macho.py artifacts/fresh-extraction/bundle/Arc/Arc.app/Contents/MacOS/Arc > artifacts/load-commands.json
python3 -m unittest discover -s tests
```

The extractor supports the observed raw/zlib HFS UDIF layout and refuses other compression types. It is not a general-purpose DMG extractor. Use a new output directory; errors may leave a partial local output. The source package is unchanged. Byte hashes verify reproduction, not publisher signing identity.

## Toolchain

Installed under `.local-tools`: Node 22.23.4, npm-managed REA 6.8.0, Ghidra 12.1.4. Existing Java/Javac 21 and procps `ps` are used. Node and Ghidra archives were checked against official published SHA-256 values. REA's npm lockfile remains with the local installation.

Codex configuration is user-local, with a backup made by REA setup. The launcher uses the absolute isolated Node executable and REA entry script, avoiding the unsupported system Node version. It sets `GHIDRA_INSTALL_DIR` and `JAVA_HOME`. Restart the Codex client to load the new MCP tools; a standalone MCP probe does not attach them to this already-running chat.

```bash
python3 scripts/rea_probe.py
```

This performs MCP initialization and tool discovery and saves the returned schemas locally. For a target, supply an advertised tool and its JSON arguments. For example, `open_binary` takes an absolute `path` and optional `provider_id`. The probe closes the target and terminates its own server on exit; analysis databases and logs stay local. It never intentionally launches the analyzed target. Each probe writes a process-specific server log.

Ghidra rejects universal Mach-O through this REA adapter. Extract a slice using the offsets and sizes in the Mach-O inventory, then retain its identity. Function analysis must use provider-returned names/addresses. Keep proprietary pseudocode and snapshots in `artifacts/`.

## Public interfaces

The research tools are command-line programs, not browser APIs. `inspect_macho.py` outputs SHA-256, size, architecture slices and load commands with offsets; `inventory.py` emits `arcreverse-inventory-v1` with relative paths, hashes, links and selected plist metadata. These research outputs do not establish runtime behavior. Browser APIs and a workspace interchange schema have not been invented ahead of evidence.

Use `scripts/rea` as the pinned local CLI launcher. Deep analysis requires a local Unix-domain socket; this sandbox blocks binding it, so run deep checks through the normal approved escalation mechanism. Metadata-only target opening does not verify decompilation.

## Persistent research sessions

`scripts/rea_session.py` initializes a local MCP session and accepts one JSON object per input line: `{"tool":"open_binary","arguments":{"path":"/absolute/path/to/target","provider_id":"ghidra"}}`. Each response is saved to a process-specific ignored directory. Send `{"close":true}` to close the target. Subsequent tool calls share the same Ghidra import. Requests have a bounded 1,020-second wait.

The focused persistence pass raises `REA_GHIDRA_STARTUP_TIMEOUT_MS` to 900000 and sets `REA_GHIDRA_DISABLED_ANALYZERS` to `Objective-C Type Metadata Analyzer` (a comma-separated list, not JSON). This omits Objective-C metadata analysis; findings must preserve that coverage limitation. It does not change the global Codex server settings.

## Persistent Ghidra project and targeted passes

The direct Ghidra workflow avoids REA's requirement that default whole-program auto-analysis finish before queries become available. It uses the installed Ghidra APIs without modifying REA or Arc. This is a separate project; it is not imported into REA's ephemeral session database.

```bash
scripts/ghidra_project.sh import
scripts/ghidra_project.sh targets "$PWD/artifacts/targeted/new-pass" \
  0x100f41540 0x100f41c50 \
  0x103373b00 0x103374cd0
```

`import` creates `artifacts/ghidra-projects/ArcPreservation` and refuses to overwrite an existing project. `targets` reopens the saved `Arc.x86_64` program with automatic analysis disabled. The output directory must be new. It runs bounded disassembly, creates functions from discovered flow where needed, records references, and attempts decompilation with a 45-second limit per function. Spans larger than 64 KiB are rejected. Changes apply to the local Ghidra database; executable bytes are not rewritten.

Keep the project closed in the GUI while a headless pass uses it. The project contains proprietary program bytes and must stay out of Git. Imported dylib declarations do not mean the referenced macOS libraries are available on this host; no dependent libraries were imported. Call target names can be missing or incomplete.

A function's observed body must stay within the selected span before decompilation proceeds. These runs do not perform global caller discovery, recover complete Swift calling conventions, or execute Arc. `report.json` records actual completion and errors. Assembly and pseudocode remain in ignored artifact directories. A script failure may leave its output directory; use a new directory for a corrected pass and check the Ghidra log for save success.

The initial selected functions dispatch through indirect jump tables. `ArcJumpTables.java` validates analyst-selected table entries against the program hash and containing code span, adds computed-jump references, and stores a Ghidra switch override. The selection is a research annotation, not a proven enumeration of all runtime cases. Apply it to the saved database before a new targeted pass:

```bash
scripts/ghidra_project.sh tables \
  "$PWD/docs/evidence/workspace-jump-table-selection.json" \
  "$PWD/artifacts/targeted/new-table-report.json"
scripts/ghidra_project.sh targets "$PWD/artifacts/targeted/after-tables" \
  0x100f41540 0x100f41c50 \
  0x103373b00 0x103374cd0
```

The targeted report also records decompiler basic blocks outside the selected span. A successful decompiler return alone does not make those blocks valid. The wrapper checks for completed script output because a Ghidra launcher exit status alone can miss a script-level failure. The project keeps analysis state between passes, including these annotations.
