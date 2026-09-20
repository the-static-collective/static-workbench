# Static Workbench

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

## Creator Desk v0.1 — local source handoff

Use **Creator Desk** in the navigator or House actions to inspect the discovered local media, research, live, and community repos through Creator Workspace-inspired workflow doors. Choose **one** discovered checkout and search its bounded Markdown/text sources. Each hit carries its configured root, repository-relative path, line, working-tree HEAD, and dirty marker; **Copy source handoff** prepares one explicitly selected excerpt for pasting into a separate Creator Workspace conversation.

The workflow registry borrows routing patterns, **not the Creator Workspace plugin runtime**. HOUSE does not invoke the plugin, send notes to a model, publish a draft, start OBS, or mutate a Help Slip. Search excludes symlinks, hidden paths and sensitive-looking filenames, but is not a secret scanner; configure roots deliberately. See [Creator Desk boundary and use](docs/creator-desk-v01.md).

A source handoff is an invitation to inspect, **not** an authoritative interpretation of the source.

## Branch Deck 001 — discover the branches hiding behind a checkout

The `Branch Deck` navigator entry and HOUSE landing card now expose every locally
known branch in configured-root checkouts, rather than only the branch currently
checked out. Search by repository, branch or exact commit; distinguish locally
checked-out branches, branches in other worktrees, and **cached (potentially
stale)** remote-tracking refs. The deck includes a manual isolated-test route
for each observed ref. It does **not** fetch new GitHub branches, switch
checkouts, run tests, assert readiness or merge code. See
[Branch Deck scope and next crossing](docs/branch-deck-001.md).

## Branch Deck 002 — inspect unfetched GitHub feature branches

After enabling `github_remote_discovery = true` in Workbench's top-level TOML
configuration, the **Check public GitHub branches** button inside Branch Deck
can inspect one selected, configured-root checkout's public Static Collective
GitHub origin. It distinguishes branches not found in the local ref inventory,
adds exact-commit navigation and open same-repository PR links, and reports
bounded pagination/rate-limit gaps. Public observations are manual dated
snapshots; **no `git fetch`, test run, worktree creation, project write, token
exchange or merge is performed**. See
[Branch Deck 002 setup and authority boundary](docs/branch-deck-002.md).

## Branch Deck 003 — two-step isolated local worktree preparation

Set `branch_worktrees_enabled = true` in the top-level Workbench TOML to
enable a separate **Preview isolated checkout → Create this isolated checkout**
workflow on an exact-SHA *local* branch card. This creates a detached Git
worktree under Workbench state with a local receipt and leaves the original
checkout's current branch untouched. It changes Git administrative worktree
metadata; Git hooks are disabled and checkout filters are refused. It does
not fetch remote-only code, install packages or run tests. See
[Branch Deck 003 setup, effects and recovery](docs/branch-deck-003.md).

## Branch Deck 004 — rolling public Collective radar

Enable `branch_radar_enabled = true` to start a local-supervisor
rolling public GitHub observation. It checks up to five repositories every
30 minutes, preserving per-branch first-seen and last-observed timestamps
in Workbench-owned SQLite. Its HOUSE/Branch Deck indicators distinguish
initial baselines from newly observed branches and show scan gaps. It does
not guarantee complete or instant public GitHub coverage, inspect private
repos, fetch project code, execute tests or merge. See
[Collective radar coverage and safeguards](docs/branch-deck-004.md).

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
