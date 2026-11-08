# Local visual reference measurements

Two public uploader files were downloaded on 2026-11-08 and inspected locally. Source identity, uploader attribution, dimensions and SHA-256 are in [sources.json](sources.json). Images remain under ignored `artifacts/reference-corpus/`; no image or extracted application artwork is committed. Their Commons pages state CC0 for uploader rights; that does not establish permission for every underlying application graphic or displayed web page. These are third-party captures, not Angle's original-app runtime observations.

## Windows 1.3.2 screenshot

[Original source page](https://commons.wikimedia.org/wiki/File:Arc_Browser_Windows_Screenshot_(version_1.3.2).png), uploader Gawiłowski, dated June 4, 2024. The downloaded PNG is 1440 × 853 pixels. Coordinates below use origin at its top-left, x rightward and y downward, with exclusive upper bounds where a rectangle is given. Regions are measured from this raster, approximately ±2 pixels because gradients and antialiasing soften boundaries.

| Region | Raster observation | Limitation |
|---|---|---|
| Left sidebar and page boundary | Page begins around x=200; sidebar occupies about 13.9% of total image width | A user-resizable state, not a default, minimum or macOS value |
| Top browser control strip | Page top begins around y=32 | Window title controls appear in this strip; native logical units/OS scaling unknown |
| Page region | Approximately x=[200,1432), y=[32,844) | Rounded corners; includes web content, not a reusable rendering asset |
| Two Favorite tiles | Approximately [9,34,95,78] and [105,34,191,78], about 86 × 44 pixels and 10-pixel horizontal gap | Only two shown; does not establish adaptive grid rules |
| Selected tab row | Approximately x=[9,191), y=[233,270), about 182 × 37 pixels | One selected state; row height under different DPI/font settings unknown |
| Organization | Favorites first; Space label, folder, separator, New Tab row and selected regular tab below | Visual state only; section semantics come from separate behavior evidence |
| Outer page right/bottom margin | Roughly 8–9 pixels | Raster observation, not a fixed implementation constant |

A simple pixel-run check confirms the page's white interior at x=201 onward in sampled rows and y=33 onward at the top. This aids reproducibility, not exact corner/radius recovery. Use the downloaded file and PIL `Image.open(...).getpixel((x,y))` to recheck. No exact font, radius, hover color, shortcut or animation duration is inferred.

## Theme demonstration GIF

[Original source page](https://commons.wikimedia.org/wiki/File:Arc_Browser.gif), uploader Elfanek, described as March 15, 2023. Commons records an upload on December 13, 2023. The file is 800 × 533 pixels with 99 frames; the page labels its loop about three seconds. Frames 0 and 49 were extracted locally and viewed: both show a browser window with left sidebar, split content and a floating theme palette; sidebar/window color changes from pink to green while the structure stays similar.

This demonstrates a pictured color-customization state. The raster contains substantial white background and window shadow, so its sidebar/window ratio cannot be compared directly with the full-window Windows capture. GIF conversion may resample, drop frames or alter playback speed; do not use it to assign Arc animation timing or original logical geometry. Theme UI implementation is deferred from current core workflow changes.

## Implementation use

Treat measurements as comparison samples for Windows historical fidelity, not universal constants. Keep macOS 1.170.0 as the separately documented reference baseline and preserve explicit uncertainty when selecting Linux dimensions. Test Angle at the same raster dimensions before comparing proportions, state which differences are intentional, and never claim a pixel-perfect match from these two examples.
