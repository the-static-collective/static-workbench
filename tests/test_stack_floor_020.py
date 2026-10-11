"""STACK² 020 — native pinned GHoT 030 single-use ACT proof."""
from __future__ import annotations
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.stack_floor_native_020 import GHOT_SHA, PLANZ_SHA, PLANZ_PATH, PLANZ_REPO, BRANCH_HINT


def fixture(tmp_path, enabled=True):
    ghot_env=os.environ.get("STACK2_020_GHOT_CHECKOUT")
    planz_env=os.environ.get("STACK2_020_PLANZ_CHECKOUT")
    if enabled and (not ghot_env or not planz_env):
        pytest.skip("original Git checkouts required for native proof")
    root=tmp_path/"root"
    root.mkdir()
    home=tmp_path/"ghot-home"
    home.mkdir()
    ghot=Path(ghot_env) if ghot_env else None
    planz=Path(planz_env) if planz_env else None
    if enabled:
        def git(path,*args):
            return subprocess.check_output(["git","-C",str(path),*args])
        assert git(ghot,"rev-parse","HEAD").decode().strip()==GHOT_SHA
        assert git(planz,"rev-parse","HEAD").decode().strip()==PLANZ_SHA
        source_hash=hashlib.sha256(git(planz,"show",PLANZ_SHA+":"+PLANZ_PATH)).hexdigest()
        context={"repository":PLANZ_REPO,"commit":PLANZ_SHA,
                 "path":PLANZ_PATH,"sha256":source_hash,"branchHint":BRANCH_HINT}
        policy={"schema":"ghot.branch-worker-sources/v0","entries":[
            {"context":context,"checkout_root":str(planz.resolve()),
             "reviewed_for_local_read":True}]}
        (home/"branch-worker").mkdir()
        (home/"branch-worker"/"sources.json").write_text(json.dumps(policy)+"\n")
    cfg=WorkbenchConfig(bind_host="127.0.0.1",port=13700,roots=(RootConfig("local",root),),
        state_dir=tmp_path/"state",stack_floor_native_enabled=enabled,
        stack_floor_ghot_checkout=ghot,stack_floor_planz_checkout=planz,
        stack_floor_ghot_home=home)
    return cfg,home


def auth(client):
    token=client.get("/api/bootstrap").json()["session_token"]
    return {"X-Workbench-Session":token,"Origin":"http://127.0.0.1"}


def target():
    return {"card_ids":["cannon","planz","ghot","relatte"],
            "operation":"hash-exact-source"}


def act(p):
    return {"card_ids":["cannon","planz","ghot","relatte"],
            "consent_nonce":p["consent_nonce"],
            "proposal_address":p["proposal_address"],
            "confirm_phrase":"ACT","acknowledge_single_use":True}


def test_default_is_disabled(tmp_path):
    cfg,_=fixture(tmp_path,False)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as c:
        assert c.get("/api/stack-floor/native/status").json()["enabled"] is False
        r=c.post("/api/stack-floor/native/preview",json=target(),headers=auth(c))
        assert r.status_code==409 and "NATIVE_FLOOR_DISABLED" in r.text


def test_one_original_native_ghot_act_and_signed_receipt(tmp_path):
    cfg,home=fixture(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as c:
        headers=auth(c)
        assert c.post("/api/stack-floor/native/preview",json=target()).status_code==403
        assert c.post("/api/stack-floor/native/preview",json=target(),
                      headers={"X-Workbench-Session":headers["X-Workbench-Session"]}).status_code==403
        assert c.post("/api/stack-floor/native/preview",json=target(),
                      headers={**headers,"Origin":"http://other.example"}).status_code==403
        assert c.post("/api/stack-floor/native/preview",json={**target(),"extra":"no"},
                      headers=headers).status_code==422
        assert c.post("/api/stack-floor/native/preview",json={
            **target(),"card_ids":["planz","cannon","ghot","relatte"]
        },headers=headers).status_code==422
        p_response=c.post("/api/stack-floor/native/preview",json=target(),headers=headers)
        assert p_response.status_code==200,p_response.text
        p=p_response.json()
        assert p["status"]=="READY" and p["executed"] is False
        assert p["fixed_source"]["commit"]==PLANZ_SHA
        a=act(p)
        assert c.post("/api/stack-floor/native/act",json={**a,"confirm_phrase":"NO"},
                      headers=headers).status_code==409
        assert c.post("/api/stack-floor/native/act",json={
            **a,"acknowledge_single_use":False},headers=headers).status_code==409
        assert c.post("/api/stack-floor/native/act",json={
            **a,"proposal_address":"sha256:"+"f"*64},headers=headers).status_code==409
        assert c.post("/api/stack-floor/native/act",json={
            **a,"unknown_action":"refused"},headers=headers).status_code==422
        done=c.post("/api/stack-floor/native/act",json=a,headers=headers)
        assert done.status_code==200,done.text
        result=done.json()
        assert result["status"]=="EXECUTED_AND_LOCAL_RECEIPT_VERIFIED"
        assert result["native_ghot_030_signature_verified"] is True
        assert result["receipt"]["status"]=="EXECUTED"
        assert result["receipt"]["ticket_spent"] is True
        assert result["receipt"]["operation_attempted"] is True
        assert result["receipt"]["success"] is True
        assert result["sha256"]==p["fixed_source"]["sha256"]
        assert result["operation"]=="hash-exact-source"
        assert result["branch_program_executed"] is False
        assert result["new_relatte_crossing_created"] is False
        assert result["receiver_admitted"] is False
        assert result["remote_effects"]==0
        assert len(list((home/"activation-tickets"/"claims").glob("*.json")))==1
        assert len(list((home/"activation-tickets"/"tickets").glob("*.json")))==1
        assert len(list((home/"activation-tickets"/"receipts").glob("*.json")))==1
        second=c.post("/api/stack-floor/native/act",json=a,headers=headers)
        assert second.status_code==409
        assert len(list((home/"activation-tickets"/"claims").glob("*.json")))==1
        assert sum(e["kind"]=="stack2.native.hash_act"
                   for e in c.get("/api/events").json()["events"])==1


def test_owner_policy_is_not_minted_by_workbench(tmp_path):
    cfg,home=fixture(tmp_path)
    (home/"branch-worker"/"sources.json").unlink()
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as c:
        r=c.post("/api/stack-floor/native/preview",json=target(),headers=auth(c))
        assert r.status_code==409 and "OWNER_GHOT_POLICY_REQUIRED" in r.text
        assert not (home/"branch-worker"/"sources.json").exists()


def test_expired_nonce_is_not_an_execution_lease(tmp_path):
    cfg,home=fixture(tmp_path)
    with TestClient(create_app(cfg),base_url="http://127.0.0.1") as c:
        headers=auth(c)
        res=c.post("/api/stack-floor/native/preview",json=target(),headers=headers)
        assert res.status_code==200,res.text
        with c.app.state.stack_floor_native_020._db() as db:
            db.execute("UPDATE previews SET expires=0")
        declined=c.post("/api/stack-floor/native/act",json=act(res.json()),headers=headers)
        assert declined.status_code==409
        assert "PREVIEW_EXPIRED_SPENT_OR_CHANGED" in declined.text
        assert not (home/"activation-tickets").exists()
