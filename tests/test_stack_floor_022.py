"""STACK² 022 — real original reLATTE receiver journal, adversarial read-only shelf."""
from pathlib import Path
import json
import shutil

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from test_stack_floor_020 import fixture as native_fixture, auth
from test_stack_floor_021 import setup, act_original, owner_policy, preview_body, cross_body


def held_example(client, receiver):
    gh, headers = act_original(client)
    owner_policy(receiver, gh)
    pre = client.post("/api/stack-floor/postoffice/preview",
                      json=preview_body(gh), headers=headers)
    assert pre.status_code == 200, pre.text
    crossing = client.post("/api/stack-floor/postoffice/cross",
                           json=cross_body(pre.json()), headers=headers)
    assert crossing.status_code == 200, crossing.text
    return crossing.json(), headers


def test_shelf_disabled_and_all_access_guarded(tmp_path):
    cfg,_=native_fixture(tmp_path, enabled=False)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as client:
        assert client.get("/api/stack-floor/shelf/status").json()["enabled"] is False
        a=auth(client)
        denied=client.post("/api/stack-floor/shelf/list",headers=a,json={})
        assert denied.status_code==409
        assert "POST_OFFICE_DISABLED" in denied.text
        assert client.get("/api/stack-floor/shelf/list").status_code==405


def test_original_relatte_shelf_shows_only_held_items_with_real_source_and_receipts(tmp_path):
    cfg, home, receiver, _=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        before=(receiver/"journal.jsonl").read_bytes()
        a=auth(client)
        assert client.get("/api/stack-floor/shelf/status").json()["enabled"] is True
        assert client.post("/api/stack-floor/shelf/list",json={}).status_code==403
        assert client.post("/api/stack-floor/shelf/list",json={},
            headers={"X-Workbench-Session":a["X-Workbench-Session"]}).status_code==403
        assert client.post("/api/stack-floor/shelf/list",json={},
            headers={**a,"Origin":"http://evil.example"}).status_code==403
        assert client.post("/api/stack-floor/shelf/list",json={"path":"/etc/passwd"},
            headers=a).status_code==422
        empty=client.post("/api/stack-floor/shelf/list",json={},headers=a)
        assert empty.status_code==200,empty.text
        assert empty.json()["counts"]["held"]==0
        assert (receiver/"journal.jsonl").read_bytes()==before

        cross,headers=held_example(client,receiver)
        journal=(receiver/"journal.jsonl").read_bytes()
        key=(receiver/"receiver-key.json").read_bytes()
        listed=client.post("/api/stack-floor/shelf/list",json={},headers=headers)
        assert listed.status_code==200,listed.text
        snapshot=listed.json()
        assert snapshot["mode"]=="list"
        assert snapshot["counts"]["held"]==1
        assert snapshot["counts"]["admitted"]==0
        assert snapshot["journal_events"]==2
        assert snapshot["original_receiver_journal_replayed"] is True
        assert snapshot["original_relatte_signatures_verified"] is True
        assert snapshot["original_ghot_signature_reverified"] is False
        assert snapshot["mutations_performed"] is False
        assert snapshot["payload_bytes_read"] is False
        assert snapshot["private_keys_exported"] is False
        assert snapshot["receiver_admission_authorized"] is False
        assert len(snapshot["records"])==1
        item=snapshot["records"][0]
        assert item["crossing_id"]==cross["crossing_id"]
        assert item["status"]=="HOLD"
        assert item["owner_admitted"] is False
        assert item["receive_receipt_id"]==cross["native_relatte_receive_receipt_id"]
        assert item["hold_receipt_id"]==cross["native_relatte_hold_receipt_id"]
        assert "payload_refs" not in item
        assert "signing" not in item
        assert "donor_claims" not in item

        assert client.post("/api/stack-floor/shelf/detail",json={
            "crossing_id":item["crossing_id"],"admit":True},
            headers=headers).status_code==422
        assert client.post("/api/stack-floor/shelf/detail",json={
            "crossing_id":"invalid"},headers=headers).status_code==409
        assert client.post("/api/stack-floor/shelf/detail",json={
            "crossing_id":"relatte-crossing-v0:"+"f"*64},
            headers=headers).status_code==409
        detail=client.post("/api/stack-floor/shelf/detail",json={
            "crossing_id":item["crossing_id"]},headers=headers)
        assert detail.status_code==200,detail.text
        d=detail.json()
        assert d["mode"]=="detail"
        p=d["records"][0]
        assert p["status"]=="HOLD"
        assert p["source_history_head"] is not None
        assert p["source_contract"]=="ghot.branch-worker@0"
        assert p["source_family"]=="organ:stack-squared/post-office-021"
        assert p["signature_status"]=="NATIVE_RELATTE_VALIDATED"
        assert p["donor_proof"]=="NOT_REVERIFIED_BY_SHELF"
        assert len(p["payload_refs"])==2
        assert p["receive_pre_state_ref"]!=p["receive_post_state_ref"]
        assert p["hold_pre_state_ref"]==p["hold_post_state_ref"]
        assert p["custody_receipt_present"] is False
        assert "private_jwk" not in json.dumps(d)
        assert "signed_crossing" not in d
        assert (receiver/"journal.jsonl").read_bytes()==journal
        assert (receiver/"receiver-key.json").read_bytes()==key
        assert not (receiver/"payloads").exists()
        assert client.get("/api/stack-floor/shelf/detail").status_code==405
        assert client.post("/api/stack-floor/shelf/admit",headers=headers,json={}).status_code==404


def test_poisoned_native_signed_journal_is_refused_and_never_cleaned(tmp_path):
    cfg,home,receiver,_=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        crossed,headers=held_example(client,receiver)
        path=receiver/"journal.jsonl"
        events=[json.loads(line) for line in path.read_text().splitlines()]
        assert len(events)==2
        events[1]["receipt"]["kind"]="R3_ADMIT"
        poisoned="".join(json.dumps(e)+"\n" for e in events).encode()
        path.write_bytes(poisoned)
        denied=client.post("/api/stack-floor/shelf/list",json={},headers=headers)
        assert denied.status_code==409
        assert (receiver/"journal.jsonl").read_bytes()==poisoned
        assert not (receiver/"payloads").exists()


def test_shelf_no_receiver_policy_required_to_read_preexisting_hold(tmp_path):
    cfg,home,receiver,_=setup(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        crossed,headers=held_example(client,receiver)
        (receiver/"stack-floor-021-inbox-policy.json").unlink()
        read=client.post("/api/stack-floor/shelf/list",json={},headers=headers)
        assert read.status_code==200,read.text
        assert read.json()["records"][0]["crossing_id"]==crossed["crossing_id"]
        assert read.json()["counts"]["held"]==1
        assert not (receiver/"stack-floor-021-inbox-policy.json").exists()
