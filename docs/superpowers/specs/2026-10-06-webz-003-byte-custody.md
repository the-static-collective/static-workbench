# WEBZ-003 — Orchard Independently Takes Custody of Real Bytes

**Status:** Approved conceptual frontier; implementation and PR pending verification.  
**Operator decision:** Extend existing Workbench WEBZ-RELATTE-002 without replacing its signed-crossing fixture.  
**Separate protocol owner:** merged reLATTE PR #63 at immutable merge revision `103c03c745968bfe2105167fa9007fab8906fc71` (previous proposed branch tip `743e5705c1e397c40aff82960e361d0b36eb11a5`).

## The missing proof

The earlier reLATTE R14 signed crossing attests that an envelope **references** `sha256:<digest>` and that Orchard's LocalReceiver received and disposed of the envelope. It does not establish that Orchard obtained the referenced bytes.

WEBZ-003 adds a **second explicit human-gated action**, after signed WEBZ-002: a bounded **literal material carrier** containing the signed envelope *and actual encoded bytes* is offered to the Orchard's separately executed receiver code. That receiver opens its independently rooted LocalReceiver, independently validates envelope signature and SHA-256 against the **actual bytes read from the carrier**, issues an additional **signed `PAYLOAD_BYTES_VERIFIED` receipt** with its **same receiver-local key**, and cold-replays the outcome. Its journal now records a signed byte-custody event. HOLD retains the verified bytes in quarantine; REFUSE verifies but does not retain them. Both remain unadmitted.

## Explicit boundaries

- **PREVIEW ≠ SEND ≠ DELIVER ≠ ADMIT.** Resolving, opening a world, inspecting a door, crossing a no-carry portal, browsing Orchard, GET previews, and local navigation logging **must not transport material**. The WEBZ-003 physical-byte handoff uses its own explicit guarded POST, with an exact matching sender-crossing ID, source digest, and `DELIVER_VERIFIED_BYTES` confirmation.
- The caller cannot provide receiver disposition, a filesystem path, a URL, base64 bytes, account identity, arbitrary artifact, or transport flags. Only the two immutable first-party fictional JSON cards already signed in WEBZ-002 are eligible.
- **Transport:** Sender bundles a signed crossing plus the actual first-party fixture bytes into a size-bounded JSON carrier in its Workbench state directory. The standalone reLATTE destination process reads **the carrier file** and does **not** receive the sender's raw source file path or the bytes in a procedure parameter. It independently verifies signature, SHA, signed RECEIVE/disposition, and writes only inside its own receiver root. The Workbench process does not mint or verify custody signatures itself; reLATTE owner seals them.
- **Authority:** The signed custody receipt is produced with the Orchard receiver's existing signing key, attests to byte verification under that local fixture owner, and is bound to the crossing and preexisting RECEIVE/disposition receipts. It is not evidence of a human identity, legal ownership, remote machine, different OS account, decentralized global identity, or independent network host.
- **Disposition:** HOLD means bytes present and safely quarantined, **not admitted**. REFUSE means bytes were independently inspected/hashed and were not retained. REFUSE ≠ nonexistent history; its signed receipt remains.
- **Replay:** Re-running an identical delivery must return the identical signed custody receipt ID, never append duplicate custody evidence, and never bypass the actual digest check. Corrupted carrier, altered crossing, changed receiver payload file, malformed stored result, missing or dirty exact checkout, transport timeout, mismatch in receiver keys, or unrecognized receiver disposition fails visibly closed. An unknown outcome is not auto-retried by browser UI.
- **Pinned owner:** Unrelated Field Reseed retains its original R14 pin. **Both** WEBZ-002's R14 envelope generation and WEBZ-003's physical-byte delivery select the custody-capable exact clean reLATTE owner revision; otherwise the old R14 receiver cannot replay a CUSTODY journal when another parcel arrives later. This explicit, tested upgrade preserves earlier signed envelopes and avoids any shadow signing code. The pin must be updated only at the already reviewed owner's merged commit.
- **Security:** Existing `_creator_write_guard` for POST session/Origin, fixed world allowlist and flat asset packaging remain. Browser UI escapes all metadata via `textContent`, no background actions or new third-party script. Existing no-carry Workbench screens remain unchanged except an additive custody cockpit and read-only Orchard custody witness.

## Workbench adapter

`WebzCustodyGate` wraps the existing `WebzParcelGate` with its existing local lock. It exposes `preview(kind)` (pure), `deliver(kind, expected_sha256, expected_crossing_id, confirmation, repos)`, `inbox()`, and `proof(kind)`. The first preview requires existing signed WEBZ-002 result but does not invoke a signer or write carrier files. Deliver requires the exact previously signed parent and stages the same exact local bytes with digest checked, writes a transport carrier under `state_dir/webz-relatte/v0/material-carriers`, and launches `node --experimental-strip-types <pinned reLATTE>/scripts/material-delivery.ts` with an explicit receiver root and crossing ID. The result is validated and saved as a durable receipt reference; `proof` returns public signed evidence, *never private JWK material*.

Routes:
- `GET /api/webz/custody/{kind}/preview` — read-only; if no signed first-phase crossing, show `NOT_READY`.
- `POST /api/webz/custody/{kind}/deliver` — explicit session/Origin guarded; body permits only `expected_sha256`, `expected_crossing_id`, `confirmation`. No recipient policy input.
- `GET /api/webz/custody/inbox`, `GET /api/webz/custody/{kind}/proof` — read-only receiver custody view/proof.

The first native browser UI places the separate `DELIVER ACTUAL BYTES` control in Sanctuary, and Orchard displays both earlier envelope outcomes and new signed byte-custody outcomes. No existing reLATTE envelope is rewritten.

## Evidence gate

1. Red tests for unknown kind, no prior signed crossing, stale digest/crossing ID, absent explicit choice, foreign Origin, missing session, arbitrary extra fields, old owner pin mismatch and material carrier corruption.
2. Real reLATTE old R14 owner signs first crossing, independently pinned new owner destination process opens **the same receiver root** and verifies actual bytes.
3. HOLD returns signed, same-local-key `PAYLOAD_BYTES_VERIFIED`, physically retained bytes, cold-open revalidation, idempotent receipt on retry.
4. REFUSE returns signed custody receipt and **no retained payload file**, no admission.
5. Tampering carrier bytes after signing fails **before custody**; changing retained bytes breaks receiver cold replay.
6. Full Workbench Python/JS tests, project smokes, installed wheel check and desktop/mobile real Chromium: explicit twice-gated transfer and read-only evidence, original navigation unchanged.

**Not yet established:** different machines, network/peer transport, separate administrative credentials, untrusted third-party worlds or STORYSHIP canonical voyage updates.

**Merge gates:** owner reLATTE PR #63 approved/merged/pin finalized, Workbench code reviewed and both final CI jobs green. Human chooses merge rather than it being inferred from feature approval.
