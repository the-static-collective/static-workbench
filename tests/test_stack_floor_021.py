"""STACK² 021: original signed GHoT ACT into independently provisioned native reLATTE HOLD."""
from __future__ import annotations
import json
import os
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from test_stack_floor_020 import fixture as native_020_fixture, auth, target, act


def setup(tmp_path: Path):
    cfg, home = native_020_fixture(tmp_path)
    relatte_path = os.environ.get("STACK2_021_RELATTE_CHECKOUT")
    if not relatte_path:
        pytest.skip("pinned original reLATTE R14 checkout required")
    relatte = Path(relatte_path).resolve()
    assert subprocess.check_output(
        ["git", "-C", str(relatte), "rev-parse", "HEAD"], text=True
    ).strip() == "dcc8cdca84c440aa4294134f020fb7095bf87f24"
    receiver = tmp_path / "owner-independent-receiver"
    # This is an independently prepared CI-only recipient; Workbench does not
    # create or mint its identity, policy or admission authority.
    creation = """
import {pathToFileURL} from 'node:url';
const root=process.argv[1],receiver=process.argv[2];
const r=await import(pathToFileURL(root+'/src/index.ts').href);
await r.LocalReceiver.create(receiver,{
  world_id:'world:stack2-021-test',
  receiver_particular:'particular:independent-ci-receiver',
  contract_ref:'contract:receipts-hold-only/v0'
});
"""
    subprocess.run(
        ["node", "--experimental-strip-types", "--input-type=module", "-e",
         creation, str(relatte), str(receiver)],
        check=True, cwd=relatte, capture_output=True, text=True, timeout=30
    )
    cfg = replace(
        cfg, stack_floor_postoffice_enabled=True,
        stack_floor_relatte_checkout=relatte,
        stack_floor_receiver_root=receiver,
    )
    return cfg, home, receiver, relatte


def act_original(client):
    a = auth(client)
    p = client.post("/api/stack-floor/native/preview", json=target(), headers=a)
    assert p.status_code == 200, p.text
    done = client.post("/api/stack-floor/native/act", json=act(p.json()), headers=a)
    assert done.status_code == 200, done.text
    result = done.json()
    assert result["ticket_spent"] is True
    assert result["native_ghot_030_signature_verified"] is True
    return result, a


def owner_policy(receiver: Path, native: dict):
    policy = {
        "schema": "workbench.stack2-021-receiver-policy/v0",
        "reviewed_for_local_hold": True,
        "disposition": "HOLD",
        "allowed_ticket_id": native["ticket_id"],
        "allowed_receipt_id": native["receipt_id"],
        "allowed_ghot_signer": native["body_signer_particular"],
        "receiver_world": "world:stack2-021-test",
        "receiver_particular": "particular:independent-ci-receiver",
        "receiver_contract": "contract:receipts-hold-only/v0",
    }
    (receiver/"stack-floor-021-inbox-policy.json").write_text(
        json.dumps(policy, indent=2)+"\n", encoding="utf8"
    )
    return policy


def preview_body(native):
    return {"card_ids": ["cannon","planz","ghot","relatte"],
            "ticket_id": native["ticket_id"]}


def cross_body(preview):
    return {"card_ids": ["cannon","planz","ghot","relatte"],
            "ticket_id": preview["ticket_id"],
            "consent_nonce": preview["consent_nonce"],
            "expected_receipt_id": preview["receipt_id"],
            "confirm_phrase": "CROSS",
            "acknowledge_receiver_hold": True}


def test_disabled_postoffice_does_not_use_native_receipt(tmp_path):
    cfg,_ = native_020_fixture(tmp_path, enabled=False)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as client:
        assert client.get("/api/stack-floor/postoffice/status").json()["enabled"] is False
        token = auth(client)
        r=client.post("/api/stack-floor/postoffice/preview",
            json={"card_ids":["cannon","planz","ghot","relatte"],"ticket_id":"x"},
            headers=token)
        assert r.status_code==409
        assert "POST_OFFICE_DISABLED" in r.text


