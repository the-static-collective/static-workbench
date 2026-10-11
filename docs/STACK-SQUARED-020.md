# STACK² 020 — one native GHoT ACT from the Living Lego Floor

**Experimental, unmerged, not deployed.** This branch builds on STACK² 019 and retains Return Room ancestry. Unlike the 019 browser-only SHA comparison, 020 introduces a separately enabled *native* action under an explicit local consent gate.

## Exactly one permitted operation

After the operator configures native access, `/stack-floor` can invoke the **original GHoT 030 branch-worker** to hash **one exact original Git source file**:

- planZ source: `the-static-collective/planZ@e8111fdb64c5587b33aece0fed639ed3d03375ac`, `002/bin/sense-global.mjs`.
- Original GHoT: `the-static-collective/GHoT@b01758bee55d66d699160715ec377b45f7589707`, `ghot/branch_worker.py`.
- Destination capability: `branch-work/hash-exact-source`; no user-supplied command, source path, checkout, executable, or destination.
- GHoT itself performs original preflight, signs a short-lived one-operation P-256 BODY activation ticket, atomically claims it, revalidates the destination and SHA, reads the local Git blob, and signs the execution receipt.
- **No donor program executes. No remote effect. No reLATTE crossing or ADMIT.** The signed GHoT receipt is not a signed reLATTE RECEIVE.

The local Workbench web preview additionally issues a 90-second, one-use nonce bound to the exact GHoT proposal and pinned source hash. The ACT endpoint atomically consumes that nonce before invoking native GHoT. A replay or retry cannot trigger a second action.

## Separately owned setup

All three paths must be provisioned *by the actual local operator*. This feature is off by default:

```toml
stack_floor_native_enabled = true
stack_floor_ghot_checkout = "/absolute/original/GHoT"
stack_floor_planz_checkout = "/absolute/original/planZ"
stack_floor_ghot_home = "/absolute/owner-local/GHoT-HOME"
```

Checkouts must have the exact pinned HEAD and corresponding Git remote origin. The Workbench does not check them out or modify them.

GHoT itself requires an existing owner-reviewed allowlist at `<GHOT-HOME>/branch-worker/sources.json` with the exact source context, the correct local checkout root, and `reviewed_for_local_read: true`.

Example allowlist shape (replace the displayed SHA placeholder with the *actual SHA-256 of the Git source bytes*):

```json
{
  "schema": "ghot.branch-worker-sources/v0",
  "entries": [
    {
      "context": {
        "repository": "the-static-collective/planZ",
        "commit": "e8111fdb64c5587b33aece0fed639ed3d03375ac",
        "path": "002/bin/sense-global.mjs",
        "sha256": "<64 lowercase hexadecimal SHA-256>",
        "branchHint": "experiment/fatherhand-grant-chain-residue-001"
      },
      "checkout_root": "/absolute/original/planZ",
      "reviewed_for_local_read": true
    }
  ]
}
```

The Workbench **never writes the source allowlist** and refuses preview unless one exact owner-reviewed match exists. CI exercises this rule with a disposable *test-only* allowlist, not a real owner grant.

## The human UI gate

1. Assemble the exact four original cards in order: CANNON → planZ → GHoT → reLATTE.
2. Click **Preview pinned native operation**. Original GHoT preflight runs read-only; no hash action is executed.
3. Review the proposal, tick the **separate one-operation consent checkbox**, type **ACT**, and click **ACT once**.
4. GHoT spends its own separate signed ticket and emits its signed one-use execution receipt. Workbench checks the exact pinned file/result and makes the receipt downloadable.
5. No later source action or receiving-world admission is inferred or performed.

The ACT route enforces the local Workbench session token, a required exact same-origin Origin, a strict four-card recipe, a known exact operation, fixed payload fields, a valid unexpired preview nonce and explicit consent. The native subprocess uses fixed argv and no shell. **It runs as the existing Workbench OS user; there is no additional OS sandbox.** Do not expose Workbench over a public proxy or create a credential bridge.

Local BODY signature verifies key possession and artifact integrity; it does *not* prove real human identity or grant access to another system.

## CI and refusal matrix

`tests/test_stack_floor_020.py` checks against actual pinned original GHoT and planZ Git objects (rather than a simulated executor):

- Disabled feature refuses by default; no operation without original checkouts and local owner allowlist.
- Missing Workbench session, wrong Origin, wrong card order, unexpected user fields or missing ACT all refuse.
- Original GHoT native PREVIEW must be READY and non-effectful.
- Exactly one successful source hash yields a spent original native GHoT ticket and a BODY-signed execution receipt.
- Replaying the exact ACT does not create an additional ticket, operation attempt or receipt.
- Expired previews refuse before issuing a native ticket.
- Workbench does not create GHoT policy, source rights, original checkout or private signer keys.

No merge, release, physical device action, or public deployment is permitted by this experimental review branch.

**ARRANGEMENT ≠ AUTHORIZATION · PREVIEW ≠ ACT · ONE ACT ≠ NEXT ACT · BODY SIGNATURE ≠ OWNER IDENTITY · HASH RECEIPT ≠ reLATTE ADMISSION.**
