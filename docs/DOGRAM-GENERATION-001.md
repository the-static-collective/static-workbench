# DOGRAM GENERATION 001 — Measure the Return Without Turning It Into a Verdict

## Claim

Once a Haunted Phonograph proposal has been explicitly admitted as a descendant radio specimen, and both parent and descendant have completed sealed First-Listen Radio cross-reads, the Field Station may expose one bounded Dogram measurement door.

The door says:

> **Measure what changed from parent to descendant**

Dogram computes a finite signal delta. It does not decide whether the descendant is better, worse, more musical, more faithful, more meaningful, or more successful.

```text
parent AUDIO WINDOW
→ sealed parent first listens
→ sealed parent cross-read
→ Phonograph proposal
→ HUMAN ADMIT
→ descendant AUDIO WINDOW
→ sealed descendant first listens
→ sealed descendant cross-read
→ DOGRAM GENERATION-DELTA-001
→ finite transform receipt
```

## Capability gate

The Field advertises Dogram only when the local discovered checkout actually contains:

`scripts/generation_delta.py`

Repository presence alone remains insufficient.

```text
REPOSITORY PRESENT != CAPABILITY AVAILABLE
```

Workbench CI pins the landed Dogram implementation at:

`f352fe50bde594f9e88ebb37a58b58fbf3aeaedd`

## Witness gate

The raw PCM math could technically execute earlier.

The Field and House deliberately require more.

Both exact generations must have sealed audio LOOK TWICE dialogue witnesses before the measurement action is admitted.

That means the comparison belongs to two encountered generations, not merely two files on disk.

```text
FILE EXISTS != GENERATION WITNESSED
PARENT WITNESS != CHILD WITNESS
MEASUREMENT GATE != MATHEMATICAL NECESSITY
```

The gate is enforced both:

1. before the Dogram subprocess runs at the API boundary;
2. again when the House records the returned receipt.

## Exact carriers

Workbench rehydrates the exact canonical bounded WAV for:

- the parent window;
- the descendant window.

It sends those bytes to Dogram with the durable Phonograph re-entry relation:

- parent window id;
- child window id;
- explicit human admission;
- proposal receipt hash;
- audition digest.

The returned Dogram receipt must preserve the exact House audio digests for both carriers.

## Measured axes

GENERATION-DELTA-001 currently receipts:

- frame-count delta;
- floor-duration delta plus frame remainder;
- four-quarter RMS amplitude delta;
- peak-amplitude delta;
- zero-crossing-activity delta.

Dogram returns:

- changed axes;
- unchanged axes;
- `MEASURED_CHANGE` or `NO_MEASURED_CHANGE`.

These are measurement classifications only.

```text
DELTA != VALUE
MEASURED CHANGE != MUSICAL MEANING
```

## Residuals

Dogram explicitly leaves unresolved:

- pitch or key;
- harmony;
- instrumentation;
- semantic meaning;
- musical value;
- listener effect.

Workbench preserves those residuals.

```text
RESIDUAL != FAILURE
UNMEASURED != ABSENT
SIGNAL DELTA != LISTENER DELTA
```

## House witness

The durable House witness is:

`dogram_generation_delta:<child-window-id>`

It binds:

- local House receipt;
- parent window;
- descendant window;
- Phonograph proposal receipt;
- exact parent/child audio digests through the Dogram receipt;
- Dogram receipt hash;
- measured classification;
- changed and unchanged axes;
- residuals;
- local receipt path.

A different measurement cannot silently replace the same descendant receipt.

## Field transition

Before measurement, after both cross-reads exist:

> **Measure what changed from parent to descendant**

After measurement:

> **Inspect the measured generation delta**

The Field does not rank that door above the Phonograph, live, present, House, or silence lanes.

There is no score.

## Six-door law

Adding Dogram creates a seventh possible lane in a fully populated field.

FIELD-STATION now preserves constitutional silence explicitly:

- at most five non-silence doors;
- **Hold silence** always survives as the final door.

This is deterministic lane coverage, not relevance ranking.

```text
MORE CAPABILITY != LESS SILENCE
```

## UI

The current descendant receipt shows either:

`MEASURE PARENT → DESCENDANT`

or, after measurement:

```text
DOGRAM · MEASURED_CHANGE
changed axes: ...
Generation delta receipt
```

The language intentionally avoids:

- improved;
- degraded;
- winner;
- score;
- quality.

## CI evidence split

The creative smoke retains two distinct claims.

### Real absence proof

The admitted Phonograph descendant starts a fresh LOOK TWICE run with no model key.

Result:

`0 descendant first listens`

This proves no listener witness is inherited or fabricated.

### Downstream measurement integration

Only after that absence proof, CI adds explicitly synthetic first-listen and cross-read fixtures for the descendant, exactly as the broadcast-assembly proof already does for downstream gates.

Then the smoke runs the real pinned Dogram implementation over the real parent and descendant WAVs and records the real Dogram measurement receipt.

```text
SYNTHETIC LISTENER FIXTURE != LIVE LISTENER EVIDENCE
REAL PCM DELTA != SYNTHETIC PCM DELTA
```

The listener fixtures open the gate; they do not supply the signal math.

## Laws

```text
DOGRAM MEASURES TRANSFORMS, NOT PEOPLE
DELTA != VALUE
MEASURED CHANGE != MUSICAL MEANING
RESIDUAL != FAILURE
SIGNAL DELTA != LISTENER DELTA
DOGRAM RECEIPT != MUSICAL VERDICT
MEASUREMENT != SELECTION
MORE CAPABILITY != LESS SILENCE
```

## Next earned door

The signal transform is now measurable.

The next distinct instrument is **listener delta**:

```text
parent sealed first listens
        ↕
descendant sealed first listens
        ↓
declared comparison dimensions
        ↓
Dogram
        ↓
what changed in the observed responses?
```

That should remain separate from signal delta so the system can eventually ask whether a measurable audio change corresponded to a measurable listener-response change without collapsing either into meaning or value.
