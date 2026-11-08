# Reconstruction status — 2026-11-08

Canonical knowledge: [CONFIRMED_BEHAVIOR.md](CONFIRMED_BEHAVIOR.md). Read that ledger first; use [WORKFLOWS.md](WORKFLOWS.md) for scenarios, [REFERENCES.md](REFERENCES.md) and sources.json for provenance, [BINARY.md](BINARY.md) for static findings, and [VISUAL.md](VISUAL.md) for inspected historical images. AGENTS.md requires future agents to maintain the ledger.

| Investigation | Outcome | Remaining work |
|---|---|---|
| Official workflows | Documented core scenarios with stable claim IDs | Original-app confirmation on reference versions remains unavailable |
| Public schema research | Two explicit community encoding variants identified | Real synthetic Arc-generated fixtures; Favorites/profile mapping; version coverage |
| Clones | Pinned source/license identities for Cra, Zen and others | Detailed CEF/extension integration experiments remain issue #7; Echo reuse excluded |
| Visual corpus | Historical Windows screenshot and theme demonstration downloaded, viewed, hashed and measured | Modern macOS/reference-build imagery; no universal dimensions or timing inferred |
| macOS metadata | 25 selected contexts resolved from hash-bound prior scan | Complete encoder value-flow, decode/migration/recovery paths |
| Persistence candidate | Existing encoder/path/write references corroborated; incoming DATA records identified as function-start declarations | Actual code callers, values, and normal persistence versus export role |
| Windows | Arc.dll identified as the richer workspace/Swift target | Swift PE metadata prefix/parser support and targeted function tracing |
| Read-only export | Separate draft implementation issue #16; independently constructed tests | Dossier review and original-app fixture validation; #5/#9 remain open |
| Pinned URLs | Separate draft implementation issue #17, source-backed core regression tests | Review, interactive controls validation |
| Sidebar | Separate draft implementation issue #20, compile/workspace validation | Pointer/keyboard interaction testing; section affiliation blocks pinned collapse commands |

This is a completed bounded evidence pass, not completion of exhaustive reconstruction or the first alpha. The blocked extension engine, downloads, whole-browser GUI interaction tests, modern reference visual comparison and runtime Arc validation remain outstanding. No automatic merge, release, engine replacement, auth bypass or account access was performed. PRs remain separate for maintainer review.

Validation: all 24 Python research tests on the dossier tree pass (17 prior plus seven new parser tests). Export branch independently adds eight exporter tests. The application change branches built with Qt 6.11.3 and passed the workspace suite, including a new saved-URL persistence test. Isolated native Wayland rendering passed with sandbox enabled; these checks do not establish original-app interaction equivalence. Remote CI results must be read from the actual PR checks rather than assumed from local results.
