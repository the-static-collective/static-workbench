# STACK² 024 — The Living Receipt Floor

**Status: draft, browser-local experimental interface.** Stacked on [STATIC WORKBENCH STACK² 019 PR #111](https://github.com/the-static-collective/static-workbench/pull/111). It preserves that native FastAPI shell, typed Lego floor, and its preexisting read-only boundaries. Nothing is merged or deployed.

## The actual native proof it presents

[CANNON STACK² 023 PR #27](https://github.com/the-static-collective/CANNON/pull/27) and [its independently passing native CI run](https://github.com/the-static-collective/CANNON/actions/runs/38165140352) executed original GHoT's deterministic text processor through its signed Instrument Rack, CANNON's source-and-signature witness, and original reLATTE R14 into a separate receiver that signed both RECEIVED and R3_HOLD.

The CI run publishes **only the redacted `public-inspection.json` artifact**. Download it locally via the run's artifact list while it is retained. It includes content digests and evidence IDs, not the underlying private text or receiver's private keys. The artifact is a public **claim** about a native proof. The browser does **not** independently verify its signatures or Git source. The native proof and the browser reading are separate events.

## Live Workbench UI

Native Workbench route: `GET /receipt-floor` (link in nav, GHoT home, and STACK² 019 Lego floor).

The UI is a moss-and-copper responsive receipt walk with:

- A local-only file picker for `public-inspection.json` (12 KiB cap; browser never uploads it).
- Strict exact-schema structural validation, source commit pins, expected 1–2 GHoT processor receipts, receipt-versus-packet correspondence, distinct reLATTE RECEIVED and R3_HOLD, and fail-closed rejection of ADMIT, external effects, source-human identity or deployment claims.
- Three apertures: **Processing**, **Crossing**, and **Receiver**. The user can click or keyboard-select a particular, inspect its entire content address and claimed role, and walk forwards one step at a time.
- Original source Git links and immutable commit IDs for GHoT, CANNON and reLATTE, with no repository network polling.
- An opt-in, SHA-256-addressed, **unsigned** local Workbench inspection JSON export. It never elevates imported claims to cryptographic trust or admission.

The import does **not** accept the private `ghot-report.json`, signed crossing bundle, journal, or receiver signing keys. Its strict field allowlist prevents accidental inclusion of private payload fields in the public view. The browser never persists the public import to server, localStorage or sessionStorage; Clear drops the in-memory reference.

## Reproduction

From a local Static Workbench checkout:

```sh
node --check static_workbench/web/receipt-floor-core.mjs
node --check static_workbench/web/receipt-floor-ui.mjs
node --test tests/receipt-floor-024.test.mjs
python -m pytest -q tests/test_receipt_floor_024.py
```

For a real Chromium desktop/mobile witness:

```sh
npm install --no-save --ignore-scripts playwright@1.56.1
npx playwright install chromium
node tests/receipt-floor-024.browser.mjs
```

The browser-test imported file is an **explicit synthetic UI fixture** with well-formed identifiers, not a forged claim of real signatures. It tests file import, keyboard traversal, camera-free presentation, local WebCrypto packet export, consent revocation and mobile overflow. Actual receipt authenticity remains in the [CANNON 023 native verifier](https://github.com/the-static-collective/CANNON/blob/experiment/stack-squared-023-ai-relatte-hold/scripts/stack-squared-023-ai.mjs), not JavaScript UI.

## What the browser can and cannot establish

| Browser checks | Must remain unverified in browser |
| --- | --- |
| Structural shape of the redacted native CI public report | P-256/GHoT signatures |
| Exact declared source Git commit strings | Actual original Git content and source ownership |
| Receipt identifier formats, counts, uniqueness and declared relations | Receiver durable journal |
| That the summary reports R3_HOLD with no ADMIT | Whether an unknown file is authentic historical testimony |
| Local SHA-256 of a *new unsigned Workbench inspection statement* | Signature / owner authority over the imported report |

A SHA-256 checksum of an unsigned inspection packet proves only that it has a reproducible content address. It does **not** authenticate a foreign signer or replace native reLATTE verification.

No new POST route, write API, arbitrary local file path input, donor subprocess, remote fetching or model inference is installed by STACK² 024. Links are navigational user actions, not automatic network calls. The historical native CI source pins remain independent of the UI.

## Constitutional boundaries

```
GHoT EXECUTION RECEIPT != reLATTE RECEIVED
reLATTE RECEIVED != reLATTE R3_HOLD
reLATTE R3_HOLD != R3_ADMIT
CANNON SOURCE WITNESS != SIGNED RECEIPT
PUBLIC SUMMARY != NATIVE CRYPTOGRAPHIC VERIFICATION
LOCAL INSPECTION CHECKSUM != SIGNATURE
BROWSER SELECTION != NATIVE EXECUTION
SOURCE COMMIT != HUMAN OWNER AUTHORITY
```

**Next candidate:** STACK² 025 could introduce an owner-controlled, read-only **verification porter**: original reLATTE source and public signed evidence verified on the local host, returning a bounded signed-or-unsigned attestational *summary*, without transporting private model prompts to the browser. Such a verifier would need explicit source pins, an independently chosen trust anchor, bounded private file roots, and a hard separation between inspect and ACT.
