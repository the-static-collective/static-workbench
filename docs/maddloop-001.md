# MADDLOOP-001 — Abstract Loop Pedal (experimental)

## Status

Workbench-owned playable local slice, accessible from the Workbench navigator through /maddloop. No external effects, media playback, remote model, project-native receipt, automatic scheduling, or permission to reuse somebody's recorded speech is supplied by this version.

## Use

1. Start the normal local Workbench and open /maddloop.
2. Name a loop and record its first human-entered layer (REC).
3. OVERDUB another layer. Every overdub creates a new immutable revision; earlier snapshots remain in state_dir/maddloop.sqlite3.
4. PLAY creates a new read-only preview encounter, with a fresh identity referring to the exact revision digest and unchanged source ids. It does not re-execute or dispatch the text, actions, historical voices, or media references.
5. LOOP explicitly arms an immediate preview pass followed by further passes at a selected 2–60 second interval, capped at eight distinct encounters per arming. STOP ends future scheduling; an in-flight local preview can still complete. Switching loops, hiding the page, or leaving it stops the timer. No background daemon or unattended project execution is involved.
6. BRANCH preserves source identities, links the child to its parent loop/revision, and allows the child to diverge without rewriting the parent.

The optional input/output class and concrete port fields are explicit synthetic witness data entered by the human; default note:note permits a simple text arrangement. Between consecutive layers, matching abstract classes with different concrete ports produces concrete_lift_gap, rather than executable status. A class mismatch produces abstract_class_gap. Both appear between exact offending layer indexes, with available and required ports retained.

concrete_route_witnessed describes only the synthetic port-check specimen. It is NOT authority or a guarantee that any real source/destination can actually process a payload. A blocked arrangement can still be previewed as a sketch with status blocked_route_preview, but not passed off as an executable train. Repair is an explicit new revision/branch, never silent adapter synthesis.

## Storage / API

- GET /maddloop, GET /api/maddloop/loops, GET /api/maddloop/loops/{id}
- Protected same-origin, session-token writes: POST /api/maddloop/loops (REC), POST /api/maddloop/loops/{id}/overdub, POST /api/maddloop/loops/{id}/branch, POST /api/maddloop/loops/{id}/encounters (PLAY).
- Mutation requests use expected_revision_id to refuse stale-head updates with HTTP 409. Invalid layer input is bounded; no user-entered text is evaluated.
- SQLite stores immutable revision snapshots and append-only preview encounters. Each source has its own id; each encounter has another id. The Workbench journal also receives lightweight local operational events.
- Persistence does not implement multi-user identity/authorization, project execution, branch merge, media input, or exact-source file import.

## Hostile fixture

Record synthetic P→Q_in and overdub Q_out→R. Both legs have abstract class Q; concrete ports are different. Preview reports the join obstruction and retains exact q_in versus q_out mismatch. Fork at the first revision and overdub an explicit Q_in→R alternative. The fork now has a locally matching route and the original remains blocked.

## Boundaries / future

Dogram DOGWOLF-002 and MARKOV-LUMPABILITY-001 motivate the distinction between abstract support, composable route, and realized occurrence; this implementation does not import Dogram or assert mathematical proof of its semantic port model. Ghostcast motivates source-versus-encounter identity but this version does not claim to implement Static Live's temporal shelf, media clock, or broadcast pipeline.

Next steps, separately reviewed: typed adapter-backed payload validation, explicit human effect authorization, source-owned receipts, reviewed duration/clock semantics, and local media audition. Do not convert a matching port into an executable capability merely by adding a Run button.
