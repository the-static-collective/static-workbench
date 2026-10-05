# MADDlibMaxhine-001 — reusable HOUSE composition contract

**Status:** proposed experimental design; no executor exists yet.  
**Baseline:** `static-workbench` main at `25efe8487efaf4af003cb887a8f0072ffcb77c9e` (2026-09-20).  
**Ownership:** HOUSE owns composition planning, local execution bookkeeping, and user decisions; each source/derived artifact retains its existing owner.  
**Purpose:** A person selects up to four explicit local ingredients, chooses a creative intention, reviews one proposed operation, turns the crank, and receives an inspectable durable creative ride and reusable *description* of the operation. No expertise with Git, terminals, or adapters is required.

## 1. Intent and scope

The first flight is deliberately **one operation**: a reviewed Creator Desk source pack or supported local file enters the existing HOUSE Native Maxhinal, whose existing deterministic `spin` produces a saved `house.native-maxhinal-ride/v0.1`. HOUSE stores an attributable composition run and exposes the ride as a result. It does **not** synthesize a song, automatically create a Creator Desk draft, execute GRAFT, or recursively follow branches.

A reusable **Machine Seed** is a versioned, immutable, content-addressed recipe containing input-slot constraints and allowed operation identity, *not* input bytes, local paths, prior consent, or an executable permission. Reapplying a seed creates a new preview and run under current local availability and authorization.

Current source contracts and limits remain authoritative:
- `native_maxhinal.preview_fuels`: one to four explicit items; either configured-root relative files or saved human-reviewed Creator source packs. Local files: regular, nonempty, at most 16 MiB; available UTF-8 inspection at most 128 KiB, excerpt at most 1,600 characters; binary/large media are metadata only. Refuse symlinks, unsafe paths, duplicates, and changed preview digests.
- `native_maxhinal.spin`: `discontinuity | braid | compose | pressure | shuffle`; seed at most 100 characters, question at most 400; deterministic creative projections, `authority:none`, `promotion:NONE`.
- Creator Desk packs and rides remain immutable in `state_dir/creator.sqlite3`; drafts remain explicit, versioned human edits, not implied output.
- HumanTerminal `Journal` preserves raw carrier, parent cuts, and unresolved senses. A sense-field cut is **not** an accepted Native Maxhinal fuel item. No silent conversion or model-selected meaning.
- No project-native execution, arbitrary host shell, external service/model calls, publishing, private recursive discovery, background loops, or automatic self-extension in v0.1.

## 2. Alternatives and selected design

A navigation-only wrapper is smaller but cannot durably attribute or resume a composition. A general autonomous executor is bigger than the present authority and recovery model. Choose a **typed, bounded HOUSE-native orchestrator**: a deterministic plan over currently declared operations, starting with the existing pure spin plus one local atomic save. Additional adapters must undergo separate explicit admission before entering this registry.

## 3. Objects and identities

Use canonical JSON (UTF-8, sorted keys, compact separators) and SHA-256 for content identities. IDs for occurrences differ from content hashes. Verify persisted payload hashes when loaded. A hash establishes byte identity, **not** truth, permission, authorship, or source equivalence.

### 3.1 `house.maddlib.intent/v0.1`

Immutable submitted human intent: explicit fuel refs (same `NativeFuelItem` shape), outcome from a bounded allowlist (`creative_proposal` for first flight), flavor (`familiar | unexpected | maddclown`), depth (`one_spin` only in first flight), optional question, and optional selected chamber. The machine must not invent human declarations. If the chamber is absent, a deterministic mapping may *propose* one, displaying it before any execution; `flavor` never widens file, network, or effect permissions.

### 3.2 `house.maddlib.machine-seed/v0.1`

Immutable recipe with stable descriptive label, content digest, an input slot accepting only `file` or `source_pack` kinds (one to four items), a declared native Maxhinal operation and engine format/version, seed/question defaults or bounded prompt slots, required preview and authorization gates, declared effect `workbench_owned_local_ride_and_composition_receipt`, and explicit limits (`max_operations:1`, `max_branch_depth:0`). Exclude saved file paths, source bytes, session token, and prior approval. Saving a seed is an explicit local action after review. Seeds are never automatically admitted project adapters.

### 3.3 `house.maddlib.plan/v0.1`

