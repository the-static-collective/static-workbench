# Static Workbench v0.2 — HOUSE

The browser is now a local habitat surface for a machine containing many Static Collective repositories.

## Added

- Default **House** landing view.
- Automatic local repository inventory under configured roots.
- Bounded core-organ presence map for Haunted Toaster, Dogram, ALEX, 3rdi, LOADOUT, Static Live, Band Runtime, Garden/NanaSpork, Jubilee Engine/Book of Acts, and Full Measure.
- Common stack-marker detection without executing manifests.
- Dirty / diverged / detached summary before any project crossing.
- Repository filter and per-repository stack/marker inspection.
- `GET /api/house` read-only habitat summary.
- `scripts/bootstrap-local.sh` for a low-friction local venv/config installation.

## Preserved

- loopback-only supervisor;
- no browser-supplied shell commands;
- bounded filesystem roots and symlink/traversal refusal;
- project state remains read-only;
- HumanTerminal/APERTURE receipts remain Workbench-owned formation history;
- project-native receipts and authority remain local to their owning projects.

## House law

```text
present != ready
ready != authorized
compatible != admitted
workbench receipt != project receipt
```

## Verification

- Python test suite: 35 passed.
- JavaScript syntax: `node --check static_workbench/web/app.js`.
- Python compile check: `python -m compileall -q static_workbench`.
- Bootstrap script syntax: `bash -n scripts/bootstrap-local.sh`.
