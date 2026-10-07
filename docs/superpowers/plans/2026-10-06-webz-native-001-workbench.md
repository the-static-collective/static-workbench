# WEBZ-NATIVE-001 — Workbench-Native World Addressing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make existing Static Workbench natively resolve `webz::` addresses and visibly navigate Sanctuary → Orchard → Sanctuary by explicit human choices, with optional deterministic browser-local voyage replay and no unintended reLATTE execution.

**Architecture:** Add a pure, allowlisted Python resolver and two first-party world declarations behind narrow read-only FastAPI endpoints. Mount the address UI and separately addressable first-party HTML worlds inside the existing Workbench browser, using a small testable JavaScript module for opt-in local navigation receipts. The actual webZ protocol core remains owned by webZ; Workbench v0 is an explicitly labeled fixture adapter, not protocol registration or federated identity.

**Tech Stack:** Python >=3.11, FastAPI >=0.115,<1, existing `pytest` / `httpx`, vanilla HTML/CSS/ES modules, browser localStorage (opt-in only), and Node.js >=22 **as an optional development-time JavaScript test runner**, not a Workbench runtime dependency.

**Spec:** `docs/superpowers/specs/2026-10-06-webz-native-001-workbench-design.md`

## Global Constraints

- **Design selection approved:** Static Workbench is the first native `webz::` browser. The reviewed specification is approved for implementation planning; **this plan still requires human review and execution-method selection** before implementation.
- The Workbench is local-first and loopback-bound at `127.0.0.1:13700`; preserve existing host/session guards, `/`, `/arg`, `/arg/world` and `/doorhouse`.
- `webz::` is Workbench-readable **textual address syntax**, not an OS handler, an HTTP protocol, or a global name registration.
- Parser grammar: literal `webz::` followed by **2–4** lower-case ASCII path segments matching `[a-z0-9][a-z0-9_-]{0,63}`; whole address length **<=256**. Refuse control characters, percent escapes, whitespace, dot segments, query, fragment, unexpected colon, encoded URLs, credentials and path traversal.
- Only `webz::static/sanctuary` → `webz:the-static-collective/sanctuary` → `/webz/world/sanctuary` and `webz::static/orchard/022100` → `webz:the-static-collective/orchard-022100` → `/webz/world/orchard` resolve in v0.
- Unknown syntactically valid addresses yield **unresolved** rather than guessed HTTP endpoints, arbitrary file paths, external fetches or auto-search.
- RESOLVE ≠ ENTER ≠ VISIT. The first slice is **NO CARRY ONLY**. No signed reLATTE envelope, SupaBardo transfer, STORYSHIP ledger update, GHoT dispatch or other project effect occurs through visiting.
- Every world keeps its own declared identity, door IDs, revision and title. Both first worlds are *trusted same-origin* pages: distinct world IDs do **not** imply browser security isolation.
- Browser-local recording is **opt-in**, contains no private human notes or identifiers, supports export and erase, survives reload if storage works, and is explicitly noncanonical. Corrupted/denied storage yields visible degraded state rather than fabricated events.
- No hidden provider API, new server, browser fork, operating-system protocol handler, third-party JavaScript CDN, telemetry, account, automatic permissions or cross-origin import.
- Use original CSS/graphics where practical; do not copy the user-supplied manga files into this public repository without a separately confirmed rights/publication scope.
- Existing `pyproject.toml` includes `static_workbench = ["web/*"]`; use flat `static_workbench/web/` assets unless installation-verification justifies an explicit change.
- Preserve existing Workbench project-native boundaries; do not refactor DoorHouse or its reLATTE capability routes.
- Each behavioral task follows **RED → GREEN → focused verification → commit**. After all mutations, run the full regression gate and record exactly what was/wasn't browser-tested.

## Review Focus

Five likely user-facing misses inferred from the spec, with their owning tests below:

