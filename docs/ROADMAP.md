# Angle contributor roadmap

The prototype is not a completed alpha. Qt extension enablement is blocked; CEF evaluation is pending. Observation work can proceed independently of engine work. macOS and Windows findings must identify their own build rather than being generalized across platforms.

Tasks are defined in [backlog.json](backlog.json) and published as GitHub issues. Each has environment requirements, scope, acceptance and dependencies. `ready` means dependencies are satisfied, not a legal approval. Binary RE additionally needs the contributor rights assessment and maintainer scope review described in the research policy. Maintainers update blocked/ready labels after prerequisite reports merge.

| Key | Task | Dependencies |
|---|---|---|
| R1 | Observe sidebar layout and keyboard behavior | None |
| R2 | Observe Spaces and profile isolation | None |
| R3 | Observe Favorites, pinned tabs and folder lifecycle | None |
| R4 | Observe command bar and tab-switching behavior | None |
| R5 | Document workspace persistence through synthetic file comparisons | None |
| R6 | Bounded static analysis of workspace serialization references | None |
| E1 | Evaluate prebuilt CEF rendering and MV3 extensions | None |
| E2 | Validate CEF embedding into Qt Quick | E1 |
| D1 | Implement a read-only synthetic Arc workspace exporter | R5 |
| U1 | Improve sidebar fidelity against reviewed observations | R1 |
| U2 | Align tab and folder lifecycle with reviewed behavior | R3 |
| Q1 | Make Linux CI reproducible from a fresh checkout | None |
| P1 | Complete Angle runtime identity and storage migration | None |
| P2 | Audit runtime dependency licensing before binary distribution | None |

Claim a task by coordinating in its issue. Use a fork and one PR per task. Include `Closes #N`; only reviewed/merged work closes an issue. Passing research tasks produce evidence, not automatic implementation or platform-support claims. Engine migration, binary releases and service replacements require separate reviewed decisions.

Maintainer tooling: `python3 scripts/publish_issues.py --repo owner/repository` previews the backlog; `--apply` publishes missing issue titles and writes the issue index. It does not close issues or overwrite existing issue discussions.
