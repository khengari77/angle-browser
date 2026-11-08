# Reconstruction reference corpus

Reviewed 2026-11-08. The canonical factual ledger is [CONFIRMED_BEHAVIOR.md](CONFIRMED_BEHAVIOR.md); implementation scenarios are [WORKFLOWS.md](WORKFLOWS.md). [sources.json](sources.json) pins reviewed repositories, license hashes and documentation URLs. This corpus contains independent summaries, not copied Arc resources.

## Vendor sources

- [ARC-MAC: macOS release notes](https://resources.arc.net/hc/en-us/articles/20498293324823-Arc-for-macOS-2024-2026-Release-Notes): use dated entries for historical behaviors. Current version entries must not be projected back onto archived Arc 1.170.0.
- [ARC-WIN: Windows release notes](https://resources.arc.net/hc/en-us/articles/22513842649623-Arc-for-Windows-2023-2026-Release-Notes): distinguish Windows-specific interactions from macOS.
- [ARC-MIGRATION: Arc-to-Dia migration](https://resources.arc.net/hc/en-us/articles/44413129117591-Move-from-Arc-to-Dia): useful evidence of Arc's data concepts; Dia behavior is not itself Arc behavior.
- [ARC-EXPORT: export instructions](https://resources.arc.net/hc/en-us/articles/25583851606039-How-Do-I-Export-My-Data-from-Arc): current export capabilities, without proving availability in every older build.

These pages were read through the web tool. Direct HTTP archiving returned 403. Their registry hashes are deliberately null; no successful image download, image measurement or animation inspection is claimed. A later researcher should add a successful local snapshot with URL/hash and image crop coordinates, without replacing the source identity of existing claims.

## Community research and independent implementations

Repository commits and original license bytes are pinned in sources.json; local license copies are in ignored artifacts/reference-corpus/. GitHub classification is advisory; inspect actual notices at the pinned revision.

| Source | Evidence role | Reuse boundary |
|---|---|---|
| [Icesource/arc-tab-organizer](https://github.com/Icesource/arc-tab-organizer) | DATA_MODEL.md and parser report sidebar schema from manual inspection | MIT; original findings remain third-party reports, not original-app validation |
| [ivnvxd/arc-export](https://github.com/ivnvxd/arc-export) | Parser uses `newContainerIDs` with tagged entries, contrasting the organizer's documented `containerIDs` shape | MIT; use differences to generate explicit supported-schema tests rather than accepting arbitrary inputs |
| [VictorKildahl/cra](https://github.com/VictorKildahl/cra) | CEF/Swift alternative; tree contains sidebar models, theme imports, profile reconstruction and extension placement modules | MIT root license verified; selected file behavior not runtime-validated here |
| [zen-browser/desktop](https://github.com/zen-browser/desktop) | Firefox-based alternative; workspace and UI architecture comparison candidate | MPL-2.0 root license verified; no code imported |
| [GR0SST/Echo](https://github.com/GR0SST/Echo) | Publicly visible Arc-like alternative with sidebar and extension modules | Original code/artwork license reserves rights. Reference-only; do not vendor or translate its implementation |

No third-party implementation code is included by this report. The researcher has seen the organizer's data-model descriptions and parts of the MIT exporter, plus repository module listings and licenses. This is not a strict clean-room history.

## Remaining corpus work

The official help-page image route was inaccessible to direct archiving. The downloaded historical uploader corpus is described in VISUAL.md; it supplies bounded raster geometry, not universal visual tokens. Current macOS sidebar dimensions, default/minimum widths, exact typography and native animation timing remain unmeasured. Do not infer those from a clone or invented mockup.

The current https://arc.net/ farewell page was captured successfully (ARC-HOME in the registry); its decorative Favorites assets are not a screenshot of the original desktop application and are not used to assign browser dimensions.

## Historical visual corpus acquired

[VISUAL.md](VISUAL.md) records two downloaded Commons uploader captures and cautious raster measurements. They are not official vendor captures or our own runtime observations. The earlier failed official-image route remains documented; the corpus now has historical Windows 1.3.2 geometry and a theme GIF, with macOS-current and interaction-timing gaps still open.
