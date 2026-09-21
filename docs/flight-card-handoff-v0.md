# HOUSE Flight Card handoff v0 — inspect before binding

**Status:** proposed Workbench-owned wire format; experimental, additive, non-executing. The Lovable *Flight Card Studio* project has **not** been verified to emit this format and is **not** connected to HOUSE. This is an integration target, not a claim of live integration. Neither this format nor its hashes are ALEX, 3rdi, or LOADOUT native receipts.

## The crossing

```text
RAW source + attributable witness entries + bounded proposed effects
          |
          v
Flight Card candidate JSON   --untrusted external input-->
          |
          v
HOUSE flight_cards.validate_candidate
  syntax / bounds / source / witness-class / exact approval-snapshot checks
          |
          v
INERT inspection record (never an invocation, authorization, or evidence verification)
          |
          v
future separately authorized LOADOUT adapter (NOT IMPLEMENTED)
          |
          v
human- or project-owned work -> independently sourced evidence as applicable
          |
          v
explicit, separately entered self-report return (NOT an execution receipt)
```

A user approving a card is testimony of intent, not evidence the claimed actor is authenticated, not authorization to mutate this machine, and not approval by a project owner. The receiver must separately prove local authority, availability, effect reachability, permission, scope and re-validation at the moment of any eventual action. An effect list is descriptive text; do not turn it into executable commands.

## Candidate shape (illustrative synthetic data)

```json
{
  "schema": "house.flight-card-candidate/v0",
  "flight_id": "ff9512ee-cb20-4a3f-9526-7b0f66cd4885",
  "raw": {
    "text": "Inspect this synthetic sample note; preserve its source.",
    "source_type": "text",
    "locator": null,
    "captured_at": "2026-09-20T10:00:00-05:00",
    "observer": "demo operator"
  },
  "witnesses": [
    {
      "id": "aa5dc38b-c67f-4346-90fb-748e56d99145",
      "class": "unresolved",
      "text": "A claim needs a source before it can be tested.",
      "observer": "demo operator",
      "source_locator": null,
      "occurred_at": null,
      "recorded_at": "2026-09-20T10:01:00-05:00",
      "known_at": null,
      "nonclaims": ["Not a verified source claim"]
    }
  ],
  "proposal": {
    "job": "Read the sample note and report a bounded observation",
    "tools": ["ALEX suggested; not invoked"],
    "effects": [],
    "fence": "No network, file writes, repo mutations or external publication",
    "unknowns": ["Source authenticity"],
    "verification": "Compare the human report against the preserved sample"
  },
  "approval": null
}
```

The original `raw.text` is the source-bearing field in the candidate. This validator cannot prove that an exporter has preserved earlier versions: Studio must preserve a separate immutable source and append-only event history, and any future receiver with a prior snapshot must compare it explicitly. The current v0 has no journal import, lineage attestation or authenticity guarantee.

For a **human approval claim**, set `approval` to an object with exactly `actor`, `approved_at` (timezone-aware ISO 8601), `proposal_sha256`, and `effects` (a byte-for-byte structurally equal list to `proposal.effects`). The digest is SHA-256 of UTF-8 JSON of the **proposal object**, with sorted keys, no spaces, and unescaped Unicode (Python: `json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`). Recompute the digest after each edit; an older approval is invalid, not silently transferred.

Validation is bounded to 128 KiB serialized input with exact object keys, canonical UUIDs, timezone-aware dates, enumerated evidence classes, explicit nonclaims, and finite lists. No arbitrary URL is fetched; source locators are inert text.

## Try it

Save a candidate JSON specimen as `flight.json`, then run:

```bash
python -m static_workbench.flight_cards flight.json
python -m pytest -q tests/test_flight_cards.py
```

Inspection prints a JSON record containing the candidate and proposal digests, witness count, whether external approval is claimed, and explicit `not_evaluated` / `not_attempted` outcomes. The CLI reads only the named local JSON file; it does not register the card with Workbench, touch any project repo, bind capabilities, or invoke LOADOUT.

`self_report(candidate, report)` is a pure Python helper for a separately supplied human report. It preserves the inspected candidate digest, exact human-chosen status (including partial/unresolved), source locators, nonclaims and optional parent receipt hash, and marks the outcome `self_reported`, `independently_verified: false`. It does not create a Workbench/project execution receipt or persist anything. The parent hash is a **reference**, not proof of a valid ancestral chain.

## Lovable adapter gate

When Flight Card Studio can export real JSON, write a narrow **translation adapter** from its observed schema to this specimen and test on anonymized examples. Do not infer that the Studio prototype already meets this format. Independently verify round-trip preservation of RAW bytes/text, observer/event time vs known-at, evidence class, unchanged approval snapshot, effect list, nonclaims, incomplete statuses, and parent/child return. Reject unknown fields rather than silently inventing permissions. Keep this specimen standalone until that gate passes.

No project execution, LOADOUT integration, authenticated human signature, source authenticity verification, append-only journal storage, import API, browser drag-and-drop, or public deployment is included in v0.
