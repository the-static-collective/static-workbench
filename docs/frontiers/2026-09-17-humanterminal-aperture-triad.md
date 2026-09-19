# HumanTerminal / APERTURE / TRIAD Integration Frontier

**Date:** 2026-09-17  
**Status:** design frontier / no executable model integration yet  
**Authority:** Workbench presentation + routing only; semantic and constitutional owners remain external.

## Purpose

Preserve the HumanTerminal seam discovered after Workbench v0.1 without smuggling a language model into the browser runtime as hidden authority.

Candidate stack:

```text
RAW HUMAN INPUT
      ↓
APERTURE
  Signal / Context / Gap
      ↓
SENSE FIELD
  bounded candidate readings
      ↓
TRIAD
  Fact / Idea / Relation
      ↓
IRON LUNG BRAID
  Substance / Lineage / Authority
      ↓
project-local routing / present admission
```

## Workbench responsibility

Workbench may:

- preserve raw input as an immutable local object;
- show APERTURE output without choosing one reading silently;
- display fact / idea / relation candidates;
- show provenance, transform provider/version, and unresolved gaps;
- route selected objects to project-owned adapters;
- witness user acceptance, correction, refusal, or deferral as new events.

Workbench must not:

- declare a model-selected reading to be human intent;
- convert `FACT` into evidence authority;
- convert a repeated relation proposal into an established relation;
- treat model confidence as admission;
- hide the raw source after transformation;
- require T5 specifically.

## Candidate HumanTerminal surface

```text
┌──────────────────────────────────────────────┐
│ > The bank moved.                            │
│                                      [SEND]  │
├─────────────────────────────────────────────┤
│ APERTURE                                     │
│ Signal  1   Context  0   Gap  1             │
├─────────────────────────────────────────────┤
│ SENSE FIELD                                  │
│ ① financial-institution reading              │
│ ② river-bank reading                         │
│ ③ banking-maneuver reading                   │
│ status: unresolved                           │
├─────────────────────────────────────────────┤
│ TRIAD                                        │
│ Fact  1   Idea  0   Relation  3              │
└──────────────────────────────────────────────┘
```

Every derived item becomes a Workbench Object with a source pointer rather than replacing the source.

## Provider boundary

Candidate capability:

```text
semantic.intake
```

Possible provider descriptor:

```text
provider_id
provider_version
model_id?              # optional
transform_contract
input_scope
context_scope
output_schema
max_candidates
supports_replay
```

A T5 / FLAN-T5 implementation may later advertise the capability, but deterministic fixtures must be usable through the same contract.

```text
APERTURE / TRIA = protocol grammarT5 = replaceable provider
```

## First executable proof

Do not load a neural model yet.

Add a deterministic test provider that maps:

```text
"The bank moved."
```

to three fixed readings and one unresolved gap.

Then submit a second cut:

```text
"After the flood, the bank moved six feet east."
```

Acceptance evidence should show:

1. raw inputs survive unchanged;
6. the second sense field narrows;
3. the first ambiguity receipt remains intact;
4. no semantic role changes constitutional authority;
5. browser restart restores both cuts and their derivation;
6. a user correction creates a new receipt rather than rewriting the model output.

## Routing targets

```text
ALEX
  inspect provenance / evidence posture

Dogram
  calculate sparse tensor / field delta / fibers

3rdi
  inspect observer-local availability / focus / known-at

Iron Lung
  circulate proposals and preserve admission boundary
```

## Seals

```text
AMBIGUITY IS INFORMATION.

POSSIBLE MEANING != INTENDED MEANING.

SEMANTIC ROLE != CONSTITUTIONAL POSTURE.

RAW SURVIVES EVERY TRANSFORM.

THE BROWSER SHOWS THE CUT.
IT DOES NOT CROWN THE CUT TRUE.
```
