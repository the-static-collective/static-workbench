# STACK² 028 — Genuine OpenManus local-model conformance attempt

**Status: experimental.** This branch is stacked on Workbench STACK² 027 and
uses the **original exact-pinned LOADOUT OPENMANUS-LIVE-001 implementation**.
Unlike the earlier deterministic fake-provider checks, this experiment
configures **real OpenManus + a real locally hosted Qwen2.5 model via Ollama**.
A green native verifier would constitute a **specimen-scoped live model
conformance pass**. A failure remains HOLD. Neither result conveys
publication/admission/merge authority or a general OS sandbox proof.

## Five separate materials

- Workbench genuine-live gate: `static_workbench.elf_live_027` (adapted
  solely to allow zero credential names for a strict local Ollama profile).
- LOADOUT original pinned `run_live_specimen` +
  `verify_live_bundle`: commit
  `dd5456d45946271e2d20d1dc6145b71576d2380b`.
- Upstream real `FoundationAgents/OpenManus` ToolCallAgent pinned
  `3309bf4e416fb1c74b008f3e86494439a31bad53`.
- Local inference server: Docker Ollama image pinned by **index digest**
  `sha256:e2f0af4a865c61b580cc17a7e2bda3c82083046b74c5a5402ce32a0d84454f9b`
  (Ollama 0.12.4, linux/amd64). Exact model requested
  `qwen2.5:3b`; model digest is printed during the ephemeral run.
- Child workspace: new, empty, benign temp directory. Original LOADOUT
  creates `specimen/input.txt`, allows only `loadout_read_text` and
  `loadout_write_text` and `Terminate`, and checks exact output bytes,
  original input bytes, sole permitted file change, separate provider and
  effect receipts, no semantic authority, pinned original sources,
  max-step bound and termination.

No user/API credentials are required: model inference is local. The profile
is exactly:

```toml
[llm]
api_type = "ollama"
model = "qwen2.5:3b"
base_url = "http://127.0.0.1:11434/v1"
api_key = "ollama"
max_tokens = 512
temperature = 0.0

[daytona]
daytona_api_key = "disabled-local-placeholder"
```

The unmodified 2025 OpenManus source eagerly constructs a Daytona settings
object even when no Daytona tools are exposed. The fixed `daytona_api_key`
value above is a deliberately invalid, nonsecret compatibility placeholder.
Workbench refuses any substituted value; it grants no Daytona network or
execution permission.

The profile is restricted to this schema and exact loopback endpoint.
`api_key` is a nonsecret Ollama placeholder. Other model credentials,
remote endpoints, extra config sections and forwarded environment variable
names are **refused** for the local profile; the original LOADOUT child
receives only `PYTHONPATH`.

## What a successful LIVE run actually establishes

1. The original clean pinned OpenManus source and original LOADOUT code
   really ran, rather than merely passing a fake JSON-stdio adapter test.
2. Ollama hosted local Qwen2.5:3b model inference, with actual generated
   tool calls in the original OpenManus reasoning loop.
3. The agent wrote one exact expected test artifact using only the LOADOUT
   declared narrow tool collection.
4. Original independent LOADOUT verification confirmed the exact file
   delta and receipts.
5. The Workbench 028 summary is scoped to this occurrence, remains
   `promotion_authorized=false`, `seedbank_admitted=false`, and
   `os_sandbox_verified=false`.

A small model could fail to use tools correctly. If so, do not relabel
a failure as a PASS or silently substitute a fake model/provider; preserve
the HOLD result and its technical reason. If the runner cannot install
dependencies, download the exact public model or launch the source-pinned
worker, those are infrastructure failures and **not** live conformance.

## Security and deployment boundary

The CI host runner is disposable. Docker is used for the Ollama model server;
the original OpenManus agent itself executes in the fresh CI runner's
restricted workspace, but **not** in an OS-level sandbox. This is a
bounded *observed* effect contract, not proof that a malicious model
couldn't affect the host. The agent has only the custom LOADOUT tools
exposed through its reasoning-loop ToolCollection, even though imported
OpenManus source includes more capabilities.

No private reLATTE bundle, GHoT model prompt, signing key, personal
projects, GitHub writing credentials, user model credentials, or production
material is made available to this live occurrence. Nothing is automatically
merged, seeded, or deployed. Only the bounded Workbench live-gate summary
may be uploaded as the public experiment receipt **after** independent
verification passes.

The pinned Ollama container digest is not a pin of model weights; the
downloaded model digest must be recorded by the workflow. The model's
training provenance and quality aren't established by this test.

## Native CI proof

`.github/workflows/stack2-028-live-local-openmanus.yml` has a fast
contract job followed by a one-time real-model trial for the experiment
branch. It checks out exact upstream source pins, installs upstream
dependencies into a fresh venv, starts the pinned Ollama model on
`127.0.0.1:11434`, downloads a small tool-calling model, writes only
the nonsecret local `config.toml` fixture, and invokes:

```sh
python -m static_workbench.elf_live_027 \
  --loadout-root /runner/loadout-source \
  --provider-checkout /runner/openmanus-source \
  --provider-python /runner/openmanus-venv/bin/python \
  --workspace /runner/fresh-child \
  --output /runner/new-live-evidence \
  --model-config-class local-ollama \
  --max-steps 8 \
  --timeout-seconds 90 \
  --approve-live-provider yes
```

The original independent LOADOUT verifier is used; no forged provider
summary can make the actual file mutation pass.

## Laws

```text
PINNED UPSTREAM SOURCE != LIVE MODEL EXECUTION
REAL MODEL EXECUTION != CORRECT EFFECT
MODEL CLAIMED COMPLETED != INDEPENDENTLY VERIFIED OUTPUT
INFERENCE PROVIDER != OWNER AUTHORITY
ELF INPUT != ELF ADMISSION
GREEN FIXTURE != GREEN LIVE MODEL
LOCAL MODEL != MODEL WEIGHTS TRUSTED
WORKSPACE DELTA CHECK != OS SANDBOX PROOF
```

This branch does not alter the original LOADOUT effects, OpenManus code,
or ELF GENESIS 001 APIs.