1. **An otherwise valid unknown address:** Task 1 asserts `unresolved` and zero attempted fetches rather than opening an arbitrary URL.
2. **A broken or stale registry file:** Task 2 asserts that webZ resolution returns a clearly labeled 503 while normal Workbench `/` still renders.
3. **A portal clicked twice / reload after arrival:** Task 6 asserts no duplicated local arrival and no fabricated destination event on an unresolved route.
4. **Browser storage denied or truncated JSON:** Task 5 unit-tests explicit unavailable/corrupt results and Task 6 requires an in-browser warning while visits remain possible.
5. **A seemingly harmless full URL pasted into `webz::`:** Task 1 rejects `webz::http://example.test`, encoded slash, dot segments, credentials, fragments and scheme-change attempts; no redirect or server-side HTTP fetch.

---

## File Map

| Path | Responsibility |
| --- | --- |
| `static_workbench/webz_native.py` | Pure parser, registry validator/loader and deterministic read-only resolver, independent of FastAPI. |
| `static_workbench/web/webz-registry.json` | Frozen Workbench-local aliases and fixed route/manifest filenames (not a global naming registry). |
| `static_workbench/web/webz-sanctuary.json`, `webz-orchard.json` | Separate `webz/world/v0` world declarations with independent identities and doors. |
| `static_workbench/app.py` | Fixed `/webz`, world-render and read-only `/api/webz` endpoints; retain guard/mount behavior. |
| `static_workbench/web/index.html` | Visible entry to webZ cockpit; do not replace existing home view. |
| `static_workbench/web/webz.html`, `webz.js`, `webz.css` | Address bar, resolve/inspect/enter screen and accessible responsive styling. |
| `static_workbench/web/webz-sanctuary.html`, `webz-orchard.html`, `webz-world.js` | Separately addressable first-party pages and explicit portal/return controls. |
| `static_workbench/web/webz-voyage.mjs` | Pure canonical local-voyage event validation, append and replay projection. |
| `static_workbench/web/webz-storage.mjs` | Browser-only opt-in preference, persistence, pending-crossing correlation, export/erase/error states. |
| `tests/test_webz_native.py` | Resolver, grammar, registry and trust-boundary tests. |
| `tests/test_webz_routes.py` | TestClient route/HTML and regression-boundary tests. |
| `tests/webz-voyage.test.mjs` | Native Node `node:test` pure deterministic replay/negative-input tests. |
| `tests/test_webz_package.py` | Installed-wheel flat-assets test; launch should not rely on repository-relative files. |
| `README.md` | How to reach webZ and its explicit non-claims. |
| `docs/receipts/webz-native-001.md` | Real run/verification outputs, browser screenshots/trace locations and honest limitations, added only after execution. |

### Contract decisions to keep stable across tasks

**Registry document:** `{"schema":"webz/registry/v0","aliases":[{"typed_address":"webz::static/sanctuary","manifest_file":"webz-sanctuary.json","entry_route":"/webz/world/sanctuary"},...]}`. Only exact frozen manifest filenames and entry routes in the v0 allowlist are permitted. No dynamic path interpolation from user input.

**World declarations:** `{"schema":"webz/world/v0","world_id":"webz:the-static-collective/sanctuary","revision":"genesis-001","title":"Psychedelic Punk Sanctuary","doors":[{"door_id":"sanctuary-to-orchard","label":"Follow the orchard light","to_world_id":"webz:the-static-collective/orchard-022100","carry_mode":"none"}]}`; Orchard has an independently identified return door `orchard-to-sanctuary`. Any manifest `entry` field must match the allowlisted route; reject unknown sidecar fields rather than executing them.

**Resolver response:** `{"status":"resolved","typed_address":"webz::static/sanctuary","world_id":"webz:the-static-collective/sanctuary","title":"Psychedelic Punk Sanctuary","entry_route":"/webz/world/sanctuary","manifest_revision":"genesis-001","source":"trusted-workbench-fixture"}`; `invalid` and `unresolved` have explicit status and no entry route. HTTP resolver always returns one tagged result on a well-formed request, never an HTTP redirect.

