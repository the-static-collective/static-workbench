# HOUSE-FLYWHEEL-002A — Read-only Return Shelf

## Dependencies and scope

This is a stacked draft on HOUSE-FLYWHEEL-001 (PR #41). Until the ledger PR is integrated, this draft targets its feature branch. The shelf reads ONLY Workbench-owned `capability_returns.sqlite3` produced by explicitly supplying packets to the v0 ledger. It does not discover, synthesize, import, or authenticate project-native returns, inspect local checkout files, trigger Git operations, or provide an effectful endpoint.

## What a person sees

HOUSE exposes **Inspect Capability Returns**, and Navigator exposes **Return Shelf**. The page reads up to 50 reports through `GET /api/house/returns?limit=50`, newest first. Each card preserves the original reported return ID, flight and source reference, effect state, capability delta, artifacts with individual owners/refs and reported capability states, evidence refs, resource costs, nonclaims, local digest, and inert next-step strings. Expanding a card is a browser-only visibility operation. This is **not** the separate Workbench operational journal.

The API also supports `GET /api/house/returns/{return_id}`; the bounded list supports 1–100 items, with invalid limits rejected and unknown identities returned as 404. No `POST`, `PUT`, `PATCH`, or `DELETE` route exists for this shelf. Import remains manual through the ledger's local Python interface and is *not* part of this PR.

## Provenance and security

The words “reported” and “not independently verified” remain visible even if the source packet claims `scoped_complete`. SHA-256 is local deduplication, not project-native provenance or source authentication. A parent-effect reference does not confer authorization. Unknown or missing evidence remains opaque text; this UI must not turn arbitrary reference strings into actionable URLs, HTML, executable instructions, or machine-readable permissions. Browser rendering uses text nodes/textContent only, never innerHTML. There is no automatic selection, sorting by human value, candidate creation, promotion or project execution.

## Validation and next flight

`pytest -q tests/test_return_shelf.py tests/test_capability_returns.py` and the full Workbench test suite should pass in CI before integrating. Tests cover bounded reads, unknown identity refusal, no write method, persistence, and hostile text remaining inert. Browser smoke test: open HOUSE, select Return Shelf with an empty DB; supply a local fixture report explicitly, refresh, inspect the card and expand/collapse; check that all fields are source-labeled and read-only.

The next **separate** flight is an inert Capability Loom that may propose two-way compositions only from human-selected exact artifact references, with independent admission before any effect.
