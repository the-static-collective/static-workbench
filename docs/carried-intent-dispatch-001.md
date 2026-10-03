# CARRIED INTENT DISPATCH 001 — Cross Into Consequence

This slice completes the first bounded Field → receiver → execution metabolism.

```text
FIELD
  → TAKE
  → reLATTE RECEIVE
  → GHoT HOLD
  → ADMIT
  → OPEN OFFER
  → CHOOSE BODY + CAPABILITY
  → ASSIGNED_NOT_EXECUTED
  → explicit DISPATCH
  → signed reLATTE dispatch crossing
  → exact pair revalidation
  → one bounded GHoT capability attempt
  → GHoT task + execution receipt
  → signed receiver consequence receipt
  → changed FIELD
```

The important boundary is not that execution exists. GHoT already knew how to
execute bounded capabilities.

The new capability is **lawful continuity into execution**: the task is tied to
the exact human assignment, exact carried intent, exact dispatch crossing, and
exact receiver consequence receipt.

## Pinned receiver

Workbench requires GHoT:

```text
e35dd470384d864b7b0b629a68dad570875a7df0
```

That revision includes `CARRIED-INTENT-DISPATCH-001`.

## Explicit dispatch

An `ASSIGNED_NOT_EXECUTED` receiver state now surfaces:

> **Dispatch the assigned capability once**

The browser exposes **DISPATCH ASSIGNMENT ONCE** / **Dispatch + execute once**.

The control requires a confirmation that names the already-assigned capability
and body. No body or capability may be selected during dispatch.

The API invokes only the exact pinned GHoT dispatch surface.

## Signed crossing

Before execution, GHoT:

1. revalidates the already-assigned body and capability;
2. derives a receiver-owned execution payload from the carried intent;
3. creates a signed `relatte.crossing-envelope/v0`;
4. persists that crossing in `PREPARED` state;
5. only then invokes the assigned bounded capability.

The donor Field door is carried as evidence inside the receiver-owned payload.
It is not parsed into a command.

## Exactly-once safety boundary

A completed dispatch is idempotent. Repeating the explicit dispatch request
returns the stored result and does not create a second task.

If GHoT has a durable `PREPARED` crossing but cannot prove completion, it
reports:

```text
DISPATCH_OUTCOME_UNKNOWN
```

Workbench persists that ambiguity and changes the Field to:

> **Inspect the ambiguous GHoT dispatch**

There is no retry control in that state.

This avoids converting uncertainty into duplicate authority.

## Consequence

A completed bounded attempt returns:

- a normal GHoT task;
- a normal GHoT execution receipt;
- a P-256 signed `relatte.receipt/v0` bound to the dispatch crossing.

Workbench persists the receiver consequence as:

```text
workbench.field-reseed-dispatch/v0
status: EXECUTED | EXECUTION_ERROR
semantic_effect: receiver-local-consequence
```

The Field then surfaces:

> **Inspect GHoT's signed execution consequence**

The Field records task id, execution receipt id, signed receipt id, capability
status, and output digest when available.

## Error is still consequence

`EXECUTION_ERROR` does not mean "nothing happened."

It means the bounded attempt occurred and returned an error consequence. The
signed receipt remains evidence of the attempt.

Therefore:

```text
DISPATCH != SUCCESS
ERROR != NON-OCCURRENCE
```

## Laws

```text
ASSIGNMENT != EXECUTION
DISPATCH REQUIRES A NEW EXPLICIT CROSSING
DISPATCH != SUCCESS
EXECUTION != RECEIPT
RECEIPT != TRUTH
PAYLOAD != AUTHORITY
DOOR != COMMAND
AMBIGUOUS OUTCOME != SAFE RETRY
EXECUTOR CONSEQUENCE != DONOR AUTHORITY
RECEIVER CONSEQUENCE != DONOR CONSEQUENCE
```

## Actual cross-project proof

CI runs:

```bash
python scripts/smoke_field_reseed_crossing.py
```

against exact pinned reLATTE and GHoT revisions.

The smoke proves:

1. exact Field observation;
2. explicit TAKE;
3. real reLATTE RECEIVE → HOLD;
4. GHoT receiver HOLD;
5. explicit admission;
6. unranked body/capability offer;
7. explicit assignment;
8. zero execution records after assignment;
9. explicit signed dispatch crossing;
10. exactly one real `system.hash` task;
11. execution receipt;
12. signed consequence receipt bound to the crossing;
13. changed Field;
14. completed-dispatch replay creates no duplicate task.

At this point the first metabolism is closed:

```text
encounter
→ human choice
→ portable possibility
→ receiver admission
→ receiver address
→ human assignment
→ explicit dispatch
→ consequence
→ witness
→ changed encounter field
```

The next opening is no longer "make it execute." It is richer: **what can a
witnessed consequence lawfully seed next?** Any recursion must begin from the
new consequence receipt, not from assumed success.
