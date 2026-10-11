# HOLOGRAPHIC-FIELD-001 — Receive / Hold / Pour

> **Status: EXPERIMENTAL / NON-CANONICAL.**
>
> This specimen extends HOLOGRAPHIC-KERNEL-001 without changing its authority rules.

## Seed thought

A useful context window may behave less like a transcript and more like a vessel:

```text
RECEIVE
  ↓
HOLD
  ↓
POUR
```

The target is not literal token exhaustion. Production systems need headroom and may suffer when every token is occupied.

The executable hypothesis is narrower:

> Keep the bounded active context as semantically full as useful, while anything that leaves the present survives as an addressable path rather than silent loss.

This creates a machine analogue of an **eternal now**: a locally complete present with explicit doors backward, forward, and sideways.

## TranchNOSE transplant

TranchNOSE models:

```text
M(t) = { X(t), G_local(t), G_field(t) }
```

with the important separation:

```text
G_field != G_local
```

This software specimen translates that architecture metaphorically:

```text
X
= durable kernel state + durable context payloads

G_local
= small coordination references, digests, addresses, and field checkpoints

G_field
= the currently inhabited bounded context frame
```

The no-cheating rule is retained: the coordination plane does not carry the full poured context payload.

## Receive

New context first lands durably.

```text
receive(signal)
→ durable ContextAtom
```

Receiving does not imply that the signal deserves permanent presence in the active field.

## Hold

The field selects a bounded working set using explicit relevance plus recency.

```text
durable context
→ rank
→ active bounded HOLD set
```

If at least `capacity` atoms exist, the semantic-slot specimen fills all available slots.

This is **semantic saturation**, not a recommendation to drive a real model to 100% of its token ceiling.

## Pour

Anything not held is not deleted.

It becomes a coordination reference and a sideways door:

```text
held now
+
poured refs
+
backward doors
+
forward return-address continuations
+
sideways context doors
```

The partition invariant is:

```text
ALL DURABLE CONTEXT
=
HELD
∪
POURED

HELD ∩ POURED = ∅
```

So leaving the active present does not mean ceasing to exist.

## Holographic implication

A Chat projection and a World projection can inhabit different presentations while preserving the same underlying field digest.

```text
CHAT ─┐
      ├─ same kernel state
WORLD ┘  same held context
         same poured references
         same door geometry
```

Presentation changes. The relational now does not.

## Strong extinction test

The active field can be destroyed completely.

A checkpoint preserves only coordination references and field geometry. A fresh field instance must reconstruct the same operational now using:

```text
durable X
+
G_local references
+
current kernel projection
```

It must refuse reconstruction when:

- the kernel has moved;
- required durable context is missing;
- a coordination reference was tampered with;
- the capacity contract changed.

This intentionally mirrors TranchNOSE's caution: successful reinstantiation does **not** mean memory lived only in the transient field.

## The three kinds of door

### Backward

A later now can reference the previous field digest.

### Forward

Forward doors come from the kernel's own return-address continuations.

The context field does not invent them.

### Sideways

Poured context remains reachable by durable context identity.

This makes `POUR` displacement rather than deletion.

## Candidate phaselift

Combined with HOLOGRAPHIC-KERNEL-001:

```text
durable kernel truth
        │
        ▼
projection
        │
        ▼
RECEIVE → HOLD → POUR
        │
        ▼
CURRENT RELATIONAL NOW
   ↙       ↓       ↘
BACK     FORWARD    SIDE
```

A possible long-range rule is:

> **The active window need not remember everything if it remembers how the present relates to everything it has poured.**

That is stronger than transcript accumulation and weaker than magical lossless compression.

It makes context a navigable field.

## BATs

The current BAT suite tests:

1. semantic saturation when sufficient context exists;
2. every durable atom is either held or poured;
3. relevance + recency can reshape the present without rewriting durable memory;
4. poured material leaves sideways doors;
5. forward doors originate in kernel return addresses;
6. successive presents leave backward doors;
7. projection kind does not change the underlying field digest;
8. the coordination plane does not contain poured payload text;
9. strong extinction can reconstruct the same now through a different projection;
10. missing durable payload prevents reconstruction;
11. tampered coordination references refuse;
12. checkpoints refuse after kernel movement;
13. empty context refuses;
14. a deterministic 100-step RECEIVE/HOLD/POUR swarm stays bounded and leaves no context orphaned.

Run:

```bash
pytest -q tests/test_holographic_field_001.py
```

## Boundary

This specimen does not claim:

- that relevance scoring is solved;
- that a slot equals a model token;
- that keeping a model near its context ceiling improves model quality;
- that all poured context should remain forever;
- that a field digest constitutes semantic equivalence in general;
- that current LLM attention behaves like an optical field.

The point is architectural:

> **present context can be transient while continuity remains durable and traversable.**
