# PINCERSMASH-002 — Independent Week Receiver (Static Workbench)

The receiver jaw is a **separate Python implementation**. It does not load the webZ JavaScript verifier, Vault Node verifier, or reLATTE signing code. It understands two distinct carriers, with no automatic merge of their claims:

1. `static-field/week-note-parcel/v0` from `webZ/week/field/`, pinned to the witnessed source-page Git blob and fourteen exact Suno IDs; verifies the JSON.stringify-compatible payload hash but returns only **unsigned human assertions in HOLD**.
2. `static-field/week-source-evidence/v0` from Autodiscography Vault. A path-free source claim is **not proof at the receiver**. Only manually chosen audio bytes, independently re-hashed and checked against the docket SHA-256 and length, earn `verifiedLocalBytes=true` — and still remain in HOLD.

Run independently on a second computer:

```sh
python scripts/inspect_week_crossing.py --notes /path/to/week-song-unsigned.json
python scripts/inspect_week_crossing.py --docket /path/to/source-docket.json
python scripts/inspect_week_crossing.py --notes /path/to/week-song-unsigned.json --docket /path/to/source-docket.json --asset /path/to/operator-carried-audio.wav
pytest -q tests/test_week_crossing.py
```

Nothing is transmitted, imported into House, persisted by this tool, made public, or selected for execution. The CLI is a read-only inspection. It parses at most 32,000 bytes per JSON carrier, rejects duplicate keys, extra or reordered browser fields, unknown tracks, wrong source revision, mismatched song identity, false signed authority, and altered bytes. It emits a machine-readable observation report on stdout.

The fixture tests use **synthetic bytes**, not a claim that a real Suno WAV has been acquired. Full proof requires one real Vault source receipt, the same manually transported bytes, and a human-witnessed receiver run. A checksum can establish matching bytes, **not** provider origin, permission, identity of a sender, artistic intent, or third-party trust. Neither this command nor the docket is a reLATTE signed crossing.

This receiver lives adjacent to the existing Workbench field-station architecture; it does **not** silently register another UI door or alter existing House authority. Promotion to a signed reLATTE exchange would be a separate, reviewable experiment.
