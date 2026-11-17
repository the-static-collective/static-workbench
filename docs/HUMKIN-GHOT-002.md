# HUMKIN-GHOT-002 — Workbench closes one *real* bounded action loop

**Status:** experiment; not merged, installed, or connected to Android gameplay.

The verified HUMKIN public catalog is already carried by GitHub into native reLATTE `RECEIVED → HOLD` in `HUMKIN-GH-RELATTE-001`. This experiment picks up only that authenticated *public evidence*. It does not infer authorization from a HOLD.

```text
actual HUMKIN discovery.json + tracks.json in GitHub
    → reLATTE catalog signed RECEIVE + HOLD
    → Workbench calls original reLATTE public verifier
    → explicit HASH_PUBLIC_CATALOG experiment approval
    → original GHoT reference body advertises local system.hash
    → GHoT executes exactly one bounded string hash; persists its native task + receipt
    → Workbench checks output against independent Python SHA-256
    → Workbench writes a compact public execution summary
    → reLATTE signs a *new* crossing bound to those exact summary bytes
    → separate reLATTE LocalReceiver signs RECEIVE + HOLD
    → independent GitHub runner verifies both chains
```

**What is real:** native GHoT `system.hash`, persisted local GHoT task and receipt, native reLATTE cryptographic sign/receive/HOLD, cold independent validation of original and returned public receipts, immutable Git source metadata and actual source bytes. The human-triggered approval is scoped to hashing *public catalog metadata* on an ephemeral GitHub runner. Other capabilities, private source, general file paths, remote shell, remote LAN execution, GitHub writes and gameplay rewards are not approved.

**What is not established:** GHoT's reference `ghot.receipt` v0 is **unsigned**; the separate reLATTE-signed return proves the claimed Workbench *record* was signed and received, not that GHoT itself cryptographically attested execution. CI runners are ephemeral, not an always-running radio server or permanent receipt custodian. A receiver signing a HOLD is not the HUMKIN app accepting a game event. No HUM, artifacts, player rewards, submissions, trades or WebZ publication are triggered.

## Implementation

- `static_workbench/humkin_ghot.py`: only recognizes the exact verified catalog and `system.hash` capability, requires `HASH_PUBLIC_CATALOG`, invokes original GHoT `reference_node` locally, records actual task/receipt, asks original reLATTE `opaque-roundtrip.ts` to sign the new return.
- `scripts/humkin_ghot_return.py`: narrow CLI, explicit `--approve-public-catalog-hash`.
- `tests/test_humkin_ghot.py`: checks no implicit execution, missing upstream native verifier, and upstream wrong-disposition refusal.
- The three-stage catalog workflow plus new Workbench/GHoT execution and independent signed-return verification are in experimental reLATTE PR #179.

The Workbench adapter has no embedded second signing implementation and no copied GHoT executor. Its only new responsibility is to verify, select one local allowlisted action, and carry truthful bounded evidence.

**Next earned boundary:** add a **separate HUMKIN-owned admission endpoint** able to evaluate this independently verified candidate and decide whether it creates a non-monetary station discovery. Until then, the radio UI must not claim the chain has been wired into actual player progression.
