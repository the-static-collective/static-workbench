# HOUSE Creator Desk × Hugh Jackman Discontinuity Maxhinal — Ride Dock v0.1

## What exists

The original [MADD Hugh Jackman Maxhinal](https://github.com/the-static-collective/the-daily-slice/blob/main/artifacts/maxhinal/README.md) belongs to the Daily Slice repository. It already provides a local browser bench, deterministic shared browser/CLI core, eight bounded chambers, derived-output ancestry, bad-spin preservation, and portable `.maxhinal.json` rides.

HOUSE is **not** a replacement Maxhinal runtime. It provides a local *ride dock* where a person can deliberately preserve a copy of an actual exported ride next to a saved Creator Desk source pack, then explicitly link the imported ride to a creative draft revision.

The distinction matters: **Daily Slice gas != arbitrary Creator Desk excerpt != a derived projection**. Associating a Maxhinal ride with a source pack is a human-declared creative-use relation, not a claim the Maxhinal consumed those source-pack passages.

## Operator flow

1. Install/clone the real `the-daily-slice` repository under a HOUSE configured root. The Creator Desk shows the expected local browser artifact path: `artifacts/2026-08-25/hugh-jackman-discontinuity-machine.html`. Confirm that file exists, then open it with the local file manager. The link to source-owned instructions explains CLI operation. HOUSE does not execute project scripts or load Daily Slice JavaScript into the HOUSE origin.
2. In the Maxhinal itself, select real Daily Slice corpus gas, choose a chamber, perform one or more operations, preserve bad spins and residuals, then export the native `.maxhinal.json` ride.
3. Open Creator Desk, select an explicitly saved source pack, paste the exported JSON into the Maxhinal Ride Dock, and choose **Preview this Maxhinal ride**.
4. HOUSE checks the bounded JSON shape (format, corpus reference, seed, Slice gas, operation/output identity and non-promotion fields). It displays the **self-reported** corpus and replay values, modes, operation references, bounded previews of actual derived projections, residuals and bad-spin reasons, and hashes the *exact pasted UTF-8 bytes*. A separate manual **Copy reviewed ride projections + residuals** action transfers those notes into a draft without silently selecting a creative interpretation.
5. Choose **Dock this reviewed ride locally** to preserve that JSON and its SHA-256 in HOUSE-owned `state_dir/creator.sqlite3`. HOUSE does not run the ride or assert it can be replayed against the currently installed corpus. The original `.maxhinal.json` remains authoritative for its own provenance only to the extent verified by the source-owned Maxhinal.
6. Choose the docked ride in Creator Desk. The **next explicit draft save** retains `maxhinal_ride_id` on that draft revision. The saved source pack remains its own source identity. Copying a finished draft includes the ride's local dock id and digest, with a warning that it is an unverified imported ride, not a publication receipt.

## Scope and safety

- No automatic conversion of search matches into canonical Slice records; no source Markdown mutation, project operation, OBS execution, Git push, publication, or LLM invocation.
- The imported JSON is untrusted text. HOUSE does not execute embedded strings or allow arbitrary file paths. Parsed information is displayed with text-only browser nodes.
- Ride imports are capped at 128 KiB, 64 operations, 64 outputs, 128 residuals, 128 bad spins, and declared Slice gas. Identity/authority fields and output ancestry must pass structural validation. A matching shape does **not** verify that the ride came from an honest machine or that its outputs are true.
- The local shelf has a separate source-pack ownership check: a docked ride cannot silently attach to a draft belonging to another pack. Draft saves append revisions and reject stale edit numbers.
- A user explicitly selects and reviews the pack, ride, and draft connection. Different origins remain distinct.
- HOUSE does not claim a newer Slice corpus merely because the historical 27-record browser projection can be found. The original machine must be run on an explicitly chosen installed corpus; reported `replay.status` is never treated as independent verification.
- This is a local single-user application, not a multi-user permission system. Configure roots carefully and avoid pasting other people's private material.

## Next bounded frontier

A read-only, version-pinned local Daily Slice *corpus index adapter* could expose actual Slice IDs and corpus digest for explicit human gas selection inside HOUSE. A separate invocation adapter would require a pinned engine version and a demonstrated replay/interrupt/reconcile contract. Neither exists in this ride-dock implementation.
