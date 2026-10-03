# FIELD RESEED CROSSING 001 — TAKE → RECEIVE → HOLD → ADMIT

FIELD RESEED CROSSING 001 turns a Workbench-native TAKE into the first complete
cross-organ continuity loop.

It deliberately does **not** turn TAKE into execution.

```text
FIELD STATION
    ↓
human TAKE
    ↓
workbench.field-reseed/v0
    ↓
human CROSS TO GHOT → HOLD
    ↓
reLATTE R14
    ↓
RECEIVED
    ↓
R3_HOLD
    ↓
GHoT receiver-local HOLD
    ↓
human ADMIT
    ↓
ghot.carried-intent/v0
    ↓
ADMITTED_NOT_ASSIGNED
    ↓
Field Station changes
```

## Version-pinned crossing

The Workbench requires exact tracked source revisions:

- reLATTE R14: `87006f3265103a8abe387d81597c58aeb39b0beb`
- GHoT FIELD RESEED RECEIVER 001: `fa3a2d81b5cebc3532c9f7f6b950039186cc37c3`

Untracked dependency/build material does not alter the pin, but tracked or
indexed changes cause the crossing to refuse. This lets a dependency-installed
checkout remain runnable without treating modified source as the pinned organ.

## Crossing boundary

Only a persisted `workbench.field-return/v0` with disposition `take` and a
valid deterministic `workbench.field-reseed/v0` may cross.

The Workbench asks reLATTE to carry the exact reseed digest as an opaque organ
artifact to:

```text
world:ghot:field-reseed-inbox
particular:ghot:field-reseed-inbox
```

The crossing is accepted only when reLATTE returns:

- the same crossing identity on all receipts;
- `RECEIVED` with `semantic_effect: none`;
- `R3_HOLD` with `semantic_effect: none`;
- the expected GHoT receiver world;
- the Static Workbench Field Return donor family;
- the exact reseed id and SHA-256 payload reference.

GHoT then independently verifies the same donor/reLATTE evidence before
persisting `ghot.field-reseed-hold/v0`.

At this point the reseed has crossed, but nothing has been admitted.

## Receiver-local admission

Admission is a second explicit human action.

GHoT creates:

- `ghot.field-reseed-admission/v0`;
- `ghot.carried-intent/v0`;
- status `admitted-not-assigned`;
- semantic effect `local-inbox-only`.

No executor body, capability, adapter action, shell command, remote dispatch,
or project execution is selected.

The Workbench stores the returned receiver witness, but GHoT remains the
authority for the receiver-local consequence.

## The Field changes

Receiver-local state re-enters Field Station as evidence.

While the reseed is held, the Field may surface:

> **Admit the carried reseed to GHoT's local inbox**

After explicit admission, that becomes:

> **Inspect GHoT's admitted carried intent**

Both remain Field doors with `effect: none`. The changed Field is evidence
that a consequence occurred elsewhere; it is not a claim that Workbench caused
or owns that consequence.

## Laws

```text
TAKE != CROSSING
CROSSING != ADMISSION
RECEIVE != ADMISSION
HOLD != EXECUTION
TRANSPORT != AUTHORITY
ADMISSION != ASSIGNMENT
ASSIGNMENT != EXECUTION
RECEIVER CONSEQUENCE != DONOR CONSEQUENCE
```

## Local state

Workbench keeps its continuity witnesses in the existing
`field_returns.sqlite3` shelf and stores receiver crossing/admission evidence
against the exact Field Return id.

GHoT keeps its receiver-owned state under:

```text
GHOT_HOME/field-reseed-inbox/
```

The two stores are related by explicit ids and receipts; neither impersonates
the other project's authority.

## Actual integration proof

CI checks out the exact pinned reLATTE and GHoT revisions and runs:

```bash
python scripts/smoke_field_reseed_crossing.py
```

The smoke proves the live sequence:

1. compose a Field;
2. TAKE one exact door;
3. cross its exact reseed through real reLATTE R14;
4. receive and HOLD it in real GHoT receiver code;
5. observe the Field change to an admission aperture;
6. explicitly admit it;
7. observe a receiver-owned carried intent;
8. observe the Field change again;
9. verify no GHoT execution state was created.

That is the first bounded whole metabolism:

```text
encounter
→ choice
→ carried possibility
→ local reception
→ local admission
→ changed field
```

The receiver-local assignment seam is now implemented separately in
[CARRIED INTENT ASSIGNMENT 001](carried-intent-assignment-001.md). It opens an
unranked body/capability offer and records one explicit assignment while still
stopping before execution.

The next unproved seam is therefore dispatch/execution, and it must begin from
the assignment receipt as a new explicit crossing rather than treating
assignment as permission to run.