**Event schema:** `webz/voyage-local/v0`. The pure module accepts a sequence of `departed` and `arrived` records with `seq`, `kind`, `from_world_id`, `to_world_id`, `door_id`, `carry_mode:"none"`, `authority:"browser-local-observation"` and `basis_departure_seq` only for an arrival. Arrival must match exactly one unmatched earlier departure. This is **local navigation testimony**, not proof of external world admission.

---

### Task 1: Safe native address resolver and independent world declarations

**Files:**
- Create: `static_workbench/webz_native.py`
- Create: `static_workbench/web/webz-registry.json`
- Create: `static_workbench/web/webz-sanctuary.json`
- Create: `static_workbench/web/webz-orchard.json`
- Test: `tests/test_webz_native.py`

**Interfaces:**
- Consumes: Python stdlib `json`, `re`, `pathlib.Path` and frozen registry/manifest bytes.
- Produces: `class WebzRegistryError(ValueError)`; `parse_webz_address(text: str) -> tuple[str, ...]`; `load_registry(web_dir: Path) -> dict`; `resolve_webz_address(address: str, registry: dict) -> dict`; `world_by_slug(slug: str, registry: dict) -> dict | None`.

- [ ] **Step 1: Write failing tests in `tests/test_webz_native.py`.** Names: `test_parser_accepts_exact_first_world_addresses`, `test_parser_rejects_unsafe_or_ambiguous_inputs`, `test_registry_loads_two_distinct_worlds_and_doors`, `test_invalid_registry_rejected`, `test_unknown_address_never_fetches`. Assert acceptance for `webz::static/sanctuary` and `webz::static/orchard/022100` and rejection for `webz::http://example.test`, `webz::static/%2f`, `webz::static/../orchard`, `webz::static/a?x=1`, `webz::static/a#x`, `webz::static/a@b`, uppercase, one segment, five segments, blank, control characters and >256 chars. Assert unknown `webz::static/unbuilt` → `{"status":"unresolved",...}` with no entry route. Mutate a copy of the registry with duplicate aliases, world IDs or door IDs, unapproved route or path-like `manifest_file` and assert `WebzRegistryError`.
- [ ] **Step 2: Run the tests RED.** `pytest -q tests/test_webz_native.py`; expected FAIL on missing module/fixtures.
- [ ] **Step 3: Implement the interfaces and frozen manifest assets.** `parse_webz_address` raises `ValueError` for invalid syntax; `resolve_webz_address` catches syntax errors into tagged `invalid`, returns `unresolved` for absent alias, otherwise `resolved`. `load_registry` reads only **two hard-coded expected manifest basenames** from the supplied trusted `web_dir`; validates exact `schema`, required keys, allowed entry routes, unique identities/doors and reciprocal declared door targets. The module never performs HTTP, traverses arbitrary paths or invokes adapters. `world_by_slug` is restricted to `"sanctuary"` or `"orchard"`.
- [ ] **Step 4: Run the tests GREEN.** `pytest -q tests/test_webz_native.py`; expected all PASS.
- [ ] **Step 5: Commit.** `git add static_workbench/webz_native.py static_workbench/web/webz-*.json tests/test_webz_native.py && git commit -m "feat(webz): validate fixed world addresses and declarations"`.

### Task 2: Read-only Workbench webZ routes, with normal Workbench surviving errors

**Files:**
- Modify: `static_workbench/app.py` (near `create_app` lines 312–375 and route declarations).
- Create: `static_workbench/web/webz.html` (minimal renderable markup, enhanced Task 3).
- Create: `static_workbench/web/webz-sanctuary.html` (minimal separate page, enhanced Task 4).
- Create: `static_workbench/web/webz-orchard.html` (minimal separate page, enhanced Task 4).
- Test: `tests/test_webz_routes.py`

**Interfaces:**
- Consumes: Task 1 `load_registry`, `resolve_webz_address`, `world_by_slug`, `WebzRegistryError`.
- Produces: `GET /api/webz/resolve?address=<encoded>` → tagged JSON; `GET /api/webz/worlds/{slug}` → declaration or 404; `GET /webz`, `GET /webz/world/sanctuary`, `GET /webz/world/orchard` → fixed HTML views, never redirects.

