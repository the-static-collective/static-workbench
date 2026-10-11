# STACK² 029 — Genuine model output becomes mortal ELF material

**Stacked experimental draft** on STACK² 028. Source code in
`static_workbench/elf_live_lineage_029.py`; independent native workflow in
`.github/workflows/stack2-029-live-elf-lineage.yml`.

The exact previously established 028 live model pass was
[Actions run 38173551886](https://github.com/the-static-collective/static-workbench/actions/runs/38173551886).
**029 does not reuse that CI status as a source receipt.**
029 creates a *fresh*, real local-model occurrence and retains its original
bundle and output until two ELF occurrences have independently verified it.

```text
Genuine pinned OpenManus ToolCallAgent
  + local Ollama Qwen2.5 3B (no credentials)
  + original LOADOUT frozen LOCAL_MUTATE tool perimeter
  -> specimen/output.txt
  -> ORIGINAL LOADOUT verify_live_bundle = (True, ())
  -> ORIGINAL Workbench live gate summary (NON-AUTHORITATIVE)
     ---- native live_source independently rechecks original source ----
  -> GENESIS-ELF-001 hatch #1: copy verified output bytes (no model run)
  -> GENESIS-ELF-001 verify #1 = (True, ())
  -> digest of first ELF receipt + copied output
  -> GENESIS-ELF-001 hatch #2: fresh new occurrence ID and workspace
  -> GENESIS-ELF-001 verify #2 checks actual parent receipt = (True, ())
  -> new separate cold verify over original LIVE evidence and both ELF receipts
  -> HOLD: no admission, no authority inheritance, no publishing
```

## Source proofs and exact claims

- Real OpenManus upstream pin:
  `FoundationAgents/OpenManus@3309bf4e416fb1c74b008f3e86494439a31bad53`.
- Original portable LOADOUT live verifier, original worker and bounded-ops pin:
  `the-static-collective/LOADOUT@dd5456d45946271e2d20d1dc6145b71576d2380b`.
- `static_workbench.elf_genesis.hatch` and `verify` originate in existing
  GENESIS-ELF-001; not reimplemented in 029.
- The model is original local Ollama `qwen2.5:3b`, image SHA
  `e2f0af4a865c61b580cc17a7e2bda3c82083046b74c5a5402ce32a0d84454f9b`,
  downloaded fresh. Model manifest digest is visible in exact 029 run logs.
- Original LOADOUT independently checks expected `specimen/input.txt`,
  `specimen/output.txt`, the complete changed path set, provider and effect
  receipts, pinned body time ID, and `semantic_authority=false`.
- 029 itself independently validates the original LIVE bundle using the
  source-pinned ORIGINAL verifier before reading output bytes. It compares
  those bytes to the original frozen `SPECIMEN_OUTPUT_BYTES`, checks the
  original Workbench gate summary and explicitly requires no admission.
- The bridge records SHA-256 of the complete original LIVE bundle, of the
  bounded original live gate summary, and of the actual output material.
  These SHA-256 references are **unsigned; they are not cryptographic
  evidence of the identity of a model or issuer**. The bounded *on-run*
  original model execution and original verification are evidenced by CI.
- 029 calls the original ELF generator twice, always `copy` (no inference),
  then invokes the original ELF verifier with the **actual** first-receipt
  bytes, rather than merely trusting reported success fields.
- A separate `recheck_lineage` proves: two distinct occurrence IDs,
  two original ELF receipts with exact digests, and byte-for-byte equal
  source → first ELF → second ELF. Both ELF receipts remain
  `producer=deterministic_fixture_not_openmanus`,
  `semantic_authority=false`, and `admitted=false`.
- Last, it rechecks the original LIVE model bundle and model workspace
  *again*, refusing any source mutation while the ELF hatches occurred.

## Local operator invocation

The user intentionally creates an operator-approved, disposable live
OpenManus occurrence via `static_workbench.elf_live_027`. Only after it
returned `SPECIMEN_SCOPED_PASS`, use the original root, untouched original
bundle and workspace, and bounded summary:

```bash
python3 -m static_workbench.elf_live_lineage_029 \
  --loadout-root /source/LOADOUT-exact-pin \
  --live-bundle /tmp/verified-live-evidence/openmanus-live-001.json \
  --live-gate-summary /tmp/verified-live-evidence/elf-live-gate-summary.json \
  --workspace /tmp/original-live-child \
  --output /tmp/new-elf-lineage-029 \
  --approve-hatch yes
```

The `--output` directory must not exist or overlap any donor workspace,
repository, or evidence directory. The caller cannot substitute a symlink to
the LIVE evidence. The seed and two receipts remain inspectable locally.

The resulting output contains `first-seed.json`, `first-workspace/`,
`successor-seed.json`, `successor-workspace/`, two actual
`occurrences/<ID>/` subdirectories with `artifact.txt` and `receipt.json`,
plus one **unsigned, bounded** `elf-live-lineage-report.json`.
CI uploads only that report and the original bounded 028 live gate summary,
**not** the original bundle, any tool transcript, private keys, or model
workspace files.

## Tests and refusals

`tests/test_elf_live_lineage_029.py` offline contract tests use a **clearly
marked fake source hook only to test ELF mechanics**. Those unit tests do
not claim a live model run. They cover source verifier refusal before hatch;
tampered first ELF receipt; tampered successor artifact; forged admission;
altered source bundle SHA; collisions or replays into existing/overlapping
output directories; source symlinks; malformed LIVE evidence paths.

The **real** 029 native CI job does not use those fake source hooks. It runs
the pinned model, the pinned original LOADOUT verifier, both original
Workbench ELF hatches and both original ELF verifiers, and the cold
bridge verifier over the actual ephemeral native material. An error in any
stage is a red/HOLD, not a fake-provider fallback.

## Authority and trust boundaries

```text
REAL LIVE MODEL WORK != AUTOMATIC ELF CHILD
LIVE OUTPUT BYTES != MODEL CAPABILITY
LOADOUT VERIFIED BUNDLE != SIGNED HUMAN ATTESTATION
FIRST ELF PARENT RECEIPT != MODEL IDENTITY
ELF SUCCESSOR != FIRST ELF PROCESS
VERIFIED COPY != MODEL-EXECUTED ELF HATCH
COLD RECHECK != OS SANDBOX PROOF
BUNDLE HASH != CRYPTOGRAPHIC MODEL PROVENANCE
RECEIVED != ADMITTED
```

GENESIS ELF copies are deterministically generated; the real OpenManus
agent produced the **original source bytes**, not the two copies.
Model credentials and process identity are not transported. This branch
does not merge, schedule, publish, issue a portable 026 signature, or
grant Seedbank/LOADOUT promotion. No original donor repo is modified.
