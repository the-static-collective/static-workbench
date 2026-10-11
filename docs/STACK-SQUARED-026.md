# STACK² 026 — OpenManus Carries, the Verifier Decides

**Status:** Experimental, stacked on Workbench STACK² 025. Reuses the
**existing actual LOADOUT OPENMANUS-BIND-001 implementation**, rather than
inventing a second agent policy. Neither LOADOUT PR #18 nor Workbench
STACK² 025 is merged by this branch.

## Why OpenManus belongs here

The first portable verification certificate should survive crossing into a
different world without inheriting its authority. OpenManus is useful as a
bounded **carrier/observer** of the PUBLIC certificate, while an independent
verifier checks cryptographic validity against a separately chosen issuer
key fingerprint.

```text
GHOT native processor
  → original CANNON 023 source/signature verification
  → original reLATTE R14 sovereign RECEIVED + R3_HOLD
  → Workbench 025 operator-run host verification (unsigned local summary)
  → operator-approved P-256 portable certificate issuance (026)
  → independent verifier, with out-of-band trust fingerprint
  → LOADOUT effect compilation: OBSERVE only
  → original source-pinned OpenManusJsonStdioAdapter
  → provider testimony + LOADOUT EffectReceipt
  → non-authoritative observation summary
```

The stage with the certificate signer is **not OpenManus**. Only the operator
can issue using their own separately managed P-256 key. The agent does not
possess the key, grant owner power, select the trust root or ADMIT the
certificate. Signing a local verification summary represents an issuer's
bounded claim, not proof of human real-world identity or permanent truth.

## Precise pins

- LOADOUT `feat/openmanus-nervous-system-v0`: exact adapter source commit
  `dd5456d45946271e2d20d1dc6145b71576d2380b`.
- Underlying OpenManus contract body:
  `FoundationAgents/OpenManus@3309bf4e416fb1c74b008f3e86494439a31bad53`.
- GHoT AI RECOMPOSITION 001:
  `6194d91ba83bad63606f6f6741723007227518f2`.
- CANNON STACK² 023:
  `2fab6e142f21f6213bbcf4e290030acfce756061`.
- reLATTE R14:
  `dcc8cdca84c440aa4294134f020fb7095bf87f24`.

Original LOADOUT owns effect compilation, OpenManus adapter invocation,
provider receipt, and effect receipt. Workbench only defines a narrow
application protocol that submits one `OBSERVE` effect to the original
LOADOUT implementation and independently checks the public certificate
before **and after** provider observation. `LOCAL_MUTATE`, browser, shell,
network, native Python, Git write, publication and agent-gated signing are
not exposed as provider capabilities by this integration.

**The LOADOUT adapter is proven with a deterministic JSON-stdio worker in
CI; live OpenManus model conformance is NOT established.** Pinning the
adapter's body-time ID does not prove a pinned upstream model instance ran.
Path scoping is not an OS/container sandbox.

## Issue portable certificate — operator action only

First explicitly run the Workbench 025 local verifier against genuine
private signed evidence; it produces
`<state-dir>/receipt-porter/latest.json`.

From this Workbench branch, after provisioning your own issuer EC P-256
private/public keypair securely:

```sh
node scripts/stack2-026-portable.mjs fingerprint \
  --public-key /private/path/issuer-public.pem

node scripts/stack2-026-portable.mjs issue \
  --state /private/workbench-state/receipt-porter/latest.json \
  --private-key /private/path/issuer-private.pem \
  --expires-at 2026-10-15T19:00:00Z \
  --output /private/new-public-026.json \
  --approve-issue yes
```

The example expiration is illustrative; choose a future expiry no more
than 30 days from issuance. **Never commit, upload, or hand the private key
to OpenManus or a browser.** The issuer key fingerprint must be communicated
to the independent verifier using a separately authenticated channel. It
must NOT be trusted simply because the certificate contains its own public key.

The public certificate consists only of the verified source pins, bounded
receipt identifiers/digests, exact native check names, expiry, and explicit
negative authority claims, signed under domain
`STATIC-STACK2-026-PORTABLE-V0|` using ECDSA P-256 SHA-256.

## Verify without the Workbench host

```sh
node scripts/stack2-026-portable.mjs verify \
  --bundle /private/new-public-026.json \
  --trust-fingerprint sha256:<64-hex-trust-anchor>
```

Here the independent verifier does not need GHoT, CANNON, reLATTE,
the private report, receiver signing key or Workbench state. It checks
the portable signature, exact schema, pins, expiry, R3_HOLD semantics,
and the trusted issuer public key **fingerprint supplied independently**.
This proves that a particular issuer key signed a bounded claim about
the original native check. It does not replace replay of the original
reLATTE journal or independently authenticate a human owner.

## Optional bounded agent observation

Use only public certificate bytes in a dedicated workspace, named
`public-026.json`; no other files may be present. The operator explicitly
permits one OBSERVE effect. In the deterministic fixture:

```sh
python -m static_workbench.openmanus_026 \
  --loadout-root /source/pinned-LOADOUT-repo \
  --workspace /disposable/agent-public-only \
  --verification-script ./scripts/stack2-026-portable.mjs \
  --trust-fingerprint sha256:<independent-trust-anchor> \
  --provider-script ./tests/fixtures/fake_receipt_openmanus_026.py \
  --approve-observe yes
```

The integration imports **original pinned LOADOUT source**, compiles a
`worker.perform / OBSERVE / workspace:public-026.json` world, invokes its
real `OpenManusJsonStdioAdapter` via the unchanged LOADOUT membrane,
and preserves separate provider and effect outcomes. It independently checks
the signed certificate before and after the worker and compares the
workspace file inventory to refuse mutations. It does **not** rely on
OpenManus `COMPLETED` testimony to decide signature validity.

This CLI deliberately accepts a provider script only as an explicit,
trusted local operator argument. It is **not** a generic safe execution
sandbox for arbitrary code or live agent models, and it should be used
with an isolated, disposable unprivileged environment. An unknown provider
could access more host resources than the file/path fence alone can prevent.

## Actual CI proof and limitations

The source-pinned test workflow executes the original four-repository
GHoT → CANNON → reLATTE → Workbench 025 chain; issues a disposable
test-key certificate only after original verification; independently
verifies with an out-of-band calculated fingerprint; and invokes LOADOUT
OPENMANUS-BIND-001 with the bounded deterministic fixture. The fixture
uses a real provider subprocess, **not the actual LLM-backed OpenManus
model**. Only the public test-key signed certificate is uploaded. The
CI disposable signing key and private donor evidence remain in the runner.

Cryptographic checks cannot guarantee a specific human owns the test key.
Receipt verification is separate from source identity, quality assessment,
ownership, or present receiver state.

## Non-collapse laws

```text
LOADOUT CONSTITUTION ≠ OPENMANUS REASONING
OPENMANUS OBSERVATION ≠ CRYPTOGRAPHIC VERIFICATION
OPENMANUS PROVIDER RECEIPT ≠ LOADOUT EFFECT RECEIPT
LOADOUT EFFECT RECEIPT ≠ OWNER APPROVAL
SIGNED CERTIFICATE ≠ INDEPENDENTLY TRUSTED ISSUER
SOURCE-PINNED CODE ≠ ACTIVE MODEL CONFORMANCE
RECEIVED ≠ R3_HOLD ≠ ADMIT
CARRIER ≠ COURT
```

**Possible next seam:** a read-only public certificate import inside the
Workbench Receipt Floor, with an *independently entered trust anchor* and
local P-256 verification. That can happen without putting agent execution
or issuer signing in the web surface.
