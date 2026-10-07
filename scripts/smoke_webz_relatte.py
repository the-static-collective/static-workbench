#!/usr/bin/env python3
"""Real WEBZ-RELATTE-002: explicit fictional carry, signed reLATTE R14, Orchard HOLD/REFUSE.

Requires a clean pinned .compat/reLATTE at RELATTE_REVISION, with its npm
dependencies installed. No provider keys, network requests or user data used.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from copy import deepcopy
from pathlib import Path

from static_workbench.field_reseed_crossing import RELATTE_REVISION
from static_workbench.repos import RepoStatus
from static_workbench.webz_parcel import WebzParcelGate, WebzParcelError, ORCHARD

ROOT = Path(__file__).resolve().parents[1]
RELATTE = ROOT / ".compat" / "reLATTE"


def verify_public(proof: dict) -> dict:
    completed = subprocess.run(
        ["node", "--experimental-strip-types", str(ROOT / "scripts" / "webz_verify_relatte.mjs")],
        cwd=ROOT,
        input=json.dumps(proof),
        text=True,
        capture_output=True,
        check=False,
        timeout=25,
        env={**os.environ, "RELATTE_ROOT": str(RELATTE), "LC_ALL": "C"},
    )
    if completed.returncode:
        raise AssertionError("Owner verification unavailable: " + completed.stderr[-1500:])
    return json.loads(completed.stdout)


def repo_status() -> RepoStatus:
    return RepoStatus(
        name="reLATTE", path=str(RELATTE), branch=None, detached=True,
        head=RELATTE_REVISION[:7], dirty=False, ahead=None, behind=None,
    )


def main() -> int:
    if not (RELATTE / "scripts" / "opaque-roundtrip.ts").is_file():
        raise SystemExit("Missing exact pinned reLATTE R14 source checkout")

    with tempfile.TemporaryDirectory(prefix="webz-sovereign-parcel-") as temp:
        gate = WebzParcelGate(Path(temp) / "workbench")
        repos = [repo_status()]
        assert gate.inbox() == []
        for kind, decision, expected_status in (
            ("fruit", "HOLD", "RECEIVED_THEN_HELD"),
            ("spore", "REFUSE", "RECEIVED_THEN_REFUSED"),
        ):
            preview = gate.preview(kind)
            assert preview["policy"] == decision
            assert gate.inbox() == [] if kind == "fruit" else len(gate.inbox()) == 1
            offer = gate.send(
                kind, preview["artifact_sha256"], "SEND_TO_ORCHARD", repos,
            )
            assert offer["status"] == expected_status
            assert offer["receiver_disposition"] == decision
            assert offer["admitted"] is False
            assert offer["semantic_effect"] == "none"
            assert offer["destination_world_id"] == ORCHARD
            proof = gate.proof(kind)
            signatures = verify_public(proof)
            assert signatures == {
                "crossing_verified": True,
                "receive_verified": True,
                "disposition_verified": True,
            }, signatures
            assert proof["crossing"]["crossing_id"] == offer["crossing_id"]
            assert proof["receive_receipt"]["crossing_id"] == offer["crossing_id"]
            assert proof["disposition_receipt"]["crossing_id"] == offer["crossing_id"]
            assert proof["crossing"]["payload_refs"][0]["address"] == "sha256:" + preview["artifact_sha256"]
            assert proof["disposition_receipt"]["kind"] == "R3_" + decision

            staged = gate.root / "staged" / f"{kind}-{preview['artifact_sha256']}.json"
            assert hashlib.sha256(staged.read_bytes()).hexdigest() == preview["artifact_sha256"]
            assert proof["artifact"] == json.loads(staged.read_bytes())
            # A completely cold Workbench instance reads the exact same result.
            again = WebzParcelGate(Path(temp) / "workbench").send(
                kind, preview["artifact_sha256"], "SEND_TO_ORCHARD", repos,
            )
            assert again == offer
            tampered = deepcopy(proof)
            tampered["crossing"]["requested_effect"]["kind"] = "ADMIT_WITHOUT_CONSENT"
            assert verify_public(tampered)["crossing_verified"] is False
            print(
                f"WEBZ-RELATTE-002 {kind}: {decision}, "
                f"crossing={offer['crossing_id']}, "
                f"receive={offer['receive_receipt_id']}, "
                f"disposition={offer['disposition_receipt_id']}, "
                "three signatures verified; tamper refused"
            )

        assert len(gate.inbox()) == 2
        assert all(not row["admitted"] for row in gate.inbox())
        print("WEBZ-RELATTE-002: two real owner-signed transfers, HOLD+REFUSE, exact bytes and cold replay PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
