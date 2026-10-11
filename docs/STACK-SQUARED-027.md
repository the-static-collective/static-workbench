# STACK² 027 — ELF Hatches the Portable Certificate

**Experimental, source-pinned, unmerged**. Builds from STACK² 026, original
GENESIS-ELF-001 in Static Workbench, and original LOADOUT
OPENMANUS-BIND-001. This is not a new generic agent or new ELF identity
system.

## Why this layer matters

ELF is a mortal bounded occurrence. The seed, verified output, and selected
lineage can survive; the runtime identity, model, credentials and authority
do not. Here a publicly verifiable STACK² 026 signed certificate becomes
*data-only hatch material*, not an executable capability grant.

```text
operator-signed STACK² 026 public certificate
    ↓ independently verify signature against OUT-OF-BAND trust fingerprint
GENESIS ELF 001 / FIRST HATCH
    ↓ independent ELF byte + receipt verification
first artifact + explicit parent receipt hash
    ↓ new workspace, seed, new occurrence ID
GENESIS ELF 001 / SECOND HATCH
    ↓ independent original ELF verifier + 026 signature recheck
public-agent-workspace / public-026.json
    ↓ optional, separately authorized LOADOUT OBSERVE
OpenManusJsonStdioAdapter
    ↓ provider testimony + LOADOUT EffectReceipt
ELF HOLD / no adoption / no inherited authority
```

This exact lane reuses original `static_workbench.elf_genesis.hatch` and
`verify`. It does not change the original deterministic genesis seed
schema or rebrand its data-only copies as model inference.

Each occurrence gets a fresh ID and new workspace. The second seed declares
`parent_receipt_sha256`. Source bytes and the cert's signature are checked
before the first hatch, and the signed certificate is checked independently
after the second. An unrelated/edited ELF receipt breaks the successor
lineage. The original certificate bytes are not rewritten.

## Actual source ownership

- Static Workbench native `GENESIS-ELF-001`: `static_workbench/elf_genesis.py`
  and `tests/test_elf_genesis.py`, originating in Workbench PR #60.
- Source-pinned LOADOUT OpenManus adapter and effect membrane:
  `LOADOUT@dd5456d45946271e2d20d1dc6145b71576d2380b`, PR #18.
- Inspected OpenManus source body identity:
  `FoundationAgents/OpenManus@3309bf4e416fb1c74b008f3e86494439a31bad53`.
- Original GHoT, CANNON 023 and reLATTE R14 remain unchanged.
- STACK² 025 original native verifier and STACK² 026 explicit portable
  P-256 issuer/independent trust-anchor verifier are reused.

## 1. Operator-run ELF carrier (data-only)

Use a **redacted public** `public-026.json` created using STACK² 026's
explicit private-key issuer and separately chosen public trust fingerprint.
Do not put a private GHoT report, key, receiver journal, or password into
any ELF workspace. Use a new dedicated output directory outside the source
certificate's parent directory.

```bash
python3 -m static_workbench.elf_receipt_027 \
  --certificate /private/public-certificates/public-026.json \
  --trust-fingerprint sha256:<64-hex-out-of-band-anchor> \
  --output /tmp/elf-proof-027 \
  --approve-hatch yes
```

This produces:

```text
elf-proof-027/
  first-seed.json
  first-workspace/input.txt
  occurrences/<unique-first>/artifact.txt
  occurrences/<unique-first>/receipt.json
  second-seed.json
  second-workspace/input.txt
  occurrences/<unique-second>/artifact.txt
  occurrences/<unique-second>/receipt.json
  public-agent-workspace/public-026.json
  carrier-report.json
```

Each ELF receipt is marked
`producer=deterministic_fixture_not_openmanus`,
`semantic_authority=false`, `admitted=false`. A real OpenManus agent
did **not** do the two copy transformations. The resulting report records
both verified occurrence IDs and digest-linked parentage. Seedbank
admission remains a *separate future owner decision*.

## 2. Optional original LOADOUT OpenManus OBSERVE

Use the same command with:

```bash
  --loadout-root /exact-pinned-LOADOUT-checkout \
  --provider-script /source/static-workbench/tests/fixtures/fake_receipt_openmanus_026.py
```