A preview-bound concrete plan: supplied human intent, exact reviewed fuel snapshot and `fuel_sha256`, operation choice, engine version, expected output schema `house.native-maxhinal-ride/v0.1`, declared local writes and limits, and canonical `plan_sha256`. Do not include variable creation times in digest inputs. Show source path/digest or pack ID/digest, available excerpt, and metadata-only limitations. A proposed plan has no authority.

### 3.4 `house.maddlib.run/v0.1`

An occurrence identifier `run_id`, `plan_sha256`, selected seed ref if any, explicit approval record (scope + exact preview digest; **never** re-use as approval for later runs), and append-only step events. Valid states: `proposed`, `admitted`, `running`, `scoped_complete`, `refused`, `failed`, `uncertain`. Run and step statuses are observations of the bounded operation, not evaluations of creative merit. A completed run references a validated existing native ride by its storage ID and exact digest; its own source/destination identifiers do not replace the ride's.

### 3.5 Later-compatible `house.maddlib.branch/v0.1`

A branch is a *proposed* continuation with a parent run/step/output ref, human decision state, and independent identity. Initial release exposes a non-executing **continue in Creator Desk / open GRAFT** action via existing explicit user-controlled surfaces. Do not claim a saved GRAFT candidate, generated draft, or completed branch until that respective owner has produced a real saved object. Future branching may preserve rejected/unresolved paths as append-only children, but has no automatic effect in v0.1.

## 4. Operation descriptor and typed handoff

Registry entries must use or map onto existing `OperationDescriptor` and `AdapterDescriptor` in `static_workbench/adapters.py`. The first admitted operation is `house.native-maxhinal.spin/v0.1`, implemented by local `preview_fuels` and pure `spin`, with input `house.maxhinal-fuel-preview/v0.1`, output `house.native-maxhinal-ride/v0.1`, declared write only into HOUSE-owned local SQLite, no project effects, and a new approval per preview.

A saved artifact ref contains: exact storage namespace and owner, object ID, kind/schema, content digest, producing run/step identity, reading (`creative_projection`), `authority:none`, and `availability:local`. The receiver dereferences the object from the owner store and re-verifies its digest and schema; it does not trust the caller-provided envelope as evidence of existence. Unknown adapter IDs, versions, effects, input kinds, and proposed conversions fail closed.

No Maxhinal ride may be recast as a Daily Slice `.maxhinal.json` ride. No APERTURE reading may become human intent, evidence, or source text by implicit conversion. No saved recipe can authorize a runtime effect.

## 5. Preview, authorization, and execution sequence

1. User selects explicit eligible fuel; server generates `preview_fuels`, preserving the exact visible preview and digest. Planner selects one compatible native chamber (or accepts a human choice); it produces a bounded plan and `plan_sha256`. No ride has been created.
2. UI shows precise input identities, excerpts/metadata-only limitations, operation name, actual output description (**creative projection, not finished art**), local writes, and unresolved gaps. User explicitly confirms that exact preview.
3. Server checks same-origin/session write guard, `plan_sha256`, schema/version, selected operation, fuel membership and local permission. It independently reruns `preview_fuels` against current sources and compares the full `fuel_sha256` to the reviewed snapshot before admitting the attempt. If any part changed, HTTP 409; show re-preview path, never substitute fresh material silently.
4. Server calls existing **pure** `spin` only after admission and validates its format, `fuel_sha256`, source refs, and expected creative status. Store the new native ride and the corresponding composition run/step association in **one SQLite transaction**. The current `CreatorShelf.save_native_ride` is a separate transaction; composition execution must use a dedicated atomic shelf method that inserts into its same canonical ride table and the new composition tables together. Never create a ride with one transaction and then associate it using an unrelated second transaction.
5. Respond with run ID, validated native ride ID/digest, source refs, and explicit next actions. No auto-navigation into an effectful workflow. Workbench operational journal may record compact IDs/digests only, with no private creative text.

The approved digest is a **one-attempt, one-operation scope**, not a blanket permission to follow novel branches. A repeat submission must include a client-generated per-attempt `request_id` recorded in a table with a uniqueness constraint: if the same key and exact plan digest were already committed, return its existing run/ride; if the key is bound to a different digest, refuse; if absent after recovery, the only previous work could have been pure computation or a rolled-back atomic save and can be safely attempted. This establishes durable idempotency without guessing from identical source material.

If the process fails during pure calculation, no ride/run persists. If it fails during the SQLite transaction, the atomic transaction commits both or neither. If the server crashes after commit but before responding, a repeated request ID returns exactly the existing run. Do not rely on a fuel hash as a unique occurrence ID.

