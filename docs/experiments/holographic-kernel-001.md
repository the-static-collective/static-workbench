# HOLOGRAPHIC-KERNEL-001 — executable projection specimen

> **Status: EXPERIMENTAL / NON-CANONICAL.**
>
> This slice tests a proposed architectural law. It grants no new execution authority to HOUSE, projections, ChatGPT, world objects, or other surfaces.

## Question

Can one durable kernel be projected into radically different surfaces without duplicating authority, rewriting witnessed meaning, or losing a lawful way to continue?

This specimen uses a tiny **Story Door** kernel and four projections:

- `chat`
- `html`
- `cli`
- `world`

The projections intentionally look different. They must nevertheless agree on the constitutional envelope:

```text
kernel identity
current witnessed state
state digest
authority owner
available affordances
lineage head
return address
```

## Proposed laws under test

### 6 — projection does not own the kernel

A projection can show state and affordances. It cannot execute a crossing.

Only the kernel-declared authority may consume an exact preview.

```text
projection != authority
presentation != state owner
displayed affordance != execution right
```

### 7 — witnessed meaning changes by relation, not silent replacement

Once a state is witnessed, the specimen provides no mutation path for rewriting its content.

A reinterpretation creates a new witnessed state linked by a typed relation:

```text
A --reframes--> B
```

The old state remains inspectable and reconstructable.

### 9 — every completed crossing emits a return address

A successful crossing returns:

```text
kernel
current state
unresolved questions
residue
valid continuations
```

The return object is projection-agnostic. Chat, HTML, CLI, and World projections can all reconstruct the same lawful continuation neighborhood from it.

## Crossing grammar

```text
SOURCE STATE
    ↓
PROPOSAL
    ↓
EXACT PREVIEW
    ↓
HUMAN CUT
    ↓
KERNEL-OWNED EXECUTION
    ↓
OBSERVED CONSEQUENCE
    ↓
TYPED LINEAGE
    ↓
RECEIPT + RETURN ADDRESS
```

The preview is a real computational object. It records the exact base state, candidate content, relation, rationale, predicted delta, and required authority.

If the kernel head changes before execution, the preview becomes stale and refuses.

## BAT suite

The tests are deliberately adversarial rather than only happy-path examples.

Current bats prove that:

1. four different projections preserve one constitutional envelope;
2. a projection cannot execute;
3. kernel authority can execute the exact inspected crossing;
4. witnessed meaning cannot be silently rewritten;
5. reinterpretation creates a `reframes` relation and preserves its source;
6. stale previews refuse after an intervening crossing;
7. tampered preview content refuses;
8. tampered relation semantics refuse;
9. a return address survives World → Chat → CLI projection changes;
10. each new projection reconstructs current lineage;
11. presentation may differ without state drift;
12. mutating a projection object does not mutate the kernel;
13. unknown projection kinds refuse instead of guessing;
14. unknown operations refuse instead of inventing affordances;
15. return addresses preserve current unresolved questions and residue;\n16. a deterministic 100-crossing projection-hopping swarm preserves lineage, immutable witnessed meaning, return-address continuity, and one shared constitutional envelope.

Run:

```bash
pytest -q tests/test_holographic_kernel_001.py
```

## What this does not prove

- network/distributed consistency;
- persistence across process restart;
- cryptographic signatures;
- multi-user authorization;
- concurrency control beyond stale-head refusal;
- safe dynamic loading of arbitrary organ kernels;
- that Story Door's exact operation vocabulary should become ecosystem law;
- that HOUSE should automatically admit arbitrary projections.

Those remain later gates.

## Why this matters

If the contract survives stronger trials, the integration question changes from:

> How do we put tool X into surface Y?

to:

> What lawful projection of kernel X belongs at Y?

That permits ChatGPT, HTML, CLI, MEMENTO objects, world rooms, physical controls, or future interfaces to inhabit the same computational organ without becoming competing sources of truth.

The intended long-range shape is:

```text
                         CHAT
                          |
HTML -------------- KERNEL -------------- WORLD
                          |
                         CLI

                          |
                   typed lineage
                          |
                   return addresses
```

HOUSE can then become a **projection composer**, while STATIC OS becomes a **projection habitat**, without absorbing project-native authority.