- [ ] **Step 1: Write failing TestClient tests.** `test_webz_pages_are_separate` asserts HTTP 200 for three pages, distinct world labels, and normal `/`/ `/arg` / `/doorhouse` still 200. `test_resolve_api_is_read_only_and_tagged` asserts exact resolved/invalid/unresolved responses and no `Location` header. `test_unknown_slug_is_404` asserts `/api/webz/worlds/elsewhere` fails. `test_corrupt_registry_does_not_break_workbench` monkeypatches the registry loader to raise `WebzRegistryError` and asserts `GET /api/webz/resolve` returns clear 503 while `GET /` remains 200. `test_webz_resolver_does_not_write_journal_or_dispatch` compares Workbench journal count and/or monkeypatches effectful adapters to fail if invoked.
- [ ] **Step 2: Run RED.** `pytest -q tests/test_webz_routes.py`; expected FAIL for absent routes/templates.
- [ ] **Step 3: Implement minimal fixed routes in `create_app`.** Use existing `web_dir`, `FileResponse` and loopback host guard. Read registry in request scope via `load_registry(web_dir)` or a validated cache; an invalid registry returns 503 **for webZ endpoints only**. Accept a bounded query string without executing it; parser returns tagged `invalid` for >256. No new POST, no third-party fetch, no dynamic `FileResponse` filename from untrusted slug. Leave session checks for effectful existing routes unchanged.
- [ ] **Step 4: Run GREEN.** `pytest -q tests/test_webz_routes.py tests/test_world_entry.py tests/test_first_door.py`; expected all PASS.
- [ ] **Step 5: Commit.** `git add static_workbench/app.py static_workbench/web/webz*.html tests/test_webz_routes.py && git commit -m "feat(webz): expose safe read-only world resolution in Workbench"`.

### Task 3: Workbench-native address input and inspect-before-enter UI

**Files:**
- Modify: `static_workbench/web/index.html`
- Modify: `static_workbench/web/webz.html`
- Create: `static_workbench/web/webz.js`
- Create: `static_workbench/web/webz.css`
- Modify: `tests/test_webz_routes.py`

**Interfaces:**
- Consumes: Task 2 `GET /api/webz/resolve` and fixed `/webz` entry.
- Produces: visible Workbench entry link, form with `id="webz-address"`, `id="webz-resolve"`, read-only result view `id="webz-result"`, and separate `id="webz-enter"` button revealed only on `resolved`.

- [ ] **Step 1: Add failing interface tests.** `test_workbench_links_to_webz_cockpit` checks `href="/webz"` on the main page; `test_webz_cockpit_uses_distinct_resolve_and_enter_controls` checks correct labels, required IDs and `<script type="module" src="/assets/webz.js">`; `test_webz_assets_use_text_nodes_and_safe_navigation` checks JS uses `textContent`, same-origin fixed `entry_route` after explicit Enter, no `innerHTML`, `eval`, or direct `webz::` `href`.
- [ ] **Step 2: Run RED.** `pytest -q tests/test_webz_routes.py`; expected FAIL for missing controls/assets.
- [ ] **Step 3: Add markup, separate event handlers, statuses and styles.** Submit/Resolve calls only the read-only API; it does not mutate `window.location`. Enter remains disabled/hidden until an exact resolved reply arrives; Enter navigates only to one of `/webz/world/sanctuary` or `/webz/world/orchard` and clears its enabled status if input changes. Render title, world ID, revision, source and no-carry label with safe text nodes. Maintain readable desktop/mobile layout, keyboard focus, `aria-live`, `prefers-reduced-motion` and error states. If API fails, show error without opening any world.
- [ ] **Step 4: Run GREEN and inspect.** `pytest -q tests/test_webz_routes.py`; expected PASS. Inspect rendered cockpit in a real browser before declaring interface ready; retain browser evidence for final task.
- [ ] **Step 5: Commit.** `git add static_workbench/web/index.html static_workbench/web/webz.html static_workbench/web/webz.js static_workbench/web/webz.css tests/test_webz_routes.py && git commit -m "feat(webz): add native address bar and explicit world entry"`.

