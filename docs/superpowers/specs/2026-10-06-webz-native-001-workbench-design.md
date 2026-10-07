# WEBZ-NATIVE-001 — Workbench Reads Worlds Natively

**Status:** Written architectural specification for human review; not approved implementation or executable evidence.  
**Date:** 2026-10-06 (human-local)  
**Owning implementation:** `the-static-collective/static-workbench`  
**Normative neighboring design:** `the-static-collective/webZ`, `docs/superpowers/specs/2026-10-06-webz-genesis-001-design.md`  
**Design methods:** Superpowers brainstorming → written specification; Riqor software-architect boundary and evidence review.

> The Workbench browser should understand `webz::static/sanctuary` as an address for an independently declared world, not as an ordinary search term or a command to run.

## 1. Intent, approval and success

**Human instruction:** Build our browser's own native understanding of `webz::`, with the Collective's Web5-shaped reLATTE architecture available when a traveler deliberately chooses to carry something between worlds.

**Human design decision approved in chat:** **Static Workbench is the first webZ browser**, rather than creating a browser engine or starting with system-wide OS protocol registration.

**Observable success:** A person opens the existing local Static Workbench, types `webz::static/sanctuary` into an obvious address field, sees the recognized world and its doors, enters the Sanctuary, explicitly crosses to the Orchard, returns, and can inspect an optional locally recorded route after reload. Ordinary Workbench functions are unaffected. A second addressed world is genuinely a different document with a different world ID. A visit does not create a signed crossing or receive authority from the visited world.

This approval **permits producing this written design**. It does not authorize code changes, cross-repository protocol promotion, reLATTE dispatch, or new process installation; the written spec must be separately reviewed.

## 2. Existing project constraints, verified in repository

The current Workbench is a Python 3.11+ **FastAPI / Uvicorn** local-first server at loopback `127.0.0.1:13700`, with packaged static files under `static_workbench/web/` and assets mounted at `/assets`. `static_workbench/app.py` already declares fixed routes for `/`, `/arg`, `/arg/world`, `/doorhouse` and other local views. Its `static_workbench/web/index.html` has a navigator, workspace and witness rail. `/arg/world` demonstrates source-linked fictional travel, explicit manual choices, and Workbench-owned local traces. The existing DoorHouse contains explicit reLATTE **effectful** actions; a webZ address must not reuse those endpoints for navigation.

The project uses pytest and optional httpx, documented under `pyproject.toml`. The current setuptools package-data glob includes `web/*` (flat paths), so any extra nested assets require a deliberate packaging change and package-install verification.

webZ's independent GENESIS-001 spec describes two separately addressable static worlds, manifest-declared logical IDs, explicit doors, default no-carry, and browser-local replay. The webZ repository currently supplies a **design**, not a production resolver or a protocol registry. Workbench must not pretend a production webZ implementation exists.

## 3. Three alternatives considered

| Alternative | Pros | Costs / why not |
| --- | --- | --- |
| **A. Native Workbench address field and resolver adapter — selected** | Immediate useful experience; exploits fixed FastAPI routes and existing world-entry UI; no browser fork, OS hooks, provider spend or installation change. | "Native" means Workbench-native, not Chrome/Android/Linux-global. The first catalog is local and fixture-backed. |
| B. Register a desktop `webz` URI handler first | Opens addresses from other apps. | OS packaging and handler permissions become the project before the resolver actually works; browser behavior varies. |
| C. Replace / fork a web engine | Highest-level URL and renderer control. | Massive security, compatibility, update and maintenance burden; not justified by the first door. |

**Decision:** A; design its resolver behind a narrow interface, so later B can pass an address into the same safe Workbench resolver without bypassing traveler consent.

## 4. Bounded contexts and authority

| Owner | Owns | Must not silently do |
| --- | --- | --- |
| **webZ** | The proposed world-address grammar, versioned manifests, declaration of doors, portable navigation contracts. | Claim global naming authority or the power to admit foreign state. |
| **Static Workbench** | The native address field, trusted local resolver adapter, scene display, optional browser-local visit records. | Rewrite project-owned artifacts; elevate visual navigation to a verified crossing. |
| **STORYSHIP** | Its own append-only canonical voyage and human steering lineage. | Treat Workbench's local browser history as a canonical Storyship receipt. |
| **reLATTE** | Signed crossing syntax, canonical identities and source/destination receipts. | Become an automatic dependency for browsing or treat HTTP arrival as admission. |
| **Destination world** | Its own presence, entry rules and interior disposition. | Inherit origin-world claims because a visitor arrived. |
| **Human** | Choice to inspect, visit, carry, remain, return, export or erase. | Be turned into an inferred persistent identity or scored participant. |

COM⁵ supplies a possible cultural-transformation grammar **when actual creative material is deliberately offered**. It is not the runtime for merely opening a URL. A user-readable address is neither a cryptographic signature nor a proof of existence.

## 5. Native address grammar (Workbench v0)

A user types exactly:

```text
webz::static/sanctuary
webz::static/orchard/022100
```

