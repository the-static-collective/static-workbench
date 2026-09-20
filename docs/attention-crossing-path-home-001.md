# PATH-ALL-HOME-001 — Explicit attention handoffs

Status: experimental, Workbench-owned. Stacked on ATTENTION-CROSSING-002,
which is stacked on ATTENTION-CROSSING-001. Neither application automatically
synchronizes its notes, audio, broadcasts, or attention history with Workbench.

A human explicitly exports one native declaration from GOATnote or Static Live,
pastes the bounded JSON into the Workbench Attention Shelf, previews the
source-owned identity, locator, dimensions and raw JSON SHA-256, and separately
clicks Import reviewed copy. Workbench checks the exact reviewed bytes again.
Only a short label/locator and value metadata are stored in
state_dir/attention-imports.sqlite3. No underlying note body, recording file,
source path access, or external application mutation occurs.

The envelope schema is attention-crossing.handoff/v0.1. The source app,
source record id, source target id, timestamp, previous source record id,
locator, optional mark combination, explicit-none flag, label and
evidence="source-export/self-reported" remain separate from the Workbench
import receipt ID and imported-at timestamp. A duplicate source-app/record-ID
with equivalent payload is idempotent; a conflicting payload is refused.
Import history is append-only. The UI presents the latest *imported* record
per source target rather than claiming to know the latest *source-side*
revision. Re-importing an older export later may change the visible imported
projection without proving source freshness; inspect the displayed source
timestamp before drawing conclusions.

Imported external marks are read-only copies and are not mounted as local
Workbench-value buttons. No cross-app writable sync, equivalence, authenticity
proof, recommendation ranking, or execution authority is claimed. The
source-export declaration and Workbench receipt are two different events.
The browser-local single-user session is not remote multiuser authentication.

Verification: run python -m pytest -q tests/test_attention_handoff.py and
node --check static_workbench/web/attention.js; CI runs the existing full
Workbench suite. Actual workstation browser paste/review/import and restart
smoke must still be performed.
