# PHONO FIELD DOOR 001 — The Field Can Answer Itself Musically

## Claim

The Static Field Station can now expose one genuinely external musical possibility when three conditions are true:

1. an exact bounded AUDIO WINDOW exists;
2. the local Haunted Phonograph checkout actually contains FIELD ANSWER 001;
3. no Phonograph proposal has already been receipted for that exact window.

The read-only Field door says:

> **Ask Haunted Phonograph to answer this window**

The actual effectful action remains on the House receipt surface.

```text
FIELD STATION
  read-only availability
        ↓
HOUSE receipt action
  explicit human request
        ↓
exact canonical AUDIO WINDOW
        ↓
HAUNTED PHONOGRAPH
  FIELD ANSWER 001
        ↓
bounded PCM facts
        ↓
proposal-only music
        ↓
MIDI + WAV audition
        ↓
Phonograph receipt
        ↓
House proposal witness
        ↓
FIELD changes
```

## Capability gate

Repository presence alone does not earn the Field door.

Workbench checks whether the discovered `the-haunted-phonography` checkout actually contains:

`scripts/field-answer.mjs`

Only then does the Field describe `field-answer-001` as available.

```text
REPOSITORY PRESENT != CAPABILITY AVAILABLE
CONCEPTUAL ORGAN != OPEN DOOR
```

The Field evidence records the discovered repo head and branch alongside the current window identity.

## Source boundary

Workbench re-inflates the exact canonical WAV previously materialized by AUDIO WINDOW.

The request sent to Phonograph includes only:

- window id;
- canonical audio SHA-256;
- parent source SHA-256;
- requested start/end bounds;
- exact canonical duration;
- canonical media type;
- exact bounded WAV bytes;
- deterministic FIELD ANSWER seed.

No full source track is sent.

```text
WINDOW != WHOLE TRACK
LOCAL SOURCE PATH != PHONOGRAPH INPUT
```

## Phonograph authority split

FIELD ANSWER 001 returns two distinct provenance classes.

Direct PCM measurements are `evidence`:

- frame count;
- duration;
- four-quarter RMS energy contour;
- peak amplitude;
- zero-crossing activity.

The generated musical object is `proposal`:

- tempo;
- pitches;
- durations;
- velocities;
- synthesis projection.

Workbench refuses the result if that authority split is missing.

```text
SIGNAL FACT != MUSICAL MEANING
PROPOSAL != SOURCE EVIDENCE
DIGEST-SEEDED CHOICE != HEARD PITCH
```

## House witness

The returned proposal is stored as:

`phonograph_field_answer:<window-id>`

The witness binds:

- local House receipt;
- exact current window id;
- exact audio digest;
- signal evidence hash;
- proposal hash;
- resolved performance hash;
- deterministic seed;
- Phonograph receipt hash;
- MIDI artifact;
- WAV audition artifact.

A different answer cannot silently replace an already receipted answer for the same window.

```text
PHONOGRAPH PROPOSAL != HOUSE ADMISSION
FIELD ANSWER != HOUSE CROSSING
```

## Audition

Once the proposal witness exists, the Field door changes to:

> **Audition Haunted Phonograph's musical proposal**

The House exposes read-only local routes for:

- `audition.wav`;
- `answer.mid`;
- Phonograph `receipt.json`.

Playing or downloading those artifacts does not mutate House state.

```text
AUDITION != ADMISSION
AUDITION PLAYBACK != CROSSING
MUSICAL POSSIBILITY != RECOMMENDATION
```

There is intentionally no reroll button in v0.

The same exact window deterministically receives the same FIELD ANSWER seed and therefore the same proposal.

A new answer requires a new bounded window or a future explicitly versioned proposal law.

## Field composition

FIELD-STATION-001 now has a first external-organ lane:

```text
RADIO
  current earned radio aperture

PHONO
  ask for bounded musical proposal
  OR
  audition existing proposal

LIVE
  Static Live availability

PRESENT
  Lifestream moment

HOUSE
  older open proposal

SILENCE
  always lawful
```

The Field remains limited to at most six doors.

It does not automatically elevate the Phonograph proposal above any other lane.

## Cross-repo smoke

Workbench CI pins Haunted Phonograph main at:

`038b7101ecff781ee2ae17a22a1323ca28740d06`

The existing creative smoke now proves:

```text
generated canonical WAV
→ Autodisco AUDIO WINDOW
→ House materialization
→ Haunted Phonograph FIELD ANSWER
→ evidence authority preserved
→ proposal authority preserved
→ WAV audition materialized
→ MIDI materialized
→ House proposal witness
→ radio LOOK TWICE continues independently
```

The Phonograph proposal does not substitute for the two real First-Listen Radio listeners.

Those are independent organs and independent authority paths.

## Laws

```text
REPOSITORY PRESENT != CAPABILITY AVAILABLE
WINDOW != WHOLE TRACK
SIGNAL FACT != MUSICAL MEANING
PROPOSAL != SOURCE EVIDENCE
RESPONSE != REMIX
AUDITION != ADMISSION
FIELD ANSWER != HOUSE CROSSING
PHONOGRAPH PROPOSAL != HOUSE ADMISSION
MUSICAL POSSIBILITY != RECOMMENDATION
MEMORY != AUTHORITY
```

## Next earned door

The next interesting composition is not to make Phonograph more autonomous.

It is to let a human explicitly admit a Phonograph proposal as a new bounded radio specimen:

```text
source window
→ Phonograph proposal
→ audition
→ HUMAN ADMIT
→ proposal audition becomes new AUDIO WINDOW source
→ two fresh first listens
→ compare response-to-source
```

That would create the first lawful recursive musical conversation without allowing recursion to erase lineage.
