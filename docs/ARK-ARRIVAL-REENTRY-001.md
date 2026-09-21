# ARK → ARRIVAL → RE-ENTRY — first bounded slice (001)

**Status:** proposed integration, tested only where evidence is recorded. This is a
read-only first-ignition CLI plus a versioned descriptive inventory, **not** a
one-click installer, all-repo downloader, browser onboarding wizard, backup
system, Linux workstation certification, or an effectful agent.

## Why this slice is independent of the rectified carrier

This PR targets the existing main branch, not draft carrier #48. It adds one
module, a packaged JSON manifest, a CLI entry via `python -m`, tests, and this
document. It does **not** modify the app routes, shared SQLite schema, UI,
existing project adapters, or any work on #48/#49/#50. Reconcile it with #48
before promoting either; do not assume their source heads are compatible.

## Run on the actual Linux workstation

Use a trusted source checkout, Python 3.11+, and the existing Workbench config.

```bash
python -m static_workbench.arrival --config ~/.config/static-workbench/config.toml
```

The JSON report identifies manifest roles, bounded discoverable local
checkouts, dirty/detached state and ambiguous duplicate checkouts. Missing
roots and optional organs are visible without being treated as failure. All
`installed`, `compatible`, and `ready` statuses remain `not_evaluated`;
`authorized` remains false. Neither the manifest nor a Git checkout
authenticates a remote history. Running discovery uses Workbench's already
existing fixed Git inspection commands, but never checks out branches,
installs dependencies, runs project code, or invokes plugins.

Once you have created and **explicitly saved** a source pack and a draft in
Creator Desk, record its numeric draft ID and run:

```bash
python -m static_workbench.arrival --config ~/.config/static-workbench/config.toml --draft-id 1
```

Replace `1` with the actual saved draft ID. The CLI opens the existing
Creator shelf SQLite file read-only, recomputes the saved source-pack digest
and the saved draft-body digest, and returns an exact resume pointer:
pack ID/hash, draft ID/revision/body hash, title and kind, and a Creator Desk
destination. It does **not** echo private draft text. The original draft and
pack stay in Creator Desk; no new re-entry database is created.

A verified **saved local snapshot** does not establish that the underlying
worktree source has stayed unchanged, that an external handoff succeeded,
that a project-native result was produced, or that an action may execute.

## First-flight checklist

1. Run ARK diagnostic before downloading project organs. Observe missing and
   ambiguous checkouts; do not mistake installed tools for tested readiness.
2. Start the existing HOUSE browser, select bounded source lines in Creator
   Desk, preview and explicitly save a source pack.
3. Create and save a lyric or other draft against that pack. Record the draft ID.
4. Run ARRIVAL with `--draft-id` and preserve its exact resume pointer.
5. Restart HOUSE; reopen Creator Desk and load the saved draft ID, compare
   revision, pack ID and hashes against the CLI pointer.
6. Change a source file and verify that its old saved snapshot remains
   historically available but source freshness cannot be inferred. Independently
   test backup/restore before relying on this as durable recovery.

## Next distinct gates

- Browser ARRIVAL card and explicit, session-scoped `Open saved draft` action.
- Reviewed export/import of source packs and drafts as user-owned files;
  versioned independent backup/restore and private-data handling.
- A separately tested, pinned installer/asset lock with offline fallback and
  Linux environment probes; no untrusted install hooks.
- Independent Linux keyboard/browser/restart/SQLite backup tests and PR #48
  reconciliation before main promotion. No automatic successor flight.

**Authority:** source ≠ interpretation; present ≠ ready; saved ≠ freshly
verified; local integrity ≠ remote provenance; re-entry ≠ authorization.
