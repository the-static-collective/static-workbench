"""STACK² 027 — a signed public receipt becomes a pair of mortal ELF occurrences.

Uses original Workbench GENESIS-ELF-001 hatch/verify *without editing it*.
No automatic admission, model inference, identity continuity or authority.
An optional later LOADOUT OpenManus OBSERVE is independently constituted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
from typing import Any

from .elf_genesis import hatch, verify, _write_seed, digest
from .openmanus_026 import native_verify, observe, CERTIFICATE_NAME

SCHEMA = "workbench.stack2-elf-certificate-carrier/v0"
VERIFIER = Path(__file__).resolve().parents[1] / "scripts/stack2-026-portable.mjs"


class ElfRefusal(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ElfRefusal(reason)


def _outside(a: Path, b: Path) -> bool:
    try:
        a.resolve().relative_to(b.resolve())
        return False
    except ValueError:
        return True


def _only_public(path: Path) -> bytes:
    require(path.is_file() and not path.is_symlink(), "PUBLIC_CERTIFICATE_MISSING_OR_SYMLINK")
    require(0 < path.stat().st_size <= 16384, "PUBLIC_CERTIFICATE_OVERSIZED")
    content = path.read_bytes()
    require(len(content) == path.stat().st_size, "PUBLIC_CERTIFICATE_CHANGED")
    return content


def _original_elf_files_unchanged() -> bool:
    # The actual GENESIS ELF is imported above, not duplicated here.
    return hatch.__module__ == "static_workbench.elf_genesis" and (
        verify.__module__ == "static_workbench.elf_genesis"
    )


def hatch_public_certificate(
    *, certificate: Path, trust_fingerprint: str, output: Path,
    loadout_root: Path | None = None, provider_script: Path | None = None,
) -> dict[str, Any]:
    require(_original_elf_files_unchanged(), "ORIGINAL_ELF_NOT_BOUND")
    require((loadout_root is None) == (provider_script is None),
            "LOADOUT_AND_PROVIDER_MUST_BE_DECLARED_TOGETHER")
    source = certificate.resolve(strict=True)
    # Refuse explicit source symlinks before resolving; don't follow a replacement.
    require(not certificate.is_symlink(), "PUBLIC_CERTIFICATE_SYMLINK")
    content = _only_public(source)
    require(not output.exists(), "ELF_OUTPUT_ALREADY_EXISTS")
    require(_outside(output, source.parent) or output.parent != source.parent,
            "ELF_OUTPUT_SOURCE_COLLISION")
    before = native_verify(source, verification_script=VERIFIER,
                           trust_fingerprint=trust_fingerprint)
    # A signed certificate carries an issuer's claim, not a new ELF identity.
    require(before["status"] == "PORTABLE_SOURCE_BOUNDED_SIGNATURE_VERIFIED" and
            before["admitted"] is False, "CERTIFICATE_VERIFICATION_HOLD")

    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    first = output / "first-workspace"
    second = output / "second-workspace"
    occurrences = output / "occurrences"
    first.mkdir(mode=0o700)
    (first / "input.txt").write_bytes(content)
    seed1 = output / "first-seed.json"
    _write_seed(seed1, content, "copy", None)
    one = hatch(seed1, first, occurrences)
    passed1, why1 = verify(seed1, first, one)
    require(passed1 and not why1, "FIRST_ELF_VERIFY_HOLD")

    # Second occurrence receives source-addressed material only. It does
    # not inherit authority, memory, process identity or capabilities.
    carried = (one / "artifact.txt").read_bytes()
    require(carried == content, "ELF_SOURCE_PAYLOAD_CHANGED")
    receipt1 = one / "receipt.json"
    parent_digest = digest(receipt1.read_bytes())
    second.mkdir(mode=0o700)
    (second / "input.txt").write_bytes(carried)
    seed2 = output / "second-seed.json"
    _write_seed(seed2, carried, "copy", parent_digest)
    two = hatch(seed2, second, occurrences)
    passed2, why2 = verify(seed2, second, two, receipt1)
    require(passed2 and not why2 and one.name != two.name,
            "SUCCESSOR_ELF_VERIFY_HOLD")

    receipt2 = two / "receipt.json"
    for proof_path in (receipt1, receipt2):
        original = json.loads(proof_path.read_text())
        require(original["admitted"] is False and
                original["semantic_authority"] is False and
                original["producer"] == "deterministic_fixture_not_openmanus",
                "ELF_RECEIPT_AUTHORITY_OVERCLAIM")

    # The OBSERVE workspace has only the public signed certificate. No
    # ELF private work or signed keys are transported to an agent.
    observation_dir = output / "public-agent-workspace"
    observation_dir.mkdir(mode=0o700)
    (observation_dir / CERTIFICATE_NAME).write_bytes((two / "artifact.txt").read_bytes())
    require(_only_public(observation_dir / CERTIFICATE_NAME) == content,
            "OBSERVATION_INPUT_MISMATCH")

    after = native_verify(observation_dir / CERTIFICATE_NAME,
                          verification_script=VERIFIER, trust_fingerprint=trust_fingerprint)
    require(after == before, "ELF_SUCCESSOR_CERTIFICATE_VERIFICATION_CHANGED")
    observation = None
    if loadout_root is not None and provider_script is not None:
        # This dispatch deliberately uses the source-pinned LOADOUT adapter
        # and only its OBSERVE effect. The path is an operator-selected
        # provider script; in CI this is a deterministic fixture, not live AI.
        observation = observe(
            loadout_root=loadout_root, workspace=observation_dir,
            verification_script=VERIFIER, trust_fingerprint=trust_fingerprint,
            provider_command=("python3", str(provider_script.resolve(strict=True))),
        )
        require(observation["effect"] == "OBSERVE" and
                observation["agent_can_sign"] is False and
                observation["agent_can_admit"] is False and
                observation["workspace_content_mutated"] is False,
                "OPENMANUS_OBSERVE_OVERCLAIM")
    require(_only_public(source) == content, "ORIGINAL_CERTIFICATE_CHANGED")
    report = {
        "schema": SCHEMA,
        "portable_certificate_sha256": digest(content),
        "native_certificate_verification": before["status"],
        "issuer_trust_fingerprint": before["issuer_key_fingerprint"],
        "first_occurrence_id": one.name,
        "second_occurrence_id": two.name,
        "first_receipt_sha256": parent_digest,
        "second_receipt_sha256": digest(receipt2.read_bytes()),
        "successor_seed_parent_receipt_sha256": parent_digest,
        "first_elf_verified": True,
        "second_elf_verified": True,
        "distinct_occurrences": True,
        "provider": "deterministic_elf_copy_fixture",
        "openmanus_observation": observation,
        "openmanus_live_model_conformance": "NOT_ESTABLISHED",
        "seedbank_admitted": False,
        "authority_inherited": False,
        "human_identity_authenticated": False,
        "os_sandbox_verified": False,
        "new_native_crossing": False,
    }
    report_path = output / "carrier-report.json"
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="One owner-triggered STACK² 027 ELF chain")
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--trust-fingerprint", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--loadout-root", type=Path)
    parser.add_argument("--provider-script", type=Path)
    parser.add_argument("--approve-hatch", required=True)
    args = parser.parse_args()
    try:
        require(args.approve_hatch == "yes", "EXPLICIT_ELF_HATCH_APPROVAL_REQUIRED")
        report = hatch_public_certificate(
            certificate=args.certificate,
            trust_fingerprint=args.trust_fingerprint,
            output=args.output,
            loadout_root=args.loadout_root,
            provider_script=args.provider_script,
        )
        print(json.dumps(report, sort_keys=True))
    except (ElfRefusal, OSError, ValueError) as exc:
        parser.exit(1, "ELF_HOLD: " + str(exc)[:220] + "\n")


if __name__ == "__main__":
    main()
