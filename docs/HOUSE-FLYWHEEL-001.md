# HOUSE-FLYWHEEL-001 — Capability Return Ledger, isolated v0

## Status
Experimental and non-canonical. Workbench-owned local persistence only. There is no route, UI, background agent, autonomous trigger, import connector, permission delegation, execution adapter, or project-owned receipt minting in this slice.

## Why
Workbench has an operational journal, but a journal event is not a source project's attestation or proof of a reusable capability. Record a bounded, explicitly reported flight return with source and artifact identities, evidence references, cost uncertainty, nonclaims, and possible later tests. This complements, but does not replace, the native source ledger or existing HOUSE Flight Cards.

## Contract
`CapabilityReturnLedger(path).append(packet)` stores the exact v0 field set validated by `validate_packet`; `latest(limit)` and `get(return_id)` only read local records. The canonical JSON SHA-256 is a *local integrity/deduplication aid*, not cryptographic provenance, source authenticity, witnessed fulfillment, or permission to execute. A supplied `scoped_complete` or `reported` is an **importer's statement**, not a Workbench verification decision. References are opaque: the ledger cannot claim to have resolved or checked them.

One `return_id` admits one immutable packet. Identical replay returns the same row; differing content with an existing id is rejected. Further correction uses a separately identified return with its own declared ancestry. A `parent_effect_ref` is informational and does not convey authorization, effect, endorsement, or successful completion. Artifacts retain owner and original identity. Proposed next steps are inert strings. There is no machine ranking of Joyful/Useful/Curiouser or promotion from proposal to proof.

## First local usage

```python
from pathlib import Path
from static_workbench.capability_returns import CapabilityReturnLedger

ledger = CapabilityReturnLedger(Path("~/.local/state/static-workbench/returns.sqlite3").expanduser())
# Build an exact v0 packet using tests/test_capability_returns.py as a fixture.
# This is a local manual import, never a project effect or human authorization.
record = ledger.append(packet)
assert ledger.get(record.packet["return_id"]).local_digest == record.local_digest
```

## Deliberate non-goals and next door
No claim of measured acceleration until a later, independently authorized flight reuses a genuinely tested artifact with effort/cost observations and regression results. Future slices may add read-only HOUSE display, explicit human import, and a Capability Loom that emits inert proposals from separately owned references. Do not grant project effects or turn reported evidence into independently verified evidence by adding an API route.

## Checks
`pytest -q tests/test_capability_returns.py` tests persistence/replay, correction-by-new-identity, duplicate identity refusal, unknown-field/authority smuggling refusal, size bounds and read limits. Existing suite must run separately after branch integration.
