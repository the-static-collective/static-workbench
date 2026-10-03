# LISTENER DELTA 001 — Compare the Encounter Without Grading the Listener

## Claim

After a Phonograph proposal has been explicitly admitted as a descendant radio specimen, the Workbench can now preserve two distinct Dogram receipts:

1. **GENERATION-DELTA-001** — what finitely measurable signal properties changed?
2. **LISTENER-DELTA-001** — what finitely measurable structure changed in the sealed first responses?

They are sequential in the Field, but they remain separate measurements.

```text
parent AUDIO WINDOW
→ 2 sealed first listens
→ sealed cross-read
→ Haunted Phonograph proposal
→ HUMAN ADMIT
→ descendant AUDIO WINDOW
→ 2 fresh sealed first listens
→ sealed cross-read
→ GENERATION-DELTA-001
→ LISTENER-DELTA-001
```

## Why signal delta comes first

Workbench requires a durable GENERATION-DELTA-001 receipt before it exposes LISTENER-DELTA-001.

This ordering does **not** mean signal change caused response change.

It guarantees only that both measurements point to the same explicitly admitted parent → descendant lineage.

```text
MEASUREMENT ORDER != CAUSAL ORDER
SIGNAL DELTA != LISTENER DELTA
RESPONSE DELTA != CAUSAL EFFECT
```

## Exact witness carrier

LISTENER-DELTA does not receive dialogue summaries or copied prose.

Workbench resolves the exact:

- parent LOOK TWICE pair;
- descendant LOOK TWICE pair;
- two sealed parent first-response receipts;
- two sealed descendant first-response receipts;
- Phonograph re-entry witness;
- GENERATION-DELTA receipt.

The Dogram instrument independently verifies each sealed Autodisco response identity before measuring it.

The House verifies the returned receipt against those same four stored `first_response_id` values before persistence.

## Field progression

The Dogram lane now has three earned states.

### 1. Signal unmeasured

> **Measure what changed from parent to descendant**

Adapter:

`Dogram / GENERATION-DELTA-001`

### 2. Signal measured, listener transform unmeasured

> **Measure how the sealed first responses changed**

Adapter:

`Dogram / LISTENER-DELTA-001`

This door appears only when:

- parent and descendant have sealed radio cross-reads;
- GENERATION-DELTA exists;
- parent has exactly two sealed first responses;
- descendant has exactly two sealed first responses;
- the local Dogram checkout actually contains `scripts/listener_delta.py`.

### 3. Listener transform measured

> **Inspect the measured listener-response delta**

The Field shows:

- Dogram listener receipt hash;
- response-change classification;
- listener count;
- changed-listener count;
- changed axes shared across both listeners.

The full receipt remains available separately.

## What Dogram measures

Per listener:

- exact persisted observations;
- exact appeared observations;
- exact disappeared observations;
- declared-mode migrations of identical normalized text;
- mode-count changes;
- lingering-intrigue transition;
- closing-line structural change;
- exact lexical vocabulary change;
- model continuity or change.

Across the two listeners:

- shared changed axes;
- union of changed axes;
- exact newly appeared tokens shared by both;
- exact disappeared tokens shared by both;
- exact newly appeared normalized observations shared by both.

This is a mechanical comparison.

```text
LEXICAL OVERLAP != SEMANTIC AGREEMENT
SHARED CHANGE AXIS != SHARED MEANING
```

## What remains residual

The receipt explicitly does **not** establish:

- semantic similarity;
- preference;
- musical value;
- anything essential about a listener;
- causal effect of the audio change;
- separation of stochastic generation effects;
- unobserved listener context.

Even when `model_used` is unchanged, two fresh generative calls are not deterministic repeated measurements.

```text
FIRST LISTEN != STABLE PREFERENCE
RESPONSE DELTA != PERSON DELTA
RESPONSE DELTA != CAUSAL EFFECT
```

## House witness

The durable House witness is:

`dogram_listener_delta:<child-window-id>`

It binds:

- local House crossing receipt;
- parent window;
- descendant window;
- Phonograph proposal receipt;
- GENERATION-DELTA receipt hash;
- Dogram LISTENER-DELTA receipt hash;
- exact parent and child first-response identities;
- classification;
- listener counts;
- shared and union changed axes;
- lexical cohort deltas;
- residuals;
- local receipt path.

A different listener measurement cannot silently replace the same descendant witness.

## API

Execute the measurement:

```text
POST /api/doorhouse/receipts/{receipt_id}/dogram/{child_window_id}/listener-delta
```

Read the exact Dogram receipt:

```text
GET /api/doorhouse/receipts/{receipt_id}/dogram/{child_window_id}/listener-delta.json
```

Receipt reads are effect-free.

## Browser surface

Once the signal receipt exists and the Field earns the listener door, the current descendant card exposes:

> **MEASURE LISTENER RESPONSE DELTA**

After measurement it shows:

```text
DOGRAM LISTENERS · MEASURED_RESPONSE_CHANGE
2/2 listeners changed on declared response axes
shared changed axes · ...
Listener delta receipt
```

The UI deliberately does not say:

- liked;
- disliked;
- improved;
- degraded;
- more emotional;
- more successful;
- winner.

## CI evidence split

The cross-repo creative smoke keeps the same honesty boundary as the signal experiment.

First it proves the admitted descendant receives **zero fabricated listeners** when no listener model is available.

Only after that proof does CI inject explicitly synthetic, valid Autodisco first-listen fixtures to exercise downstream gates.

For LISTENER-DELTA, the synthetic parent and descendant responses intentionally differ.

Then CI runs the **real pinned Dogram LISTENER-DELTA-001 implementation** over those exact sealed response receipts.

Thus:

```text
SYNTHETIC RESPONSE CONTENT != LIVE LISTENER EVIDENCE
REAL DOGRAM COMPARISON != SIMULATED DELTA
```

The fixture supplies bounded test witnesses. Dogram performs the real identity verification and transform measurement.

## Laws

```text
DOGRAM MEASURES TRANSFORMS, NOT PEOPLE
RESPONSE DELTA != PERSON DELTA
RESPONSE DELTA != CAUSAL EFFECT
SIGNAL DELTA != LISTENER DELTA
LEXICAL OVERLAP != SEMANTIC AGREEMENT
FIRST LISTEN != STABLE PREFERENCE
DELTA != VALUE
RESIDUAL != FAILURE
MEASUREMENT != SELECTION
```

## Next earned aperture

The next instrument should not merge these receipts.

It should compose a bounded **paired experiment receipt**:

```text
GENERATION-DELTA receipt
        +
LISTENER-DELTA receipt
        +
declared experimental conditions
        ↓
PAIRED EXPERIMENT RECEIPT
```

That receipt could make the question inspectable:

> What changed in the artifact, and what changed in the observed encounter?

while preserving:

```text
CO-OCCURRENCE != CAUSATION
CORRESPONDENCE != EXPLANATION
```