The `webz::` spelling is the **application's textual address notation**. It is **not** a browser-native transport, installed operating-system protocol, globally registered DNS scheme, or authority claim. Do not inject it directly into an HTML `href` and expect the browser to resolve it.

The first parser recognizes `webz::` plus 2–4 lower-case ASCII path segments, each `[a-z0-9][a-z0-9_-]{0,63}`, with the entire input length capped at 256 characters. No whitespace, query parameters, fragments, credentials, encodings, Unicode confusables, control characters, percent-decoding, dot segments, colons within segments, or protocol-relative links are accepted in v0. Display a clear syntax error without redirecting.

A **closed, explicitly versioned fixture registry** maps exact human aliases to declared world IDs and local entry documents:

| Typed address | Declared world ID | Workbench render route |
| --- | --- | --- |
| `webz::static/sanctuary` | `webz:the-static-collective/sanctuary` | `/webz/world/sanctuary` |
| `webz::static/orchard/022100` | `webz:the-static-collective/orchard-022100` | `/webz/world/orchard` |

The `static` namespace and this alias map are **local fixture aliases**, not a Collective-wide namespace registration. The difference between an address alias and world identity is intentional: no rule deduces a `world_id` from string segments. Later webZ manifests can supply the mappings.

**No arbitrary URL fetch or filesystem path** may be synthesized from a typed address. The v0 registry is fixed, first-party, opt-in, and locally hosted. Unknown well-formed addresses show `UNRESOLVED — no installed world`; never guess an HTTPS endpoint or perform web search.

### First boundary interface

A pure resolver function accepts one address and one immutable registry snapshot and returns an unambiguous tagged value:

```text
ResolvedWorld {
  status: "resolved",
  typed_address: string,
  world_id: string,
  title: string,
  entry_route: string,
  manifest_revision: string,
  source: "trusted-workbench-fixture"
}
InvalidAddress {status:"invalid", error_code:string}
UnresolvedWorld {status:"unresolved", typed_address:string}
```

No state changes. No automatic navigation. The response is presented as **registry lookup**, not provenance verification. The browser UI uses text nodes/textContent for displayed manifest fields.

## 6. The browser experience

**Workbench home:** Add one clearly labeled `webZ address` input next to or within existing navigator chrome, and a visible **Resolve** button. Ordinary Workbench navigation and its existing `/arg` and `/doorhouse` continue working without typing a webZ address.

**Resolver state:** Display human-readable world ID, title, declared origin, current registry revision, resolved/unresolved/error status and a separate **Enter** button. A user can dismiss the proposal. The address bar never runs a shell command, project adapter, browser handler, or network fetch.

**World entry:** A dedicated Workbench `/webz` cockpit plus two independent `/webz/world/{slug}` pages. Use a coherent visual theme evoking the Phase 01 Sanctuary and Orchard. A portal renders the destination and **what carries: NONE**. The visitor chooses **Inspect → Cross**, **Remain**, or **Return**. Navigation among public fictional scenes is not called `ADMIT`.

**Optional voyage log:** A small, clearly marked **browser-local navigation trace** is recorded only after an explicit **Begin voyage recording** action. The user may pause, export and erase it. By default, only non-sensitive aliases, world IDs, local sequence integers and human-selected door IDs are recorded; no human names, notes, image uploads, location, secrets, or inferred traits. It is not signed, authoritative, universally replayable without exporting the same bytes, or merged into STORYSHIP automatically.

For browser storage failure or corruption, show explicit degraded state; do not fabricate a recovered history. An ordinary reload must preserve the opt-in local log when browser storage remains available. A separate pure replay test from a frozen export must reconstruct the same route.

**Source images:** The first published implementation may use CSS-designed scene silhouettes and original visual elements. Do not silently commit the chat-provided manga pages into the public Workbench repo; permissions, exact artifact provenance, and desired public scope must be explicitly resolved.

## 7. Carry and reLATTE: v0 line in the sand

Phase 1 native browsing supports **NO CARRY ONLY**. It can show a read-only, visibly disabled **Bring something across (future)** affordance, but there is no reLATTE call during RESOLVE, INSPECT, ENTER, CROSS-as-visit, RETURN or replay. A click into another world is normal web navigation, not a reLATTE `CrossingEnvelopeV0`.

A **later, separate implementation gate** may add deliberately chosen, non-sensitive artifacts:

```text
traveler declares artifact + scope
→ optional COM⁵ capsule when it is actually a creative grammar
→ preflight presentation of what would leave
→ explicit authorizing act
→ reLATTE signed crossing using an owner-pinned adapter
→ transport receipt
→ destination-local RECEIVE then HOLD/ADMIT/REFUSE/RETURN
→ traveler-facing witness/return link
```

That later gate must reuse the **real** reLATTE owner implementation through a pinned adapter and preserve its own signature and receiver laws. A regular web browser cannot simply manufacture human identity, keys, consent or destination admission. Unrecognized schemas or inaccessible destination customs fail closed.

## 8. Security, privacy, failure, and isolation

The first two worlds are **trusted first-party pages under the Workbench origin**. They have **different declared world identities**, not different browser security principals. A page hosted under the same origin may be able to read common local storage, so untrusted community-authored worlds must not be added to this design without separate origins or equivalent sandboxing and an explicit revised threat model.

