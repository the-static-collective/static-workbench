"""Offline GENESIS-ELF-001 contract tests; does not invoke OpenManus."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from static_workbench.elf_genesis import (
    SCHEMA, demo, digest, hatch, verify,
)


def make_seed(path: Path, raw: bytes, operation: str = "uppercase_ascii",
              parent: str | None = None) -> Path:
    path.write_text(json.dumps({
        "schema": SCHEMA, "input_sha256": digest(raw),
        "operation": operation, "parent_receipt_sha256": parent,
    }) + "\n", encoding="utf-8")
    return path


def test_two_distinct_occurrences_verified_without_provider() -> None:
    result = demo()
    assert result["first_verified"] and result["second_verified"]
    assert result["distinct_occurrences"]
    assert result["output"] == "SEED BECOMES SIGNAL"
    assert result["live_provider_conformance"] == "NOT_RUN"


def test_hatch_preserves_source_and_marks_output_unadmitted(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    raw = b"hello world\n"
    (workspace / "input.txt").write_bytes(raw)
    seed = make_seed(tmp_path / "seed.json", raw)
    occurrence = hatch(seed, workspace, tmp_path / "outputs")
    assert (workspace / "input.txt").read_bytes() == raw
    assert (occurrence / "artifact.txt").read_bytes() == b"HELLO WORLD\n"
    receipt = json.loads((occurrence / "receipt.json").read_text())
    assert receipt["admitted"] is False
    assert receipt["semantic_authority"] is False
    assert receipt["producer"] == "deterministic_fixture_not_openmanus"
    assert verify(seed, workspace, occurrence) == (True, ())


def test_wrong_input_refuses_before_occurrence(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_bytes(b"changed")
    seed = make_seed(tmp_path / "seed.json", b"original")
    with pytest.raises(ValueError, match="STALE_INPUT"):
        hatch(seed, workspace, tmp_path / "outputs")
    assert not (tmp_path / "outputs").exists()


def test_wrong_artifact_and_receipt_are_independently_detected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_bytes(b"original")
    seed = make_seed(tmp_path / "seed.json", b"original")
    occurrence = hatch(seed, workspace, tmp_path / "outputs")
    (occurrence / "artifact.txt").write_bytes(b"tampered")
    ok, reasons = verify(seed, workspace, occurrence)
    assert not ok and "WRONG_ARTIFACT" in reasons and "RECEIPT_MISMATCH" in reasons


def test_parent_is_not_auto_inherited_or_unverified(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_bytes(b"new input")
    seed = make_seed(tmp_path / "seed.json", b"new input", parent="a" * 64)
    occurrence = hatch(seed, workspace, tmp_path / "outputs")
    assert verify(seed, workspace, occurrence) == (False, ("PARENT_RECEIPT_MISSING",))
    fake_parent = tmp_path / "fake-parent.json"
    fake_parent.write_text(json.dumps({"output_sha256": digest(b"other")}))
    ok, reasons = verify(seed, workspace, occurrence, fake_parent)
    assert not ok and "PARENT_RECEIPT_MISMATCH" in reasons


def test_bad_seed_and_output_inside_workspace_refuse(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_bytes(b"hello")
    seed = make_seed(tmp_path / "seed.json", b"hello")
    with pytest.raises(ValueError, match="OUTPUT_INSIDE_WORKSPACE"):
        hatch(seed, workspace, workspace / "artifacts")
    seed.write_text(json.dumps({"schema": SCHEMA, "operation": "shell"}))
    with pytest.raises(ValueError, match="BAD_SEED_SHAPE"):
        hatch(seed, workspace, tmp_path / "outputs")


def test_symlinked_input_and_extra_output_refuse(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    external = tmp_path / "external.txt"
    external.write_bytes(b"hello")
    (workspace / "input.txt").symlink_to(external)
    seed = make_seed(tmp_path / "seed.json", b"hello")
    with pytest.raises(ValueError, match="INPUT_MISSING_OR_SYMLINK"):
        hatch(seed, workspace, tmp_path / "outputs")
    (workspace / "input.txt").unlink()
    (workspace / "input.txt").write_bytes(b"hello")
    occurrence = hatch(seed, workspace, tmp_path / "outputs")
    (occurrence / "unexpected.txt").write_bytes(b"surprise")
    assert "UNEXPECTED_OUTPUT" in verify(seed, workspace, occurrence)[1]
