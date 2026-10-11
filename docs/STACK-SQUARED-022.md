# STACK² 022 — The Receiver's HOLD Shelf

**Experiment branch:** \`experiment/stack-squared-022-hold-shelf\`, stacked on the unmerged native STACK² 021 Post Office branch. No merge or deployment.

The Lego Floor's new **08 / HOLD Shelf** is a real, read-only reLATTE R14 receiver instrument. It makes already-received source particulars visible, including signed lineage and receiving-world HOLD receipts. It does not accept payload content, operate the original donor, produce new crossing receipts, admit artifacts, or reassign source authority.

## Provenance stays with the particular

For each *currently* HELD crossing, the source-addressed shelf lists:
- original crossing ID, declaration kind, source world and source particular;
- original source history head (from the signed crossing);
- original native RECEIVED receipt ID and timestamp;
- distinct native R3_HOLD receipt ID and timestamp;
- original receiver history head and current snapshot state ref;
- number of *declared source pointers*.

Selecting a card performs **a fresh read** of that exact crossing ID through the native verifier. It additionally reveals declared payload reference roles/addresses (not bytes), original source adapter family and donor contract, receiver's own contract and state transitions, custody-receipt presence, and whether the wrapper signatures verify.

Every screen labels the original **GHoT donor claims as *not reverified by this shelf*.** Native reLATTE signature validity protects the crossing's attribution and receipt integrity; it does not prove arbitrary statements inside donor_claims or human identity.

## Original native receiver, not an invented cache

\`scripts/stack-floor-022-shelf.mjs\` uses the original pinned \`reLATTE@dcc8cdca84c440aa4294134f020fb7095bf87f24\` \`LocalReceiver.open()\` on an existing local receiver directory. The reLATTE original code replays the **entire receiver journal**, validates event chaining, original crossing signatures, signed RECEIVED/DISPOSITION receipts and chronology. This tool then independently:
- enumerates **only** the actual \`snapshot.held\` IDs (not IDs from a browser input);
- checks each expected RECEIVE precedes its HOLD and agrees with the receiver's verified native receipts;
- calls the original native signature verifiers again on each displayed crossing, RECEIVE and HOLD;
- refuses tampered, missing, inconsistent or overlarge journals (maximum 4 MiB / 1000 journal events / 100 held items);
- verifies a selected item is STILL held before showing its detail.

No separate cached shelf database is introduced. Refresh always reflects current receiver state; an item moved out of HOLD disappears from its next snapshot. This branch provides **no means** to change that disposition.

## API and access

A distinct \`GET /api/stack-floor/shelf/status\` reveals only an enabled boolean and read-only capability (no paths or actual receiver identity).

Two **read-only** operations use POST to enable body-based strict selection and preserve the existing Workbench session / Origin protections:

- \`POST /api/stack-floor/shelf/list\` with an exact empty JSON object.
- \`POST /api/stack-floor/shelf/detail\` with only one validated canonical crossing ID.

Both require the preexisting same-origin \`X-Workbench-Session\` local token and exact Origin. The server supplies its own locally configured original reLATTE checkout and existing receiver root; the browser can never choose a filesystem path, checkout, command, key file or an ADMIT operation. Original TypeScript source pins are verified using the preexisting 021 operator loader. Nothing runs if the receiving Post Office is not enabled.

The shelf view calls native reLATTE locally, including its private-key-containing receiver opening process, but **does not transmit, export or serialize any receiver private JWK**. It also never opens payload bytes, issues an owner grant or invokes any mutation method. The view runs as the local Workbench OS user and should **never be exposed through a public proxy**.

## Browser

Real DOM, responsive moss-and-copper "wooden shelf" cards. The user can:
1. Inspect the receiver's HOLD shelf on demand;
2. Tap a particular to inspect signed history and declared original references;
3. Save an explicitly **unsigned** JSON inspection card containing only redacted/sanitized metadata.

After a genuinely successful separate 021 CROSS, the shelf may refresh observationally to show the new item. Merely visiting or tapping never issues new source permission, an ACT ticket, a CROSS request, or receiver-owned ADMIT.

No HTML is rendered from any source string; data is placed through DOM textContent only.

## Proof

\`tests/test_stack_floor_022.py\` runs the original GHoT 030 source-hash ACT and original reLATTE R14 source crossing with a separately fabricated **test-only** receiver policy, then reads the actual receiver journal via the shelf.

Hostile probes confirm: no access without local session + correct Origin, no arbitrary paths/extra fields, no input-controlled admission, no detail access to non-held IDs, no reading before a receiver exists, refusal after tampered native signatures, no payload byte read, no private key in response, no silent policy creation, and no mutation of original journal or key bytes by shelf inspection.

Those CI fixture keys are not the user's local receiver credentials and do not establish user-machine deployment. Native owner configuration, privacy review and mobile walkthrough remain release gates.

**PARTICULAR ≠ PAYLOAD EXECUTION · VERIFY RECEIPT ≠ VERIFY DONOR CLAIM · HOLD ≠ ADMIT · INSPECTION ≠ OWNER SELECTION · READING HISTORY ≠ CHANGING HISTORY.**
