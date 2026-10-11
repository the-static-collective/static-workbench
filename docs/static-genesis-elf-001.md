# STATIC-GENESIS-ELF-001 — Two bounded occurrences

Status: **experimental deterministic offline specimen; not an OS image or an OpenManus run.**

This is the smallest executable seed-to-successor proof for the STATIC OS moonshot. It tests the *carrier* independently of the future agent provider. It deliberately does not import LOADOUT or grant authority; a future integration must use the project-owned LOADOUT gate and the pinned OpenManus provider from [LOADOUT #18](https://github.com/the-static-collective/LOADOUT/pull/18).

## Try it on Zorin or in a virtual environment

From a checkout of this branch with Python 3.11+:

```bash
python3 -m static_workbench.elf_genesis demo
python3 -m pytest -q tests/test_elf_genesis.py
```

The `demo` creates a temporary first workspace with `input.txt`, hatches an occurrence using a data-only uppercase operation, independently verifies the artifact and receipt, then creates a **new workspace** from the first artifact and hatches a second occurrence with an explicit parent-receipt digest. It verifies the second output and checks the two occurrence identifiers differ. Temporary workspaces are deleted when the command returns; the demo does not persist a seedbank.

Manual mode:

```bash
python3 -m static_workbench.elf_genesis hatch --seed /absolute/seed.json --workspace /absolute/working-dir --output /absolute/receipt-store
python3 -m static_workbench.elf_genesis verify --seed /absolute/seed.json --workspace /absolute/working-dir --output /absolute/receipt-store/<occurrence-id>
```

The input is always `workspace/input.txt`, output is always `occurrence/artifact.txt`, and the separate `receipt.json` declares `produced_unverified`, `admitted=false`, `semantic_authority=false`, and `producer=deterministic_fixture_not_openmanus`. A child seed must declare `parent_receipt_sha256`; verification of parent linkage requires the named parent receipt to be supplied separately. A digest and matching fields do not prove that the parent receipt was truthful or admitted.

## Boundaries

* No model, OpenManus process, command execution, file-system sandbox, network access, OS image, Git mutation, or authority transfer is implemented by this specimen.
* The scripted deterministic transform is a stand-in for a future bounded provider effect. Verification recomputes its expected bytes independently; it is **not** a general-purpose validator for AI-produced creative material.
* Parent artifact copying in the demo is an explicit operator action, not a background transfer.
* Source file and seed are content-digested; source workspace is never modified by the scripted hatch.
* A successful byte check does not constitute a LOADOUT approval, a TranchNode Workmark, a Vault admission, or a production-ready security boundary.
* Do not run this proof on untrusted input or interpret the path checks as OS-level confinement.

## Next separate gates

1. **Provider gate:** Run the existing `OPENMANUS-LIVE-001` exact-pinned specimen through LOADOUT and STATIC-NODE in a disposable child; preserve independent provider/effect/delta receipts. The documented live conformance gate has not been established by the present demo.
2. **ELF binding gate:** Replace only the deterministic transform in this proof with a version-pinned, LOADOUT-authorized provider invocation. Keep hatch identity, explicit bounded workspace, input/output digests, and no automatic admission. Add hostile tests for stale input, wrong target, wrong effect, interrupted worker, and unresolved result.
3. **OS gate:** Build and boot a reproducible STATIC OS image in a VM; run both occurrences inside the guest, reboot between them, prove persistence/restore and independent access to Zorin/host data.
4. **Seedbank gate:** Add a separately authorized receipt/admission mechanism for selecting material worth preserving and transporting. Never copy credentials or execution authority into the Ark.

Core law: **a seed can carry viability; a new occurrence must obtain its own authority.**