## 6. Persistence, security, and host boundaries

Extend `CreatorShelf`'s owner-only SQLite store, or a narrow companion module using that same database/connection, with `maddlib_seeds`, `maddlib_plans`, `maddlib_runs`, and `maddlib_step_events` (step events append-only; current run state is an indexed projection). New tables must be additive and must not rewrite existing packs/rides/drafts/GRAFT objects. A minimal first flight need not create `maddlib_branches` until the first independent branch action is implemented; keep the branch schema in the design. Keep `Journal` for compact operational witness only, not source truth or duplicate storage.

Use the existing loopback-only server and `_creator_write_guard` for **all** composition mutations, including previews that touch sensitive local source content. Enforce source-root containment, existing limits, request shape/size, bounded output storage, origin/session checks, deterministic allowlist planning, and no browser-supplied shell or arbitrary import path. Local browser session token is not a multi-user authentication system. Protect shelf/backups as private. Do not display a saved source excerpt in history unless the user explicitly opens that local object.

## 7. UI and API first flight

Suggested additive endpoints:
- `POST /api/maddlib/plans/preview` — validate human intent, recompute native fuel preview, return bounded plan, its digest, and a human-readable effect summary.
- `POST /api/maddlib/runs` — request ID, exact reviewed plan+digest and explicit confirmation; revalidate source, atomically persist one native ride + run; return saved IDs/digests. Retry of same request ID returns same committed run.
- `GET /api/maddlib/runs/{run_id}` — receipt/status and referenced ride; use the existing owner route to inspect its complete content.
- `POST /api/maddlib/seeds` and `GET /api/maddlib/seeds` — explicit seed save/list, no execution privilege; a seed applied to new fuel must go through preview and new approval.

The HOUSE home and supported fuel surfaces expose a contextual **MADDlib this** button, preselecting only the actual referenced eligible fuel. Default UI: choose fuel → outcome/flavor (advanced chamber optional) → review → **Spin and save** → inspect ride → optionally save recipe, open Creator Desk, or open GRAFT. Show unknown/unsupported fuel as unavailable with a precise explanation, not as selectable. Avoid asking a nontechnical user to type repository paths if the item already has a typed local reference. No fabricated generated-song copy, capability, or test success.

## 8. Acceptance proof

Tests (including API integration and persistent SQLite restart tests) must establish:
1. One reviewed saved Creator pack produces exactly one immutable ride and one associated composition run; stand-alone native Maxhinal flow remains unchanged.
2. Source content edits, changed file/pack preview digest, missing packs, unsafe/symlink paths, duplicate fuel, >4 fuel selections, and unsupported kinds/modes refuse before writes.
3. Metadata-only media remains labeled as uninterpreted; no fabricated multimedia semantics.
4. A HumanTerminal sense-field ref cannot enter the first-flight native fuel path, and unknown text remains unresolved.
5. Same request ID + plan returns same run/ride after repeated request or process restart; same ID + different plan refuses. Simulated save failure commits neither new ride nor new run.
6. A completed run opens after restart; stored ride digest mismatch refuses rather than silently reconstructing.
7. Unapproved proposal, stale plan, wrong session token, cross-origin write, unexpected effect, unsupported adapter version, and unreviewed seed cannot cause a spin.
8. Saved seed contains no absolute path or prior token/approval, and its reuse requires fresh source preview and confirmation.
9. Existing Creator Desk draft versioning and HumanTerminal append-only sense-field history remain unaffected.
10. Browser first flight does not require a terminal or adapter identifier; UI copy distinguishes proposal, saved ride, and finished creative artifact.

**Not acceptance criteria for v0.1:** an AI-written song, a generated video, a live OBS session, running Dogram, a project source edit, or automatic multi-branch traversal.

## 9. Suggested bounded implementation order

A. Frozen schemas, typed adapter descriptor, plan preview and contract tests.  
B. Atomic ride/run/attempt storage with crash/retry/restart tests.  
C. Narrow FastAPI endpoints with origin/session and stale-preview tests.  
D. Contextual browser interface and human-readable inspect/seed actions with UI smoke tests.  
E. Review the first flight on the target Linux machine before proposing any wider effectful adapters.

**Core law:** The human selects the particular; the machine proposes the composition; admission is local to the exact reviewed attempt; the result keeps its source and owner; the recipe may travel, but permission does not.
