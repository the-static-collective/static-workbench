# HOUSE LOOK TWICE 005 — Two First Looks, Then One Door

## Claim

The House can now preserve the temporal structure required by First-Listen Radio:

```text
returned Toaster artifact
        ↓
LOOK TWICE pair
   ┌────┴────┐
   ↓         ↓
Static Sam  Juniper
first look  first look
   ↓         ↓
sealed A    sealed B
   └────┬────┘
        ↓
cross-read unlocks
        ↓
short dialogue
        ↓
lingering intrigue?
        ↓
new sealed House letter
```

## Storage law

The House stores the stages as separate witnesses:

- `look_twice_pair`
- `look_twice_first:static-sam`
- `look_twice_first:juniper`
- `look_twice_dialogue_packet`
- `look_twice_dialogue`

The dialogue endpoint refuses to run until exactly two first-response witnesses exist.

The dialogue packet is inspected again on return and is rejected if it contains the original artifact bytes. Cross-read therefore operates on the already sealed responses, not by secretly reopening the source.

## Honest absence

When no real model is available during the encounter stage:

```text
first_responses = []
```

The House preserves the pair but stores no response witness.

When two valid first responses already exist but no real model is available for dialogue:

```text
look_twice_dialogue_packet exists
look_twice_dialogue does not
```

No simulated exchange is created.

## Door threshold

A sealed dialogue does not automatically become a future crossing.

Only when the dialogue reports `lingering_intrigue = true` does the House create:

> **They looked twice. Something was still pulling.**

The returned `door_seed` becomes the label of one proposed door.

```text
LINGERING INTRIGUE != SOURCE TRUTH
DOOR SEED != CROSSING
```

The human must still open the letter, inspect the proposal, select the door, and cross it.

## Actual cross-repo proof

Workbench CI pins landed versions of:

- GHoT;
- Haunted Toaster;
- Autodisco LOOK TWICE.

The real smoke performs:

```text
House local artifact
→ GHoT body discovery
→ Haunted Toaster witness sigil
→ verified returned SVG
→ LOOK TWICE pair preparation
→ two isolated packet identities
→ no-key encounter
→ zero fabricated first responses
```

Autodisco's own CI separately proves that fabricated test first responses cannot enter dialogue until both identities verify, and that the dialogue packet does not reopen the artifact.

## Laws

```text
SAME ARTIFACT != SHARED CONTEXT
PAIR != FIRST RESPONSE
FIRST RESPONSE PRECEDES CROSS-READ
SEALED != SHARED
DIALOGUE != RETROACTIVE FIRST IMPRESSION
ORIGINAL ARTIFACT IS NOT REOPENED
SIMULATION != FIRST ENCOUNTER
SIMULATION != DIALOGUE
LINGERING INTRIGUE != SOURCE TRUTH
DOOR SEED != CROSSING
MEMORY != AUTHORITY
```

## Next carrier

Once this visual LOOK TWICE seam is stable, replace the SVG carrier with one bounded audio window.

The temporal protocol does not need to change.
