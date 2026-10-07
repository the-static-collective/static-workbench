"""WEBZ-003: physical carrier bytes are a distinct, explicitly authorized crossing."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig,WorkbenchConfig
from static_workbench.webz_parcel import WebzParcelGate,WebzParcelError
from static_workbench import webz_custody as module
from static_workbench.webz_custody import WebzCustodyGate, WebzCustodyError, CUSTODY_RELATTE_REVISION


A = "webz:the-static-collective/sanctuary"
B = "webz:the-static-collective/orchard-022100"
CROSSING = "relatte-crossing-v0:" + "a"*64
RECEIVE = "relatte-receipt-v0:" + "b"*64
DISPOSITION = "relatte-receipt-v0:" + "c"*64
CUSTODY = "relatte-receipt-v0:" + "d"*64


def prepare(tmp_path, monkeypatch, kind="fruit"):
    parent=WebzParcelGate(tmp_path/"state")
    _,raw,digest,policy=parent._fixture(kind)
    parent._verify_stage(kind,digest,raw)
    result={
        "schema":"workbench.webz-parcel-result/v0",
        "kind":kind,"artifact_sha256":digest,
        "crossing_id":CROSSING,"source_world_id":A,
        "destination_world_id":B,"receiver_disposition":policy,
        "receive_receipt_id":RECEIVE,"disposition_receipt_id":DISPOSITION,
        "admitted":False,"semantic_effect":"none",
    }
    crossing={
        "schema":"relatte.crossing-envelope/v0",
        "crossing_id":CROSSING,
        "payload_refs":[{"address":"sha256:"+digest,"role":"fictional-first-party-artifact","media_type":"application/json"}],
    }
    proof={
        "schema":"workbench.webz-parcel-proof/v0",
        "crossing":crossing,
        "artifact_sha256":digest,
        "receive_receipt":{"receipt_id":RECEIVE,"crossing_id":CROSSING,"signing":{"public_key":{"kty":"EC","x":"e","y":"f"}}},
        "disposition_receipt":{"receipt_id":DISPOSITION,"crossing_id":CROSSING,"kind":"R3_"+policy,"signing":{"public_key":{"kty":"EC","x":"e","y":"f"}}},
    }
    monkeypatch.setattr(parent,"_stored",lambda *args: result)
    monkeypatch.setattr(parent,"proof",lambda *args:proof)
    gate=WebzCustodyGate(parent)
    return gate,raw,digest,policy


def owner_result(digest, policy, length):
    receipt={
      "schema":"relatte.receipt/v0", "kind":"PAYLOAD_BYTES_VERIFIED",
      "receipt_id":CUSTODY,"crossing_id":CROSSING,
      "world_id":B,"receiver_particular":"particular:webz:orchard-local-inbox",
      "semantic_effect":"none",
      "signing":{"public_key":{"kty":"EC","x":"e","y":"f"}},
      "extensions":{"local_receiver":{"payload_custody":{
         "sha256":digest,"byte_length":length,"disposition":policy,
         "retained":policy=="HOLD","receive_receipt_id":RECEIVE,
         "disposition_receipt_id":DISPOSITION,
      }}},
    }
    return {
      "schema":"relatte.material-delivery-result/v0",
      "crossing_id":CROSSING,
      "receiver_world_id":B,
      "payload_sha256":digest,
      "received_byte_length":length,
      "receiver_disposition":"R3_"+policy,
      "retained":policy=="HOLD",
      "receive_receipt":{"receipt_id":RECEIVE,"crossing_id":CROSSING,"signing":{"public_key":{"kty":"EC","x":"e","y":"f"}}},
      "disposition_receipt":{"receipt_id":DISPOSITION,"crossing_id":CROSSING,"kind":"R3_"+policy,"signing":{"public_key":{"kty":"EC","x":"e","y":"f"}}},
      "custody_receipt":receipt,
      "receiver_snapshot":{"admitted":[],"held":[CROSSING] if policy=="HOLD" else [],"refused":[CROSSING] if policy=="REFUSE" else []},
    }


def stub_owner(tmp_path, monkeypatch, received):
    owner=tmp_path/"checked-out-reLATTE"
    owner.mkdir(exist_ok=True)
    monkeypatch.setattr(module,"_find_pinned",lambda *a,**k:owner)
    def run(command,cwd,payload,env,label,timeout=30):
        result=received(payload)
        if result.get("retained") is True:
            import base64
            carrier=json.loads(Path(payload["carrier_path"]).read_text())
            target=Path(payload["receiver_root"])/"payloads"/(CROSSING+".bin")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(base64.b64decode(carrier["payload_base64"]))
        return result
    monkeypatch.setattr(module,"_run_json",run)
    return owner


def test_preview_requires_existing_first_phase_but_never_creates_state(tmp_path):
    parent=WebzParcelGate(tmp_path/"state")
    gate=WebzCustodyGate(parent)
    p=gate.preview("fruit")
    assert p["status"]=="NOT_READY"
    assert p["ready"] is False
    assert p["artifact_sha256"]==parent.preview("fruit")["artifact_sha256"]
    assert gate.inbox()==[]
    assert not parent.root.exists()
    with pytest.raises(WebzCustodyError):
        gate.preview("../secrets")


def test_ready_preview_requires_exact_signed_parent_and_is_still_read_only(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch)
    result=gate.preview("fruit")
    assert result["status"]=="READY"
    assert result["ready"] is True
    assert result["crossing_id"]==CROSSING
    assert result["artifact_sha256"]==digest
    assert result["receiver_policy"]=="HOLD"
    assert not (gate.root/"material-carriers").exists()


@pytest.mark.parametrize("digest,identity,confirmation",[
    ("0"*64,CROSSING,"DELIVER_VERIFIED_BYTES"),
    ("correct","relatte-crossing-v0:"+"e"*64,"DELIVER_VERIFIED_BYTES"),
    ("correct",CROSSING,"WRONG_CONFIRMATION"),
])
def test_stale_digest_crossing_or_consent_refused_before_transport(tmp_path,monkeypatch,digest,identity,confirmation):
    gate,raw,wanted,policy=prepare(tmp_path,monkeypatch)
    if digest=="correct": digest=wanted
    with pytest.raises(WebzCustodyError):
        gate.deliver("fruit",digest,identity,confirmation,[])
    assert not (gate.root/"material-carriers").exists()


def test_missing_pinned_relatte_refuses_without_carrier(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch)
    with pytest.raises(WebzCustodyError,match="pinned"):
        gate.deliver("fruit",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])
    assert not (gate.root/"material-carriers").exists()


def test_delivery_uses_literal_bytes_from_fixed_staged_payload_not_arbitrary_source_path(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch)
    calls=[]
    def invoke(req):
        calls.append(req)
        carrier_path=Path(req["carrier_path"])
        carrier=json.loads(carrier_path.read_text())
        assert carrier["schema"]=="webz.material-carrier/v0"
        assert carrier["crossing"]["crossing_id"]==CROSSING
        import base64
        assert base64.b64decode(carrier["payload_base64"])==raw
        assert "source_path" not in req and "disposition" not in req
        return owner_result(digest,policy,len(raw))
    stub_owner(tmp_path,monkeypatch,invoke)
    receipt=gate.deliver("fruit",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])
    assert receipt["schema"]=="workbench.webz-material-custody/v0"
    assert receipt["status"]=="BYTES_VERIFIED_AND_HELD"
    assert receipt["admitted"] is False
    assert receipt["retained"] is True
    assert receipt["custody_receipt_id"]==CUSTODY
    assert receipt["artifact_sha256"]==digest
    assert receipt["pinned_relatte"]==CUSTODY_RELATTE_REVISION
    assert len(calls)==1
    assert gate.inbox()==[receipt]
    assert gate.deliver("fruit",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])==receipt
    assert len(calls)==1


def test_receiver_refusal_can_sign_byte_verification_without_retention(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch,kind="spore")
    stub_owner(tmp_path,monkeypatch,lambda req:owner_result(digest,policy,len(raw)))
    receipt=gate.deliver("spore",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])
    assert receipt["status"]=="BYTES_VERIFIED_AND_REFUSED"
    assert receipt["retained"] is False
    assert receipt["admitted"] is False


def test_tampered_owner_custody_receipt_refused_without_durable_summary(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch)
    bad=owner_result(digest,policy,len(raw))
    bad["custody_receipt"]["extensions"]["local_receiver"]["payload_custody"]["sha256"]="0"*64
    stub_owner(tmp_path,monkeypatch,lambda req:bad)
    with pytest.raises(WebzCustodyError):
        gate.deliver("fruit",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])
    assert gate.inbox()==[]


def test_staged_source_byte_tamper_refuses_even_when_signed_envelope_still_exists(tmp_path,monkeypatch):
    gate,raw,digest,policy=prepare(tmp_path,monkeypatch)
    gate.parent._staged_path("fruit",digest).write_bytes(b"{\"forged\":true}")
    stub_owner(tmp_path,monkeypatch,lambda req:owner_result(digest,policy,len(raw)))
    with pytest.raises(WebzCustodyError,match="staged|bytes|SHA"):
        gate.deliver("fruit",digest,CROSSING,"DELIVER_VERIFIED_BYTES",[])
    assert not (gate.root/"material-carriers").exists()


def test_read_only_api_and_explicit_session_origin_extra_field_guard(tmp_path):
    root=tmp_path/"projects"
    root.mkdir()
    cfg=WorkbenchConfig(bind_host="127.0.0.1",port=13700,state_dir=tmp_path/"state",roots=(RootConfig("static",root),))
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        view=client.get("/api/webz/custody/fruit/preview")
        assert view.status_code==200
        assert view.json()["status"]=="NOT_READY"
        assert client.get("/api/webz/custody/inbox").json()=={"parcels":[]}
        assert not cfg.state_dir.joinpath("webz-relatte").exists()
        url="/api/webz/custody/fruit/deliver"
        data={"expected_sha256":"a"*64,"expected_crossing_id":CROSSING,"confirmation":"DELIVER_VERIFIED_BYTES"}
        assert client.post(url,json=data).status_code==403
        token=client.get("/api/bootstrap").json()["session_token"]
        headers={"x-workbench-session":token}
        assert client.post(url,json=data,headers={**headers,"origin":"http://untrusted.test"}).status_code==403
        assert client.post(url,json={**data,"receiver_policy":"ADMIT"},headers=headers).status_code==422
        assert client.post(url,json=data,headers=headers).status_code==409
        assert client.get("/api/webz/custody/bad/preview").status_code==404
        assert client.get("/webz/world/sanctuary").status_code==200
        assert client.get("/webz/world/orchard").status_code==200
