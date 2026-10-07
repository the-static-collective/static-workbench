# Static Workbench

> **Static Collective compass:** [Front Room](https://github.com/the-static-collective/What-is-the-static-collective-) · [Living Git Map](https://github.com/the-static-collective/What-is-the-static-collective-/tree/main/atlas)

A local-first browser workbench for a dedicated Static Collective Linux machine.

**v0.2 remains intentionally read-only against project state.** It exposes the host, configured filesystem roots, Git repository state, a durable Workbench witness journal, and a deterministic HumanTerminal/APERTURE specimen that writes only Workbench-owned local semantic receipts. It does **not** yet execute or mutate Toaster, Dogram, ALEX, 3rdi, LOADOUT, or Static Live.

The browser is the desk. The supervisor is the local process boundary. Project-native identities and receipts remain owned by their projects.

## What v0.2 does

- serves a three-region browser desk at `http://127.0.0.1:13700`
- samples CPU, memory, disks, uptime, load average, and Linux thermal sensors when available
- discovers Git repos below explicitly configured roots
- shows branch, HEAD, clean/dirty state, and upstream ahead/behind when available
- inspects files/directories only inside configured roots
- previews bounded UTF-8 text without evaluating imported content
- refuses absolute paths, parent traversal, and symlink escape
- persists Workbench operational events in SQLite across browser and supervisor restarts
- adds a HumanTerminal view that preserves RAW input, APERTURE Signal/Context/Gap, bounded sense-field readings, and TRIAD candidates
- keeps sense-field history append-only: later context creates a child cut rather than rewriting earlier ambiguity
- uses a deliberately tiny deterministic provider for the frozen `The bank moved.` ambiguity specimen; unknown text returns a literal carrier plus an unresolved-gap receipt rather than invented semantics
- keeps T5/FLAN-T5 outside v0.1: APERTURE/TRIAD is the protocol grammar; a model is only a future replaceable provider
- keeps the future project-adapter contract descriptor-only in v0.1

## STATIC ARG / First Door (experimental)

Open **STATIC ARG · First Door** in the navigator, or visit `/arg`, to opt into a
local-only seed → machine → world → door → return composition game. Human-entered
Seeds are immutable and source-linked; Machines preserve two distinct Seed digests;
Worlds need a fresh third Seed and one human-authored rule. A World offers explicit
navigation to the existing House, MADDLOOP, and Book of Machines surfaces, preserving
a local encounter trail across restarts in `state_dir/static_arg.sqlite3`.

This is an optional creative/game sketch, not integration with the Full Measure
shared world, project-native execution, or an automatic source of project authority.
Normal Workbench works without entering the game. See
[STATIC-ARG-001 scope and first-use guide](docs/static-arg-first-door-001.md).

## STATIC ARG / World Entry 001 (experimental)

A composed World now has an **Enter World** doorway on its ARG collection card.
It opens a four-location, source-linked fictional world: Threshold, Workshop,
Seed Garden, and a Return Archive that unlocks after examining the first three
objects. Room visits and source-linked discoveries survive Workbench restart
in the existing local ARG SQLite database. This is manual, local-only game
navigation, not project execution, shared multiplayer, or Full Measure
admission. See [World Entry play guide](docs/static-arg-world-entry-002.md).

## HumanTerminal / APERTURE v0.1

> **Status: ACTIVE / EXPERIMENTAL.** This is a live Workbench development surface and the current HumanTerminal intake frontier. It is intentionally non-canonical: active means we are using and testing it, not that APERTURE/TRIAD has been promoted into ecosystem-wide law.

Open **HumanTerminal** in the navigator and submit:

```text
The bank moved.
```

The deterministic specimen preserves three readings rather than choosing one:

```text
bank.financial
bank.river
bank.maneuver
```

Then keep that cut selected as the parent and add attributable context:

```text
After the flood, the bank moved six feet east.
```

The new cut narrows to `bank.river`, while the earlier three-reading cut remains present in SQLite as historically correct for its earlier context.

The boundary is explicit:

```text
possible meaning != intended meaning
semantic role != constitutional posture
```

Unknown input is not sent through a hidden general-purpose model. Until a provider is explicitly added, it is retained as a literal carrier with `no_deterministic_fixture` and `status: unresolved`. This refusal is intentional.

## Zorin / Ubuntu-family install

From a terminal:

```bash
sudo apt update
sudo apt install -y python3-venv git

# Put the source wherever you want the Workbench itself to live.
cd ~/static-workbench
python3 -m venv .venv
.venv/bin/pip install -e .

mkdir -p ~/.config/static-workbench
cp config.example.toml ~/.config/static-workbench/config.toml
nano ~/.config/static-workbench/config.toml
```

Point the first `[[roots]]` entry at the parent directory containing the repos you want visible. A practical layout is:

```text
~/static/
  the-haunted-toaster/
  Dogram/
  ALEX.2/
  3rdi/
  LOADOUT/
  static-live/
```

Then run directly:

```bash
STATIC_WORKBENCH_CONFIG=~/.config/static-workbench/config.toml .venv/bin/static-workbench
```

Open `http://127.0.0.1:13700` in the local browser.

## Start automatically at login

After the virtualenv install and config edit:

```bash
./scripts/install-user-service.sh
```

Useful commands:

```bash
systemctl --user status static-workbench.service
journalctl --user -u static-workbench.service -f
systemctl --user restart static-workbench.service
systemctl --user disable --now static-workbench.service
```

The unit binds only to loopback through the Workbench configuration. v0.1 does not expose a LAN service.

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest -q
```

Run manually:

```bash
STATIC_WORKBENCH_CONFIG=./config.example.toml static-workbench
```

If `~/static` does not exist yet, either create it or edit the example configuration before starting.

## Current boundaries

The Workbench journal is operational bookkeeping, **not** a replacement for project-native receipts or TranchNode. HumanTerminal sense-field receipts are likewise Workbench-owned formation history, not evidence or project authority. A Workbench invocation/correlation identity never replaces source or destination identity.

No browser request can provide a shell command. Git inspection uses fixed command arrays. Filesystem inspection resolves root-qualified relative paths and verifies the final target remains within the root.

The future adapter shape is represented in `static_workbench/adapters.py`, but descriptor presence grants no execution authority. The intended lifecycle remains:

```text
prepare → execute → inspect → cancel/reconcile
```

with acceptance distinct from completion and reconciliation required before retry when an outcome is uncertain.

## Design provenance

- `docs/design-study.html` preserves the original standalone design study supplied before implementation.
- `docs/frontiers/2026-09-17-humanterminal-aperture-triad.md` preserves the next HumanTerminal semantic-intake frontier: APERTURE → sense field → TRIAD, with T5 kept replaceable.
- `docs/superpowers/specs/2026-09-17-static-workbench-v0.1-design.md` is the bounded v0.1 implementation constitution.
- `docs/superpowers/plans/2026-09-17-static-workbench-v0.1.md` is the implementation plan.

## Next breach

First run APERTURE v0.1 on the actual Zorin machine and collect human corrections/refusals as formation receipts without training anything yet. Once the deterministic constitutional boundary survives use, compare a replaceable local T5/FLAN-T5 provider against it. Project effects remain separately gated: the first effectful project slice should still be **one version-pinned adapter only**, preferably the current Toaster → Dogram comparison path, with restart/interruption reconciliation proved before wider execution authority.

## v0.2 — HOUSE / local habitat

v0.2 keeps the v0.1 authority boundary and makes the browser materially more useful on a machine that is about to contain many Static Collective repositories.

The default **House** surface now:

- inventories every Git repository under the configured roots;
- distinguishes repository presence from readiness, compatibility, admission, and authority;
- detects common local stack markers (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, and others) without executing them;
- surfaces dirty, diverged, and detached worktrees before a crossing is attempted;
- recognizes a bounded set of core Collective organs by local checkout name and marks them only `present` or `missing`;
- offers direct inspection doors into present organs;
- keeps HumanTerminal/APERTURE and the Workbench-owned witness rail available from the same desk.

The House laws are explicit:

```text
present != ready
ready != authorized
compatible != admitted
workbench receipt != project receipt
```

Repository manifests are treated as data. Stack detection does not run install hooks, package scripts, project CLIs, or arbitrary shell commands.

## Listener Delta 001 — compare the encounter without grading the listener

After an admitted Phonograph descendant has fresh sealed radio witness, the Field's Dogram lane now advances from **GENERATION-DELTA-001** to **LISTENER-DELTA-001**. The second instrument binds the exact two parent and two descendant first-response receipts and measures only declared response structure: observation persistence/appearance/disappearance, mode migrations, intrigue transitions, closing-line structure, lexical deltas, and model continuity. It does not score listeners, infer preference, or claim that the signal change caused the response change. See [LISTENER DELTA 001](docs/LISTENER-DELTA-001.md).

## Field Return 001 — the human return from a nearby door

Field Station doors now support an explicit local **TAKE / HOLD / PASS** disposition. The browser binds the choice to the exact `field_state_id` the human saw; if the field changes before submission, the choice is refused as stale. Returns persist in a Workbench-owned shelf across restart without mutating DoorHouse world state.

A **TAKE** produces a deterministic `workbench.field-reseed/v0` object that can be inspected, copied, or downloaded. It remains proposal-only: selection is not execution, a reseed is not admission, and no downstream project is called automatically. See [FIELD RETURN 001](docs/field-return-001.md).

## Field Reseed Crossing 001 — first whole cross-organ metabolism

A persisted **TAKE** can now be crossed by a second explicit human action through
exactly pinned reLATTE R14 into GHoT's Field Reseed Receiver. reLATTE must return
`RECEIVED → R3_HOLD` with zero semantic effect; GHoT independently verifies and
persists the exact reseed in receiver-local HOLD.

A third explicit **Admit to GHoT inbox** action creates a GHoT-owned
`ghot.carried-intent/v0` with status `admitted-not-assigned` and effect
`local-inbox-only`. No body, capability, adapter execution, or remote dispatch
is selected. Receiver HOLD and admission re-enter Field Station as witnessed
state, so the Field changes without Workbench claiming receiver authority.

Pinned organs: reLATTE `87006f3…`; GHoT `fa3a2d8…`. See
[FIELD RESEED CROSSING 001](docs/field-reseed-crossing-001.md).

## Carried Intent Assignment 001 — point it without running it

After a Field TAKE has crossed reLATTE, entered GHoT HOLD, and been explicitly
admitted, the Workbench can now ask pinned GHoT `0812164…` for its current
unranked body/capability field. The human then chooses one exact eligible pair.
GHoT revalidates that pair and persists `ASSIGNED_NOT_EXECUTED`.

The browser deliberately exposes no execute control. Assignment creates no
`ghot.task`, adapter invocation, LAN dispatch, or execution receipt. A future
dispatch must be a new explicit crossing. See
[Carried Intent Assignment 001](docs/carried-intent-assignment-001.md).

## Carried Intent Dispatch 001 — signed consequence crossing

A durable `ASSIGNED_NOT_EXECUTED` carried intent can now cross one final,
separately authorized boundary: **DISPATCH**. Workbench pins GHoT
`e35dd47…`, which revalidates the exact assigned body/capability pair, creates
a P-256 signed reLATTE dispatch crossing, persists PREPARED state, and performs
one bounded capability attempt.

The result includes the normal GHoT task/receipt plus a signed receiver
consequence receipt bound to the dispatch crossing. Completed dispatch replay
is idempotent; prepared-but-unproven dispatch becomes
`DISPATCH_OUTCOME_UNKNOWN` and is never auto-retried.

Field Station changes from **Dispatch the assigned capability once** to either
**Inspect GHoT's signed execution consequence** or **Inspect the ambiguous GHoT
dispatch**. See [Carried Intent Dispatch 001](docs/carried-intent-dispatch-001.md).

## Banana-Elf Co-Delight 001 — sideways return after consequence\n\nA signed GHoT execution consequence now sprouts three unranked Field doors:\n**delightfuler** (tiny gift), **helpfuler** (make room), and **curiouser**\n(keep weird). Each door is grounded in the exact dispatch/task/signed-receipt\nevidence and remains `effect: none`.\n\nThey use the existing human **TAKE / HOLD / PASS** return. TAKE creates only a\nproposal-only reseed; it does not auto-cross, auto-admit, auto-assign, or\nauto-execute. There is no delight score.\n\nThis makes co-delight a reciprocal return surface rather than a metric:\nmachine consequence → sideways possibility → human relation → optional fresh\nmetabolism. See\n[Banana-Elf Co-Delight 001](docs/banana-elf-co-delight-001.md).\n\n## Banana-Elf Fork 001 — independent return before relation\n\nFrom an exact three-facet co-delight consequence field, Workbench can now open\na **2–6 booth sealed fork**. Every named booth receives the same frozen signed\nconsequence and the same delightfuler / helpfuler / curiouser doors. Earlier\nreturns expose only submitted/waiting state; their choices and notes remain hidden\nuntil every fixed booth has answered.\n\nReveal places all returns side-by-side with no winner, score, rank, majority, or\nconsensus. Every unordered pair of TAKE descendants becomes an unranked relation\ndoor: two independent returns may meet without being declared equivalent or merged.\nA relation TAKE becomes an ordinary proposal-only Field reseed and can re-enter the\nexisting explicit reLATTE → GHoT metabolism. Forking itself never inherits execution.\n\nSee [Banana-Elf Fork 001](docs/banana-elf-fork-001.md).\n\n## Creator Desk v0.1 — local source handoff

Use **Creator Desk** in the navigator or House actions to inspect the discovered local media, research, live, and community repos through Creator Workspace-inspired workflow doors. Choose **one** discovered checkout and search its bounded Markdown/text sources. Each hit carries its configured root, repository-relative path, line, working-tree HEAD, and dirty marker; **Copy source handoff** prepares one explicitly selected excerpt for pasting into a separate Creator Workspace conversation.

The workflow registry borrows routing patterns, **not the Creator Workspace plugin runtime**. HOUSE does not invoke the plugin, send notes to a model, publish a draft, start OBS, or mutate a Help Slip. Search excludes symlinks, hidden paths and sensitive-looking filenames, but is not a secret scanner; configure roots deliberately. See [Creator Desk boundary and use](docs/creator-desk-v01.md).

A source handoff is an invitation to inspect, **not** an authoritative interpretation of the source.

## HOUSE ↔ Static Broadcast v0.1 — an operator door, not an operator proxy

To enable the **Open Static Broadcast** action in HOUSE, first install/checkout
[Static Live](https://github.com/the-static-collective/static-live) under a
configured HOUSE root. Start its own STREAM-001 server with a real project-owned
broadcast packet and OBS preflight; note the *actual* local port printed by
Static Live. Set that specific number in your HOUSE config:

```toml
broadcast_port = 3008 # replace with Static Live's actual chosen port
```

Restart HOUSE. Its default House action area distinguishes: downloaded
checkout, unconfigured console, offline/incompatible local service, incompatible
self-reported identity, and reachable local console. Only a reachable service
whose `/api/house/identity` matches the Static Live contract and whose
`/api/status` reports the same event and valid state enables a manual
`http://127.0.0.1:<declared-port>/` link. It reports the controller's
recording, streaming and state flags separately; these remain self-reported,
not independent proof that OBS or a streaming platform succeeded.

HOUSE does **not** autostart OBS, run project scripts, proxy control requests,
store stream keys or OBS credentials, create a remote/LAN control surface, or
write project-native receipts. The destination service itself owns GO LIVE,
scene selection, END + PRESERVE, preflight, event and stream-state authority.
Neither a running port nor a descriptive identity response constitutes
cryptographic service authentication.

Use the Static Live [STREAM-001 setup](https://github.com/the-static-collective/static-live/blob/main/examples/stream-001/README.md)
for real OBS configuration. No real performance or stream is claimed by this
integration's isolated service tests.

## Creator Desk v0.2 — select, preserve, draft

Creator Desk now supports **human-selected local source packs** and a **local draft
shelf**. Choose up to eight matching lines from configured checkouts, preview
the exact root/repository/path/line/excerpt and file digests, then explicitly
save the reviewed packet. Changed source files refuse stale saves. A pack is
an immutable selected working-tree snapshot, not a frozen Git commit, complete
source, AI-generated interpretation, or project-native receipt.

Write lyrics, podcast scripts, posts, briefs and other drafts against a saved
pack; creative assumptions and unresolved gaps have separate fields.
Revisions append to Workbench-owned `state_dir/creator.sqlite3`, survive
restarts, and refuse stale-editor overwrites. **Copy draft + source references**
is an explicit manual handoff: nothing is automatically sent to Creator
Workspace, GitBook, Suno, Static Live, or other services, and no project source
is changed. The local single-user browser/session boundary is not a
multi-user authentication system.

See [Creator Desk v0.2 boundaries and use](docs/creator-desk-v02.md).

## Hugh Jackman Discontinuity Maxhinal — Creator Desk Ride Dock

HOUSE now exposes a **project-native Maxhinal door and an explicit imported-ride
dock** in the Creator Desk. The real eight-chamber Maxhinal continues to run in
`the-daily-slice` against actual Slice corpus gas, not generic search hits.
From a saved Creator Desk source pack, paste a genuine exported
`.maxhinal.json` ride, review its self-reported gas/operations/residuals/bad
spins and exact pasted-byte SHA-256, then intentionally save a Workbench-owned
copy. A person can associate that ride with a local draft on the next explicit
revision save; the draft's manual copy handoff carries the dock id/digest.

The relation between a source pack and a ride is **human-declared creative use**,
not a claim that the Maxhinal executed on the pack, that its corpus replay was
independently verified, or that a creative relation proves source identity.
Neither HOUSE nor the dock runs Daily Slice code, edits Slice history,
publishes drafts, or promotes projections to evidence. The original Maxhinal
machine, its corpus and its receipts remain project-owned.

See [Maxhinal Ride Dock setup and boundaries](docs/creator-maxhinal-ride-dock.md).

## HOUSE Native Maxhinal v0.1 — selected local computer fuel

**HOUSE Maxhinal** is a separate deterministic creative instrument in the
navigator and House action grid. Select one to four explicit files underneath
configured HOUSE roots and/or previously reviewed saved Creator Desk source
packs. Preview every item's root-relative identity, SHA-256 and bounded text
excerpt before selecting Discontinuity, Braid, Compose, Pressure or Shuffle,
an optional creative question and reproducible seed.

A confirmed spin **re-reads and checks the entire previewed fuel digest**,
then saves an immutable HOUSE-native ride with projections, unresolved residuals,
bad spins and exact source references into the Workbench-owned local shelf.
Copying a ride into a Creator Desk draft is an explicit manual action; no
source file, project receipt, Daily Slice corpus or draft is silently modified.

Unlike Daily Slice's Hugh Jackman Maxhinal, HOUSE Native Maxhinal accepts
user-chosen local fuel; it does not claim Daily Slice's engine or receipt
format. Binary, image, audio and large-text files yield **metadata/digest
only**, not invented media understanding. Individual files are capped at
16 MiB; text inspection is capped at 128 KiB and a 1,600-character excerpt.
No recursive whole-computer search, arbitrary script execution, external
model call, media transcription or automatic publication occurs.

See [Native Maxhinal setup, limits and source-law](docs/house-native-maxhinal-v01.md).


## Dogram Impact Desk 001 — committed Python change instrument

Open **Dogram Lab** in HOUSE, choose a discovered Python repo with at least two
commits, preview its first-parent HEAD comparison and explicitly run the
comparison using exactly one clean, discovered local Dogram checkout. HOUSE
materializes only bounded Python blobs from Git commits into temporary snapshots
and invokes Dogram's existing internal repository-impact research kernel; it
does **not** import or execute the selected project's code. Dirty working-tree
content is excluded and marked as such. A moved HEAD, altered preview, dirty
Dogram checkout or unsupported Python path refuses.

A successful calculation produces a SHA-256-addressed, Workbench-owned local
report containing Dogram's exact node/edge/reachability deltas and source/version
references. It can be reopened by report ID after restart. This is an
experimental internal-kernel integration, **not** a public Dogram operator or
a project-native Dogram receipt, a merge verdict, or automatic execution rights.

See [Dogram Impact Desk setup and boundaries](docs/dogram-impact-desk-001.md).


## GROUNDKEEPER-001 — synthetic field laboratory

HOUSE now exposes an experimental **GROUNDKEEPER** door. Run a reproducible simulated ground signal through a coupled sound/visual feedback network; inspect a derived note phrase, visual frame, three bounded graph-change comparisons, and an exact-replay receipt. It does **not** access live sensors, mutate project state, admit generated capabilities, or implement a TranchNOSE optical field.

Use the **GROUNDKEEPER** navigator view or run `python -m static_workbench.groundkeeper --seed static-first-ignition --output ~/groundkeeper-first.json`, followed by `python -m static_workbench.groundkeeper --replay ~/groundkeeper-first.json`. The output file must not already exist. Read [first-flight setup, controls, and next stages](docs/groundkeeper-001.md).


## webZ Native 001 — Workbench reads worlds

**Experimental first-party address instrument.** Run Workbench with your existing local configuration and open `http://127.0.0.1:13700/webz` (or select **webZ · World Wide Web of Worlds** from the navigator).

Type one of the installed local addresses:

```text
webz::static/sanctuary
webz::static/orchard/022100
```

Choose **Resolve world** to inspect the declared world, then deliberately choose **Enter selected world**. Each world owns a separately addressable HTML page and an inspectable portal. A visitor can inspect the door, remain, cross to the other world, and explicitly return. Unknown addresses stay **UNRESOLVED** rather than triggering network requests or arbitrary filesystem lookups.

A **local voyage log** is optional and **off by default**. Inside a world, choose **Begin voyage recording** if you want a browser-local sequence of source world, destination world, door and departure/arrival. The record survives browser reload on the same Workbench origin while browser storage remains available. You can pause/resume it, export its noncanonical JSON, or erase it with confirmation; malformed stored history is exposed, not silently repaired. Browser storage is not a secret vault. No personal notes, coordinates, account identities, or uploaded images are included. Ordinary scene navigation works even if storage is denied. Exports are local testimony, **not** canonical STORYSHIP history or signed reLATTE receipts.

**Boundaries:** Workbench understands `webz::` inside its own interface, but this is not registered with the operating system, Chrome, or a custom network stack. Initial worlds are trusted first-party and share the Workbench browser security origin; independent world IDs are *not* security isolation. No transport of personal material or signed reLATTE crossing occurs during visits, and destination-local admission remains separate. Scene graphics are original CSS constructions rather than copies of the manga source assets.

Run verification:

```bash
python -m pytest -q
node --test tests/webz-*.test.mjs
# To exercise real desktop/mobile Chromium:
python -m pip install 'playwright==1.56.0'
python -m playwright install chromium
python scripts/smoke_webz_browser.py --out browser-artifacts
```

Source decisions: [WEBZ-NATIVE-001 design](docs/superpowers/specs/2026-10-06-webz-native-001-workbench-design.md) and [implementation plan](docs/superpowers/plans/2026-10-06-webz-native-001-workbench.md). A later separate proposal can join chosen artifact crossings to reLATTE's signed crossing/receiver contracts.


## WEBZ-RELATTE-002 — First accountable material offer (experimental)

The Sanctuary's **The fruit may travel** instrument is a separate, **effectful** action from ordinary `webz::` navigation. The familiar Inspect / Cross / Return portal still carries **nothing**. Browsing or recording a local voyage does not sign, send, import, or admit any artifact.

In `/webz/world/sanctuary`, choose the original fictional **Impossible orange** or **Uninvited story-spore**, press **Inspect exact parcel**, read the SHA-256 and Orchard receiver policy, check the explicit confirmation, and **Sign and offer parcel through reLATTE**. The app rejects different files, client-supplied recipient decisions and stale digests. No user uploads, photographs, memories, personal information or network URLs are accepted.

This action requires a **clean local checkout of reLATTE at exactly `87006f3265103a8abe387d81597c58aeb39b0beb`** (the same pinned owner already used by Workbench's Field Reseed path), discoverable under a configured Workbench repository root. Without it, the action fails visibly and does not impersonate signed evidence. The sender chooses **whether** to offer a declared fixture; the Orchard's local policy fixes the disposition: fruit → signed `RECEIVED` + `R3_HOLD`, spore → signed `RECEIVED` + `R3_REFUSE`. Neither admits material into the world.

The Workbench stages **exact JSON bytes** in operator-local quarantine and verifies their SHA-256 against the signed crossing's payload reference. reLATTE signs the crossing envelope and the independent Orchard `LocalReceiver` signs receipt/disposition. The signed RECEIVE covers the **envelope and digest reference**; the separate Workbench byte check is not a receiver signature over physically ingested bytes. The first two worlds share one trusted browser origin; this is **not** open federation, cryptographic human identity, cross-origin isolation, or an installed OS-wide `webz::` handler.

Visit `/webz/world/orchard` to view the **read-only** receiver inbox and inspect its public signed evidence. Repeating the same offer reuses durable results instead of minting another crossing. Intent, staged material, bundle, receiver journal, signed result and compact summaries remain under the configured Workbench `state_dir/webz-relatte/v0/`, not in the STORYSHIP canonical voyage ledger. Rejected/corrupt state returns an error rather than inventing success or erasing provenance.

Verification:

```bash
python -m pytest -q
node --test tests/webz-*.test.mjs
# after checking out and installing the exact pinned reLATTE owner in .compat/reLATTE:
python scripts/smoke_webz_relatte.py
# with Playwright and Chromium installed:
python scripts/smoke_webz_relatte_browser.py --out browser-artifacts
```

Design: [WEBZ-RELATTE-002](docs/superpowers/specs/2026-10-06-webz-relatte-002-first-sovereign-parcel.md). Do not treat these first-party fixtures as untrusted community worlds or as authorization for real third-party asset transfer.


## WEBZ-003 — Independently verified actual-byte custody (experimental)

WEBZ-002 signs a crossing with a declared SHA-256 **payload reference**, then the Orchard signs RECEIVE and HOLD/REFUSE on that **envelope**. WEBZ-003 adds the previously missing physical-byte observation. It is a **second explicit human decision** after the first signed offer, not a change to ordinary no-carry navigation.

In `/webz/world/sanctuary`:

1. **Inspect and SEND a first-party fictional parcel** through the existing WEBZ-002 reLATTE instrument.
2. At the separate **WEBZ-003 / DESTINATION BYTE CUSTODY** instrument, select that already-signed specimen, **Inspect physical-delivery readiness**, verify its full crossing ID and SHA-256, check the independent consent box, and click **Deliver actual bytes to independent receiver**.
3. Visit `/webz/world/orchard` to inspect the read-only receiver-key signed **PAYLOAD_BYTES_VERIFIED** receipt bound to the previous RECEIVE and disposition. The receiving process independently read literal material bytes from a separate bounded file carrier, validated them against the signed crossing, and cold-replayed its journal.

**HOLD** retains the exact verified bytes under the receiver's **local quarantine**, not in the world. **REFUSE** verifies and signs what was received but **does not retain** the material. Neither outcome grants admission, identity authority or capability execution. No personal input/files/links are accepted in this specimen.

The implementation deliberately keeps **two exact pinned reLATTE checkouts** after the owner change merged: the original R14 `87006f3265103a8abe387d81597c58aeb39b0beb` **for existing Field Reseed and other legacy adapters**, and custody-capable reLATTE owner `103c03c745968bfe2105167fa9007fab8906fc71` **for both WEBZ-002 signed envelopes and WEBZ-003 byte delivery**. This is required: the original R14 code cannot replay a receiver journal once it contains a new CUSTODY event. Existing first-phase crossing envelopes are preserved; no prior signature is rewritten. Both can be configured as Workbench roots with actual checkout basename `reLATTE`; the full clean tracked commit is verified and ambiguous duplicate pins are rejected. No dirty checkout or latest mutable HEAD is accepted.

**Proof scope:** The new receipt is signed with the Orchard receiver's existing local P-256 signing key and binds the actual SHA, byte length, retained/refused status and prior receipt IDs. This proves the separately executed recipient code inspected the carrier bytes in a **local filesystem process**. It is **not yet remote network transport**, separate-machine/administrator isolation, global webZ protocol registration, a legal identity claim or an admitted world object. The carrier and signed proofs are retained under the operator-controlled `state_dir/webz-relatte/v0/`; neither affects STORYSHIP canonical history.

To repeat the exact integration proof in a prepared development checkout:

```bash
python -m pytest -q tests/test_webz_custody.py tests/test_pinned_owner_selection.py
# Existing R14 owner: .compat/reLATTE
# Custody owner: .compat/custody/reLATTE (both clean at their exact documented SHAs)
python scripts/smoke_webz_custody.py
# With Playwright/Chromium installed:
python scripts/smoke_webz_custody_browser.py --out browser-artifacts
```

See [WEBZ-003 design](docs/superpowers/specs/2026-10-06-webz-003-byte-custody.md). Owner protocol changes were merged from `the-static-collective/reLATTE` PR #63.
