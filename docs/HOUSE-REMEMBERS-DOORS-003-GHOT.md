# HOUSE-REMEMBERS-DOORS-003 — GHoT Body Choice

## Claim

After a local DoorHouse crossing has been carried through reLATTE and returned in **HOLD**, the House may ask GHoT which currently awake bodies offer one bounded capability.

Nothing is assigned by discovery.

```text
local DoorHouse receipt
        ↓
reLATTE RECEIVED → HOLD
        ↓
ask GHoT for bodies
        ↓
BODY-CHOICE OFFER
        ↓
human reviews exact candidates
        ↓
human selects one node
        ↓
GHoT revalidates that node
        ↓
ASSIGNMENT
        ↓
bounded system.hash execution
        ↓
GHoT receipt
        ↓
House external witness
```

## Why `system.hash`

The first body-choice crossing uses GHoT's built-in `system.hash` capability.

That is intentionally small:

- every reference body can offer it;
- it is a real computation;
- it does not require arbitrary shell execution;
- the exact local artifact can be carried as bounded input;
- the returned digest gives us a concrete execution witness before adding renderers or model runtimes.

## Authority sequence

```text
reLATTE HOLD != GHoT ASSIGNMENT
DISCOVERY != TRUST
OFFER != ASSIGNMENT
CAPABILITY != AUTHORITY
ASSIGNMENT != EXECUTION
EXECUTION != RECEIPT
GHOT RECEIPT != LOCAL RECEIPT
```

The user-facing House calls discovery first. The stored offer contains no selected body.

Only a second explicit request names `selected_node_id`.

The assignment uses the exact latest stored offer id. If the offer changes, the House requires review again.

GHoT revalidates that selected body before execution. A body that disappeared, slept, withdrew the capability, or lost its route cannot execute merely because it appeared in an older offer.

## What the House stores

The House stores the GHoT offer separately from the GHoT execution witness.

The execution witness carries:

- local receipt id + digest;
- exact body-offer id;
- GHoT assignment id;
- selected node id;
- selection source;
- capability;
- GHoT receipt id;
- executor node id;
- output + output digest;
- status.

This is evidence of execution, not proof that the result is semantically correct.

## User-facing language

When the offer has one eligible candidate:

> One body is awake and able to run this capability.

When it has several:

> N bodies are awake and able to run this capability. Choose one.

When none are eligible:

> No currently observed body is eligible.

The interface must not imply multiple machines exist when only one is observed.

## Next earned door

Once body choice works, replace the harmless hash capability with a bounded creative execution organ:

1. Haunted Toaster render adapter;
2. local model inference;
3. ffmpeg transform;
4. First-Listen packet production.

That future execution must preserve the same explicit body-assignment boundary.
