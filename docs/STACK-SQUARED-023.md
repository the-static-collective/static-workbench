# STACK² 023 — Mycelium Shelf

**Experimental, review only.** Branch \`experiment/stack-squared-023-mycelium-shelf\` targets STACK² 022. All 019–022 stacked experimental ancestors remain separate and unmerged. No public release, receiver mutation, source installation, graph persistence or authority grant.

## The actual difference

STACK² 022 let an owner view the original signed reLATTE receiver's HOLD shelf. STACK² 023 lets **two or more sovereign held particulars be compared without joining their histories**.

The new **09 / Mycelium Shelf** in \`/stack-floor\` offers:

- a bounded original-journal-derived constellation of held particulars, including visible islands with no connection;
- five locally switchable lenses: **Origin**, **Trace**, **Structure**, **Address**, **Arrival**;
- "threads worth inspecting" as keyboard-accessible proposal cards showing exactly why each was suggested;
- focus a single node to see its local proposal neighborhood, and choose the minimum number of matching facts;
- a separately labeled **unsigned question export**; no relation writes or signatures are produced;
- observably fresh re-inspection after the previous Post Office's separately approved CROSS, only if this viewer was already open.

**No similarity model, cross-source recommendation engine, embeddings or inference of human meaning is silently involved.** Every edge is the result of exact comparisons of fields in independently verified **reLATTE-signed wrappers** and their original receiver journal.

## Source and proof boundaries

The new original-native reader \`scripts/stack-floor-023-mycelium.mjs\` opens the already-configured local original pinned \`reLATTE@dcc8cdca84c440aa4294134f020fb7095bf87f24\` \`LocalReceiver\`. The same original repository pin verification and local receiver configuration from 021/022 apply; no new configuration setting is added.

Reader behavior:
1. read and size-check the receiver's journal, require a directory/file without top-level symlinks;
2. cold replay \`LocalReceiver.open()\`, which validates event sequence, hash chain and signed receipt/crossing evidence;
3. re-read journal and refuse a changed journal snapshot; cap to 4 MiB, 1000 events and 100 HELD IDs;
4. include **only** crossing IDs in \`receiver.snapshot().held\`, never an admitted crossing; independently reverify the original crossing/RECEIVED/HOLD signatures and their pairings;
5. extract only bounded, declared source-world, source-particular, history-head, adapter family, donor contract, stated payload-reference addresses, held timestamps and receiving journal arrival order;
6. generate deterministic **unsigned proposals** from those exact fields, with evidence kind, lens, matching literal value, an explicit explanation and a stable hash-based proposal reference bound to the current receiver state;
7. return a read-only field snapshot, never private key bytes, payload bytes, full \`donor_claims\`, donor program outputs or arbitrary file bytes.

The original GHoT execution receipt is **not reverified by this relationship view**. Matching addresses are from verified **envelopes**, not a byte-by-byte retrieval or validation of the referenced content. The original reLATTE signatures establish wrapper integrity and receiver events, not real-world human identity or truth of donor assertions.

### Five evidence lenses

| Lens | Supported exact comparison | What it **does not** prove |
|---|---|---|
| Origin | Same sender-declared world or particular | Common ownership, source identity or consent |
| Trace | Same declared source-history head | Parentage, causal or historical continuity |
| Structure | Same declared adapter family or donor contract | Functional compatibility, admission right |
| Address | Exact matching declared payload address | Same available bytes, permission to fetch, copy or execute |
| Arrival | Consecutive RECEIVE entries in the signed receiver journal | Content similarity or shared source |

No measured "confidence score". The on-screen number of facts is a count, not a probability. Positions use fixed phyllotaxis-style geometry only as a visualization, not a learned semantic distance.

## Authority and boundedness

- Graph is recomputed **on demand** from original receiver HOLD state. No relationship table or local proposal database.
- At most **60 nodes and 360 proposals** returned; counts and truncation indicators show omitted nodes or threads. At most 180 drawn stems and 40 accessible thread-list entries per lens to keep the interface responsive.
- Original current receiver journal never changes during inspection. A nonempty field requires signed, receiver-local HOLD receipts.
- A missing or invalid native source checkout, tampered/changed receiver journal, wrong session, Origin, extra fields or an unconfigured receiver refuses the read. There is no POST action to create, accept or admit a relation.
- \`GET /api/stack-floor/mycelium/status\` reveals only opt-in capability flags, not local user paths.
- \`POST /api/stack-floor/mycelium/inspect\` requires **exactly an empty object**, same-origin \`Origin\` plus the existing local Workbench session token, and no user-provided path/source/node identifier.
- Graph operates with Workbench's local OS process permissions. Keep Workbench loopback only; do not publish this endpoint through a reverse proxy.
- An exported **unsigned question** includes the specific attributed evidence and a bound receiver state reference. It is not a signed crossing, relation selection, receiver judgment, or new owner permission.

## Test matrix

\`tests/stack-floor-023.test.mjs\` validates deterministic pure-core relationships and preserved facts; exact shared pointers vs unverified bytes; truly isolated held islands; sorted, stable proposal references; canonical IDs, HOLD only and bounded truncation.

\`tests/test_stack_floor_023.py\` runs pinned original GHoT 030 + reLATTE R14 with a synthetic, independently provisioned receiver. It creates one real signed original Post Office receipt and three **disposable native reLATTE-signed test specimens** (two HELD with matching declared addresses and a third ADMITTED). It proves the Graph includes ONLY the HELD originals, attributes a specific shared address, excludes the admitted particular, preserves journal/private key bytes exactly through repeat inspections, requires original same-origin/session protections and refuses tampered journal signatures. The test fixture is synthetic, not a real user's authorization.

\`tests/stack-floor-023.browser.mjs\` uses real headless Chromium to click the original GHoT ACT → independent CROSS → HOLD chain and grow a graph from extra native signed fixture specimens. It switches to the Address lens, inspects an attributed thread, downloads the unsigned question, and captures desktop/mobile screenshots.

## Laws

**RELATIONSHIP PROPOSAL ≠ RELATIONSHIP SELECTED.**

**SHARED ADDRESS ≠ SHARED MEANING.**

**SIGNED ENVELOPE ≠ VERIFIED DONOR CLAIM.**

**ARRIVAL ORDER ≠ CAUSAL LINK.**

**HOLD ≠ ADMIT.**

**FIELD VIEW ≠ RECEIVER AUTHORITY.**
