# WEBZ-NATIVE-001 — Executable Witness and Limits

**Scope:** `the-static-collective/static-workbench` pull request #107, branch `docs/webz-native-001-workbench`.  
**Verified code commit:** `a969af07251f75249ed201ee2340774849c262d6` (prior to this evidence-only documentation commit).  
**Date:** 2026-10-06 (operator-local) / 2026-10-07 UTC (CI).  
**Status:** First-party Workbench-native `webz::` browser specimen executed with real tests. **Not merged or installed on the operator's machine.**

## What actually ran

GitHub Actions on the implementation branch, [run 37569249142](https://github.com/the-static-collective/static-workbench/actions/runs/37569249142), reported both required jobs successful:

- **Workbench checks:** full `python -m pytest -q`: **275 passed, 1 warning, 19.58 seconds**. The existing pinned cross-project smokes and browser script syntax also succeeded. The action's `node --test tests/webz-*.test.mjs` step succeeded; independent local Node 22 verification from matching Git blob bytes reported **16 tests passed, 0 failed** (8 voyage-projection tests, 8 browser-storage tests).
- **Real browser job:** Linux headless Chromium through Playwright against an actual loopback FastAPI/Uvicorn Workbench instance. Both desktop **1366×880** and mobile-sized **390×844** sessions completed: Workbench → webZ address field → Resolve → Enter Sanctuary → Inspect/Remain/Inspect/Cross → Orchard → separately chosen Return → Sanctuary. Opt-in browser-local voyage survived reload, exported four declared navigation events, erased only after confirmation, and refused an unknown address without navigation. Each viewport was checked for horizontal page overflow.
- **Negative browser case:** an independently typed/direct Orchard URL **must not** silently complete a previous pending portal departure. An earlier browser test at `b4f1413582dbe73c099fe60cb0b15839d68a8aff` failed exactly because an unrelated direct address visit fabricated arrival. The updated world browser at `a969af0` uses a short-lived, same-tab, same-origin-referrer portal handoff before a local arrival can be recorded. The same real Chromium witness then passed. The handoff is **local UX correlation**, not cryptographic proof, permanent world identity, or receiver acceptance.

### Browser artifacts

The successful run uploaded **`webz-native-001-browser-witness`** (artifact ID `11460062376`, ~7.3 MB). Its screenshots include desktop and mobile views of the Sanctuary, Orchard, return and unresolved address, plus machine-readable voyage exports. Open the GitHub Actions run's Artifacts section to view the bundle.

### Testable contract

```bash
python -m pytest -q
node --check static_workbench/web/webz.js
node --check static_workbench/web/webz-world.js
node --check static_workbench/web/webz-voyage.mjs
node --check static_workbench/web/webz-storage.mjs
node --test tests/webz-*.test.mjs

# separate real-browser smoke (CI includes Playwright setup)
python scripts/smoke_webz_browser.py --out browser-artifacts
```

The installed-wheel test checks presence of the native resolver's flat packaged assets (manifest JSON, two world documents, JS/CSS and voyage modules). The resolver never converts an unknown address into an arbitrary HTTPS fetch or filesystem read.

## Actual ownership boundaries

- **webZ / Workbench native support:** the application recognizes `webz::` as a **textual logical address**, resolves an explicitly installed local registry, and renders distinct first-party documents.
- **STORYSHIP:** unchanged sovereign canonical voyage. The optional `webz/voyage-local/v0` log is explicitly browser-local testimony, not a STORYSHIP, SupaBardo or reLATTE receipt.
- **reLATTE / COM⁵:** no signed envelope is emitted during simple visits. No external item, identity, local memory, key or image crosses by default. Formal signed carries remain a separate proposed experiment.
- **Human:** Resolve, Enter, Inspect, Cross, Return, Begin recording, Export and Erase are distinct visible actions. The UI does not choose a route or enable recording implicitly.
- **Worlds:** same-origin trusted first-party pages with different declared world IDs; **not browser security-isolated tenants**.

## Limits and deferred work

This does **not** install a global browser/OS `webz::` handler, provide public federated name resolution, cryptographically identify worlds, implement reLATTE receiver admissions, make a playable 3D simulation, or ship a STATIC OS installer. All present webZ worlds are trusted first-party Workbench fixtures, with newly drawn CSS scenes rather than redistributed manga image assets. Playwright exercised a real browser on GitHub-hosted Linux with a mobile-sized viewport; it did **not** validate the operator's actual phone or Linux desktop installation.

Review method: author completed a separate code/security/negative-test self-review using Superpowers and Riqor code-review criteria. A fresh reviewer subagent was **unavailable in this harness**, so the self-review is not represented as independent signoff.

> **The browser recognizes the address. The door presents the destination. The traveler decides. The world keeps its own laws.**
