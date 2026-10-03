# FIELD RETURN 001 — Native Door → Human Disposition → Reseed

FIELD RETURN 001 is a small native Workbench composition primitive.

It exists because several previously separate lines have converged:

- **FIELD-STATION-001** can now compose a bounded set of nearby, attributable doors without ranking or selecting them.
- **RSC Composer** established that a useful composition can end in a portable reseed rather than a flattened conclusion.
- **reLATTE** keeps proposal, transport, admission, local consequence, and authority distinct.
- **GHoT / HOUSE** makes observed state playable without pretending observation is command authority.
- **Phonograph FIELD ANSWER 001** proved that a neighboring organ can answer a bounded specimen while remaining proposal-only.
- the wider Collective keeps returning to the same law: transformation should preserve enough provenance to reconstruct what changed.

The missing seam was the human return.

Before this slice, the Field could say: **these doors are nearby**.

Now the Workbench can also represent:

> **I saw this exact field, I deliberately took / held / passed this exact door, and here is the receipt for that disposition.**

If the disposition is `take`, the exact door can become a proposal-only reseed packet.

## Grammar

```text
observed field
    ↓
attributable door
    ↓
human disposition
    ├── TAKE ──→ proposal-only reseed
    ├── HOLD ──→ retained possibility
    └── PASS ──→ explicit local non-selection
    ↓
Workbench-owned return receipt
```

The important part is what does **not** collapse:

```text
FIELD OBSERVATION != HUMAN DISPOSITION
RECOMMENDATION != SELECTION
SELECTION != EXECUTION
DOOR != CROSSING
RESEED != ADMISSION
RECEIPT != AUTHORITY
```

## Schemas

A return is `workbench.field-return/v0`.

It binds:

- the exact verified `field_state_id`;
- the exact `door_id`;
- the human disposition;
- an optional human note;
- a detached canonical snapshot of the selected door;
- `effect: none`.

For `take`, the return also carries a `workbench.field-reseed/v0` packet with its own deterministic identity.

The reseed carries the exact selected door, its evidence, target metadata, adapter label, and human note. It remains:

```text
status: proposal-only
effect: none
```

A downstream organ may later define how it receives such a reseed, but receipt of a packet must not be confused with admission or authority.

## Why this is native

This is not a wrapper around a single external project.

The primitive belongs to the Workbench's own job:

1. witness the local field;
2. preserve the exact aperture shown to the human;
3. preserve the human's explicit disposition;
4. produce continuity material another instrument can inspect.

That makes it a House-native connective tissue rather than an adapter-specific feature.

It also gives the recent growth a common user-facing sentence:

> **The system can show me where I could go, preserve what I chose, and carry that choice forward without pretending it already happened.**

## Current boundary

FIELD RETURN 001 is deliberately a pure logic slice.

It does **not** yet:

- persist returns in SQLite;
- add UI controls to Field Station;
- execute a target;
- call another project;
- send a reLATTE crossing;
- write TranchNode continuity;
- imply that a downstream organ accepted the reseed.

Those are separate seams and should be proved separately.

## Next breach

The next honest native slice is:

```text
Field Station UI
    ↓
explicit TAKE / HOLD / PASS
    ↓
persist Workbench return receipt
    ↓
inspect/copy/export exact reseed
```

Only after that survives local use should one version-pinned receiver be allowed to ingest a reseed, ideally through a boundary-preserving crossing whose destination keeps local admission authority.