The original LOADOUT compiler binds only
`worker.perform / OBSERVE / workspace:public-026.json`.
Its original OpenManusJsonStdioAdapter launches the declared test provider
over JSON-stdio, keeping provider testimony separate from the resulting
effect receipt. Before and after the observation, the native certificate
verifier rechecks the P-256 signature and declared external issuer trust.

**CI uses a deterministic fake agent provider**, explicitly **not**
a genuine configured OpenManus LLM. A nonstandard operator-supplied
provider-script is executable host code, and the workspace path fence
is not an OS-level security sandbox. Use a disposable, unprivileged
environment and trusted provider code only.

## 3. Genuine model-backed OpenManus — separate operator gate

Also added `static_workbench.elf_live_027`, which delegates to **original
LOADOUT** `run_live_specimen` and `verify_live_bundle`. It requires:

- exact pinned original LOADOUT checkout;
- exact **clean** `FoundationAgents/OpenManus` checkout at
  `3309bf4e416fb1c74b008f3e86494439a31bad53`;
- a trusted OpenManus-compatible Python runtime with intentionally
  installed dependencies and an explicitly configured
  `config/config.toml`;
- an empty disposable child workspace independent of repos,
  output receipt directory and signer material;
- a named model configuration class and **explicitly named**
  environment variables (no automatic secret inheritance);
- explicit `--approve-live-provider yes`, max 10 steps and at most
  90 seconds of runtime, with no unattended retry.

Example (replace values with a real, secured, disposable installation):

```bash
python3 -m static_workbench.elf_live_027 \
  --loadout-root /source/pinned-LOADOUT \
  --provider-checkout /source/pinned-OpenManus \
  --provider-python /trusted/openmanus-venv/bin/python \
  --workspace /tmp/empty-disposable-elf-child \
  --output /tmp/new-openmanus-elf-receipts \
  --model-config-class configured-operator-model \
  --forward-env EXPLICIT_MODEL_TOKEN_NAME \
  --max-steps 6 \
  --timeout-seconds 60 \
  --approve-live-provider yes
```

The actual LOADOUT live specimen asks a model to use its scoped read/write
tools to mutate *one frozen test fixture*. LOADOUT independently verifies
the expected output, changed-path set, provider and effect receipts, and
no semantic authority. This model-backed occurrence must be executed by
an operator with the real configured runtime; **no credentials are
available or used in CI, and no claim of live OpenManus conformance is
made here.**

Passing the genuine model test would prove only that specific bounded
fixture. It is not a general sandbox security proof, an ELF successor
identity, permission to use remote tools, or authorization to promote
a child. To combine its success with a portable signed certificate
requires another explicit owner review/issue gate, not an automatic
adapter callback.

## Native proof

The dedicated STACK² 027 GitHub Actions workflow checks out exact
original GHoT, CANNON, reLATTE, and LOADOUT sources, and uses the actual
Workbench ELF generator:
1. native GHoT deterministic work and Instrument Rack signatures;
2. original CANNON 023 verifier and original reLATTE R14 receiver HOLD;
3. Workbench 025 *separate* original-native cold verification;
4. owner-flagged **test-key** 026 P-256 portable certificate and
   independently supplied test trust fingerprint;
5. two distinct original ELF genesis hatches and original ELF verify;
6. source-pinned original LOADOUT adapter observing only the public
   certificate in a one-file workspace;
7. independent revalidation of signed certificate, no admission,
   fresh ELF IDs, no transferred authority.

Only the public ephemeral test-key signed certificate is exported from CI.
No private donor evidence, issuer key, workspace or provider secrets
become published artifacts.

## Non-collapses

```text
ELF SEED != RUNNING ELF
ONE ELF OCCURRENCE != NEXT OCCURRENCE
PARENT RECEIPT != INHERITED AUTHORITY
SIGNED CERTIFICATE != AGENT CREDENTIAL
OPENMANUS OBSERVE != ORIGINAL ELF DATA TRANSFORM
OPENMANUS COMPLETED != INDEPENDENT SIGNATURE VERIFIED
LOADOUT EFFECT RECEIPT != ELF ADMISSION
HATCH != SEEDBANK ADMIT
CONFIGURED LIVE MODEL != OS SANDBOX
SOURCE PIN != TRUSTED HUMAN IDENTITY
```

Original Workbench ELF receipt formats and LOADOUT effects remain under
their respective owners. This branch does not land, merge, deploy, publish,
run a live LLM, or schedule an agent.