No user-supplied URL-to-server fetch (SSRF), no arbitrary filesystem access, no dynamic import/eval/inline script from manifests, no protocol handler execution, no open redirect, and no privileged Workbench API automatically invoked by visiting a page. Use a fixed route allowlist and a CSP appropriate to the static view.

Errors remain visible, including invalid syntax, unknown alias, missing fixture entry, changed registry, browser storage denied, corrupted navigation log, and an attempted sensitive carry. A user may continue using normal Workbench after any failure.

No telemetry or synchronization is added. Any operational receipts remain Workbench-local; they cannot imply STORYSHIP, reLATTE, SupaBardo or human identity proof.

## 9. Executable proof contract: WEBZ-NATIVE-001

A successful implementation must produce **fresh evidence from the changed repository state**:

1. **Pure parser unit tests:** two accepted exact addresses; invalid scheme/spelling, uppercase, overlong, path traversal, escapes, whitespace, query, fragments, credentials, script-like values; unknown syntactically valid addresses yield `unresolved`, not fetch.
2. **Registry tests:** distinct world IDs, entry routes and door IDs; duplicate IDs, unapproved route, or malformed declaration rejected.
3. **Workbench API tests:** read-only resolver endpoint returning tagged outcomes with no code execution, filesystem traversal, redirect or permission escalation.
4. **Browser behavior:** address entered → Resolve → explicit Enter → Sanctuary; Inspect → Cross → Orchard; explicit Return → Sanctuary. "Remain" does nothing. Resolve never navigates.
5. **Local log:** opt-in before recording; reload persistence; explicit export/erase; corrupted or unavailable storage visible; same exported events produce byte-identical canonical route projection in independent processes.
6. **Reroute/negative witness:** a nonexistent world does not display a fabricated arrival and the browser stays usable; no automatic reLATTE crossing or adapter invocation occurs.
7. **Compatibility:** existing `/arg`, `/arg/world`, `/doorhouse`, `/`, package installation and relevant pytest suites remain operational; no change to repo-owned project state by a GET request.
8. **UI checks:** mobile and desktop layout, keyboard operation, focus visibility, reduced motion, accessible statuses and no hidden auto-crossing.
9. **Evidence output:** exact code commit, test command outputs, browser screenshots or session trace and a limitation report; no claim of browser test completion if only Python tests ran.

An accepted WEBZ-NATIVE-001 does **not** establish public Web5 federation, registered protocol-handler support, reLATTE signed portal crossing, cross-origin sandbox isolation, or a working STATIC OS distribution.

## 10. Expected file map for implementation planning

Provisional, to be verified and narrowed against current code during the plan:

```text
static_workbench/webz_native.py                    # Pure, no-network parser/registry resolver
static_workbench/web/webz-registry.json             # Frozen first-party v0 fixture
static_workbench/web/webz.html                      # Native Workbench cockpit
static_workbench/web/webz.js                        # Address + explicit entry UI
static_workbench/web/webz.css                       # Responsive portal treatment
static_workbench/web/webz-sanctuary.html            # Independent local first-party world
static_workbench/web/webz-orchard.html              # Independent local first-party world
static_workbench/web/index.html                     # Native browser link/field
static_workbench/app.py                             # Add fixed read-only resolver and render routes
tests/test_webz_native.py                           # Grammar, registry, route, security
tests/test_webz_voyage.py                           # Pure local-log replay, negative scenarios
docs/superpowers/specs/2026-10-06-webz-native-001-workbench-design.md
```

The flat `static_workbench/web/*` layout is intentional for the existing packaging glob. If the implementation plan instead uses nested assets, it must explicitly test the installed wheel/venv for their presence.

Separate, independently governed webZ manifests may later replace these frozen snapshots through exact-version bindings. The adapter must not learn reLATTE's internal receipt grammar as part of mere address resolution.

## 11. Architectural decision record

### ADR-WEBZ-NATIVE-001 — First-native browser = Workbench

**Status:** Design selection approved in chat; specification pending review.

**Context:** The Collective has a local-first browser workbench, an authored STORYSHIP scene-world, a foundational webZ design and working reLATTE crossing machinery. A person needs to type `webz::` and reach an authored world *now*, without replacing the Internet or inheriting foreign authority.

**Decision:** Put the address bar and safe, deterministic resolver adapter in Static Workbench. Keep logical world declaration under webZ design ownership. Treat initial aliases as local fixtures. Show separate human gates for resolving, entering and crossing; treat no-carry visits as navigation only. Defer OS URI handler registration and signed material crossings.

**Consequences:** Fast, testable, reversible native experience for Workbench. No global discovery or cross-origin trust claims. Later system-wide handlers can delegate to the same resolver if a separate authority/security review permits them.

> **The browser recognizes the address. The door presents the destination. The traveler decides. The world keeps its own laws.**

---

**Next required gate:** human review of this committed design. After explicit approval, use Superpowers `writing-plans` to prepare an implementation plan for the real Workbench and webZ codebase, then ask the human to choose the execution method. Runtime implementation must wait for those gates.
