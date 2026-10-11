from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.receipt_porter import (
    GHOT, RELATTE, CANNON, CHECKS, SCHEMA, STATUS, PorterRefusal,
    _validate_state, compact, digest, latest_summary, verify_existing,
)

def ids(prefix, n):
    return prefix + ":" + format(n, "x") * 64

def native_fixture(tmp_path: Path):
    cannon = tmp_path / "cannon"
    ghot = tmp_path / "ghot"
    relatte = tmp_path / "relatte"
    out = tmp_path / "private-crossing"
    for folder in (cannon, ghot, relatte, out):
        folder.mkdir()
    secret = "SECRET SONG INPUT DOES NOT BELONG IN WEB RESPONSE"
    report = {
        "schema": "ghot.ai-recomposition-report/v0",
        "report_id": ids("ai-recomposition-report-v0", 10),
        "private_text": secret,
    }
    report_path = tmp_path / "private-report.json"
    report_path.write_text(json.dumps(report))
    public = {
        "schema": "cannon.stack-squared-ai-relatte-public/v0",
        "source_commit": GHOT, "relatte_commit": RELATTE,
        "ghot_report_id": report["report_id"],
        "relatte_crossing_id": ids("relatte-crossing-v0", 11),
        "relatte_received_receipt_id": ids("relatte-receipt-v0", 12),
        "relatte_hold_receipt_id": ids("relatte-receipt-v0", 13),
        "destination": "R3_HOLD",
        "receiver_admitted": False, "original_ghot_donor_reexecuted": False,
        "original_relatte_receiver_used": True,
        "source_human_identity_established": False,
        "external_effects": 0, "production_deployed": False,
    }
    (out / "public-inspection.json").write_text(json.dumps(public))
    return cannon, ghot, relatte, out, report_path, public, secret

def test_porter_native_validation_only_writes_redacted_state(tmp_path):
    cannon, ghot, relatte, out, report, public, secret = native_fixture(tmp_path)
    observed = []
    def runner(argv, **kwargs):
        observed.append(argv)
        assert argv[0:2] == ["node", "--experimental-strip-types"]
        assert argv[3] == "verify"
        assert "public-inspection" not in " ".join(argv)
        return CompletedProcess(argv, 0, stdout=json.dumps({
            "status": "STACK_SQUARED_023_NATIVE_R3_HOLD_COLD_VERIFIED",
            "admitted": False, "crossing_id": public["relatte_crossing_id"],
            "received": public["relatte_received_receipt_id"],
            "hold": public["relatte_hold_receipt_id"],
        }), stderr="")
    state = tmp_path / "local-state"
    with patch("static_workbench.receipt_porter.exact_cannon_root", return_value=cannon):
        with patch("static_workbench.receipt_porter.subprocess.run", side_effect=runner):
            summary = verify_existing(
                cannon_root=cannon, ghot_root=ghot, relatte_root=relatte,
                original_report=report, crossing_output=out, state_dir=state)
    assert len(observed) == 1
    assert summary["status"] == STATUS
    assert summary["checks"] == CHECKS
    assert latest_summary(state) == summary
    stored = (state / "receipt-porter/latest.json").read_text()
    assert secret not in stored
    assert str(report) not in stored
    assert str(out) not in stored
    assert summary["receiver_admitted"] is False
    assert summary["browser_execution"] is False

def test_refuse_native_failed_verification_and_no_state(tmp_path):
    cannon, ghot, relatte, out, report, public, _ = native_fixture(tmp_path)
    with patch("static_workbench.receipt_porter.exact_cannon_root", return_value=cannon):
        with patch("static_workbench.receipt_porter.subprocess.run",
                   return_value=CompletedProcess([], 1, stdout="", stderr="HOLD")):
            with pytest.raises(PorterRefusal, match="ORIGINAL_NATIVE_VERIFIER_REFUSED"):
                verify_existing(cannon_root=cannon, ghot_root=ghot,
                    relatte_root=relatte, original_report=report,
                    crossing_output=out, state_dir=tmp_path/"state")
    assert not (tmp_path/"state/receipt-porter/latest.json").exists()

