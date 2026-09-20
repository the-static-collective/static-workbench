# GRAFT × DOGRAM — STRUCTURAL WITNESS 001

Status: experimental, opt-in structural measurement attached to an already saved
HOUSE-native Maxhinal ride. This is **not** the full GRAFT candidate-generation,
seedFORK retrieval, or BananaGram participation workflow.

## Local operator workflow

1. Run HOUSE on loopback. Put exactly one trusted, clean local checkout of
   [Dogram](https://github.com/the-static-collective/Dogram) under configured
   HOUSE roots. The checkout must include the existing public `dogram.engine`.
2. Open **HOUSE Maxhinal**, explicitly select source material, preview it, and
   save a native ride. Open that ride from the saved history if needed.
3. In the ride's **GRAFT × DOGRAM** section, supply a **human-declared hypothetical**
   JSON directed graph: `{"nodes":["seed","candidate","saved_proposal"],"edges":[["seed","candidate"]]}`.
   The prefilled graph is an illustrative fixture, **not** extracted from the
   source material. Replace or review it before interpreting a result.
4. Select `reach@1` to add/remove one existing-node edge, or `ablate@1` to
   remove exactly one existing edge. Provide at most eight explicit path queries.
5. **Preview declared GRAFT graph** to review the exact public
   `dogram.specimen/v0`, source ride digest, and pinned Dogram commit. Choose
   **Run reviewed graph through Dogram** to measure that exact specimen.
6. The public Dogram `dogram.receipt/v0` is preserved as a distinct, unchanged
   object inside a Workbench-owned `house.graft-structural-witness/v0.1`
   attachment. Return to a saved ride and open its earlier measurements.

## Boundaries and refused inputs

- Only existing, digested HOUSE-native rides are eligible. The ride, its fuel
  and its source checkout are not modified. No source content is converted into
  inferred graph edges or automatic execution plans.
- The operator floor is exactly `reach@1` and `ablate@1` with strict,
  reviewed, finite directed graphs: 2–12 unique labeled nodes, up to 32
  unique edges, up to 8 queries, and one explicit, feasible existing-node edge
  addition/removal. No code is run from the selected source fuel.
- The browser's prefilled graph is only a documented illustration. Graph
  structure, KEEP/BEND continuity, impact claims, artistic meaning, causal
  relationships and implementation status remain human-supplied or unresolved.
- Every measurement rechecks the saved native ride content address, declared
  specimen SHA-256, and a clean Dogram HEAD, including a post-run check.
  Changed inputs require a fresh review. The trusted local Dogram Python code
  is executed; HOUSE does **not** sandbox a malicious checkout.
- Immutable local SQLite witness entries have SHA-256 content identities.
  HOUSE's event journal only references the ride and witness ID. A successful
  Dogram receipt is **calculation evidence for the provided graph**; it grants
  no project authority, is not an ALEX conclusion, and cannot harvest a
  proposal, publish a community offer, or claim an act was fulfilled.
- GRAFT's two-stage proposed-vs-observed comparison and full orphan-repo
  transformation workflow are future, separately authorized increments.

## Verification

`tests/test_graft_witness.py` exercises guarded API preview/measure/readback,
committed local ride linkage, stale preview refusal, invalid/oversized graphs,
dirty Dogram refusal, idempotent saved witnesses, digest tamper rejection and
browser wiring. A stub Dogram operator is used only as a unit-test transport
fixture, **not** as a claimed upstream result.

CI separately checks out upstream Dogram at a pinned commit and runs
`scripts/smoke_graft_witness.py`, exercising actual public `reach@1` and
`ablate@1` receipts against a frozen fixture and persisted HOUSE witness.
Actual Linux field deployment remains a separate acceptance milestone.
