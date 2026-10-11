"""STACK² 029: negative and cold checks of genuine live-output -> ELF material."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from static_workbench.elf_genesis import digest, verify
from static_workbench.elf_live_lineage_029 import (
    LineageHold, hatch_verified_live_output, live_source, recheck_lineage,
    REPORT_NAME, SCHEMA,
)


MODEL_RESULT = b"OPENMANUS-LIVE-001 OUTPUT\n"
PROOF = {
    "source_bundle_sha256": digest(b"genuine-source-bundle-evidence-test-shim"),
    "source_gate_summary_sha256": digest(b"genuine-gate-report-evidence-test-shim"),
    "model_output_sha256": digest(MODEL_RESULT),
}


def inputs(tmp_path: Path) -> dict:
    root = tmp_path / "loadout-original"
    root.mkdir()
    workspace = tmp_path / "model-child"
    (workspace / "specimen").mkdir(parents=True)
    (workspace / "specimen/input.txt").write_bytes(b"OPENMANUS-LIVE-001 INPUT\n")
    (workspace / "specimen/output.txt").write_bytes(MODEL_RESULT)
    evidence = tmp_path / "original-loadout-evidence"
    evidence.mkdir()
    bundle = evidence / "openmanus-live-001.json"
    gate = evidence / "elf-live-gate-summary.json"
    bundle.write_text('{"original":"unit shim — not real inference"}')
    gate.write_text('{"original":"unit shim — not real inference"}')
    return {
        "loadout_root": root, "live_bundle": bundle, "workspace": workspace,
        "live_gate_summary": gate, "output": tmp_path / "new-elf-chain",
    }


def fake_verified_source(**kwargs):
    # ONLY an offline ELF-carrier unit fixture. The full Actions integration
    # uses real live_source and ORIGINAL LOADOUT verifier, never this stub.
    return MODEL_RESULT, dict(PROOF)


def produce(tmp_path: Path):
    paths = inputs(tmp_path)
    with patch("static_workbench.elf_live_lineage_029.live_source",
               side_effect=fake_verified_source) as source:
        report = hatch_verified_live_output(**paths)
    assert source.call_count == 2
    return paths, report


def test_two_original_elf_occurrences_from_model_bytes_with_distinct_lineage(tmp_path):
    paths, report = produce(tmp_path)
    output = paths["output"]
    assert report["schema"] == SCHEMA
    assert report["model_output_sha256"] == digest(MODEL_RESULT)
    assert report["live_source_verification"] == "ORIGINAL_LOADOUT_RECHECK_PASS"
    assert report["live_model_occurrence"] == "SPECIMEN_SCOPED_PASS"
    assert report["elf_producer"] == "deterministic_fixture_not_openmanus"
    assert report["first_elf_id"] != report["successor_elf_id"]
    assert report["authority_inherited"] is False
    assert report["new_cryptographic_signature"] is False
    assert report["bundle_self_authenticating"] is False
    assert report["seedbank_admitted"] is False
    assert report["os_sandbox_verified"] is False
    assert recheck_lineage(output=output, source_bytes=MODEL_RESULT, fingerprints=PROOF) == report
    first = output / "occurrences" / report["first_elf_id"]
    second = output / "occurrences" / report["successor_elf_id"]
    assert verify(output / "first-seed.json", output / "first-workspace", first) == (True, ())
    assert verify(output / "successor-seed.json", output / "successor-workspace",
                  second, first / "receipt.json") == (True, ())
    assert (second / "artifact.txt").read_bytes() == MODEL_RESULT
    assert (paths["workspace"] / "specimen/output.txt").read_bytes() == MODEL_RESULT
    assert (paths["workspace"] / "specimen/input.txt").read_bytes() == b"OPENMANUS-LIVE-001 INPUT\n"
    assert {x.name for x in paths["workspace"].rglob("*") if x.is_file()} == {
        "input.txt", "output.txt"
    }


def test_original_verifier_refusal_causes_no_elf_or_side_effect(tmp_path):
    paths = inputs(tmp_path)
    with patch("static_workbench.elf_live_lineage_029.live_source",
               side_effect=LineageHold("ORIGINAL_LOADOUT_LIVE_VERIFICATION_HOLD:WRONG_OUTPUT")):
        with pytest.raises(LineageHold, match="ORIGINAL_LOADOUT_LIVE_VERIFICATION_HOLD"):
            hatch_verified_live_output(**paths)
    assert not paths["output"].exists()


def test_tampered_elf_receipts_and_bytes_are_refused_cold(tmp_path):
    paths, report = produce(tmp_path)
    output = paths["output"]
    first_receipt = output / "occurrences" / report["first_elf_id"] / "receipt.json"
    first_receipt.write_text('{"forged":"authority"}')
    with pytest.raises(LineageHold, match="ELF_RECEIPT_DIGEST_MISMATCH"):
        recheck_lineage(output=output, source_bytes=MODEL_RESULT, fingerprints=PROOF)


def test_tampered_successor_payload_is_refused_cold(tmp_path):
    paths, report = produce(tmp_path)
    second = paths["output"] / "occurrences" / report["successor_elf_id"]
    (second / "artifact.txt").write_bytes(b"FAKE AI ASSIGNED AUTHORITY")
    with pytest.raises(LineageHold, match="ORIGINAL_ELF_LINEAGE_HOLD"):
        recheck_lineage(output=paths["output"],source_bytes=MODEL_RESULT,
                        fingerprints=PROOF)


def test_forged_admission_and_edited_model_source_digest_refuse(tmp_path):
    paths, report = produce(tmp_path)
    output = paths["output"]
    path = output / REPORT_NAME
    value = json.loads(path.read_text())
    value["seedbank_admitted"] = True
    path.write_text(json.dumps(value))
    with pytest.raises(LineageHold, match="BRIDGE_AUTHORITY_OVERCLAIM"):
        recheck_lineage(output=output,source_bytes=MODEL_RESULT,fingerprints=PROOF)
    value["seedbank_admitted"] = False
    value["source_bundle_sha256"] = "0"*64
    path.write_text(json.dumps(value))
    with pytest.raises(LineageHold, match="BRIDGE_SOURCE_DIGEST_MISMATCH"):
        recheck_lineage(output=output,source_bytes=MODEL_RESULT,fingerprints=PROOF)


def test_replay_into_existing_or_overlapping_location_fails_before_hatch(tmp_path):
    paths, report = produce(tmp_path)
    with pytest.raises(LineageHold, match="BRIDGE_OUTPUT_ALREADY_EXISTS"):
        hatch_verified_live_output(**paths)
    paths["output"] = paths["workspace"] / "wrong-place"
    with pytest.raises(LineageHold, match="BRIDGE_SOURCE_DESTINATION_OVERLAP"):
        hatch_verified_live_output(**paths)
    assert not paths["output"].exists()


def test_source_evidence_symlink_refused_before_admission(tmp_path):
    paths = inputs(tmp_path)
    gate = paths["live_gate_summary"]
    link = tmp_path / "elf-live-gate-summary.json"
    link.symlink_to(gate)
    paths["live_gate_summary"] = link
    with pytest.raises(LineageHold, match="SYMLINKED_LIVE_SOURCE"):
        live_source(**{k:paths[k] for k in (
            "loadout_root","live_bundle","workspace","live_gate_summary"
        )})
    assert not paths["output"].exists()


def test_model_source_requires_actual_original_live_bundle_shape(tmp_path):
    paths = inputs(tmp_path)
    paths["live_bundle"] = tmp_path / "fake-summary.json"
    with pytest.raises(LineageHold,match="LIVE_EVIDENCE_PATHS_MISMATCH"):
        live_source(**{k:paths[k] for k in (
            "loadout_root","live_bundle","workspace","live_gate_summary"
        )})
