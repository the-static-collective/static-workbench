"""STACK² 025 — operator-run read-only native re-verification; bounded local summary.

The web server NEVER invokes this verifier. An operator explicitly runs the CLI,
which launches exact source-pinned CANNON 023 'verify' against already-existing
private evidence. Only an independently reduced summary enters Workbench state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone
from typing import Any

GHOT = "6194d91ba83bad63606f6f6741723007227518f2"
RELATTE = "dcc8cdca84c440aa4294134f020fb7095bf87f24"
CANNON = "2fab6e142f21f6213bbcf4e290030acfce756061"
SOURCE_FILES = (
    "scripts/stack-squared-023-ai.mjs",
    "scripts/stack-squared-022-ai.mjs",
    "examples/stack-squared-023-ai.plan.json",
    "examples/stack-squared-022-ai.plan.json",
)
SCHEMA = "workbench.stack-squared-native-verification/v0"
PUBLIC_SCHEMA = "cannon.stack-squared-ai-relatte-public/v0"
STATUS = "LOCAL_NATIVE_SIGNED_CHAIN_VERIFIED"
SHA = re.compile(r"^[0-9a-f]{64}$")
CROSSING = re.compile(r"^relatte-crossing-v0:[0-9a-f]{64}$")
RECEIPT = re.compile(r"^relatte-receipt-v0:[0-9a-f]{64}$")
GHOT_REPORT = re.compile(r"^ai-recomposition-report-v0:[0-9a-f]{64}$")
CHECKS = [
    "EXACT_CANNON_023_SOURCE_BYTES",
    "GHOT_SIGNED_INSTRUMENT_PACKET",
    "ORIGINAL_RELATTE_R14_CROSSING",
    "DISTINCT_RECEIVED_AND_R3_HOLD_SIGNATURES",
    "ORIGINAL_RECEIVER_DURABLE_JOURNAL",
    "PRIVATE_REPORT_EXACT_BINDING",
    "NO_ADMIT_OR_OWNER_ACT",
]


class PorterRefusal(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise PorterRefusal(code)


def compact(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_file(path: Path, *, limit: int) -> tuple[dict[str, Any], bytes]:
    require(path.is_file() and not path.is_symlink(), "MISSING_OR_SYMLINK_FILE")
    require(0 < path.stat().st_size <= limit, "EVIDENCE_SIZE_REFUSED")
    raw = path.read_bytes()
    result = json.loads(raw)
    require(type(result) is dict, "INVALID_EVIDENCE_OBJECT")
    return result, raw


def exact_cannon_root(root: Path) -> Path:
    require(root.is_dir(), "MISSING_CANNON_CHECKOUT")
    original = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True, timeout=12)
    require(original.stdout.strip() == CANNON, "CANNON_COMMIT_MISMATCH")
    for source in SOURCE_FILES:
        local = root / source
        require(local.is_file() and not local.is_symlink(), "CANNON_SOURCE_MISSING")
        committed = subprocess.run(["git", "-C", str(root), "show", f"{CANNON}:{source}"],
                                   capture_output=True, check=True, timeout=12)
        require(digest(local.read_bytes()) == digest(committed.stdout),
                "CANNON_SOURCE_CHANGED")
    return root


def _validate_public(value: dict[str, Any]) -> None:
    require(value.get("schema") == PUBLIC_SCHEMA, "UNEXPECTED_PUBLIC_SCHEMA")
    require(value.get("source_commit") == GHOT and value.get("relatte_commit") == RELATTE,
            "UNEXPECTED_PUBLIC_SOURCE_PIN")
    require(value.get("destination") == "R3_HOLD" and value.get("receiver_admitted") is False
            and value.get("original_ghot_donor_reexecuted") is False
            and value.get("source_human_identity_established") is False
            and value.get("external_effects") == 0
            and value.get("production_deployed") is False
            and value.get("original_relatte_receiver_used") is True,
            "PUBLIC_AUTHORITY_OVERCLAIM")
    require(type(value.get("ghot_report_id")) is str
            and bool(GHOT_REPORT.fullmatch(value["ghot_report_id"])), "INVALID_GHOT_REPORT_ID")
    for key, regex in (("relatte_crossing_id", CROSSING),
                       ("relatte_received_receipt_id", RECEIPT),
                       ("relatte_hold_receipt_id", RECEIPT)):
        require(type(value.get(key)) is str and bool(regex.fullmatch(value[key])),
                "INVALID_PUBLIC_RECEIPT")
    require(value["relatte_received_receipt_id"] != value["relatte_hold_receipt_id"],
            "COLLAPSED_RECEIVER_RECEIPTS")


def _validate_state(obj: Any) -> dict[str, Any]:
    """Apply the same static constraints to the server's read-only state."""
    require(type(obj) is dict, "PORTER_STATE_INVALID")
    fields = {
        "schema", "status", "verified_at", "source_pins", "public_inspection_sha256",
        "public_canonical_sha256", "ghot_report_id", "relatte_crossing_id",
        "relatte_received_receipt_id", "relatte_hold_receipt_id", "checks",
        "receiver_disposition", "receiver_admitted", "human_identity_authenticated",
        "operator_permission_inferred", "browser_execution", "signature_trust",
        "attestation_sha256",
    }
    require(set(obj) == fields and obj["schema"] == SCHEMA and obj["status"] == STATUS,
            "PORTER_STATE_SCHEMA_INVALID")
    require(obj["source_pins"] == {"GHoT": GHOT, "CANNON": CANNON, "reLATTE": RELATTE},
            "PORTER_SOURCE_PINS_INVALID")
    require(type(obj["verified_at"]) is str and
            bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", obj["verified_at"])),
            "PORTER_TIMESTAMP_INVALID")
    require(obj["checks"] == CHECKS and obj["receiver_disposition"] == "R3_HOLD"
            and obj["receiver_admitted"] is False
            and obj["human_identity_authenticated"] is False
            and obj["operator_permission_inferred"] is False
            and obj["browser_execution"] is False
            and obj["signature_trust"] == "SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY",
            "PORTER_AUTHORITY_PROMOTION")
    for field in ("public_inspection_sha256", "public_canonical_sha256",
                  "attestation_sha256"):
        require(type(obj[field]) is str and bool(SHA.fullmatch(obj[field])),
                "PORTER_INVALID_DIGEST")
    for key, pattern in (("ghot_report_id", GHOT_REPORT),
                         ("relatte_crossing_id", CROSSING),
                         ("relatte_received_receipt_id", RECEIPT),
                         ("relatte_hold_receipt_id", RECEIPT)):
        require(type(obj[key]) is str and bool(pattern.fullmatch(obj[key])),
                "PORTER_INVALID_ID")
    body = {k: v for k, v in obj.items() if k != "attestation_sha256"}
    require(obj["attestation_sha256"] == digest(compact(body)), "PORTER_STATE_MODIFIED")
    return obj


