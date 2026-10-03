# PHONO RE-ENTRY 001 — The Answer May Return, But It Cannot Erase Its Parent

## Claim

A human may explicitly admit a receipted Haunted Phonograph audition as a new bounded First-Listen Radio specimen.

That action creates a descendant.

It does not overwrite the source window, promote the Phonograph proposal into source truth, or grant Phonograph permission to recursively answer itself without fresh witness.

```text
SOURCE AUDIO WINDOW
      ↓
Haunted Phonograph FIELD ANSWER
      ↓
proposal receipt
      ↓
WAV audition
      ↓
HUMAN: ADMIT AS NEW RADIO SPECIMEN
      ↓
NEW AUDIO WINDOW
      ↓
fresh LOOK TWICE
      ↓
fresh sealed cross-read
      ↓
Phonograph may become available again
```

## Explicit admission

The proposal surface now includes:

> **ADMIT AS NEW RADIO SPECIMEN**

Playback alone does nothing.

Downloading MIDI does nothing.

The existence of a proposal does nothing.

Only the explicit admission action creates the descendant AUDIO WINDOW.

```text
AUDITION != ADMISSION
PROPOSAL != CROSSING
AVAILABILITY != OBLIGATION
```

## Source material

Admission uses the exact WAV audition bound by the Phonograph field-answer receipt.

Before re-entry Workbench verifies:

- the audition file still exists;
- its SHA-256 still matches the Phonograph receipt;
- it is canonical stereo 44.1 kHz 16-bit PCM;
- its frame count is positive.

AUDIO WINDOW v0 accepts integer-millisecond bounds. Re-entry therefore admits the largest complete integer-millisecond prefix of the audition and explicitly records whether a sub-millisecond tail was left outside the child specimen.

That bounded cut is honest rather than silently claiming bytes beyond the requested window.

## Descendant lineage

The child AUDIO WINDOW carries:

`workbench.phonograph-reentry-lineage/v0`

with:

- parent window id;
- parent audio digest;
- Phonograph proposal receipt hash;
- proposal hash;
- resolved performance hash;
- audition digest;
- audition frame count;
- admitted start/end milliseconds;
- whether a sub-millisecond tail was excluded;
- `human_action: explicit-admit`.

The House also records a separate durable witness:

`phonograph_reentry:<child-window-id>`

This witness binds parent, proposal, audition, child, and the local House receipt.

```text
DESCENDANT != PARENT
REENTRY != RESET
LINEAGE != AUTHORITY
HUMAN ADMISSION != PHONOGRAPH AUTHORITY
```

## Stale-parent refusal

Once the descendant becomes the current AUDIO WINDOW, the former parent proposal cannot be admitted again through the same current-window action.

The original proposal and source remain historical witnesses, but the active radio specimen has moved forward.

```text
HISTORY PERSISTS
CURRENT SPECIMEN MOVES
```

## Recursion guard

A Phonograph-derived descendant is not immediately eligible for another Phonograph answer.

It must first obtain a fresh sealed audio cross-read for that exact descendant window.

The guard is enforced twice:

1. FIELD-STATION-001 omits the Phonograph door;
2. the House write boundary refuses a direct FIELD ANSWER request.

Only after:

```text
descendant window
→ exact audio LOOK TWICE pair
→ two sealed first listens
→ sealed cross-read
```

may Haunted Phonograph answer that descendant again.

```text
RECURSION REQUIRES FRESH WITNESS
SELF-FEEDING != CONVERSATION
NEW GENERATION != NEW AUTHORITY
```

## Why this matters

Without the guard, the system could become:

```text
Phonograph
→ Phonograph
→ Phonograph
→ Phonograph
```

where each generated artifact becomes the next generator input without any new encounter.

PHONO RE-ENTRY 001 instead creates:

```text
music
→ response
→ human admission
→ strangers encounter descendant
→ cross-read
→ response
→ human admission
→ ...
```

The recursive unit is therefore not generation.

It is:

> **proposal → human admission → fresh encounter → attributable return**

## CI proof

The pinned creative smoke now runs:

```text
generated canonical source WAV
→ AUDIO WINDOW
→ real landed Haunted Phonograph FIELD ANSWER
→ proposal receipt
→ original First-Listen Radio proof
→ radio episode assembly
→ explicit Phonograph admission
→ descendant AUDIO WINDOW
→ lineage witness
→ fresh descendant LOOK TWICE pair
→ no model key
→ exactly zero fabricated descendant first listens
```

The final absence is intentional proof that re-entry does not inherit the parent's listeners.

```text
PARENT FIRST LISTEN != DESCENDANT FIRST LISTEN
PARENT DIALOGUE != DESCENDANT DIALOGUE
```

## Laws

```text
AUDITION != ADMISSION
HUMAN ADMISSION CREATES DESCENDANT
DESCENDANT != PARENT
REENTRY != RESET
LINEAGE != AUTHORITY
PROPOSAL LINEAGE != SOURCE TRUTH
RECURSION REQUIRES FRESH WITNESS
PARENT FIRST LISTEN != DESCENDANT FIRST LISTEN
SELF-FEEDING != CONVERSATION
```

## Next earned door

Once two real listeners actually encounter a Phonograph descendant, the system can compare generations without collapsing them:

```text
parent window first-listen receipts
        ↕
descendant window first-listen receipts
        ↓
Dogram
"What changed under this admitted musical perturbation?"
```

That would make the next layer measurement rather than another generator.
