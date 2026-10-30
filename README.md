# Angle

An independent research project to preserve Arc's existing desktop browser experience through reverse engineering, documented behavior, and open-source implementation.

**Status:** initial static research and tooling implemented. Official Mac and Windows packages are archived locally; the Mac executable and bundle have been inventoried. A runnable Qt browsing prototype is present; the required extension engine gate is blocked and the planned alpha is not complete. Angle is independent and is not affiliated with The Browser Company or Google’s unrelated ANGLE graphics project.

## Purpose

Preserve the interface and workflows people already use: the sidebar, Spaces, Profiles, Favorites, pinned tabs, folders, command bar, split views, and tab lifecycle. Improvements should follow a documented compatibility baseline so changes can be assessed against actual Arc behavior.

The project starts by studying the existing application, rather than designing an alternative browser from memory. Research will determine which components can be maintained or reused under their licenses, which require independent replacements, and which cannot realistically be preserved.

## What preservation requires

- Record a specific Arc version and operating system as the reference for each observation.
- Document behavior, local file formats, and dependencies with reproducible evidence.
- Separate observed facts, public statements, and hypotheses.
- Investigate whether essential workflows depend on accounts or remote services.
- Keep the browser engine maintainable with upstream security updates. An unchanged old executable is not a sustainable browser release.
- Support local operation and migration of user-owned data as early goals.

Arc and its Arc Development Kit are not a complete publicly available source tree we can simply fork. Reverse engineering can reveal behavior and interfaces, but does not automatically recover the original maintainable source code or grant redistribution rights. Any independently written replacement must be identified as such.

## First milestone

Produce a reproducible technical assessment of one desktop release:

1. Inventory its package, components, dependencies, and version information.
2. Capture a behavior specification for core browsing workflows.
3. Describe the local workspace data format using synthetic profiles.
4. Export that synthetic workspace into a documented, engine-independent format.
5. Assess engine update feasibility and service dependencies, then recommend an implementation path with evidence.

See [the research plan](docs/RESEARCH_PLAN.md). The reference is macOS Arc 1.170.0 / 89123. Native Linux is the first new platform; Windows remains a compatibility target. A Linux development environment does not establish how the macOS or Windows application behaves; platform-specific findings need access to that platform.

## Contributions and research material

Commit original code, reproducible observations, and synthetic test fixtures. Record the origin and license of any third-party code before adding it. Keep proprietary installers, executables, copied application resources, real browser profiles, credentials, and personal browsing data out of the repository. Permissions for inspecting, reusing, or distributing particular artifacts need separate assessment; this document grants none.

Original code is MPL-2.0. The initial prototype uses C++20, Qt Quick/QML, Qt WebEngine, and SQLite. Prebuilt CEF evaluation is the next engine investigation after Qt extension enablement failed validation.

## Public background

- [Arc's shutdown announcement](https://arc.net/) — currently announces December 22, 2026 as the desktop shutdown date. Capture dates matter because the site can change.
- [Letter to Arc members, May 26, 2025](https://browsercompany.substack.com/p/letter-to-arc-members-2025) — describes the proprietary ADK dependency and why the company had not open-sourced Arc. Its maintenance assurances describe that earlier date, not the later shutdown announcement.
- [Arc FAQ](https://arc.net/faq) — describes Chromium compatibility and platform support.

These are background sources, not evidence of the contents or behavior of any executable we have inspected.

## Research results

See [the workspace persistence dossier](docs/WORKSPACE_PERSISTENCE.md), [the feasibility assessment](docs/FEASIBILITY.md), [reproduction instructions](docs/REPRODUCING.md), and the evidence inventories in `docs/evidence/`. Proprietary artifacts, toolchains, snapshots and decompiler output remain in ignored local directories.

## Browser development

See [build instructions and validation status](docs/BROWSER.md). Run `scripts/build_browser.sh`, then `build/arcreverse`. This is a development prototype; required alpha acceptance checks remain incomplete.

## Contribute

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). Pick a scoped GitHub issue; Mac and Windows Arc users can contribute reproducible observations without building Angle. Read the [research policy](docs/RESEARCH_POLICY.md) before inspecting Arc or submitting evidence. The [roadmap](docs/ROADMAP.md) identifies dependencies and acceptance criteria.

Angle is the public project name. Existing executable names, internal schema identifiers and local storage paths still use `arcreverse`/`ArcReverse` for compatibility; this publication does not migrate user data. The UI is a development prototype, not a finished alpha. No binary release is published.
