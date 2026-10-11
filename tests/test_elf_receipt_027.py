"""STACK² 027 ELF signed-public-certificate carrier + separate live gate."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from static_workbench.elf_genesis import digest, verify
from static_workbench.elf_receipt_027 import (
    ElfRefusal, hatch_public_certificate,
)
from static_workbench.elf_live_027 import live_elf_probe, LiveGateRefusal


def source(tmp_path: Path):
    original = tmp_path / "public-source"
    original.mkdir()
    cert = original / "public-026.json"
    cert.write_text('{"schema":"public-issuer-demo","source":"test-only"}\n')
    return cert


def verified():
    return {
        "status": "PORTABLE_SOURCE_BOUNDED_SIGNATURE_VERIFIED",
        "issuer_key_fingerprint": "sha256:"+"1"*64,
        "admitted": False,
        "agent_authority": False,
    }


def test_original_genesis_elf_carrier_hatches_two_distinct_verified_occurrences(tmp_path):
    cert = source(tmp_path)
    out = tmp_path / "elf-carrier"
    with patch("static_workbench.elf_receipt_027.native_verify", return_value=verified()) as native:
        report = hatch_public_certificate(
            certificate=cert, trust_fingerprint=verified()["issuer_key_fingerprint"],
            output=out,
        )
    assert native.call_count == 2
    assert report["first_elf_verified"] is True
    assert report["second_elf_verified"] is True
    assert report["distinct_occurrences"] is True
    assert report["seedbank_admitted"] is False
    assert report["authority_inherited"] is False
    assert report["openmanus_live_model_conformance"] == "NOT_ESTABLISHED"
    assert report["openmanus_observation"] is None
    assert report["first_occurrence_id"] != report["second_occurrence_id"]
    assert report["provider"] == "deterministic_elf_copy_fixture"
    assert report["portable_certificate_sha256"] == digest(cert.read_bytes())
    assert (out / "public-agent-workspace/public-026.json").read_bytes() == cert.read_bytes()
    assert cert.read_bytes() == b'{"schema":"public-issuer-demo","source":"test-only"}\n'
    one = out / "occurrences" / report["first_occurrence_id"]
    two = out / "occurrences" / report["second_occurrence_id"]
    ok, reasons = verify(out / "first-seed.json", out / "first-workspace", one)
    assert ok and reasons == ()
    ok2, reasons2 = verify(out / "second-seed.json", out / "second-workspace",
                           two, one / "receipt.json")
    assert ok2 and reasons2 == ()
    first_receipt = json.loads((one / "receipt.json").read_text())
    second_receipt = json.loads((two / "receipt.json").read_text())
    assert first_receipt["admitted"] is False
    assert second_receipt["admitted"] is False
    assert second_receipt["semantic_authority"] is False
    assert second_receipt["parent_receipt_sha256"] == digest((one / "receipt.json").read_bytes())
    # Tampering with the first verified receipt breaks child lineage.
    (one / "receipt.json").write_text('{"fake":"claimed parent"}')
    ok3, reasons3 = verify(out / "second-seed.json", out / "second-workspace",
                           two, one / "receipt.json")
    assert not ok3 and "PARENT_RECEIPT_MISMATCH" in reasons3


def test_signature_refusal_prevents_any_hatch(tmp_path):
    cert = source(tmp_path)
    out = tmp_path / "elf-carrier"
    with patch("static_workbench.elf_receipt_027.native_verify",
               side_effect=ValueError("ISSUER_NOT_TRUSTED")):
        with pytest.raises(ValueError, match="ISSUER_NOT_TRUSTED"):
            hatch_public_certificate(
                certificate=cert, trust_fingerprint="sha256:"+"1"*64,
                output=out,
            )
    assert not out.exists()


def test_refuse_symlinked_source_existing_output_or_collocated_output(tmp_path):
    cert = source(tmp_path)
    link = tmp_path / "symlink.json"
    link.symlink_to(cert)
    with pytest.raises(ElfRefusal, match="PUBLIC_CERTIFICATE_SYMLINK"):
        hatch_public_certificate(certificate=link, trust_fingerprint="sha256:"+"1"*64,
                                 output=tmp_path/"out")
    existing = tmp_path / "old-out"
    existing.mkdir()
    with pytest.raises(ElfRefusal, match="ALREADY_EXISTS"):
        hatch_public_certificate(certificate=cert, trust_fingerprint="sha256:"+"1"*64,
                                 output=existing)
    with pytest.raises(ElfRefusal, match="SOURCE_COLLISION"):
        hatch_public_certificate(certificate=cert, trust_fingerprint="sha256:"+"1"*64,
                                 output=cert.parent/"nested-outputs")


def test_elf_separate_agent_observation_cannot_promote_admit(tmp_path):
    cert = source(tmp_path)
    loadout_root = tmp_path / "LOADOUT"
    loadout_root.mkdir()
    provider = tmp_path / "provider.py"
    provider.write_text("print('test fixture')")
    with patch("static_workbench.elf_receipt_027.native_verify", return_value=verified()), patch(
            "static_workbench.elf_receipt_027.observe",
            return_value={
                "effect": "OBSERVE", "agent_can_sign": False,
                "agent_can_admit": False, "workspace_content_mutated": False,
                "openmanus_live_provider_conformance": "NOT_RUN_OR_ATTESTED"
            }) as observe:
        report = hatch_public_certificate(
            certificate=cert, trust_fingerprint="sha256:"+"1"*64,
            output=tmp_path/"hatch",
            loadout_root=loadout_root, provider_script=provider,
        )
    assert observe.call_count == 1
    assert report["openmanus_observation"]["effect"] == "OBSERVE"
    assert report["authority_inherited"] is False
    with patch("static_workbench.elf_receipt_027.native_verify", return_value=verified()), patch(
            "static_workbench.elf_receipt_027.observe",
            return_value={
                "effect": "OBSERVE", "agent_can_sign": False,
                "agent_can_admit": True, "workspace_content_mutated": False,
            }):
        with pytest.raises(ElfRefusal, match="OPENMANUS_OBSERVE_OVERCLAIM"):
            hatch_public_certificate(
                certificate=cert, trust_fingerprint="sha256:"+"1"*64,
                output=tmp_path/"hatch-refused",
                loadout_root=loadout_root, provider_script=provider,
            )
    assert not (tmp_path/"hatch-refused/carrier-report.json").exists()


def test_live_genuine_probe_refuses_bad_gate_before_provider_launch(tmp_path):
    home = tmp_path / "child";home.mkdir()
    with pytest.raises(LiveGateRefusal, match="EXPLICIT_MODEL_ENV_ALLOWLIST_REQUIRED"):
        live_elf_probe(
            loadout_root=tmp_path/"loadout",provider_checkout=tmp_path/"provider",
            provider_python=tmp_path/"python",workspace=home,
            output=tmp_path/"out",model_config_class="disposable",
            forwarded_env_names=(),source_env={},
        )
    with pytest.raises(LiveGateRefusal, match="UNBOUNDED_AGENT_BUDGET"):
        live_elf_probe(
            loadout_root=tmp_path/"loadout",provider_checkout=tmp_path/"provider",
            provider_python=tmp_path/"python",workspace=home,
            output=tmp_path/"out",model_config_class="disposable",
            forwarded_env_names=("TEST_MODEL_KEY",),source_env={"TEST_MODEL_KEY":"never print"},
            timeout_seconds=200,
        )
    with pytest.raises(LiveGateRefusal, match="MODEL_CONFIG_CLASS_REQUIRED"):
        live_elf_probe(
            loadout_root=tmp_path/"loadout",provider_checkout=tmp_path/"provider",
            provider_python=tmp_path/"python",workspace=home,
            output=tmp_path/"out",model_config_class="../bad",
            forwarded_env_names=("TEST_MODEL_KEY",),source_env={"TEST_MODEL_KEY":"never print"},
        )
