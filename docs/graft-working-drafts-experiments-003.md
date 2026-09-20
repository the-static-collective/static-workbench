# GRAFT 003 — Working candidate drafts and bounded experiment cards

Status: experimental; an extension of [GRAFT 002](graft-native-candidate-table-002.md).
The previous Dogram [Structural Witness 001](graft-dogram-structural-witness-001.md)
remains an independently reviewed graph calculation, not an implementation
witness or automatic evaluation of a draft.

## Operator journey

In HOUSE → HOUSE Maxhinal, open a saved ride and one of its previously saved
three-card GRAFT rounds. Each immutable candidate now has **Open working draft +
bounded experiment**. HOUSE displays an editable, deterministic starter tied
to that candidate's SHA-256, its parent round and ride SHA-256, source refs,
human KEEP/BEND/INTRUDER declarations and the candidate's actual question.

Edit the mechanism/content draft, input fixture, bounded procedure,
**predeclared observable**, stop condition, assumptions and unresolved
questions. The starter is an illustrative proposal; only the human can make
its claims, mechanism and fixture concrete. Save with an explicit button.
Reopen older drafts, inspect earlier revisions in read-only form, and continue
from the current revision. The local SQLite shelf refuses concurrent/stale
revision writes, validates the parent round and ride, and content-addresses
each revision with a parent revision hash. It does **not** write into the
original repository or the Creator Desk draft table.

A selected GRAFT candidate can still be measured through the existing
Dogram structural witness form. That measurement is bound to the candidate's
identity; it is **not** an observation of the draft's executable behavior.
No draft is silently harvested, published to a community desk, inferred to
fulfill a need, or treated as a tested implementation.

## Design limits and next seam

The initial draft template is deterministic text assembled from explicit
human declarations and the selected candidate's variant. It is not an LLM
completion and does not discover unseen source contents, infer an accurate
interface, execute arbitrary repo code or fabricate an experimental result.
The experiment card records a **proposed** observable and stop condition;
actual execution and attributable observed outcomes need a separate
human-approved, scoped test adapter and distinct witness.

Local read endpoints follow HOUSE's existing loopback/session design;
writes require its guarded local session token and same-origin posture.
Field lengths, candidate hashes, parent round/ride identity, revision
optimistic concurrency and historical content digests are checked server-side.