### Task 4: Two independently addressable fictional worlds and real visible portals

**Files:**
- Modify: `static_workbench/web/webz-sanctuary.html`
- Modify: `static_workbench/web/webz-orchard.html`
- Create: `static_workbench/web/webz-world.js`
- Modify: `static_workbench/web/webz.css`
- Modify: `tests/test_webz_routes.py`

**Interfaces:**
- Consumes: Task 1 world/door IDs, Task 2 `GET /api/webz/worlds/{slug}`, Task 3 styles.
- Produces: a scene-led Sanctuary and Orchard with `data-webz-world="sanctuary"` / `"orchard"`, inspectable portal details and separate **Inspect**, **Cross**, **Remain**, **Return** controls. The `webz-world.js` file gets declared doors only from trusted local API.

- [ ] **Step 1: Write failing world assertions.** `test_both_worlds_have_distinct_identity_and_accessible_portals` asserts both pages have distinct `data-webz-world`, manifest-backed IDs, visible no-carry notice and module script; `test_unknown_portal_target_is_not_browsed` checks unknown IDs result in an unresolved view and no generated external link. Add a JS browser-level trace assertion in final Task 7: no navigation before clicking Cross.
- [ ] **Step 2: Run RED.** `pytest -q tests/test_webz_routes.py`; expected FAIL.
- [ ] **Step 3: Implement two original HTML/CSS scenes plus `webz-world.js`.** Use original CSS silhouettes and copy (do **not** silently publish manga source files). On load, read known slug, query `/api/webz/worlds/{slug}`, and show world/door data safely. Inspect only reveals the destination and `carry_mode:"none"`. Cross requires a second deliberate click, looks up the target in the bounded local registry / resolver and navigates to the fixed route. Remain hides the proposal. Return is the independently declared Orchard→Sanctuary door, not browser history heuristics. Invalid or missing declarations display unresolved status with the current world still usable.
- [ ] **Step 4: Run GREEN.** `pytest -q tests/test_webz_routes.py`; expected PASS. Browser walkthrough: enter Sanctuary, inspect (no navigation), remain (no navigation), inspect again, cross to Orchard, return. Record screenshots after actual run; no mere text-test claim is sufficient.
- [ ] **Step 5: Commit.** `git add static_workbench/web/webz-*.html static_workbench/web/webz-world.js static_workbench/web/webz.css tests/test_webz_routes.py && git commit -m "feat(webz): open independently declared Sanctuary and Orchard worlds"`.

### Task 5: Deterministic, append-only **local** voyage projection

**Files:**
- Create: `static_workbench/web/webz-voyage.mjs`
- Create: `tests/webz-voyage.test.mjs`

**Interfaces:**
- Consumes: plain JSON event arrays (no DOM, filesystem, clocks or localStorage).
- Produces: `appendVoyageEvent(events, event) -> newEvents`; `projectVoyage(events) -> {schema,visits,pending_departure_seq,current_world_id}`; `canonicalVoyageProjection(events) -> string`; `parseVoyageExport(text) -> events` (validate exact `webz/voyage-local/v0` export wrapper with explicit `events`).

