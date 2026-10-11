# RETURN ROOM × STATIC WORKBENCH 001 — Eleven Dials for the Unfinished

**Status: draft experimental Workbench UI, stacked on the real GHoT idle-control shell.**
This is a standalone browser interface hosted by the existing loopback Workbench, linked from the GHoT landing and left-hand navigator. It does **not** replace the existing Return Desk, Road Desk, Attention Shelf, project ownership, reLATTE verifier or STATIC OS CLI.

## Operator walkthrough

1. Start the ordinary Workbench at its existing `127.0.0.1:13700` loopback address. Choose **Return Room · 11 dials** or open `/return-room`.
2. Bring `session.json` from a completed **STATIC-OS RETURN ROOM 001** session. Optionally bring `checkpoint.json` and an explicitly generated read-only `replay` JSON. Files are read **locally in the browser**, never sent to a server.
3. Press **Inspect local session**. WebCrypto SHA-256 recomputes the canonical STATIC-OS session address, checks exact claimed state fields and the optional checkpoint/replay's claimed relationship.
4. Use any of the **eleven actual controls**: SOURCE, RECEIPT, HOLD, WITNESS, NEIGHBOR, QUESTION, GAP, RETURN, CUSTODY, FUTURE, DOOR. Each reads the *same imported, checked session* through a different bounded interpretive lens without mutating it.
5. With a checked session, explicitly download `return-room-next-reader.json`, a minimal unsigned question packet with the existing crossing ID and required unresolved-source aperture. It is **not** a new reLATTE crossing or permission to operate another instrument.
6. **Clear from this page** discards imported in-memory data and resets file controls. No browser storage, network upload, telemetry, local project state modification, or server-side source inspection is performed.

The page has a CSP that forbids `connect-src` to other systems. The only Workbench server actions involved are **GET** requests to the HTML/CSS/JS static files. There is no `POST /api/return-room`, no shell command parameter accepted by Workbench, and no private signing keys in the browser.

## Actual vs unearned checks

| Surface | Verified | Not verified |
| --- | --- | --- |
| STATIC-OS CLI and native reLATTE | Native P-256 crossing/receipt identity, input source bytes, local HOLD, source-linked Question Box aperture | Historic source truth, human operator identity, booted hardware |
| Workbench browser | LOCAL **self-addressed session SHA-256**, exact non-authority fields, optional checkpoint/replay structural linkage | Native P-256 crossing/receipt signatures, original source bytes, sender/operator identity |
| Downloaded next-reader packet | Only projected fields from locally checked session; explicit no-admission/no-automatic-action | New reLATTE grant, admission, independent custodian signature, independently verified MEMENTO source |

Browser displays `LOCAL_SESSION_ADDRESS_CHECKED` and `NOT_REVERIFIED_IN_BROWSER` explicitly. A local attacker could rehash a forged session; the exact shape check prevents simple promotion, but a browser-only receipt is **never** trustworthy third-party evidence. It is a usable offline operator view, not a replacement for native reLATTE verification.

## Existing lineage

- STATIC WORKBENCH **GHoT idle shell** [PR #89](https://github.com/the-static-collective/static-workbench/pull/89): actual navigable Workbench and read-only RPG/quest projection.
- STATIC OS **RETURN ROOM 001** [PR #86](https://github.com/the-static-collective/static-os/pull/86): native verifications, human-selected local session and cold replay. This UI consumes only its portable session output.
- Private MEMENTO [PR #52](https://github.com/the-static-collective/MEMENTO/pull/52): signed HOLD, local encounter, question seed.
- National Treasure Question Box [PR #85](https://github.com/the-static-collective/national-treasure/pull/85): maintains `source-object` aperture and speculative unsupported status.

## CI and independent compatibility

The dedicated `return-room-001.yml` workflow **pins public donor commits**, checks out actual STATIC OS source (`2201d09107c31e5823ef641643b269fbd765c0d1`), native reLATTE (`dcc8cdca84c440aa4294134f020fb7095bf87f24`) and National Treasure (`d6ff149a7a2d59dcb41c2c61606204b20b56a2fa`). No private MEMENTO repo is fetched.

A synthetic donor creates a genuine signed reLATTE crossing and three receiver receipts. STATIC OS writes a real content-addressed question session. The **exact shipped Workbench browser-core** validates that session and optional checkpoint/replay. Hostile tests tamper local hashes, signed-claim labels, authority, original-source ancestry, autoexecution, next-turn permission, and file bindings. API smoke tests load the real Workbench page, prove GHoT/home navigation, refuse POST, and enforce the existing loopback Host guard.

The test is **not** a physical Android/browser interaction pass and does not assert a bootable OS, actual website deployment, or persisted in-browser storage. The intentionally browser-local page should later receive an accessibility/manual-phone pass.

## Future grown-up gates

- Add an operator-selected, strictly bounded native-verification bridge for browser-picked files **only if** a secure local service contract is separately approved; never secretly replace Static OS source authority.
- Allow a human to hand the redacted question to a GHoT candidate instrument; this is a **new** explicit turn, not implied by a prior `HELD_QUESTION`.
- Add independent recoverability/backup/mirror for long-lived questions, after privacy and true-world custodian approval.
- Evaluate physical hardware, offline battery, and future-reader material preservation separately.

## Laws

```text
DIAL != AUTHORITY
UI DIGEST != SIGNATURE VERIFICATION
LOCAL QUESTION != PROJECT EXECUTION
ARRIVAL != ADMISSION
RECEIPT != HISTORIC SOURCE TRUTH
HELD_QUESTION != NEXT TURN
NEW VIEW != RETROACTIVE KNOWLEDGE
SESSION != OWNER OF SOURCE
DOWNLOAD != RE-LATTE CROSSING
INSTALLED WORKBENCH != BOOTED STATIC OS
```

**Workbench provides the porch and dials. Static OS owns the session. MEMENTO owns its memory. reLATTE carries what can be verified. National Treasure keeps the question open.**
