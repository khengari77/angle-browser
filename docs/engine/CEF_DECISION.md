# CEF feasibility decision — 2026-11-08

**CEF Chrome style passes the standalone capability gate on native Wayland and X11/XWayland. CEF with Qt Quick is not qualified for production.** The tested Qt off-screen route renders through Alloy, but its extension sees no Chrome host window and cannot exercise the required action popup. Do not combine Chrome-style popup success with Alloy-style rendering into a compatibility claim. No production engine replacement is made.

## Tested configuration and provenance

CEF 156.0.14+g4fa4ab5, Chromium 156.0.8078.48, upstream CEF revision `4fa4ab516dacf6c49fc7e6e70d2b7ebce29fa35f`. [The lock](../../experiments/cef/lock.json) records vendor archive identity plus independently computed SHA-256. The minimal SDK supplies prebuilt Chromium; only its wrapper and Angle's small original diagnostic were compiled. SDK/runtime files stay ignored locally.

The host is Fedora/Hyprland with native Wayland and XWayland. Backend switches are explicit; the alternate display environment is removed. X11 results do not establish native Xorg-session coverage. Windows and macOS were not tested. All URLs and profiles belong to the diagnostic. DevTools is loopback-only and closes with the owned browser process. No personal profile or Arc account is used.

## Standalone results

| Configuration | Rendering/content script | Profile/extension isolation | Action popup | Restart | Result |
|---|---|---|---|---|---|
| Prebuilt cefsimple Chrome and Alloy, both backends | Pass | Not tested | Not tested | Not tested | Preliminary samples only |
| Two request contexts, shared load-extension command | Pass | Fails: script appears in both contexts | Not reached | Not reached | Reject this configuration |
| Separate processes, native Chrome host, Wayland | Pass | Pass | Pass, actual chrome.action.openPopup and popup counter | Pass, three two-launch cycles | Standalone pass |
| Separate processes, native Chrome host, X11/XWayland | Pass | Pass | Pass, same action test | Pass, three two-launch cycles | Standalone pass |
| Separate processes, Alloy Views, both backends | Pass | Pass | No extension-visible host window | Not reached | Not qualified |

Successful Chrome runs verify persistent local storage/cookies, popup chrome.storage retention, no extension or website-state leakage to profile B, namespace/seccomp sandbox status and normal exit after Browser.close. Initial launch naturally has no restart assertion; restoration assertions run on the second launch of each cycle.

Extension restoration is **application-managed**: first launch persists the enabled unpacked paths under the probe's owned profile root; OnBeforeCommandLineProcessing restores them on relaunch. The runner omits the external load-extension argument on relaunch. A prior run without this registry lost content-script enablement; native CEF persistence of command-line extension installation is not claimed. This registry is diagnostic code, not a production extension installer, permission review UI or general profile manager.

The shared command-line extension configuration applied to both request contexts. The alternative uses one CEF process per profile, with separate root/cache paths and extension configuration. That architecture has memory/process/IPC costs and is not yet selected for Angle.

## Probe corrections and coverage limits

- The SDK separates Release and Resources. ICU lookup required a complete adjacent runtime plus $ORIGIN library lookup. Earlier missing-ICU aborts were packaging defects in the diagnostic, not CEF capability failures.
- A DevTools target exists before its document finishes loading. The gate now waits for the owned fixture title with a bounded deadline instead of a fixed startup sleep.
- Chrome may restore extra session tabs. The gate selects a fixture target independently from each profile process and retains target records; this is not Angle tab-restoration behavior.
- Real action popups require an active host. Chrome's window API alone did not activate it reliably on this compositor. The runner explicitly focuses its owned PID through Hyprland before invoking the action. Results therefore establish this owned-window setup, not arbitrary compositor activation support.
- The baseline launch checks and normal Chrome routes report namespace/seccomp sandboxing active; no no-sandbox flag is used. Raw traces stay in ignored artifacts/cef-gate. Published summaries exclude profile paths, target/session IDs and raw logs.

## Qt embedding and next decision

The separate issue #8 spike uses QQuickPaintedItem, copied CEF paint buffers and a 10 ms external message-pump timer. It tests actual Qt windows rather than assuming CEF's independent window is embedded. Its report must distinguish rendering, sandbox and extension results from unimplemented input, DPI, performance and lifecycle work.

The pinned [runtime API](https://github.com/chromiumembedded/cef/blob/4fa4ab516dacf6c49fc7e6e70d2b7ebce29fa35f/include/internal/cef_types_runtime.h) and Linux SetAsWindowless explicitly select Alloy for off-screen rendering. The standard action-popup gate cannot be met by the tested Alloy host. A standalone native Chrome window does not prove native Wayland embedding into Qt Quick.

Keep Qt WebEngine extension enablement guarded. Before production migration, review a distinct architecture proposal for either a supported Chrome-style host composition or a properly specified extension host for the off-screen route. Do not substitute direct popup-HTML navigation for action semantics, introduce hidden browser workarounds, or assume foreign X11 parenting solves native Wayland. No such alternative is implemented by this investigation.

Reproduction commands are in [the experiment README](../../experiments/cef/README.md). [Machine-readable results](../evidence/cef-capability-validation.json) retain each executed phase and explicit not_run checks.