def test_real_ghot_execution_signatures_to_native_relatte_sovereign_hold(tmp_path):
    cfg, home, receiver, relatte = setup(tmp_path)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as client:
        native,headers=act_original(client)
        assert client.get("/api/stack-floor/postoffice/status").json()["enabled"] is True
        assert client.post("/api/stack-floor/postoffice/preview",
             json=preview_body(native)).status_code==403
        assert client.post("/api/stack-floor/postoffice/preview",
             json=preview_body(native),headers={
                 "X-Workbench-Session":headers["X-Workbench-Session"]
             }).status_code==403
        assert client.post("/api/stack-floor/postoffice/preview",
             json={**preview_body(native),"arbitrary":"no"},headers=headers).status_code==422
        missing=client.post("/api/stack-floor/postoffice/preview",
            json=preview_body(native),headers=headers)
        assert missing.status_code==409
        assert "RECEIVER_OWNER_POLICY_REQUIRED" in missing.text
        assert not (receiver/"stack-floor-021-inbox-policy.json").exists()

        owner_policy(receiver,native)
        prepare=client.post("/api/stack-floor/postoffice/preview",
            json=preview_body(native),headers=headers)
        assert prepare.status_code==200,prepare.text
        proposal=prepare.json()
        assert proposal["ghot_signature_verified"] is True
        assert proposal["crossing_performed"] is False
        assert proposal["disposition"]=="HOLD"
        assert proposal["receiver_policy"]=="OWNER_SELECTED_EXACT_TICKET_HOLD"
        cross=cross_body(proposal)
        for change in (
            {**cross,"confirm_phrase":"PASS"},
            {**cross,"acknowledge_receiver_hold":False},
            {**cross,"expected_receipt_id":"wrong"},
            {**cross,"card_ids":["ghot","planz","cannon","relatte"]},
            {**cross,"unknown_field":"refuse"},
        ):
            bad=client.post("/api/stack-floor/postoffice/cross",json=change,headers=headers)
            assert bad.status_code in (409,422),bad.text
        done=client.post("/api/stack-floor/postoffice/cross",json=cross,headers=headers)
        assert done.status_code==200,done.text
        result=done.json()
        assert result["status"]=="RECEIVED_AND_HELD"
        assert result["disposition"]=="HOLD"
        assert result["relatte_signatures_verified"]==3
        assert result["ghot_signature_verified"] is True
        assert result["receiver_admitted"] is False
        assert result["foreign_admission_authorized"] is False
        assert result["native_signed_crossing"]["declared_kind"]=="OPAQUE_ORGAN_ARTIFACT"
        assert result["native_signed_receive_receipt"]["kind"]=="RECEIVED"
        assert result["native_signed_hold_receipt"]["kind"]=="R3_HOLD"
        assert result["signed_original_ghot_execution_receipt"]["receipt_id"]==native["receipt_id"]
        assert result["native_signed_crossing"]["source_particular"]!=native["body_signer_particular"]
        assert result["remote_effects"]==0

        # Verify native reLATTE R14 independent signed artifacts and durable journal.
        delivery=cfg.state_dir/"stack-floor-021-crossings"/native["ticket_id"].split(":")[-1]
        verifier=Path("scripts/stack-floor-021-verify.mjs").resolve()
        args=[
            "node","--experimental-strip-types",str(verifier),"verify",
            str(relatte),str(receiver),
            str(delivery/"request.json"),str(delivery/"roundtrip-result.json")
        ]
        report=subprocess.run(args,cwd=relatte,capture_output=True,text=True,timeout=35)
        assert report.returncode==0,report.stderr
        evidence=json.loads(report.stdout)
        assert evidence["crossing_id"]==result["crossing_id"]
        assert evidence["signatures_cold_verified"]==3
        assert evidence["receiver_admitted"] is False
        assert len((receiver/"journal.jsonl").read_text().splitlines())==2

        retry=client.post("/api/stack-floor/postoffice/cross",json=cross,headers=headers)
        assert retry.status_code==409
        next_preview=client.post("/api/stack-floor/postoffice/preview",
            json=preview_body(native),headers=headers)
        assert next_preview.status_code==409
        assert len((receiver/"journal.jsonl").read_text().splitlines())==2
        events=client.get("/api/events").json()["events"]
        assert sum(e["kind"]=="stack2.postoffice.crossing_held" for e in events)==1


def test_changed_receiver_policy_before_cross_consumes_nonce_and_refuses(tmp_path):
    cfg,home,receiver,_=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        native,headers=act_original(client)
        policy=owner_policy(receiver,native)
        preview=client.post("/api/stack-floor/postoffice/preview",
            json=preview_body(native),headers=headers)
        assert preview.status_code==200,preview.text
        policy["disposition"]="ADMIT"
        (receiver/"stack-floor-021-inbox-policy.json").write_text(json.dumps(policy)+"\n")
        denied=client.post("/api/stack-floor/postoffice/cross",
            json=cross_body(preview.json()),headers=headers)
        assert denied.status_code==409
        assert "RECEIVER_POLICY_NOT_SPECIFIC_HOLD" in denied.text
        assert (receiver/"journal.jsonl").read_text()==""


def test_expired_crossing_proposal_does_not_touch_receiver(tmp_path):
    cfg,home,receiver,_=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        native,headers=act_original(client)
        owner_policy(receiver,native)
        prepare=client.post("/api/stack-floor/postoffice/preview",
             json=preview_body(native),headers=headers)
        assert prepare.status_code==200,prepare.text
        store=client.app.state.stack_floor_postoffice_021
        with store._db() as db:
            db.execute("UPDATE previews SET expiry=0")
        res=client.post("/api/stack-floor/postoffice/cross",
              json=cross_body(prepare.json()),headers=headers)
        assert res.status_code==409
        assert "PREVIEW_EXPIRED_USED_OR_CHANGED" in res.text
        assert (receiver/"journal.jsonl").read_text()==""
