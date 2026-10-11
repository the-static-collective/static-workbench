"""STACK² 024 — original Haunted Toaster brains stay below receiver authority."""
import os
import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from test_stack_floor_020 import fixture as native_fixture, auth
from test_stack_floor_021 import setup
from test_stack_floor_022 import held_example
from test_stack_floor_023 import add_native_fixture_sources

TOASTER_SHA = "74365daa3351555d17482662a9a13cc6a316f1e1"


def configured(tmp_path):
    cfg, home, receiver, relatte = setup(tmp_path)
    toaster_path=os.environ.get("STACK2_024_TOASTER_CHECKOUT")
    if not toaster_path:
        raise AssertionError("Original pinned Toaster checkout is required for these CI tests")
    import subprocess
    toaster=Path(toaster_path).resolve()
    assert subprocess.check_output(
        ["git","-C",str(toaster),"rev-parse","HEAD"],text=True).strip()==TOASTER_SHA
    return replace(cfg,stack_floor_toaster_enabled=True,
                   stack_floor_toaster_checkout=toaster),receiver,relatte


def selected_proposal(client,headers):
    result=client.post("/api/stack-floor/mycelium/inspect",json={},headers=headers)
    assert result.status_code==200,result.text
    field=result.json()
    edge=next(e for e in field["edges"] if
              any(f["kind"]=="SAME_DECLARED_PAYLOAD_ADDRESS" for f in e["evidence"]))
    return edge,field


def test_disabled_no_execution_or_media_interface(tmp_path):
    cfg,_=native_fixture(tmp_path,enabled=False)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        status=client.get("/api/stack-floor/delight/status").json()
        assert status["enabled"] is False
        assert status["media_execution_available"] is False
        a=auth(client)
        r=client.post("/api/stack-floor/delight/preview",json={
            "proposal_id":"proposal-023:"+"a"*64,"deal_index":0},headers=a)
        assert r.status_code==409
        assert "USEFUL_DELIGHT_DISABLED" in r.text


def test_original_toaster_move_deck_generates_six_attributed_non_acts(tmp_path):
    cfg,receiver,relatte=configured(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        _,headers=held_example(client,receiver)
        add_native_fixture_sources(relatte,receiver)
        edge,field=selected_proposal(client,headers)
        journal_before=(receiver/"journal.jsonl").read_bytes()
        keys_before=(receiver/"receiver-key.json").read_bytes()
        status=client.get("/api/stack-floor/delight/status").json()
        assert status["enabled"] is True
        assert client.post("/api/stack-floor/delight/preview",json={
            "proposal_id":edge["proposal_id"],"deal_index":0}).status_code==403
        assert client.post("/api/stack-floor/delight/preview",json={
            "proposal_id":edge["proposal_id"],"deal_index":0},
            headers={"X-Workbench-Session":headers["X-Workbench-Session"]}).status_code==403
        assert client.post("/api/stack-floor/delight/preview",json={
            "proposal_id":edge["proposal_id"],"deal_index":0},
            headers={**headers,"Origin":"http://evil.example"}).status_code==403
        for bad in [
            {"proposal_id":edge["proposal_id"],"deal_index":0,"run_video":True},
            {"proposal_id":"forged","deal_index":0},
            {"proposal_id":"proposal-023:"+"f"*64,"deal_index":0},
            {"proposal_id":edge["proposal_id"],"deal_index":9},
            {"proposal_id":edge["proposal_id"],"deal_index":True},
            {"proposal_id":edge["proposal_id"],"deal_index":0,"admit":True},
        ]:
            denied=client.post("/api/stack-floor/delight/preview",
                               json=bad,headers=headers)
            assert denied.status_code in (409,422),denied.text

        req={"proposal_id":edge["proposal_id"],"deal_index":0}
        response=client.post("/api/stack-floor/delight/preview",json=req,headers=headers)
        assert response.status_code==200,response.text
        record=response.json()
        assert record["original_toaster_repository"]=="the-static-collective/the-haunted-toaster"
        assert record["original_toaster_commit"]==TOASTER_SHA
        assert record["original_toaster_policy"]=="candidate-move-deck/v1"
        assert record["original_toaster_deal_address"].startswith("candidate-move-deal:sha256:")
        assert record["selected_relation_proposal_id"]==edge["proposal_id"]
        assert record["receiver_state_ref"]==field["state_ref"]
        assert [v["kind"] for v in record["cards"]]==[
            "expand","mutate","converge","stomp","cross","cross"]
        assert all(v["suggested_only"] is True and
                   v["source_material_loaded"] is False and
                   v["receiver_admitted"] is False and
                   v["original_toaster_move_address"].startswith("candidate-move:sha256:")
                   for v in record["cards"])
        assert sum(c["available"] for c in record["cards"] if c["kind"]=="cross")==1
        assert any(c["refusal"]=="NO_CURRENT_SIGNED_RELATION_BETWEEN_CROSS_PARENTS"
                   for c in record["cards"])
        assert record["original_toaster_renderer_executed"] is False
        assert record["original_toaster_source_media_loaded"] is False
        assert record["original_ghot_signed_receipt_reverified"] is False
        assert record["native_relatte_signatures_verified"] is True
        assert record["source_claims_independently_verified"] is False
        assert record["source_bytes_read"] is False
        assert record["original_receiver_changed"] is False
        assert record["relations_persisted"] is False
        assert record["admissions_performed"]==0
        assert record["creative_output_authorized"] is False
        assert record["human_selection_inferred"] is False
        again=client.post("/api/stack-floor/delight/preview",json=req,headers=headers)
        assert again.status_code==200,again.text
        assert again.json()==record, "same source, receiver snapshot, and deck index => exact same deal"
        next_deal=client.post("/api/stack-floor/delight/preview",json={
            **req,"deal_index":1},headers=headers)
        assert next_deal.status_code==200
        assert next_deal.json()["original_toaster_deal_address"]!=record["original_toaster_deal_address"]
        assert (receiver/"journal.jsonl").read_bytes()==journal_before
        assert (receiver/"receiver-key.json").read_bytes()==keys_before
        assert client.post("/api/stack-floor/delight/act",json={},headers=headers).status_code==404
        assert client.post("/api/stack-floor/delight/admit",json={},headers=headers).status_code==404


def test_tampered_receiver_signature_blocks_toaster_deal(tmp_path):
    cfg,receiver,relatte=configured(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as client:
        actual,headers=held_example(client,receiver)
        add_native_fixture_sources(relatte,receiver)
        edge,_=selected_proposal(client,headers)
        journal=receiver/"journal.jsonl"
        entries=[json.loads(x) for x in journal.read_text().splitlines()]
        entries[1]["receipt"]["kind"]="R3_ADMIT"
        changed="".join(json.dumps(x)+"\n" for x in entries).encode()
        journal.write_bytes(changed)
        denied=client.post("/api/stack-floor/delight/preview",json={
            "proposal_id":edge["proposal_id"],"deal_index":0},headers=headers)
        assert denied.status_code==409
        assert journal.read_bytes()==changed
