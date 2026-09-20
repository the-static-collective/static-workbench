# HOUSE Staged Rocket v0.1 — temporary composition, accountable growth

Status: experimental local Workbench capability, stacked on Return Desk PR #21.
No direct GOATnote, Free Graph, Dogram, ALEX, LOADOUT, or remote agent invocation.

A rocket is an on-demand, bounded mission, not a resident daemon:

    DECLARE (one operation + exact selected sources + purpose)
      -> PREPARE (repo.snapshot/v0)
      -> EXECUTE (source.preview/v0 OR body.overlap/v0)
      -> SEPARATE (mission.seed/v0, a human-declared next action)
      -> [optional] DECLARE a new mission referencing the exact parent receipt

Each stage is explicitly launched and keeps one append-only HOUSE receipt with
SHA-256 content addressing. Failed, stale, or denied attempts are returned as
errors; v0 does not persist refusal receipts for these unsuccessful requests.

## Available operations

repo.snapshot/v0 observes each human-selected checkout under configured roots,
requires an exact 40-character HEAD and clean working tree, and saves a bounded
observation. It does not checkout, install, or modify projects.

source.preview/v0 rechecks the prepared exact source selection before reading
one explicit tracked, non-hidden, repository-relative UTF-8 Markdown, text,
JSON or TOML file up to 64 KiB. It records its full byte digest, a bounded
4,000-character excerpt and truncation status. Parent traversal, hidden paths,
symlinks, missing/untracked source, sensitive-looking secret filenames,
binary content and oversized data are refused. Filename filtering is not a
secret scanner; select the roots and specific files deliberately.

body.overlap/v0 reads tracked owner-published BODY manifests from TWO clean,
exactly pinned checkouts. It checks basic schema and authority fields and
calculates equal kind + protocol + version with opposing emit/accept directions,
retaining separate owners, source commits and manifest digests. This is a
HOUSE-local read-only calculation, NOT Free Graph execution, full JSON Schema
validation, remote origin authentication, or runtime compatibility proof.

mission.seed/v0 records a human-authored next action and unresolved questions
after one executed receipt. It is a proposal only.

The user can explicitly declare a child mission referencing one separated
parent receipt. The child chooses its own sources and operation, starts with
zero stages and must separately prepare/execute/separate. No automatic child
launch is permitted. Old receipts remain intact when the source moves.

## Permission and recovery

Only Workbench-owned local state at state_dir/rockets.sqlite3 and the existing
operational journal are written. No project code or arbitrary commands are
executed: repo discovery uses fixed Git read operations, and stage actions
are a closed allowlist. The same local Host, Origin and session-token guards
as the Creator Desk protect mutations to the Workbench state.

The local single-user guard is NOT multi-user authentication. Private mission
text and source excerpts are stored in plain text. Back up state privately and
do not expose the service on a LAN. SHA-256 establishes stored content identity,
not real-world outcome, actor authentication, semantic truth or authorization.

A local source can change between observations despite clean/HEAD checks:
the system protects against ordinary stale sources, not adversarial
filesystem races. New effectful adapters need versioned project interfaces,
a separate authorization gate, narrow LOADOUT effect fences, project-native
receipts, outcome uncertainty/reconciliation and interruption tests BEFORE
they are admitted into the rocket registry.

## First workstation exercise

Select clean local free-graph and Dogram repos in BODY comparison mode.
Prepare and execute. A zero-overlap result remains an honest calculated result.
Separate with a proposed next inspection; deliberately declare a second rocket
with newly selected source and observe that it does not run automatically.

Alternatively run a one-repo source-preview mission on its README, separate
with a proposed next source, and declare a descendant on a different repository.
Restart HOUSE and verify that both missions, native source references and
all three stage receipts return unchanged.

Possible next action != performed next action != established consequence.
