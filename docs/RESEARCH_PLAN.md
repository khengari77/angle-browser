# Desktop preservation research plan

## Research rules

Use a dedicated OS user or disposable VM with a synthetic browser profile. Keep the original installation and profile untouched; work from copies where practical. Do not commit personal browsing records, cookies, credentials, account tokens, or machine identifiers.

Inspect local artifacts and observe normal use first. Do not modify authentication, signatures, or executables as a prerequisite to establishing what the application actually does. Remote service replacement remains a hypothesis until dependencies and interfaces have been characterized using authorized observations.

Do not mistake a library name, string, screenshot, or a single successful run for proof of an architectural conclusion. Attach the relevant evidence and state its limits.

## 1. Choose and identify the reference

Record:

- Operating system, version, architecture, and Arc version/build.
- Installer source, acquisition date, SHA-256, and locally observed signature information.
- Whether the environment has an existing Arc account or profile, and the test date relative to the shutdown timeline.
- Which permissions and licenses apply to the artifacts and intended research.

Keep macOS and Windows findings separate. Do not assume that features, storage formats, or service dependencies match.

Deliverable: a reference-build record without proprietary binaries or personal identifiers.

## 2. Inventory components

Inspect package layout, version metadata, shipped license notices, dynamic dependencies, helpers, frameworks, and any available symbols. Identify engine version and the boundary between the Chromium components, application UI, and proprietary infrastructure where evidence permits.

Questions:

- Which components have public source and usable licenses?
- How does the UI communicate with browser processes?
- What is required to build or update the engine-facing integration?
- Are extension loading, downloads, permissions, DevTools, and profile isolation provided by the engine or custom application code?

Deliverable: a component map with evidence and unresolved questions. No engine choice is final at this stage.

## 3. Specify existing behavior

For every workflow, record initial state, actions, visible result, persisted result, shortcuts, edge cases, and platform/build. Use synthetic websites and identities where needed.

| Area | Cases to investigate |
| --- | --- |
| Sidebar | Show/hide, resizing, focus, keyboard traversal, drag and drop |
| Spaces | Creation, order, switching, themes, window interactions |
| Profiles | Space assignment, cookie isolation, settings, extensions |
| Tabs | Favorites, pins, folders, temporary tabs, archive timing, restore |
| Command bar | URLs, searches, tab selection, commands, keyboard behavior |
| Split View | Creation, resizing, navigation focus, persistence |
| Lifecycle | Restart, crash recovery, multiple windows, offline launch |
| Compatibility | Downloads, permissions, extensions, authentication flows |

Deliverable: versioned behavior specifications. Screenshots and recordings may remain local where distribution rights are unresolved.

## 4. Understand and export workspace data

Create one small synthetic workspace and change one property at a time. Compare copies of the local files before and after each change. Determine formats, identifiers, relationships, schema versions, persistence timing, and whether each file is authoritative or a cache.

Prioritize Spaces, folder hierarchy, pinned URLs, Favorites, tab order, and split-view relationships. Preserve unknown fields in research notes rather than silently assigning meanings. Investigate credentials separately; they are not part of the first exporter.

Build a read-only exporter only after sample formats are understood. It must read copies, avoid executing profile content, report unsupported schemas, and leave inputs unchanged. Test with synthetic cases containing nested folders, Unicode names, duplicate URLs, absent optional fields, and malformed input.

Deliverable: documented file formats, synthetic fixtures, and an exporter to a versioned JSON representation. Import into another browser is a separate milestone.

## 5. Identify service dependencies

Compare normal online use with operation offline in the disposable environment. Record what happens at startup, restart, Space changes, and sync attempts. Distinguish observed requests from proven requirements; an observed request does not establish that the browser needs its response to operate.

Questions include whether existing profiles can open locally, which actions require an account, what local data survives service loss, and which functionality is tied to remote services. Do not promise continued use of the original binary after shutdown without evidence.

Deliverable: a dependency table listing each operation, observed service involvement, local fallback behavior, and uncertainty. Remove tokens and personal data from any evidence that is retained.

## 6. Select a maintenance path

Compare paths after collecting evidence:

| Path | Evidence required |
| --- | --- |
| Maintain existing components | Usable source or independently maintainable interfaces, appropriate permissions, viable engine updates |
| Independently implement private components | Sufficient behavior and interface specifications, a viable maintained engine integration |
| Seek an upstream source release | A concrete request identifying the components and licenses needed; no assumption that a release will happen |

An indefinitely frozen Chromium build does not satisfy the maintenance goal. A browser mockup does not establish compatibility. If the original executable cannot be sustainably maintained, explain that finding before implementing a faithful independent continuation.

Deliverable: an architecture decision with measured feasibility, explicit unknowns, required platform/toolchain access, and the smallest demonstrable next milestone.

## Observation template

```text
ID:
Date:
Platform and Arc build:
Evidence type: local observation / public source / hypothesis
Source or artifact identifier:
Initial synthetic state:
Actions or inspection commands:
Observed result:
Interpretation:
Uncertainty and alternative explanations:
Reproduction steps:
Distribution and redaction notes:
```