def latest_summary(state_dir: Path) -> dict[str, Any] | None:
    directory = state_dir / "receipt-porter"
    target = directory / "latest.json"
    require(not target.is_symlink() and not directory.is_symlink(), "PORTER_SYMLINK_REFUSED")
    if not target.exists():
        return None
    return _validate_state(_json_file(target, limit=4096)[0])


def verify_existing(
    *,
    cannon_root: Path, ghot_root: Path, relatte_root: Path,
    original_report: Path, crossing_output: Path, state_dir: Path,
) -> dict[str, Any]:
    cannon = exact_cannon_root(cannon_root.resolve(strict=True))
    for folder in (ghot_root, relatte_root, crossing_output):
        require(folder.is_dir(), "NATIVE_SOURCE_OR_OUTPUT_MISSING")
    original_report_path = original_report.resolve(strict=True)
    original_report, _ = _json_file(original_report_path, limit=8 * 1024 * 1024)
    require(original_report.get("schema") == "ghot.ai-recomposition-report/v0",
            "INVALID_ORIGINAL_REPORT")
    public, raw_public = _json_file(crossing_output / "public-inspection.json", limit=4096)
    _validate_public(public)

    # Fixed program, fixed arguments; never supplied by an HTTP client.
    completed = subprocess.run([
        "node", "--experimental-strip-types",
        str(cannon / "scripts/stack-squared-023-ai.mjs"), "verify",
        str(cannon / "examples/stack-squared-023-ai.plan.json"),
        str(ghot_root.resolve(strict=True)), str(relatte_root.resolve(strict=True)),
        str(original_report_path), str(crossing_output.resolve(strict=True)),
    ], cwd=cannon, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
       timeout=95, check=False, env={**os.environ, "NODE_NO_WARNINGS": "1"})
    require(completed.returncode == 0, "ORIGINAL_NATIVE_VERIFIER_REFUSED")
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PorterRefusal("NATIVE_VERIFIER_OUTPUT_INVALID") from exc

    require(result.get("status") == "STACK_SQUARED_023_NATIVE_R3_HOLD_COLD_VERIFIED"
            and result.get("admitted") is False, "ORIGINAL_NATIVE_COLD_VERIFICATION_FAILED")
    require(result.get("crossing_id") == public["relatte_crossing_id"] and
            result.get("received") == public["relatte_received_receipt_id"] and
            result.get("hold") == public["relatte_hold_receipt_id"] and
            original_report.get("report_id") == public["ghot_report_id"],
            "PUBLIC_WITNESS_DOES_NOT_MATCH_VERIFIED_PRIVATE_RECORDS")

    result_body: dict[str, Any] = {
        "schema": SCHEMA, "status": STATUS,
        "verified_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_pins": {"GHoT": GHOT, "CANNON": CANNON, "reLATTE": RELATTE},
        "public_inspection_sha256": digest(raw_public),
        "public_canonical_sha256": digest(compact(public)),
        "ghot_report_id": public["ghot_report_id"],
        "relatte_crossing_id": public["relatte_crossing_id"],
        "relatte_received_receipt_id": public["relatte_received_receipt_id"],
        "relatte_hold_receipt_id": public["relatte_hold_receipt_id"],
        "checks": list(CHECKS), "receiver_disposition": "R3_HOLD",
        "receiver_admitted": False, "human_identity_authenticated": False,
        "operator_permission_inferred": False, "browser_execution": False,
        "signature_trust": "SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY",
    }
    summary = {**result_body, "attestation_sha256": digest(compact(result_body))}
    _validate_state(summary)
    state_dir.mkdir(parents=True, exist_ok=True)
    directory = state_dir / "receipt-porter"
    require(not directory.is_symlink() and not (directory / "latest.json").is_symlink(),
            "PORTER_SYMLINK_REFUSED")
    directory.mkdir(mode=0o700, exist_ok=True)
    directory.chmod(0o700)
    target = directory / "latest.json"
    tmp = directory / (".latest-" + os.urandom(8).hex())
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(json.dumps(summary, indent=2, sort_keys=True).encode("utf-8") + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Owner-invoked native CANNON 023 verifier")
    parser.add_argument("--cannon-root", type=Path, required=True)
    parser.add_argument("--ghot-root", type=Path, required=True)
    parser.add_argument("--relatte-root", type=Path, required=True)
    parser.add_argument("--original-report", type=Path, required=True)
    parser.add_argument("--crossing-output", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    args = parser.parse_args()
    # The original report path is never passed to the browser or to an HTTP command.
    try:
        summary = verify_existing(
            cannon_root=args.cannon_root, ghot_root=args.ghot_root,
            relatte_root=args.relatte_root, original_report=args.original_report,
            crossing_output=args.crossing_output, state_dir=args.state_dir)
        print(json.dumps({"status": summary["status"],
                          "attestation_sha256": summary["attestation_sha256"],
                          "verified_at": summary["verified_at"],
                          "receiver_disposition": "R3_HOLD"}))
    except (PorterRefusal, OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, "HOLD: " + type(exc).__name__ + ": " + str(exc)[:140] + "\n")


if __name__ == "__main__":
    main()