- [ ] **Step 1: Write failing Node tests.** `test("Sanctuary Orchard Sanctuary reconstructs")` supplies frozen six-event `departed/arrived` sequence for Sanctuary→Orchard and Orchard→Sanctuary plus a separate starting-world declaration encoded in export metadata; assert visits equal `["webz:the-static-collective/sanctuary","webz:the-static-collective/orchard-022100","webz:the-static-collective/sanctuary"]` and canonical byte-string stable on repeated replay. `test("mutating input does not mutate ancestors")`, `test("double arrival or wrong door refuses")`, `test("arrival cannot predate departure")`, `test("truncated malformed export fails closed")`, `test("unknown event field or sensitive note rejected")`, `test("unmatched departure stays pending")`. Encode starting world and its world identity in export metadata, not by inventing an arrival. Correct the event count in fixture to **four** crossing events (two departed + two arrived); use an explicit initial-world metadata field, rather than a fake departure/arrival pair.
- [ ] **Step 2: Run RED.** `node --test tests/webz-voyage.test.mjs`; expected FAIL because module is missing.
- [ ] **Step 3: Implement pure immutable schema validation, correlation and projection.** `appendVoyageEvent` clones input, enforces monotonically increasing seq starting at 1, exact permitted fields, safe IDs, `carry_mode:"none"` and `authority:"browser-local-observation"`. Each `arrived` names an existing unmatched `departed` by `basis_departure_seq` and must match its source/destination/door; duplicate arrival throws. Projection carries initial world separately, includes only completed arrivals as visits, and reports unmatched departures without pretending successful arrival. `canonicalVoyageProjection` uses a fixed-key-order JSON object, excludes wall-clock timestamps, and is stable for identical validated inputs. A hash (if added) only addresses bytes, never human identity or signature.
- [ ] **Step 4: Run GREEN.** `node --test tests/webz-voyage.test.mjs`; expected PASS in two fresh Node processes with byte-identical projection.
- [ ] **Step 5: Commit.** `git add static_workbench/web/webz-voyage.mjs tests/webz-voyage.test.mjs && git commit -m "feat(webz): replay browser-local voyage without authority claims"`.

### Task 6: Opt-in browser storage, single arrival per crossing and export/erase controls

**Files:**
- Create: `static_workbench/web/webz-storage.mjs`
- Modify: `static_workbench/web/webz-world.js`
- Modify: `static_workbench/web/webz.html`
- Modify: `static_workbench/web/webz.js`
- Modify: `static_workbench/web/webz.css`
- Modify: `tests/webz-voyage.test.mjs`
- Modify: `tests/test_webz_routes.py`

**Interfaces:**
- Consumes: Task 5 pure `appendVoyageEvent`, `projectVoyage`, `parseVoyageExport` and browser `Storage`.
- Produces: `readVoyage(storage) -> tagged state`; `beginRecording(storage, initial_world_id) -> tagged state`; `recordDeparture(storage, from_world_id, to_world_id, door_id) -> tagged state`; `confirmArrival(storage, to_world_id) -> tagged state`; `exportVoyage(storage) -> string`; `eraseVoyage(storage) -> void`. All user-visible UI actions call these helpers only when explicitly requested.

- [ ] **Step 1: Write RED tests.** Use an in-memory Storage stub with `getItem/setItem/removeItem`, one stub that throws `QuotaExceededError`, and one that returns truncated JSON. Assert recording defaults OFF; only **Begin voyage recording** persists a log; reading denied/corrupt data returns `unavailable`/`corrupt` without overwriting it; exporting a valid log is deterministic and contains no notes/identities; erase removes the log; clicking the same portal twice and reloading the destination never creates duplicate `arrived` events. Add route HTML tests for visible opt-in, export, erase, disabled-recording label.
- [ ] **Step 2: Run RED.** `node --test tests/webz-voyage.test.mjs && pytest -q tests/test_webz_routes.py`; expected FAIL for absent module/controls.
- [ ] **Step 3: Implement storage adapter and UI.** Use a single namespaced localStorage key `webz.voyage-local.v0`, no notes, no hidden default recording. Persist a `departed` event *before* navigation only if recording is enabled; on destination page load, call `confirmArrival` only if its exact world ID matches the pending event and that arrival has not already been recorded. If target fails to load, leave `pending_departure_seq` visible. Storage errors show a status message, **do not block no-carry visits**, and never silently reset corrupted history. Separate export to downloaded JSON and erase with explicit confirmation.
- [ ] **Step 4: Run GREEN.** `node --test tests/webz-voyage.test.mjs && pytest -q tests/test_webz_routes.py`; expected PASS. Verify browser reload preserves opted-in itinerary; fresh browser without recorded events begins empty; failure-mode UI remains usable.
- [ ] **Step 5: Commit.** `git add static_workbench/web/webz-storage.mjs static_workbench/web/webz-world.js static_workbench/web/webz.html static_workbench/web/webz.js static_workbench/web/webz.css tests/webz-voyage.test.mjs tests/test_webz_routes.py && git commit -m "feat(webz): gate and persist optional local voyage records"`.

