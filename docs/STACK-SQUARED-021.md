# STACK² 021 — Post Office Lego

**Branch:** `experiment/stack-squared-021-post-office-lego`. Stacks on unmerged STACK² 020; no merge, release, remote sending, or deployment.

## Real operation

The GHoT 030 native `ACT` performed in STACK² 020 produced an original signed one-use execution receipt for one exact planZ Git source. STACK² 021 allows an **entirely separate** human decision to carry that *existing* receipt to an **already provisioned, independently configured reLATTE R14 LocalReceiver**.

This is a **local real crossing**, not a mock or simply viewing a hash. reLATTE signs a new opaque organ crossing, physically transports its envelope as a file bundle, lets the recipient sign a **RECEIVED**, then independently signs **R3_HOLD** in its durable journal. All three reLATTE signatures and the receiver's reloaded state are cold verified.

Nothing may automatically ADMIT, execute a planZ proposal, infer the signed GHoT owner, invent the receiver's allowlist, send externally, merge Git, or reuse the previous one-use ACT approval.

## Whose decisions are these?

- **Original GHoT**: signs a genuine source-hash execution receipt. Workbench 021 reads it *from the local GHoT ticket store*, never from a browser-supplied receipt body. GHoT's original verifier must say it is signed, spent, executed and successful; signed `result_address` must commit to the persisted exact Git source hash result.
- **Sender operator**: previews this exact receipt; a unique 120-second nonce binds its identity, signed content and the receiver's current state; the operator separately checks a new box and types **CROSS**. The lease is atomically spent before native code can execute.
- **Owner of receiving world**: must **already** have created a native reLATTE R14 receiver directory containing its own keys, config and journal; must independently write an exact-ticket, exact-receipt, exact-signer policy allowing only `HOLD`. Workbench **never creates the receiver or writes this policy**. The original receiver replays its journal and owns the signed disposition; nothing is admitted.

Note: A policy file in the same local filesystem is an authorization *configuration chosen by that installation's operator*, not proof that two real-world humans independently consented. ReLATTE P-256 signatures attest control of keys, not legal human identity.

## Local owner configuration (off by default)

STACK² 020 opt-in must already be configured. Add these independent keys in the Workbench TOML:

```toml
stack_floor_postoffice_enabled = true
stack_floor_relatte_checkout = "/exact/original/reLATTE"
stack_floor_receiver_root = "/existing/owner/provisioned/receiver"
```

The reLATTE checkout must be original `dcc8cdca84c440aa4294134f020fb7095bf87f24`. Workbench verifies all tracked original native TypeScript source files, forbids added native TypeScript code, and reads an existing receiver with original reLATTE itself. Node 24 and original reLATTE dependencies must have been installed by the operator.

Receiver prepares `<receiver>/stack-floor-021-inbox-policy.json` **by hand**, after reviewing the signed GHoT record. Exact schema (substitute actual local signed IDs and receiver config):

```json
{
  "schema": "workbench.stack2-021-receiver-policy/v0",
  "reviewed_for_local_hold": true,
  "disposition": "HOLD",
  "allowed_ticket_id": "ghot-activation-ticket-v0:<64 lowercase hex>",
  "allowed_receipt_id": "ghot-activation-execution-receipt-v0:<64 lowercase hex>",
  "allowed_ghot_signer": "ghot-p256:<64 lowercase hex>",
  "receiver_world": "world:receiver-you-provisioned",
  "receiver_particular": "particular:receiver-you-provisioned",
  "receiver_contract": "contract:your-specific-HOLD-policy"
}
```

The receiver config strings must exactly match those in its own native `receiver.json`. Workbench 021 will refuse missing/changed recipient policy; it will not attempt to create the target receiver.

## Workbench sequence

1. Put the four approved CANNON / planZ / GHoT / reLATTE cards into the appropriate native sockets.
2. Obtain the **signed activation ticket ID** from the finished original STACK² 020 GHoT source-hash ACT (auto-filled from a successful in-page 020 run; an existing ID can be pasted).
3. Click **Preview exact receiver-held crossing**. This verifies the old signed GHoT result, the pinned original repositories, and replays the target receiver read-only. It requires a separately authored exact-ticket receiving policy. No effectful crossing happens at preview.
4. Explicitly approve a new checkbox, type **CROSS**, and request one new crossing. This cannot reuse the old GHoT ACT grant.
5. reLATTE's original opaque-roundtrip code signs and transports its evidence, the receiving world writes signed `RECEIVED → HOLD`, and Workbench invokes a separate native cold verifier for the signed crossing, signed receipts, transport file and receiver journal. Only then is the new result shown as verified.
6. Download the signed GHoT receipt, signed reLATTE crossing, signed RECEIVE and HOLD receipts. No keys are included.

The Workbench server applies a loopback Host guard, exact same-origin Origin guard, local session token, exact card order, exact endpoint fields, atomic one-use local lease, pin checks and fail-closed recipient policy.

## Native verification and idempotence

Independent `scripts/stack-floor-021-verify.mjs` imports original reLATTE R14 on the specific pinned checkout; it **cryptographically** checks the three new signatures, original GHoT donor claims carried in the crossing, file transport matching crossing ID, requested non-authority, matching receiver config, actual signed receiving journal and a held/not-admitted disposition.

A completed local delivery creates a deterministic destination folder bound to the original GHoT ticket. Further previews of that ticket and replayed CROSS requests refuse. There is no automatic retry after partial failure; if native transport commits a receiver journal event but a process fails before final reporting, the operator must inspect the saved state and decide on a separate recovery. Durable prepared checkpoints belong to original reLATTE; this surface does not infer permission to replay them.

The receiver's signed journal and original Workbench native output are **local effects**. It is misleading to call the operation effect-free; no remote effect, public deployment, repository mutation or automatic ADMIT occurs.

## CI test

`tests/test_stack_floor_021.py` uses separately checked-out original pinned GHoT 030, planZ and reLATTE R14. It provisions a disposable **synthetic owner receiver** with native reLATTE keys in the GitHub Actions runner; separately seeds a synthetic receiver owner-HOLD policy *in the test fixture*; executes an actual STACK² 020 GHoT `ACT`; then calls the actual 021 Web API preview and CROSS. It cold verifies all original signed artifacts and the durable journal.

Adversarial cases cover missing local policy, wrong origin/session, extra request fields, wrong source recipe, wrong consent, altered receiver policy, expired preview, replay and duplicate delivery. Tests are evidence about the bounded code, *not* a claim that any real owner's machine has been configured.

**ACT ≠ CROSS · CROSS ≠ ADMIT · RECEIVED ≠ OWNER SELECTION · SIGNER KEY ≠ HUMAN IDENTITY · OLD RECEIPT ≠ NEW PERMISSION.**
