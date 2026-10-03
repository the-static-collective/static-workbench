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
