# HOUSE-FLYWHEEL-003 — Capability Loom, inert v0 preview

## Position in the stack

This draft builds on the Return Shelf branch / PR #43, which builds on the local Return Ledger branch / PR #41. Keep the ancestry explicit; neither draft grants additional project mutation rights. The only new effect on a preview request is transient local HTTP handling. The local Workbench ledger remains unchanged.

## Human workflow

In HOUSE → Return Shelf, expand the reported return cards and **explicitly check exactly two** individually identified artifacts. Enter a nonblank, at-most-512-character question, then click **Preview selected composition**. No artifacts are preselected. The button is disabled until two are selected and a question exists. Selecting an artifact never runs or approves it. Changing the question or selected inputs clears an earlier preview; a stale asynchronous response cannot overwrite the newer selection.

The session-protected `POST /api/house/loom/preview` accepts only `{selections: [two exact selectors], question: text}`. Each selector contains the exact `return_id`, local `return_digest` (request field `local_digest`), source-owned `owner`, and original `artifact_ref`. The server independently reopens its own local return record, checks exact digest and artifact membership, refuses missing or changed records, unknown fields, repeated artifact identity and ambiguous input count.

## Returned candidate

A deterministic `house.capability-loom-proposal/v0` card contains the two independently identified inputs and their reported state/evidence/nonclaims, the human's question, three **questions for a future experiment**, and a local content fingerprint. It explicitly says `state: inert_unrun`, `compatibility/verification/authorization: not_evaluated`, `execution: not_attempted`, and `declared_effects: []`. The preview does not infer equivalence, actual reuse, measured growth, permission, or evidence authenticity. Source-owned identity is never replaced by the Workbench digest.

## Deliberate boundaries

- No automated candidate generation, self-execution, branch checkout, adapter invocation, cross-project mutation, publication, persistent proposal save, auto-approval, or inherited descendant permission.
- No human-value score, ordering, or automatic reading of Joyful / Useful / Curiouser marks. Exact optional attention-mark integration is a **separate** future flight, so this slice does not fabricate a revision, consent or user preference.
- No Free Graph/Dogram/Wolfram claim of actual compatibility. Those are later optional calculations over independently supplied, version-pinned fixtures; the preview makes no such calculation.
- Client-rendered source strings are text nodes, not HTML or source-provided links. Preview POST requires same-origin local-session guard despite non-effectful response.
- Empty or missing local return shelf remains empty. Operational journal entries do not mint return records.

## Validation / manual smoke

Run `pytest -q tests/test_capability_returns.py tests/test_return_shelf.py tests/test_capability_loom.py` plus the complete Workbench CI before merge. In a local browser with two explicitly imported fixture returns, verify selection count and disabled state, uncheck behavior, same-owner/ref refusal, preview display and inert state, clearing of stale results, and that no new returns or project effects occur.

## Next independently authorized proof

Freeze a first tested fixture, instrument a second selected reuse experiment, declare input pins/permissions/budget/stop condition, and inspect owner-native tests, uncertain outcomes and measured time/cost. Only an independently verified second-use result can support a **specific observed** compounding claim; this preview does not.
