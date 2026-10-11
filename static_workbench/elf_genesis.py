"""GENESIS-ELF-001: offline, deterministic seed/receipt specimen.

This is a data-only hatch test, NOT an AI agent, OS sandbox, LOADOUT
authorization, OpenManus conformance, or automatic Seedbank admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import uuid

SCHEMA = "static.genesis-elf-seed/v0"
RECEIPT_SCHEMA = "static.genesis-elf-occurrence/v0"
MAX_BYTES = 65536
HEX = re.compile(r"^[0-9a-f]{64}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_seed(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("SEED_TOO_LARGE")
    try:
        seed = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("BAD_SEED") from exc
    if not isinstance(seed, dict) or set(seed) != {
        "schema", "operation", "input_sha256", "parent_receipt_sha256"
    }:
        raise ValueError("BAD_SEED_SHAPE")
    if seed["schema"] != SCHEMA or seed["operation"] not in ("copy", "uppercase_ascii"):
        raise ValueError("BAD_SEED_OPERATION")
    if not isinstance(seed["input_sha256"], str) or not HEX.fullmatch(seed["input_sha256"]):
        raise ValueError("BAD_INPUT_DIGEST")
    parent = seed["parent_receipt_sha256"]
    if parent is not None and (not isinstance(parent, str) or not HEX.fullmatch(parent)):
        raise ValueError("BAD_PARENT_DIGEST")
    return seed, raw


def _input(workspace: Path) -> bytes:
    source = workspace / "input.txt"
    if source.is_symlink() or not source.is_file():
        raise ValueError("INPUT_MISSING_OR_SYMLINK")
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("INPUT_TOO_LARGE")
    raw = source.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("INPUT_TOO_LARGE")
    return raw


def _transform(operation: str, raw: bytes) -> bytes:
    if operation == "copy":
        return raw
    try:
        return raw.decode("ascii").upper().encode("ascii")
    except UnicodeError as exc:
        raise ValueError("NON_ASCII_INPUT") from exc


def _receipt_bytes(receipt: dict) -> bytes:
    return (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _outside(workspace: Path, output_root: Path) -> None:
    try:
        output_root.resolve().relative_to(workspace.resolve())
    except ValueError:
        return
    raise ValueError("OUTPUT_INSIDE_WORKSPACE")


def hatch(seed_path: Path, workspace: Path, output_root: Path) -> Path:
    """Create one non-authoritative occurrence; never modify the source workspace."""
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError("WORKSPACE_MISSING")
    _outside(workspace, output_root)
    seed, seed_raw = _load_seed(seed_path)
    source = _input(workspace)
    if digest(source) != seed["input_sha256"]:
        raise ValueError("STALE_INPUT")
    artifact = _transform(seed["operation"], source)
    output_root.mkdir(parents=True, exist_ok=True)
    occurrence = output_root / uuid.uuid4().hex
    occurrence.mkdir(exist_ok=False)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "occurrence_id": occurrence.name,
        "seed_sha256": digest(seed_raw),
        "input_sha256": digest(source),
        "output_sha256": digest(artifact),
        "operation": seed["operation"],
        "parent_receipt_sha256": seed["parent_receipt_sha256"],
        "producer": "deterministic_fixture_not_openmanus",
        "status": "produced_unverified",
        "semantic_authority": False,
        "admitted": False,
    }
    (occurrence / "artifact.txt").write_bytes(artifact)
    (occurrence / "receipt.json").write_bytes(_receipt_bytes(receipt))
    return occurrence


def verify(
    seed_path: Path, workspace: Path, occurrence: Path,
    parent_receipt: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Independently check bytes and stated lineage; no promotion or authorization."""
    reasons: list[str] = []
    try:
        seed, seed_raw = _load_seed(seed_path)
        source = _input(workspace.resolve())
        if digest(source) != seed["input_sha256"]:
            reasons.append("STALE_INPUT")
        expected = _transform(seed["operation"], source)
    except (OSError, ValueError) as exc:
        return False, (str(exc),)
    expected_parent = seed["parent_receipt_sha256"]
    if expected_parent is not None:
        if parent_receipt is None or not parent_receipt.is_file():
            reasons.append("PARENT_RECEIPT_MISSING")
        elif digest(parent_receipt.read_bytes()) != expected_parent:
            reasons.append("PARENT_RECEIPT_MISMATCH")
        else:
            try:
                parent = json.loads(parent_receipt.read_bytes())
                if parent["output_sha256"] != digest(source):
                    reasons.append("PARENT_OUTPUT_MISMATCH")
            except (ValueError, KeyError, TypeError):
                reasons.append("PARENT_RECEIPT_INVALID")
    elif parent_receipt is not None:
        reasons.append("UNDECLARED_PARENT")
    if occurrence.is_symlink() or not occurrence.is_dir():
        return False, tuple(reasons + ["OCCURRENCE_MISSING_OR_SYMLINK"])
    artifact_path = occurrence / "artifact.txt"
    receipt_path = occurrence / "receipt.json"
    if artifact_path.is_symlink() or receipt_path.is_symlink():
        return False, tuple(reasons + ["SYMLINK_OUTPUT"])
    if {p.name for p in occurrence.iterdir()} != {"artifact.txt", "receipt.json"}:
        reasons.append("UNEXPECTED_OUTPUT")
    try:
        artifact = artifact_path.read_bytes()
        receipt = json.loads(receipt_path.read_bytes())
    except (OSError, ValueError):
        return False, tuple(reasons + ["OUTPUT_OR_RECEIPT_MISSING"])
    if artifact != expected:
        reasons.append("WRONG_ARTIFACT")
    expected_receipt = {
        "schema": RECEIPT_SCHEMA,
        "occurrence_id": occurrence.name,
        "seed_sha256": digest(seed_raw),
        "input_sha256": digest(source),
        "output_sha256": digest(artifact),
        "operation": seed["operation"],
        "parent_receipt_sha256": expected_parent,
        "producer": "deterministic_fixture_not_openmanus",
        "status": "produced_unverified",
        "semantic_authority": False,
        "admitted": False,
    }
    if receipt != expected_receipt:
        reasons.append("RECEIPT_MISMATCH")
    return not reasons, tuple(reasons)


