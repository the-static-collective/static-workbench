# CARRIED INTENT ASSIGNMENT 001 — Pointed, Not Run

This slice extends the Field Reseed metabolism by exactly one receiver-local
decision.

```text
Field TAKE
→ reLATTE RECEIVE
→ GHoT HOLD
→ human ADMIT
→ carried intent
→ human OPEN OFFER
→ current GHoT body × capability field
→ human CHOOSE EXACT PAIR
→ ASSIGNED_NOT_EXECUTED
```

The assignment says where an admitted intent is pointed. It does not say that
the selected body performed anything.

## Pinned receiver

Workbench requires GHoT revision:

```text
0812164737fc890a813aa965f8a5cf00701def3e
```

That revision contains GHoT `CARRIED-INTENT-ASSIGNMENT-001`.

Tracked source must exactly match the pin. Dependency/build artifacts may exist
without being treated as source changes.

## Open offer

After an intent is admitted, the human may explicitly ask GHoT to expose its
current receiver-owned body/capability field.

Workbench stores:

```text
workbench.field-reseed-assignment-offer/v0
status: OFFER_READY
semantic_effect: none
```

The underlying GHoT offer:

- contains no selected body;
- contains no selected capability;
- contains no score or ranking;
- binds the exact admitted intent;
- records each current body and declared capability availability.

The Field changes from:

> Open GHoT's body + capability field

to:

> Choose one GHoT body + capability

Availability still is not selection.

## Explicit assignment

The browser presents only currently eligible body/capability pairs from the
exact stored offer. A person selects one pair and confirms **Assign exact pair**.

GHoT revalidates that exact body and capability before writing:

```text
ghot.carried-intent-assignment/v0
status: ASSIGNED_NOT_EXECUTED
semantic_effect: assignment-only
```

Workbench stores the receiver receipt as:

```text
workbench.field-reseed-assignment/v0
status: ASSIGNED_NOT_EXECUTED
semantic_effect: receiver-assignment-only
```

After that receipt, the Field changes to:

> Inspect GHoT's assignment-only receipt

There is deliberately no **Execute** button in this slice.

## What assignment does not create

The actual integration smoke proves assignment does not create:

- a `ghot.task`;
- a GHoT execution receipt;
- an adapter invocation;
- a LAN dispatch;
- a remote request;
- a shell action.

The selected capability may be executable in some later protocol, but capability
availability and assignment do not authorize execution.

## Durable state

The existing Workbench `field_returns.sqlite3` receiver shelf migrates in place
with two nullable columns:

- `assignment_offer_json`;
- `assignment_json`.

Existing HOLD/admission installations remain readable.

Receiver ordering uses the latest receiver-local consequence time:

```text
assigned_at
→ offered observed_at
→ admitted_at
→ received_at
→ Workbench stored_at
```

## Laws

```text
ADMISSION != ASSIGNMENT
OFFER != ASSIGNMENT
BODY AVAILABILITY != SELECTION
NO SCORE != NO INFORMATION
ASSIGNMENT != EXECUTION
ASSIGNMENT != TASK
CAPABILITY != EXECUTION
DISPATCH REQUIRES A NEW EXPLICIT CROSSING
RECEIVER CONSEQUENCE != DONOR CONSEQUENCE
```

## Actual proof

CI runs the real pinned sequence through:

```bash
python scripts/smoke_field_reseed_crossing.py
```

The smoke now proves:

1. TAKE;
2. real reLATTE RECEIVE → HOLD;
3. real GHoT HOLD;
4. explicit GHoT admission;
5. receiver-owned unranked assignment offer;
6. explicit human body/capability choice;
7. revalidation;
8. durable assignment-only receipt;
9. changed Field after assignment;
10. no task or execution receipt.

The next seam, if opened, must therefore begin from the assignment receipt and
create a **new explicit dispatch/execution crossing**. It may not infer execution
from assignment.
