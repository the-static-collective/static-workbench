"""WEBZ-003 — transport *actual bytes* to independently executing Orchard receiver.

Deliberate second material gate AFTER WEBZ-RELATTE-002's signed envelope.
The destination process and signing key are owned by exact pinned reLATTE.
No automatic dispatch on browse, inspect, no-carry Cross, or any GET.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .field_reseed_crossing import (
    FieldReseedCrossingError, _find_pinned, _run_json,
)
from .webz_parcel import (
    WEBZ_RELATTE_REVISION,
    ORCHARD, SANCTUARY, POLICY, WebzParcelError, WebzParcelGate,
    _read_exact, _local_json, _atomic_bytes, _valid_identity,
)
from .repos import RepoStatus

CUSTODY_RELATTE_REVISION = WEBZ_RELATTE_REVISION
RECEIVER_PARTICULAR = "particular:webz:orchard-local-inbox"
CONFIRMATION = "DELIVER_VERIFIED_BYTES"


class WebzCustodyError(ValueError):
    """Custody was not established or local evidence is corrupted."""


def _known(kind: str) -> None:
    if not isinstance(kind,str) or kind not in POLICY:
        raise WebzCustodyError("unknown first-party material kind")


class WebzCustodyGate:
    """Additive byte-transport gate, sharing the existing parent's local mutex."""

    def __init__(self, parent: WebzParcelGate):
        self.parent = parent
        self.root = parent.root
        self.lock = parent.lock

    def _prior(self, kind: str) -> tuple[dict, dict, bytes, str, str]:
        _known(kind)
        _, raw, digest, policy = self.parent._fixture(kind)
        # A missing initial signed result is a normal NOT_READY preview, not
        # a corrupt material-delivery attempt. GET must remain side-effect-free.
        try:
            summary = self.parent._stored(kind,digest,raw)
        except WebzParcelError as exc:
            raise WebzCustodyError(f"source staged bytes or parent receipt invalid: {exc}") from exc
        if summary is None:
            raise WebzCustodyError("no signed WEBZ-002 envelope; first explicitly offer the material")
        # After the parent crossing exists, independently recheck exact sender
        # staging, even if a mocked/legacy parent summary was presented.
        try:
            staged = _read_exact(self.parent._staged_path(kind,digest), limit=4096)
        except WebzParcelError as exc:
            raise WebzCustodyError(f"source staged bytes unavailable: {exc}") from exc
        if staged != raw or hashlib.sha256(staged).hexdigest() != digest:
            raise WebzCustodyError("source staged bytes SHA digest mismatch")
        try:
            proof = self.parent.proof(kind)
        except WebzParcelError as exc:
            raise WebzCustodyError(f"signed source envelope unavailable: {exc}") from exc
        crossing = proof.get("crossing")
        if (
            not isinstance(crossing,dict)
            or crossing.get("crossing_id") != summary.get("crossing_id")
            or proof.get("artifact_sha256") != digest
            or not isinstance(crossing.get("payload_refs"),list)
            or not any(
                isinstance(ref,dict) and ref.get("address") == "sha256:"+digest
                for ref in crossing["payload_refs"]
            )
            or summary.get("receiver_disposition") != policy
            or summary.get("admitted") is not False
        ):
            raise WebzCustodyError("source envelope does not match exact first-party bytes")
        return summary, proof, raw, digest, policy

    def preview(self, kind: str) -> dict:
        _known(kind)
        source=self.parent.preview(kind)
        data={
            "schema":"workbench.webz-custody-preview/v0",
            "kind":kind,
            "artifact_sha256":source["artifact_sha256"],
            "source_world_id":SANCTUARY,
            "destination_world_id":ORCHARD,
            "receiver_policy":source["policy"],
            "carry_mode":"explicit-material-bytes-only",
            "pinned_owner":CUSTODY_RELATTE_REVISION,
            "admitted":False,
        }
        with self.lock:
            try:
                summary,proof,raw,digest,policy=self._prior(kind)
            except WebzCustodyError as exc:
                if "no signed WEBZ-002 envelope" in str(exc):
                    return {**data,"status":"NOT_READY","ready":False,
                        "reason":"First explicitly SEND the fictional artifact through WEBZ-002."}
                raise
            stored=self._stored(kind,digest,raw,summary,policy)
            return {**data,"status":"ALREADY_VERIFIED" if stored else "READY",
                "ready":True,"crossing_id":summary["crossing_id"],
                "custody_receipt_id":stored["custody_receipt_id"] if stored else None}

    def _carrier_path(self,kind: str,digest: str) -> Path:
        return self.root/"material-carriers"/f"{kind}-{digest}.json"

    def _result_path(self,kind: str,digest: str) -> Path:
        return self.root/"material-results"/f"{kind}-{digest}.json"

    def _summary_path(self,kind: str,digest: str) -> Path:
        return self.root/"material-summaries"/f"{kind}-{digest}.json"

    def _verified_receiver_payload(self, kind: str, digest: str, raw: bytes, policy: str, crossing_id: str) -> None:
        # The destination's LOCAL receiver owns the retained file. Check again
        # whenever a stored summary is presented; otherwise never claim live custody.
        file=self.root/"orchard-receiver"/"payloads"/(crossing_id+".bin")
        if policy=="HOLD":
            try:
                received=_read_exact(file,limit=65536)
            except WebzParcelError as exc:
                raise WebzCustodyError("receiver-local retained bytes unavailable or corrupt") from exc
            if received!=raw or hashlib.sha256(received).hexdigest()!=digest:
                raise WebzCustodyError("receiver-local retained bytes digest mismatch")
        elif file.exists() or file.is_symlink():
            raise WebzCustodyError("REFUSE receiver improperly retained source bytes")

    def _validate_owner(self,result: dict, kind: str,raw: bytes,digest: str,policy: str,parent: dict) -> dict:
        if not isinstance(result,dict):
            raise WebzCustodyError("receiver process produced no material evidence")
        receipt=result.get("custody_receipt")
        receive=result.get("receive_receipt")
        disposition=result.get("disposition_receipt")
        snapshot=result.get("receiver_snapshot")
        if not all(isinstance(x,dict) for x in (receipt,receive,disposition,snapshot)):
            raise WebzCustodyError("incomplete signed receiver material evidence")
        custody=receipt.get("extensions",{}).get("local_receiver",{}).get("payload_custody",{})
        retained=(policy=="HOLD")
        key=receipt.get("signing",{}).get("public_key")
        if (
            result.get("schema")!="relatte.material-delivery-result/v0"
            or result.get("crossing_id")!=parent["crossing_id"]
            or result.get("receiver_world_id")!=ORCHARD
            or result.get("payload_sha256")!=digest
            or result.get("received_byte_length")!=len(raw)
            or result.get("receiver_disposition")!="R3_"+policy
            or result.get("retained") is not retained
            or receipt.get("schema")!="relatte.receipt/v0"
            or receipt.get("kind")!="PAYLOAD_BYTES_VERIFIED"
            or receipt.get("semantic_effect")!="none"
            or not _valid_identity(receipt.get("receipt_id"),"relatte-receipt-v0:")
            or receipt.get("crossing_id")!=parent["crossing_id"]
            or receipt.get("world_id")!=ORCHARD
            or receipt.get("receiver_particular")!=RECEIVER_PARTICULAR
            or not isinstance(key,dict) or key.get("kty")!="EC"
            or receive.get("receipt_id")!=parent["receive_receipt_id"]
            or disposition.get("receipt_id")!=parent["disposition_receipt_id"]
            or receive.get("crossing_id")!=parent["crossing_id"]
            or disposition.get("crossing_id")!=parent["crossing_id"]
            or disposition.get("kind")!="R3_"+policy
            or snapshot.get("admitted")!=[]
            or parent["crossing_id"] not in snapshot.get("held" if retained else "refused",[])
            or not isinstance(custody,dict)
            or custody.get("sha256")!=digest
            or custody.get("byte_length")!=len(raw)
            or custody.get("disposition")!=policy
            or custody.get("retained") is not retained
            or custody.get("receive_receipt_id")!=parent["receive_receipt_id"]
            or custody.get("disposition_receipt_id")!=parent["disposition_receipt_id"]
        ):
            raise WebzCustodyError("receiver custody evidence does not bind exact signed bytes/disposition")
        for name in ("receive_receipt","disposition_receipt"):
            other=result[name].get("signing",{}).get("public_key")
            if other!=key:
                raise WebzCustodyError("custody receipt was not signed by the receiver's existing key")
        return {
            "schema":"workbench.webz-material-custody/v0",
            "kind":kind,
            "artifact_sha256":digest,
            "source_world_id":SANCTUARY,
            "destination_world_id":ORCHARD,
            "crossing_id":parent["crossing_id"],
            "receiver_disposition":policy,
            "status":"BYTES_VERIFIED_AND_HELD" if retained else "BYTES_VERIFIED_AND_REFUSED",
            "retained":retained,
            "admitted":False,
            "semantic_effect":"none",
            "received_byte_length":len(raw),
            "receive_receipt_id":parent["receive_receipt_id"],
            "disposition_receipt_id":parent["disposition_receipt_id"],
            "custody_receipt_id":receipt["receipt_id"],
            "pinned_relatte":CUSTODY_RELATTE_REVISION,
            "witness_scope":"receiver-process-signed-actual-payload-bytes;local-file-carrier;no-admission",
        }

    def _stored(self,kind: str,digest: str,raw: bytes,parent: dict,policy: str) -> dict|None:
        path=self._summary_path(kind,digest)
        if not path.exists() and not path.is_symlink():
            return None
        summary=_local_json(path,"webZ custody summary")
        result=_local_json(self._result_path(kind,digest),"webZ custody result",limit=256000)
        expected=self._validate_owner(result,kind,raw,digest,policy,parent)
        if summary!=expected:
            raise WebzCustodyError("local custody summary conflicts with signed owner output")
        self._verified_receiver_payload(kind,digest,raw,policy,parent["crossing_id"])
        return summary

    def deliver(self,kind: str,expected_sha256: str,expected_crossing_id: str,
                confirmation: str,repos: list[RepoStatus]) -> dict:
        _known(kind)
        if confirmation!=CONFIRMATION or not isinstance(expected_sha256,str) or (
            not _valid_identity(expected_crossing_id,"relatte-crossing-v0:")
        ):
            raise WebzCustodyError("explicit custody confirmation and exact crossing ID required")
        with self.lock:
            parent,proof,raw,digest,policy=self._prior(kind)
            if expected_sha256!=digest or expected_crossing_id!=parent["crossing_id"]:
                raise WebzCustodyError("stale or unrecognized signed source bytes / crossing ID")
            try:
                owner=_find_pinned(
                    repos,"reLATTE",CUSTODY_RELATTE_REVISION,
                    "scripts/material-delivery.ts",
                )
            except FieldReseedCrossingError as exc:
                raise WebzCustodyError(f"pinned receiver owner unavailable: {exc}") from exc
            existing=self._stored(kind,digest,raw,parent,policy)
            if existing is not None:
                return existing
            carrier={
                "schema":"webz.material-carrier/v0",
                "crossing":proof["crossing"],
                "payload_base64":base64.b64encode(raw).decode("ascii"),
            }
            blob=(json.dumps(carrier,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
            carrier_path=self._carrier_path(kind,digest)
            if carrier_path.exists() or carrier_path.is_symlink():
                if _read_exact(carrier_path,limit=110000)!=blob:
                    raise WebzCustodyError("existing material carrier bytes conflict with current signed source")
            else:
                _atomic_bytes(carrier_path,blob)
            request={
                "schema":"relatte.material-delivery/v0",
                "carrier_path":str(carrier_path.resolve()),
                "receiver_root":str((self.root/"orchard-receiver").resolve()),
                "expected_crossing_id":parent["crossing_id"],
                "created_at":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z",
            }
            # Explicit, bounded destination-side process; no source fixture path
            # or caller-controlled receiver decision is passed to the owner.
            try:
                result=_run_json(
                    ["node","--experimental-strip-types",str(owner/"scripts"/"material-delivery.ts")],
                    owner,request,{**os.environ,"LC_ALL":"C"},
                    "pinned reLATTE Orchard custody receiver",timeout=30.0,
                )
            except (FieldReseedCrossingError,OSError) as exc:
                raise WebzCustodyError(f"destination byte-custody outcome unknown or refused: {exc}") from exc
            summary=self._validate_owner(result,kind,raw,digest,policy,parent)
            # Physical held bytes are verified *after* the independent process,
            # not manufactured by the Workbench adapter.
            self._verified_receiver_payload(kind,digest,raw,policy,parent["crossing_id"])
            _atomic_bytes(self._result_path(kind,digest),
                (json.dumps(result,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8"))
            _atomic_bytes(self._summary_path(kind,digest),
                (json.dumps(summary,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8"))
            return summary

    def inbox(self) -> list[dict]:
        with self.lock:
            rows=[]
            for kind in POLICY:
                _,raw,digest,_=self.parent._fixture(kind)
                path=self._summary_path(kind,digest)
                if not path.exists() and not path.is_symlink():
                    continue
                parent,proof,raw,digest,policy=self._prior(kind)
                stored=self._stored(kind,digest,raw,parent,policy)
                if stored is not None:
                    rows.append(stored)
            return rows

    def proof(self,kind: str) -> dict:
        with self.lock:
            parent,prior,raw,digest,policy=self._prior(kind)
            if self._stored(kind,digest,raw,parent,policy) is None:
                raise WebzCustodyError("no Orchard byte-custody receipt for this material")
            result=_local_json(self._result_path(kind,digest),"webZ custody result",limit=256000)
            return {
                "schema":"workbench.webz-byte-custody-proof/v0",
                "kind":kind,
                "source_proof":prior,
                "destination_proof":result,
                "witness_scope":"exact-owner-signed-receiver-custody;local-process-only;not-remote-identity",
            }