### Task 7: Wheel packaging, regression gates, browser evidence and operator documentation

**Files:**
- Create: `tests/test_webz_package.py`
- Modify: `README.md`
- Create: `docs/receipts/webz-native-001.md`
- Modify: `pyproject.toml` **only if needed** to include the planned flat assets in the installed wheel.

**Interfaces:**
- Consumes: committed code and fixtures from Tasks 1–6.
- Produces: reproducible installed-wheel, Python/Node and actual-browser evidence with explicit status.

- [ ] **Step 1: Write RED packaging test.** `test_webz_flat_assets_are_in_installed_wheel` builds a wheel in a temporary directory via `python -m pip wheel --no-deps . -w <temp-wheel-dir>` and inspects its ZIP members for `webz.html`, `webz.js`, `webz.css`, `webz-world.js`, `webz-voyage.mjs`, `webz-storage.mjs`, `webz-registry.json`, the two manifests, and the two world HTML pages. Assert missing asset fails. Use the existing flat `web/*` pattern unless this actual check proves otherwise.
- [ ] **Step 2: Run RED or justified initial GREEN.** `pytest -q tests/test_webz_package.py`; expected FAIL until all expected installed assets exist. If files already satisfy it, record **initial GREEN** rather than inventing a RED.
- [ ] **Step 3: Finish packaging/doc details only.** Include clear `README.md` local instructions (existing Workbench launch at `127.0.0.1:13700`, then `/webz`), examples of both address strings, no-carry law, local recording opt-in, privacy/export/erase steps, and explicit distinction between Workbench textual scheme support and future OS-native handler/reLATTE crossings. Avoid new runtime dependencies.
- [ ] **Step 4: Run full fresh verification against final tree.** `pytest -q` then `node --test tests/webz-voyage.test.mjs`; `python -m pip wheel --no-deps . -w <temp-wheel-dir>`; `pytest -q tests/test_webz_package.py`. Use a real local browser to inspect **desktop and mobile layouts**, keyboard-only Resolve/Enter/Inspect/Remain/Cross/Return, focus and reduced-motion, A→B→A route, empty/default no-recording, record/reload/export/erase, unknown address, corrupt/denied storage, and unavailable target. Capture actual screenshots or a browser trace; do not claim browser validation if unavailable.
- [ ] **Step 5: Record evidence and commit.** In `docs/receipts/webz-native-001.md`, write final commit SHA, exact commands, pass/fail counts, screenshot artifact paths and unverified limits; if screenshots cannot be produced, mark **browser proof not run** and do not upgrade to "native browser verified." `git add tests/test_webz_package.py README.md docs/receipts/webz-native-001.md pyproject.toml && git commit -m "docs(test): record verified native webZ browser limits"`. Re-run required verification after this final mutation (including the wheel check), capturing the **final** commit head.

---

## Review / Integration Gates

1. **Design owner:** The approved spec remains linked; re-check any code/manifest change against the explicit no-carry, local-authority and privacy constraints.
2. **Reviewer:** Inspect unknown addresses, `file://`/URL injection, JSON corruption, storage ownership, route allowlists, untrusted-data rendering and GET side effects. Workbench serves **trusted same-origin** worlds only; no security equivalence to cross-origin federation.
3. **Independent run:** Compare the same frozen export in two fresh processes; run Python tests and browser proof from the same branch head after the final code mutation. Project startup journal behavior must not be confused with resolution side effects.
4. **PR:** Present exact commits, reviewer findings, completed checks and unearned capabilities. Do not auto-merge, call a demo a protocol deployment, or call a visit a signed reLATTE crossing.
5. **Next independent proposal:** A later `WEBZ-RELATTE-002` could add a truly signed, human-selected artifact crossing using reLATTE's own pinned receiver/porch contracts. That must have a separate human authorization, threat model and testable evidence.

**Execution handoff:** Human reviews this implementation plan and chooses **Subagent-driven** or **Native**. Neither choice is presumed by design approval; code work starts only after explicit selection.