def test_refuse_public_receipt_swapping_and_claimed_admit(tmp_path):
    cannon, ghot, relatte, out, report, public, _ = native_fixture(tmp_path)
    for field, value in [("receiver_admitted",True),
                         ("relatte_crossing_id",ids("relatte-crossing-v0",15))]:
        changed=copy.deepcopy(public)
        changed[field]=value
        (out / "public-inspection.json").write_text(json.dumps(changed))
        with patch("static_workbench.receipt_porter.exact_cannon_root", return_value=cannon):
            with patch("static_workbench.receipt_porter.subprocess.run",
                       return_value=CompletedProcess([], 0, stdout=json.dumps({
                           "status":"STACK_SQUARED_023_NATIVE_R3_HOLD_COLD_VERIFIED",
                           "admitted":False,
                           "crossing_id":public["relatte_crossing_id"],
                           "received":public["relatte_received_receipt_id"],
                           "hold":public["relatte_hold_receipt_id"],
                       }), stderr="")):
                with pytest.raises(PorterRefusal):
                    verify_existing(cannon_root=cannon, ghot_root=ghot,
                        relatte_root=relatte, original_report=report,
                        crossing_output=out, state_dir=tmp_path/"state")
        assert not (tmp_path/"state/receipt-porter/latest.json").exists()
    (out / "public-inspection.json").write_text(json.dumps(public))

def test_porter_state_rejects_tamper_or_authority_promotion(tmp_path):
    body = {
        "schema":SCHEMA,"status":STATUS,
        "verified_at":"2026-10-11T18:00:00Z",
        "source_pins":{"GHoT":GHOT,"CANNON":CANNON,"reLATTE":RELATTE},
        "public_inspection_sha256":"a"*64,"public_canonical_sha256":"b"*64,
        "ghot_report_id":ids("ai-recomposition-report-v0",10),
        "relatte_crossing_id":ids("relatte-crossing-v0",11),
        "relatte_received_receipt_id":ids("relatte-receipt-v0",12),
        "relatte_hold_receipt_id":ids("relatte-receipt-v0",13),
        "checks":CHECKS,"receiver_disposition":"R3_HOLD",
        "receiver_admitted":False,"human_identity_authenticated":False,
        "operator_permission_inferred":False,"browser_execution":False,
        "signature_trust":"SELF_DESCRIBING_TEST_KEYS_NOT_HUMAN_IDENTITY",
    }
    state={**body,"attestation_sha256":digest(compact(body))}
    assert _validate_state(state)==state
    for mutation in ({"receiver_admitted":True},
                     {"source_pins":{**body["source_pins"],"GHoT":"0"*40}},
                     {"ghot_report_id":"private-leak"},
                     {"attestation_sha256":"0"*64}):
        with pytest.raises(PorterRefusal):
            _validate_state({**state, **mutation})
    directory=tmp_path/"receipt-porter"
    directory.mkdir()
    latest=directory/"latest.json"
    latest.write_text(json.dumps(state))
    assert latest_summary(tmp_path)==state
    latest.unlink()
    latest.symlink_to(tmp_path/"outside.json")
    with pytest.raises(PorterRefusal, match="PORTER_SYMLINK_REFUSED"):
        latest_summary(tmp_path)

def config(tmp_path, bind_host="127.0.0.1"):
    root=tmp_path/"sources";root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host=bind_host, port=13700, state_dir=tmp_path/"state",
        roots=(RootConfig("sources",root),))

def test_host_exposes_only_fixed_get_and_never_launches_native_verifier(tmp_path):
    cfg=config(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        page=client.get("/receipt-verification")
        js=client.get("/assets/receipt-verification-ui.mjs")
        core=client.get("/assets/receipt-verification-core.mjs")
        empty=client.get("/api/receipt-verification/latest")
        assert all(x.status_code==200 for x in (page,js,core,empty))
        assert "connect-src 'self'" in page.text
        assert "fetch('/api/receipt-verification/latest'" in js.text
        assert "/receipt-verification" in client.get("/").text
        assert "/receipt-verification" in client.get("/receipt-floor").text
        assert empty.json()["state"]=="NO_OPERATOR_VERIFICATION"
        assert empty.headers["cache-control"]=="no-store"
        assert client.post("/api/receipt-verification/latest",json={"execute":True}).status_code==405
        assert client.post("/receipt-verification",json={"run":True}).status_code==405
        assert client.get("/receipt-verification",headers={"host":"evil.example"}).status_code==400

def test_non_loopback_binding_withholds_even_existing_verification(tmp_path):
    cfg=config(tmp_path,bind_host="0.0.0.0")
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        assert client.get("/api/receipt-verification/latest").status_code==403
