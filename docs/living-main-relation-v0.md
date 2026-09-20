# Living Main v0.B — Relation Chamber (proposal-only)

**Stage B is a stacked change on Living Main PR #19.** It extends the human-selected composition preview with one *declared*, scoped, inspectable relationship between two different member bodies. Its source of inspiration is Dogram's DECLARED-PATH-EQUIVALENCE-001 and HOUSE GRAFT issue #17, but this implementation does not compute a quotient, infer source relationships, modify GRAFT's stored rounds, or claim mathematical equivalence.

## Human workflow

1. Open **Living Main**, select at least two clean local Git checkouts and click **Preview this body**.
2. In the Relation Chamber, select distinct left and right bodies, choose `equivalent_for_this_experiment`, `substitutable_for_this_step`, or `contrast_pair`.
3. Enter a human-authored statement and bounded scope; click **Preview declared relation**.
4. Inspect the separate `relation_id`, source identities, source-independent status, and explicit nonclaims. **Remove relation preview** forgets only the ephemeral relation on screen, not either source or the configuration.

The relation is a proposed lens, not a discovered fact. Relation orientation is preserved: switching left and right changes the proposal identity rather than silently asserting symmetry. Declarations that differ in wording, kind, or scope receive different hashes. No GRAFT round, Dogram result, frozen prediction, or replay state is written.

## Endpoint

`POST /api/living-main/relations/preview` requires the existing local Workbench session token and same-origin guard. Payload has exactly:

```json
{
  "selections": [
    {"root_id": "static", "relative_path": "sources/ALEX.2", "expected_sha": "<40-character-commit-sha>"},
    {"root_id": "static", "relative_path": "sources/Dogram", "expected_sha": "<40-character-commit-sha>"}
  ],
  "expected_configuration_id": "living-main@sha256:<64-character-configuration-hash>",
  "declaration": {
    "left": "<first-member-body_time_id-from-composition-preview>",
    "right": "<second-member-body_time_id-from-composition-preview>",
    "kind": "contrast_pair",
    "statement": "Compare two declared interfaces without claiming either is compatible.",
    "scope": "One synthetic proposal only"
  }
}
```

Paths are illustrative; use the exact root-qualified paths and body-time IDs from the previous preview. The server rebuilds the composition from actual local HEAD and clean checkout state before validating the relation. Changed source versions, dirty sources, absent endpoints, the same endpoint twice, unsupported kind, extra fields, empty declaration, and different configuration identity are refused. Responses are ephemeral; this endpoint does not persist or execute.

## Next distinct slices

- GRAFT #17: bind a relation to one saved GRAFT round and two legitimate source/candidate handles; add hostile cross-round controls and an optional **separate** Dogram research witness.
- GRAFT #18: optional immutable pre-run FREEZE and append-only outcome, with independently identified occurrence and delta.
- No automatic project promotion, installation, source mutation, runtime invocation, or relation inference.
