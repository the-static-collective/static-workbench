#!/usr/bin/env python3
"""WEBZ-003: compatible R14 signed sender → material carrier → separate receiver process.

No synthetic crypto, mocked signatures, external files or third-party artifacts.
The destination is a separate Node process which reads the literal carrier bytes.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from static_workbench.webz_parcel import WEBZ_RELATTE_REVISION
from static_workbench.repos import RepoStatus
from static_workbench.webz_parcel import WebzParcelGate
from static_workbench.webz_custody import WebzCustodyGate,CUSTODY_RELATTE_REVISION,WebzCustodyError

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/".compat"/"reLATTE"
NEW=ROOT/".compat"/"custody"/"reLATTE"


def repo(path: Path, sha: str) -> RepoStatus:
    return RepoStatus(
        name="reLATTE",path=str(path),branch=None,detached=True,
        head=sha[:7],dirty=False,ahead=None,behind=None,
    )


def verify_signatures(crossing: dict, receive: dict, disposition: dict) -> None:
    packet={"crossing":crossing,"receive_receipt":receive,"disposition_receipt":disposition}
    proc=subprocess.run(
        ["node","--experimental-strip-types",str(ROOT/"scripts"/"webz_verify_relatte.mjs")],
        cwd=ROOT,env={**os.environ,"RELATTE_ROOT":str(NEW),"LC_ALL":"C"},
        input=json.dumps(packet),text=True,capture_output=True,check=False,timeout=25,
    )
    assert proc.returncode==0,proc.stderr[-1400:]
    result=json.loads(proc.stdout)
    assert result=={"crossing_verified":True,"receive_verified":True,"disposition_verified":True},result


def main() -> int:
    assert (NEW/"scripts"/"opaque-roundtrip.ts").is_file(),"missing compatible pinned R14 envelope owner"
    assert (NEW/"scripts"/"material-delivery.ts").is_file(),"missing exact new custody owner"
    with tempfile.TemporaryDirectory(prefix="webz-003-real-byte-custody-") as td:
        parent=WebzParcelGate(Path(td)/"state")
        custody=WebzCustodyGate(parent)
        assert custody.inbox()==[]
        assert custody.preview("fruit")["status"]=="NOT_READY"
        old_roots=[repo(NEW,WEBZ_RELATTE_REVISION)]
        new_roots=[repo(NEW,CUSTODY_RELATTE_REVISION)]
        for kind, expected in (("fruit","HOLD"),("spore","REFUSE")):
            source=parent.preview(kind)
            sent=parent.send(kind,source["artifact_sha256"],"SEND_TO_ORCHARD",old_roots)
            assert sent["receiver_disposition"]==expected
            ready=custody.preview(kind)
            assert ready["status"]=="READY" and ready["crossing_id"]==sent["crossing_id"]
            received=custody.deliver(kind,source["artifact_sha256"],sent["crossing_id"],
                                    "DELIVER_VERIFIED_BYTES",new_roots)
            assert received["schema"]=="workbench.webz-material-custody/v0"
            assert received["status"]==("BYTES_VERIFIED_AND_HELD" if expected=="HOLD"
                                       else "BYTES_VERIFIED_AND_REFUSED")
            assert received["admitted"] is False
            assert received["retained"] is (expected=="HOLD")
            proof=custody.proof(kind)
            origin=proof["source_proof"]
            destination=proof["destination_proof"]
            verify_signatures(origin["crossing"],origin["receive_receipt"],origin["disposition_receipt"])
            verify_signatures(origin["crossing"],destination["receive_receipt"],destination["custody_receipt"])
            assert destination["receiver_snapshot"]["admitted"]==[]
            assert destination["custody_receipt"]["signing"]["public_key"]==origin["receive_receipt"]["signing"]["public_key"]
            staged=parent._staged_path(kind,source["artifact_sha256"]).read_bytes()
            assert hashlib.sha256(staged).hexdigest()==source["artifact_sha256"]
            receiver_file=parent.root/"orchard-receiver"/"payloads"/(sent["crossing_id"]+".bin")
            if expected=="HOLD":
                assert receiver_file.read_bytes()==staged
            else:
                assert not receiver_file.exists()
            cold=WebzCustodyGate(WebzParcelGate(Path(td)/"state"))
            repeated=cold.deliver(kind,source["artifact_sha256"],sent["crossing_id"],
                                  "DELIVER_VERIFIED_BYTES",new_roots)
            assert repeated==received
            assert cold.preview(kind)["status"]=="ALREADY_VERIFIED"
            print(f"WEBZ-003 {kind}: OWNER SIGNED BYTES {expected}, identity {received['custody_receipt_id']}; cold replay matched")

        assert len(custody.inbox())==2
        # Mutate carrier bytes only; envelope signature still valid. The
        # destination process must reject byte/hash mismatch independently.
        source=parent.preview("spore")
        crossing=parent.inbox()[1]["crossing_id"]
        carrier_path=custody._carrier_path("spore",source["artifact_sha256"])
        actual=json.loads(carrier_path.read_text())
        actual["payload_base64"]=base64.b64encode(b'{"fake":true}').decode("ascii")
        carrier_path.write_text(json.dumps(actual))
        intent={
            "schema":"relatte.material-delivery/v0",
            "carrier_path":str(carrier_path.resolve()),
            "receiver_root":str((parent.root/"orchard-receiver").resolve()),
            "expected_crossing_id":crossing,
            "created_at":"2026-10-07T04:58:00.000Z",
        }
        failed=subprocess.run(
            ["node","--experimental-strip-types",str(NEW/"scripts"/"material-delivery.ts")],
            cwd=NEW,env={**os.environ,"LC_ALL":"C"},
            input=json.dumps(intent),text=True,capture_output=True,check=False,timeout=25,
        )
        assert failed.returncode!=0, "destination incorrectly accepted forged material carrier"
        assert "MATERIAL_BYTES_NOT_BOUND_TO_SIGNED_CROSSING" in failed.stderr,failed.stderr[-600:]
        print("WEBZ-003 negative: tampered carrier bytes refused even with original signed envelope")

        # Mutate retained bytes after receipt. The locally independent receiver
        # should no longer be counted as holding *valid* material.
        held=parent.inbox()[0]
        fruit=parent.preview("fruit")
        held_file=parent.root/"orchard-receiver"/"payloads"/(held["crossing_id"]+".bin")
        original=held_file.read_bytes()
        held_file.write_bytes(b"mutated")
        try:
            try:
                custody.inbox()
            except WebzCustodyError as exc:
                assert "digest" in str(exc),str(exc)
            else:
                raise AssertionError("tampered destination custody remained visible as verified")
        finally:
            held_file.write_bytes(original)
        assert len(custody.inbox())==2
        print("WEBZ-003 negative: post-receipt retained material mutation detected on read")

    print("WEBZ-003 PASS: separate destination process, original signed crossing, actual byte acquisition, receiver-key signed custody, HOLD/REFUSE, cold replay and tamper refusal.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
