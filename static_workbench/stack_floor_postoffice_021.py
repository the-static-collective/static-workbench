"""STACK² 021: a second human gate from real signed GHoT ACT to native reLATTE HOLD.

Separate sender permission and owner-preprovisioned receiving-world policy.
No receiver key generation, ADMIT, shell selection, remote work, or replay.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .stack_floor_native_020 import (
    StackFloorActHold, StackFloorNative020, GHOT_SHA, PLANZ_SHA,
    PLANZ_PATH, PLANZ_REPO, check, _git, _root,
)

RELATTE_REPO="the-static-collective/reLATTE"
RELATTE_SHA="dcc8cdca84c440aa4294134f020fb7095bf87f24"
TICKET=re.compile(r"^ghot-activation-ticket-v0:[a-f0-9]{64}$")
TTL=120
MAX_OUTPUT=5*1024*1024
WORLD_POLICY="stack-floor-021-inbox-policy.json"

def exact_json(data: Any)->bytes:
    return json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False,
                      allow_nan=False).encode("utf8")

def sha(data: Any)->str:
    return hashlib.sha256(exact_json(data)).hexdigest()

def stamp(offset=0):
    return (datetime.now(timezone.utc)+timedelta(seconds=offset)).isoformat(
        timespec="milliseconds").replace("+00:00","Z")

def native_process(argv: list[str], *,cwd:Path, env:dict[str,str]|None=None,
                   stdin:bytes|None=None, max_time=55) -> dict[str,Any]:
    run=subprocess.run(argv,cwd=cwd,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1",
                              **(env or {})},
        input=stdin,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        timeout=max_time,check=False)
    check(len(run.stdout)<=MAX_OUTPUT and len(run.stderr)<=8192,"NATIVE_OUTPUT_TOO_LARGE")
    if run.returncode:
        raise StackFloorActHold("NATIVE_POST_OFFICE_HOLD:"+run.stderr.decode("utf8","replace")[:180])
    try:
        result=json.loads(run.stdout.decode("utf8"))
    except (UnicodeError,ValueError) as exc:
        raise StackFloorActHold("NATIVE_POST_OFFICE_NOT_JSON") from exc
    check(isinstance(result,dict),"NATIVE_POST_OFFICE_NOT_RECORD")
    return result


class StackFloorPostOffice021:
    def __init__(self, *, state_dir:Path, enabled:bool, previous:StackFloorNative020,
                 relatte_checkout:Path|None, receiver_root:Path|None):
        self.enabled=enabled
        self.previous=previous
        self.relatte_checkout=relatte_checkout
        self.receiver_root=receiver_root
        self.state_dir=state_dir
        self.db_path=state_dir/"stack-floor-021.sqlite3"
        self.outbox=state_dir/"stack-floor-021-crossings"
        self.verifier=Path(__file__).resolve().parent.parent/"scripts"/"stack-floor-021-verify.mjs"
        if enabled:
            check(previous.enabled,"PREVIOUS_NATIVE_020_NOT_ENABLED")
            check(isinstance(relatte_checkout,Path) and isinstance(receiver_root,Path),
                  "RECEIVING_WORLD_NOT_CONFIGURED")
            state_dir.mkdir(parents=True,exist_ok=True)
            with self._db() as db:
                db.execute("""CREATE TABLE IF NOT EXISTS previews(
                    nonce_hash TEXT PRIMARY KEY, ticket_id TEXT NOT NULL,
                    receipt_id TEXT NOT NULL, receipt_hash TEXT NOT NULL,
                    receiver_ref TEXT NOT NULL, expiry REAL NOT NULL,
                    consumed INTEGER NOT NULL DEFAULT 0)""")
                db.execute("""CREATE TABLE IF NOT EXISTS completed(
                    ticket_id TEXT PRIMARY KEY, crossing_id TEXT NOT NULL)""")

    def _db(self):
        return sqlite3.connect(self.db_path,timeout=20,isolation_level=None)

    def _relatte(self)->Path:
        check(self.enabled,"POST_OFFICE_DISABLED")
        relatte=_root(self.relatte_checkout,RELATTE_REPO,RELATTE_SHA)
        originals=str(_git(relatte,"ls-tree","-r","--name-only",RELATTE_SHA,"--","src","scripts")).splitlines()
        tsfiles={name for name in originals if name.endswith(".ts")}
        check("src/index.ts" in tsfiles and "src/receiver.ts" in tsfiles and
              "src/roundtrip.ts" in tsfiles and
              "scripts/opaque-roundtrip.ts" in tsfiles,
              "RELATTE_ORIGINAL_RUNTIME_MISSING")
        check(0<len(tsfiles)<=400,"RELATTE_PINNED_FILES_UNBOUNDED")
        for prefix in ("src","scripts"):
            for file in (relatte/prefix).rglob("*.ts"):
                check(not file.is_symlink() and file.relative_to(relatte).as_posix() in tsfiles,
                      "UNPINNED_RELATTE_TYPESCRIPT")
        for relative in sorted(tsfiles):
            file=relatte/relative
            check(file.is_file() and not file.is_symlink() and
                  file.read_bytes()==_git(relatte,"show",f"{RELATTE_SHA}:{relative}",binary=True),
                  "RELATTE_SOURCE_WORKTREE_CHANGED")
        return relatte

    def _ghot(self,ticket_id:str):
        check(isinstance(ticket_id,str) and TICKET.fullmatch(ticket_id) is not None,
              "INVALID_GHOT_TICKET_ID")
        ghot,_,home,context=self.previous._ready()
        self.previous._source_policy(home,context)
        show=native_process(
            [sys.executable,str(ghot/"ghot/activation_ticket.py"),"show",ticket_id],
            cwd=ghot,env={"GHOT_HOME":str(home)},max_time=30)
        ticket=show.get("ticket");receipt=show.get("receipt");result=show.get("result")
        check(isinstance(ticket,dict) and isinstance(receipt,dict) and
              isinstance(result,dict),"MISSING_GHOT_NATIVE_SIGNED_RECORD")
        desc=ticket.get("descriptor") or {}
        dest=desc.get("destination") or {}
        check(show.get("receipt_verified") is True and show.get("spent") is True and
              ticket.get("ticket_id")==ticket_id and
              ticket.get("one_operation") is True and
              ticket.get("consent_mode")=="explicit-local-ACT" and
              dest.get("app_id")=="branch-work" and
              dest.get("operation")=="hash-exact-source" and
              desc.get("context")==context and
              receipt.get("ticket_id")==ticket_id and
              receipt.get("status")=="EXECUTED" and
              receipt.get("success") is True and
              receipt.get("ticket_spent") is True and
              receipt.get("result_address")=="sha256:"+sha(result) and
              receipt.get("operation_attempted") is True and
              result.get("repository")==PLANZ_REPO and
              result.get("commit")==PLANZ_SHA and
              result.get("path")==PLANZ_PATH and
              result.get("blob_sha256")==context["sha256"] and
              result.get("operation")=="hash-exact-source" and
              result.get("branch_program_executed") is False and
              result.get("remote_effects")==0,
              "GHOT_RECEIPT_NOT_EXACT_SUCCESSFUL_SOURCE_HASH")
        check(isinstance(receipt.get("receipt_id"),str) and
              receipt.get("issuer_particular")==ticket.get("issuer_particular"),
              "GHOT_SIGNER_OR_RECEIPT_ID_MISMATCH")
        return {"ticket":ticket,"receipt":receipt,"result":result,
                "receipt_hash":sha(receipt),"source_sha256":context["sha256"]}

    def _receiver(self,relatte:Path,ticket_id:str,ghot:dict[str,Any]):
        check(isinstance(self.receiver_root,Path) and self.receiver_root.exists(),
              "RECEIVER_MUST_ALREADY_EXIST")
        root=self.receiver_root.resolve(strict=True)
        check(root.is_dir() and root!=relatte and not self.receiver_root.is_symlink(),
              "INVALID_RECEIVER_ROOT")
        policy_file=root/WORLD_POLICY
        check(policy_file.is_file() and not policy_file.is_symlink(),
              "RECEIVER_OWNER_POLICY_REQUIRED")
        try:
            policy=json.loads(policy_file.read_text("utf8"))
        except (UnicodeError,ValueError) as exc:
            raise StackFloorActHold("RECEIVER_OWNER_POLICY_INVALID") from exc
        expected={
          "schema":"workbench.stack2-021-receiver-policy/v0",
          "reviewed_for_local_hold":True,"disposition":"HOLD",
          "allowed_ticket_id":ticket_id,
          "allowed_receipt_id":ghot["receipt"]["receipt_id"],
          "allowed_ghot_signer":ghot["receipt"]["issuer_particular"],
          "receiver_world":None,
          "receiver_particular":None,
          "receiver_contract":None,
        }
        check(isinstance(policy,dict) and set(policy)==set(expected) and
              all(policy.get(k)==v for k,v in expected.items() if v is not None),
              "RECEIVER_POLICY_NOT_SPECIFIC_HOLD")
        snap=native_process(
            ["node","--experimental-strip-types",str(self.verifier),
             "receiver",str(relatte),str(root)],
            cwd=relatte,max_time=35)
        check(snap.get("schema")=="workbench.stack2-native-receiver-inspection/v0" and
              snap.get("world_id")==policy["receiver_world"] and
              snap.get("receiver_particular")==policy["receiver_particular"] and
              snap.get("contract_ref")==policy["receiver_contract"] and
              isinstance(snap.get("state_ref"),str) and
              snap.get("admitted_count")==0,
              "RECEIVER_CURRENT_STATE_NOT_OWNER_POLICY")
        return root,policy,snap

    def _already(self,ticket_id:str):
        with self._db() as db:
            check(db.execute("SELECT 1 FROM completed WHERE ticket_id=?",
                             (ticket_id,)).fetchone() is None,"ALREADY_DELIVERED")
        check(not (self.outbox/ticket_id.split(":")[-1]).exists(),
              "PREVIOUS_DELIVERY_ALREADY_PRESENT")

    def preview(self, ticket_id:str):
        relatte=self._relatte()
        ghot=self._ghot(ticket_id)
        root,policy,snap=self._receiver(relatte,ticket_id,ghot)
        self._already(ticket_id)
        nonce=secrets.token_urlsafe(32)
        with self._db() as db:
            db.execute("""INSERT INTO previews(nonce_hash,ticket_id,receipt_id,
                         receipt_hash,receiver_ref,expiry) VALUES(?,?,?,?,?,?)""",
                       (hashlib.sha256(nonce.encode()).hexdigest(),
                        ticket_id,ghot["receipt"]["receipt_id"],
                        ghot["receipt_hash"],snap["state_ref"],time.time()+TTL))
        return {
            "schema":"workbench.stack2-021-crossing-preview/v0",
            "status":"READY_TO_REQUEST_HOLD",
            "consent_nonce":nonce,"ttl_seconds":TTL,
            "ticket_id":ticket_id,"receipt_id":ghot["receipt"]["receipt_id"],
            "ghot_signature_verified":True,
            "source_sha256":ghot["source_sha256"],
            "receiver_world":policy["receiver_world"],
            "receiver_particular":policy["receiver_particular"],
            "receiver_state_ref":snap["state_ref"],
            "receiver_policy":"OWNER_SELECTED_EXACT_TICKET_HOLD",
            "disposition":"HOLD","new_permission_granted":False,
            "receiver_admitted":False,"crossing_performed":False,
        }

    def cross(self, *, ticket_id:str, nonce:str, expected_receipt_id:str,
              phrase:str, acknowledge:bool):
        check(self.enabled,"POST_OFFICE_DISABLED")
        check(isinstance(nonce,str) and re.fullmatch(r"[A-Za-z0-9_-]{30,100}",nonce),
              "INVALID_CROSSING_NONCE")
        check(isinstance(ticket_id,str) and TICKET.fullmatch(ticket_id) is not None,
              "INVALID_CROSSING_TICKET")
        check(isinstance(expected_receipt_id,str) and
              expected_receipt_id.startswith("ghot-activation-execution-receipt-v0:"),
              "INVALID_CROSSING_RECEIPT")
        check(phrase=="CROSS" and acknowledge is True,"SEPARATE_CROSS_APPROVAL_REQUIRED")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row=db.execute("""SELECT ticket_id,receipt_id,receipt_hash,receiver_ref,
                                  expiry,consumed FROM previews WHERE nonce_hash=?""",
                               (hashlib.sha256(nonce.encode()).hexdigest(),)).fetchone()
                check(row is not None and row[5]==0 and
                      row[4]>=time.time() and row[0]==ticket_id and
                      row[1]==expected_receipt_id,"PREVIEW_EXPIRED_USED_OR_CHANGED")
                check(db.execute("UPDATE previews SET consumed=1 WHERE nonce_hash=? AND consumed=0",
                      (hashlib.sha256(nonce.encode()).hexdigest(),)).rowcount==1,
                      "CROSSING_PREVIEW_ALREADY_CONSUMED")
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        # Repeat original GHoT signature, original source, receiver owner
        # policy and sovereign state before any reLATTE files are written.
        relatte=self._relatte()
        ghot=self._ghot(ticket_id)
        root,policy,snap=self._receiver(relatte,ticket_id,ghot)
        check(row[2]==ghot["receipt_hash"] and
              row[3]==snap["state_ref"],"SOURCE_OR_RECEIVER_CHANGED_AFTER_PREVIEW")
        self._already(ticket_id)
        self.outbox.mkdir(mode=0o700,exist_ok=True)
        delivery=self.outbox/ticket_id.split(":")[-1]
        delivery.mkdir(mode=0o700)
        receipt=ghot["receipt"]
        record={
            "ticket":ghot["ticket"],"execution_receipt":receipt,
            "execution_result":ghot["result"],
            "original_ghot_sha":GHOT_SHA,
            "original_planz_sha":PLANZ_SHA,
            "original_relatte_sha":RELATTE_SHA,
            "source_blob_sha256":ghot["source_sha256"],
            "original_ghot_native_signature_verified":True,
            "receiver_policy_specific_hold":True,
            "workbench_cross_authorized":True,
            "human_identity_authenticated":False,
            "external_effects":0,"donor_programs_executed":0,
        }
        recv={"world_id":policy["receiver_world"],
              "receiver_particular":policy["receiver_particular"],
              "contract_ref":policy["receiver_contract"]}
        request={
            "schema":"relatte.opaque-roundtrip-request/v0",
            "spec":{
                "schema":"relatte.opaque-organ-spec/v0",
                "family_ref":"organ:stack-squared/post-office-021",
                "donor_contract_ref":"ghot.branch-worker@0",
                "artifact_kind":"original-ghot-030-signed-source-hash-execution",
                "source_world":"world:stack-squared-021-workbench",
                "source_particular":"particular:workbench-stack2-021-sender",
                "source_history_head":"sha256:"+ghot["receipt_hash"],
                "payload_refs":[
                    {"address":"sha256:"+ghot["receipt_hash"],
                     "role":"original-signed-ghot-execution-receipt",
                     "media_type":"application/json"},
                    {"address":"sha256:"+ghot["source_sha256"],
                     "role":"verified-original-planz-source","media_type":"text/javascript"},
                ],
                "donor_claims":record,
                "requested_effect":{"kind":"candidate-ingress",
                                    "authority":"receiver-local",
                                    "execution_authorized":False},
                "return_address":"return:workbench/stack-squared-021",
                "created_at":stamp(),
            },
            "receiver_root":str(root),"receiver":recv,
            "bundle_path":str(delivery/"transport.json"),
            "result_path":str(delivery/"roundtrip-result.json"),
            "disposition":"HOLD",
            "transport_created_at":stamp(1),"received_at":stamp(2),
            "disposed_at":stamp(3),
            "route_note":"GHoT 030 signed receipt to receiver-owned native HOLD; no ADMIT",
        }
        (delivery/"request.json").write_text(json.dumps(request,indent=2)+"\n",
                                              encoding="utf8")
        native=native_process(
            ["node","--experimental-strip-types",
             str(relatte/"scripts/opaque-roundtrip.ts")],
            cwd=relatte,stdin=exact_json(request),max_time=65)
        check(native.get("schema")=="relatte.opaque-roundtrip-result/v0",
              "NATIVE_RELATTE_ROUNDTRIP_NOT_FINISHED")
        proof=native_process(
            ["node","--experimental-strip-types",str(self.verifier),
             "verify",str(relatte),str(root),str(delivery/"request.json"),
             str(delivery/"roundtrip-result.json")],
            cwd=relatte,max_time=35)
        check(proof.get("status")=="CROSSING_RECEIVED_AND_HELD" and
              proof.get("signatures_cold_verified")==3 and
              proof.get("receiver_admitted") is False,
              "NATIVE_COLD_VERIFICATION_REFUSED")
        with self._db() as db:
            db.execute("INSERT INTO completed(ticket_id,crossing_id) VALUES(?,?)",
                       (ticket_id,proof["crossing_id"]))
        return {
            "schema":"workbench.stack2-021-post-office-result/v0",
            "status":"RECEIVED_AND_HELD","ticket_id":ticket_id,
            "original_ghot_receipt_id":expected_receipt_id,
            "crossing_id":proof["crossing_id"],
            "native_relatte_receive_receipt_id":proof["receive_receipt_id"],
            "native_relatte_hold_receipt_id":proof["hold_receipt_id"],
            "receiver_world":policy["receiver_world"],
            "receiver_state_ref":proof["receiver_state_ref"],
            "ghot_signature_verified":True,"relatte_signatures_verified":3,
            "receiver_admitted":False,"disposition":"HOLD",
            "real_world_effects":"local_receiver_journal_RECEIVE_AND_HOLD_ONLY",
            "remote_effects":0,"source_programs_executed":0,
            "sender_identity_authenticated":False,
            "foreign_admission_authorized":False,
            "signed_original_ghot_execution_receipt":ghot["receipt"],
            "native_signed_crossing":native["crossing"],
            "native_signed_receive_receipt":native["receive_receipt"],
            "native_signed_hold_receipt":native["disposition_receipt"],
        }