def _write_seed(path: Path, data: bytes, operation: str, parent: str | None) -> None:
    path.write_text(json.dumps({
        "schema": SCHEMA, "operation": operation,
        "input_sha256": digest(data), "parent_receipt_sha256": parent,
    }, sort_keys=True) + "\n", encoding="utf-8")


def demo() -> dict:
    """Prove a two-occurrence handoff from verified bytes, not inherited runtime."""
    with tempfile.TemporaryDirectory(prefix="static-genesis-elf-") as tmp:
        root = Path(tmp)
        first = root / "first"
        first.mkdir()
        (first / "input.txt").write_bytes(b"seed becomes signal\n")
        seed1 = root / "seed1.json"
        _write_seed(seed1, b"seed becomes signal\n", "uppercase_ascii", None)
        occurrence1 = hatch(seed1, first, root / "occurrences")
        ok1, why1 = verify(seed1, first, occurrence1)
        if not ok1:
            raise RuntimeError(f"FIRST_VERIFY_FAILED: {why1}")
        second = root / "second"
        second.mkdir()
        inherited = (occurrence1 / "artifact.txt").read_bytes()
        (second / "input.txt").write_bytes(inherited)
        seed2 = root / "seed2.json"
        _write_seed(
            seed2, inherited, "copy",
            digest((occurrence1 / "receipt.json").read_bytes()),
        )
        occurrence2 = hatch(seed2, second, root / "occurrences")
        ok2, why2 = verify(
            seed2, second, occurrence2, occurrence1 / "receipt.json"
        )
        if not ok2:
            raise RuntimeError(f"SECOND_VERIFY_FAILED: {why2}")
        return {
            "schema": "static.genesis-elf-demo/v0",
            "first_verified": ok1, "second_verified": ok2,
            "distinct_occurrences": occurrence1.name != occurrence2.name,
            "output": (occurrence2 / "artifact.txt").read_text(encoding="ascii").strip(),
            "provider": "deterministic_fixture_not_openmanus",
            "live_provider_conformance": "NOT_RUN",
            "os_image_boot": "NOT_RUN",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo")
    for name in ("hatch", "verify"):
        command = sub.add_parser(name)
        command.add_argument("--seed", type=Path, required=True)
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "verify":
            command.add_argument("--parent-receipt", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(demo(), indent=2))
        return 0
    if args.command == "hatch":
        print(hatch(args.seed, args.workspace, args.output))
        return 0
    ok, reasons = verify(args.seed, args.workspace, args.output, args.parent_receipt)
    print(json.dumps({"verified": ok, "reasons": reasons}, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
