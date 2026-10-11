"""STACK² 029: original verified LIVE OpenManus output becomes mortal ELF material.

The real model and the original ELF transformations are DISTINCT producers.
Never inherit the model's process, tools, credentials, permissions, identity,
or admission power. This bridge is UNSIGNED and specimen-scoped.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .elf_genesis import (
    _write_seed, digest, hatch, verify, MAX_BYTES, RECEIPT_SCHEMA,
)
from .elf_live_027 import verify_original_live_loadout_files
from .openmanus_026 import pinned_loadout, LOADOUT_SHA, UPSTREAM_OPENMANUS

SCHEMA = "workbench.stack2-029-live-elf-lineage/v0"
GATE_SCHEMA = "workbench.stack2-elf-live-provider-gate/v0"
BUNDLE_NAME = "openmanus-live-001.json"
GATE_NAME = "elf-live-gate-summary.json"
MATERIAL = "specimen/output.txt"
REPORT_NAME = "elf-live-lineage-report.json"


class LineageHold(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise LineageHold(reason)


def outside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return False
    except ValueError:
        return True


def exact_file(path: Path, size: int) -> bytes:
    require(path.is_file() and not path.is_symlink(), "MISSING_OR_SYMLINK_SOURCE")
    require(path.stat().st_size <= size, "SOURCE_TOO_LARGE")
    data = path.read_bytes()
    require(len(data) <= size, "SOURCE_CHANGED_OR_TOO_LARGE")
    return data


def live_source(
    *, loadout_root: Path, live_bundle: Path, workspace: Path,
    live_gate_summary: Path,
) -> tuple[bytes, dict[str, str]]:
    """Reverify original LOADOUT real-run proof on disk, not just a green summary."""
    require(not any(p.is_symlink() for p in (
        loadout_root, live_bundle, workspace, live_gate_summary
    )), "SYMLINKED_LIVE_SOURCE")
    require(workspace.is_dir() and live_bundle.name == BUNDLE_NAME and
            live_gate_summary.name == GATE_NAME,
            "LIVE_EVIDENCE_PATHS_MISMATCH")
    original_bundle = exact_file(live_bundle, 256 * 1024)
    original_gate = exact_file(live_gate_summary, 16384)
    require(outside(live_bundle, workspace) and
            outside(live_gate_summary, workspace), "SOURCE_EVIDENCE_IN_MODEL_WORKSPACE")

    root = pinned_loadout(loadout_root)
    verify_original_live_loadout_files(root)
    sys.path.insert(0, str(root / "src"))
    from loadout.dev.openmanus_live import (
        verify_live_bundle, PINNED_OPENMANUS_SHA,
        SPECIMEN_OUTPUT_PATH, SPECIMEN_OUTPUT_BYTES,
    )
    require(PINNED_OPENMANUS_SHA == UPSTREAM_OPENMANUS and
            SPECIMEN_OUTPUT_PATH == MATERIAL,
            "LIVE_DONOR_CONTRACT_CHANGED")
    passed, reasons = verify_live_bundle(live_bundle, workspace)
    require(passed and not reasons,
            "ORIGINAL_LOADOUT_LIVE_VERIFICATION_HOLD:" + ",".join(reasons))
    try:
        gate = json.loads(original_gate)
        bundle = json.loads(original_bundle)
    except (ValueError, UnicodeError) as exc:
        raise LineageHold("INVALID_ORIGINAL_LIVE_EVIDENCE_JSON") from exc
    require(isinstance(gate, dict) and
            gate.get("schema") == GATE_SCHEMA and
            gate.get("live_provider_conformance") == "SPECIMEN_SCOPED_PASS" and
            gate.get("loadout_original_live_verifier") == "PASS" and
            gate.get("effect") == "LOCAL_MUTATE" and
            gate.get("provider_checkout_pin") == UPSTREAM_OPENMANUS and
            gate.get("loadout_source_commit") == LOADOUT_SHA and
            gate.get("seedbank_admitted") is False and
            gate.get("promotion_authorized") is False and
            gate.get("semantic_authority") is False and
            gate.get("elf_successor_identity_inherited") is False and
            gate.get("os_sandbox_verified") is False and
            gate.get("external_model_config_class") == "local-ollama" and
            gate.get("forwarded_env_names") == [],
            "LIVE_GATE_SUMMARY_REFUSED")
    require(isinstance(bundle, dict) and
            bundle.get("provider", {}).get("checkout_sha") == UPSTREAM_OPENMANUS and
            bundle.get("provider", {}).get("model_config_class") == "local-ollama" and
            bundle.get("provider_receipt", {}).get("disposition") == "COMPLETED" and
            bundle.get("effect_receipt", {}).get("semantic_authority") is False,
            "ORIGINAL_PROVIDER_EFFECT_REFUSED")

    material = exact_file(workspace / MATERIAL, MAX_BYTES)
    require(material == SPECIMEN_OUTPUT_BYTES, "LIVE_OUTPUT_BYTES_CHANGED")
    return material, {
        "source_bundle_sha256": digest(original_bundle),
        "source_gate_summary_sha256": digest(original_gate),
        "model_output_sha256": digest(material),
    }


def recheck_lineage(
    *, output: Path, source_bytes: bytes, fingerprints: dict[str, str],
) -> dict[str, Any]:
    report_file = output / REPORT_NAME
    report_bytes = exact_file(report_file, 16384)
    try:
        report = json.loads(report_bytes)
    except (UnicodeError, ValueError) as exc:
        raise LineageHold("BAD_BRIDGE_REPORT") from exc
    require(isinstance(report, dict) and
            report.get("schema") == SCHEMA, "BAD_BRIDGE_REPORT_SCHEMA")
    for key, expected in fingerprints.items():
        require(report.get(key) == expected, "BRIDGE_SOURCE_DIGEST_MISMATCH:" + key)
    require(report.get("openmanus_source_pin") == UPSTREAM_OPENMANUS and
            report.get("loadout_source_pin") == LOADOUT_SHA,
            "BRIDGE_SOURCE_PIN_MISMATCH")
    require(report.get("model_output_sha256") == digest(source_bytes),
            "BRIDGE_MODEL_OUTPUT_MISMATCH")
    one_id = report.get("first_elf_id")
    two_id = report.get("successor_elf_id")
    require(isinstance(one_id, str) and isinstance(two_id, str) and
            len(one_id) == len(two_id) == 32 and one_id != two_id and
            all(c in "0123456789abcdef" for c in one_id + two_id),
            "ELF_IDENTITY_COLLAPSE")
    one = output / "occurrences" / one_id
    two = output / "occurrences" / two_id
    r1 = one / "receipt.json"
    r2 = two / "receipt.json"
    require(digest(exact_file(r1, 8192)) == report.get("first_elf_receipt_sha256") and
            digest(exact_file(r2, 8192)) == report.get("successor_elf_receipt_sha256"),
            "ELF_RECEIPT_DIGEST_MISMATCH")
    ok1, why1 = verify(output / "first-seed.json",
                       output / "first-workspace", one)
    ok2, why2 = verify(output / "successor-seed.json",
                       output / "successor-workspace", two, r1)
    require(ok1 and ok2 and not why1 and not why2, "ORIGINAL_ELF_LINEAGE_HOLD")
    receipt1 = json.loads(r1.read_bytes())
    receipt2 = json.loads(r2.read_bytes())
    require(receipt1.get("schema") == RECEIPT_SCHEMA and
            receipt2.get("schema") == RECEIPT_SCHEMA and
            receipt2.get("parent_receipt_sha256") == digest(r1.read_bytes()) and
            receipt1.get("parent_receipt_sha256") is None and
            all(r.get("admitted") is False and
                r.get("semantic_authority") is False and
                r.get("producer") == "deterministic_fixture_not_openmanus"
                for r in (receipt1, receipt2)),
            "ELF_RECEIPT_AUTHORITY_OR_LINEAGE_MISMATCH")
    for path in (
        output / "first-workspace/input.txt",
        one / "artifact.txt",
        output / "successor-workspace/input.txt",
        two / "artifact.txt",
    ):
        require(exact_file(path, MAX_BYTES) == source_bytes,
                "ELF_MATERIAL_DIVERGED")
    require(report.get("live_model_occurrence") == "SPECIMEN_SCOPED_PASS" and
            report.get("elf_producer") == "deterministic_fixture_not_openmanus" and
            report.get("seedbank_admitted") is False and
            report.get("authority_inherited") is False and
            report.get("os_sandbox_verified") is False and
            report.get("new_cryptographic_signature") is False,
            "BRIDGE_AUTHORITY_OVERCLAIM")
    return report


def hatch_verified_live_output(
    *, loadout_root: Path, live_bundle: Path, workspace: Path,
    live_gate_summary: Path, output: Path,
) -> dict[str, Any]:
    """Operator-approved data-only handoff; never acts as an ELF agent."""
    require(not output.exists() and not output.is_symlink(),
            "BRIDGE_OUTPUT_ALREADY_EXISTS")
    require(all(outside(output, p) and outside(p, output) for p in (
        workspace, loadout_root, live_bundle.parent, live_gate_summary.parent
    )), "BRIDGE_SOURCE_DESTINATION_OVERLAP")
    source, proof = live_source(
        loadout_root=loadout_root, live_bundle=live_bundle,
        workspace=workspace, live_gate_summary=live_gate_summary,
    )
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    occurrences = output / "occurrences"
    one_workspace = output / "first-workspace"
    one_workspace.mkdir(mode=0o700)
    (one_workspace / "input.txt").write_bytes(source)
    seed1 = output / "first-seed.json"
    _write_seed(seed1, source, "copy", None)
    one = hatch(seed1, one_workspace, occurrences)
    require(verify(seed1, one_workspace, one) == (True, ()),
            "FIRST_ORIGINAL_ELF_VERIFICATION_HOLD")
    parent_receipt = one / "receipt.json"
    two_workspace = output / "successor-workspace"
    two_workspace.mkdir(mode=0o700)
    (two_workspace / "input.txt").write_bytes(exact_file(
        one / "artifact.txt", MAX_BYTES))
    seed2 = output / "successor-seed.json"
    _write_seed(seed2, source, "copy", digest(parent_receipt.read_bytes()))
    two = hatch(seed2, two_workspace, occurrences)
    require(verify(seed2, two_workspace, two, parent_receipt) == (True, ()) and
            one.name != two.name, "SUCCESSOR_ORIGINAL_ELF_VERIFICATION_HOLD")

    report = {
        "schema": SCHEMA,
        **proof,
        "loadout_source_pin": LOADOUT_SHA,
        "openmanus_source_pin": UPSTREAM_OPENMANUS,
        "live_model_occurrence": "SPECIMEN_SCOPED_PASS",
        "live_source_verification": "ORIGINAL_LOADOUT_RECHECK_PASS",
        "first_elf_id": one.name,
        "successor_elf_id": two.name,
        "first_elf_receipt_sha256": digest(parent_receipt.read_bytes()),
        "successor_elf_receipt_sha256": digest((two / "receipt.json").read_bytes()),
        "elf_producer": "deterministic_fixture_not_openmanus",
        "elf_transform": "copy",
        "first_elf_verified": True,
        "successor_elf_verified": True,
        "seedbank_admitted": False,
        "authority_inherited": False,
        "os_sandbox_verified": False,
        "new_cryptographic_signature": False,
        "bundle_self_authenticating": False,
        "upstream_model_weights_provenance_attested": False,
    }
    (output / REPORT_NAME).write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    require(recheck_lineage(output=output, source_bytes=source, fingerprints=proof)
            == report, "COLD_LINEAGE_VERIFICATION_HOLD")
    # A second recheck of the original model bundle is mandatory *after*
    # all ELF work; no model workspace files are mutated in the hatch.
    again, repro = live_source(
        loadout_root=loadout_root, live_bundle=live_bundle,
        workspace=workspace, live_gate_summary=live_gate_summary,
    )
    require(again == source and repro == proof, "ORIGINAL_MODEL_EVIDENCE_CHANGED")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="STACK² 029 live evidence to ELF lineage")
    parser.add_argument("--loadout-root", required=True, type=Path)
    parser.add_argument("--live-bundle", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--live-gate-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--approve-hatch", required=True)
    args = parser.parse_args()
    try:
        require(args.approve_hatch == "yes", "EXPLICIT_ELF_HATCH_APPROVAL_REQUIRED")
        result = hatch_verified_live_output(
            loadout_root=args.loadout_root, live_bundle=args.live_bundle,
            workspace=args.workspace, live_gate_summary=args.live_gate_summary,
            output=args.output,
        )
        print(json.dumps(result, sort_keys=True))
    except (LineageHold, OSError, ValueError) as error:
        parser.exit(1, "STACK2_029_HOLD: " + str(error)[:220] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
