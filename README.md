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
