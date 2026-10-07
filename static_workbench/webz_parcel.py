"""WEBZ-RELATTE-002 — first signed, *fixture-only* sovereign parcel.

WorkBench controls the explicit human offer, fixed source bytes and a local
display. The pinned reLATTE owner seals crossing/receiver receipts. The Orchard
policy is fixed here, independently of any parameter supplied by the sender.

Crucially: signed reLATTE RECEIVE covers the crossing envelope and payload
digest reference. Workbench separately stages/verifies the exact JSON bytes.
Neither a HOLD nor a REFUSE admits content into an inhabited world.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .field_reseed_crossing import (
    FieldReseedCrossingError,
    _find_pinned,
    _run_json,
)
from .repos import RepoStatus


# WEBZ-003 upgrades only the webZ receiver lineage to the additive owner.
# Field Reseed and other Workbench adapters keep their earlier R14 pin.
WEBZ_RELATTE_REVISION = "103c03c745968bfe2105167fa9007fab8906fc71"

SANCTUARY = "webz:the-static-collective/sanctuary"
ORCHARD = "webz:the-static-collective/orchard-022100"
POLICY = {
    "fruit": ("fictional-reality-fruit", "HOLD"),
    "spore": ("fictional-uninvited-spore", "REFUSE"),
}
FIXTURE_FIELDS = {
    "schema", "artifact_kind", "world_id", "title", "description",
    "fictional", "publication_scope", "seed",
}
RECEIVER_PARTICULAR = "particular:webz:orchard-local-inbox"
RECEIVER_CONTRACT = "contract:webz:orchard-fixture-inbox/v0"
DONOR_FAMILY = "organ:static-workbench/webz-fictional-parcel"
SHA_RE = re.compile(r"[a-f0-9]{64}\Z", re.ASCII)


class WebzParcelError(ValueError):
    """A proposed fictional parcel or its accountable transport was refused."""


def _read_exact(path: Path, *, limit: int = 128_000) -> bytes:
    try:
        if path.is_symlink():
            raise WebzParcelError("unsafe local parcel file")
        if path.stat().st_size > limit:
            raise WebzParcelError("local parcel file exceeds size limit")
        return path.read_bytes()
    except OSError as exc:
        raise WebzParcelError("local parcel file unavailable") from exc


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise WebzParcelError("unsafe local parcel file")
    name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=".webz-", delete=False,
        ) as handle:
            name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def _utc_stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _object(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise WebzParcelError(f"{label} must be an object")
    return value


def _local_json(path: Path, label: str, *, limit: int = 128_000) -> dict:
    try:
        return _object(json.loads(_read_exact(path, limit=limit).decode("utf-8")), label)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WebzParcelError(f"stored {label} JSON is corrupt; no reconstruction was inferred") from exc


def _valid_identity(value: Any, prefix: str) -> bool:
    return (
        isinstance(value, str) and value.startswith(prefix)
        and bool(SHA_RE.fullmatch(value[len(prefix):]))
    )


class WebzParcelGate:
    """One instance per Workbench app. Serialize a bounded local first-party bridge."""

    def __init__(self, state_dir: Path, web_dir: Path | None = None):
        self.root = Path(state_dir) / "webz-relatte" / "v0"
        self.web_dir = Path(web_dir) if web_dir is not None else Path(__file__).resolve().parent / "web"
        self.lock = threading.RLock()

    def _fixture(self, kind: str) -> tuple[dict, bytes, str, str]:
        if not isinstance(kind, str) or kind not in POLICY:
            raise WebzParcelError("unknown first-party parcel kind")
        raw = _read_exact(self.web_dir / f"webz-{kind}.json", limit=4096)
        try:
            data = _object(json.loads(raw.decode("utf-8")), "fixture")
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WebzParcelError("first-party parcel fixture is invalid") from exc
        declared_kind, policy = POLICY[kind]
        if (
            set(data) != FIXTURE_FIELDS
            or data.get("schema") != "webz.artifact/v0"
            or data.get("artifact_kind") != declared_kind
            or data.get("world_id") != SANCTUARY
            or data.get("fictional") is not True
            or data.get("publication_scope") != "public-first-party-test-fixture"
            or data.get("seed") != "022100"
            or not isinstance(data.get("title"), str)
            or not 1 <= len(data["title"]) <= 120
            or not isinstance(data.get("description"), str)
            or not 1 <= len(data["description"]) <= 500
        ):
            raise WebzParcelError("first-party parcel identity or provenance changed")
        return data, raw, hashlib.sha256(raw).hexdigest(), policy

    def preview(self, kind: str) -> dict:
        data, raw, digest, policy = self._fixture(kind)
        return {
            "schema": "workbench.webz-parcel-preview/v0",
            "kind": kind,
            "title": data["title"],
            "description": data["description"],
            "artifact_kind": data["artifact_kind"],
            "artifact_sha256": digest,
            "artifact_bytes": len(raw),
            "source_world_id": SANCTUARY,
            "destination_world_id": ORCHARD,
            "carry_mode": "explicit-synthetic-artifact",
            "policy": policy,
            "admission": "not-authorized",
            "relatte_pin": WEBZ_RELATTE_REVISION,
            "law": "PREVIEW != OFFER; RECEIVE != ADMIT",
        }

    def _staged_path(self, kind: str, digest: str) -> Path:
        return self.root / "staged" / f"{kind}-{digest}.json"

    def _intent_path(self, kind: str) -> Path:
        return self.root / "intents" / f"{kind}.json"

    def _summary_path(self, kind: str) -> Path:
        return self.root / "summaries" / f"{kind}.json"

    def _intent(self, kind: str, digest: str) -> str:
        """Durable human-selected first occurrence time; never silently redate a retry."""
        path = self._intent_path(kind)
        if path.exists() or path.is_symlink():
            saved = _local_json(path, "intent")
            if (
                set(saved) != {"schema", "kind", "artifact_sha256", "created_at"}
                or saved["schema"] != "workbench.webz-parcel-intent/v0"
                or saved["kind"] != kind or saved["artifact_sha256"] != digest
                or not isinstance(saved["created_at"], str)
            ):
                raise WebzParcelError("stored parcel intent conflicts with current fixture")
            try:
                datetime.strptime(saved["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError as exc:
                raise WebzParcelError("stored parcel intent timestamp is invalid") from exc
            return saved["created_at"]
        stamp = _utc_stamp(datetime.now(timezone.utc))
        body = {
            "schema": "workbench.webz-parcel-intent/v0",
            "kind": kind, "artifact_sha256": digest, "created_at": stamp,
        }
        _atomic_bytes(path, (json.dumps(body, separators=(",", ":")) + "\n").encode("utf-8"))
        return stamp

    def _request(self, kind: str, digest: str, created_at: str) -> dict:
        dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        stamps = [_utc_stamp(dt + timedelta(milliseconds=i)) for i in range(1, 4)]
        policy = POLICY[kind][1]
        route = f"{kind}-{digest}"
        return {
            "schema": "relatte.opaque-roundtrip-request/v0",
            "spec": {
                "schema": "relatte.opaque-organ-spec/v0",
                "family_ref": DONOR_FAMILY,
                "donor_contract_ref": (
                    "github:the-static-collective/static-workbench#"
                    "docs/superpowers/specs/2026-10-06-webz-relatte-002-first-sovereign-parcel.md"
                ),
                "artifact_kind": POLICY[kind][0],
                "source_world": SANCTUARY,
                "source_particular": f"particular:webz:fixture:{kind}:sha256:{digest}",
                "source_history_head": None,
                "payload_refs": [{
                    "address": f"sha256:{digest}",
                    "role": "fictional-first-party-artifact",
                    "media_type": "application/json",
                }],
                "donor_claims": {
                    "source_world_id": SANCTUARY,
                    "destination_world_id": ORCHARD,
                    "fictional": True,
                    "artifact_kind": POLICY[kind][0],
                    "artifact_sha256": digest,
                    "fixture_only": True,
                    "sender_controls_disposition": False,
                },
                "requested_effect": {
                    "kind": "candidate-world-parcel-ingress",
                    "authority": "orchard-receiver-local",
                },
                "return_address": "webz::static/sanctuary",
                "created_at": created_at,
            },
            "receiver_root": str(self.root / "orchard-receiver"),
            "receiver": {
                "world_id": ORCHARD,
                "receiver_particular": RECEIVER_PARTICULAR,
                "contract_ref": RECEIVER_CONTRACT,
            },
            "bundle_path": str(self.root / "bundles" / (route + ".json")),
            "result_path": str(self.root / "results" / (route + ".json")),
            "disposition": policy,
            "transport_created_at": stamps[0],
            "received_at": stamps[1],
            "disposed_at": stamps[2],
            "route_note": "webZ first-party fictional parcel; fixed Orchard receiver policy",
        }

    def _verify_result(self, result: dict, req: dict, kind: str, digest: str) -> dict:
        if result.get("schema") != "relatte.opaque-roundtrip-result/v0":
            raise WebzParcelError("reLATTE returned the wrong result schema")
        crossing = _object(result.get("crossing"), "signed crossing")
        received = _object(result.get("receive_receipt"), "signed RECEIVE")
        disposition = _object(result.get("disposition_receipt"), "signed disposition")
        snapshot = _object(result.get("receiver_snapshot"), "receiver snapshot")
        crossing_id = crossing.get("crossing_id")
        policy = POLICY[kind][1]
        expected_status = "RECEIVED_THEN_HELD" if policy == "HOLD" else "RECEIVED_THEN_REFUSED"
        adapter = _object(_object(crossing.get("extensions"), "crossing extensions").get("organ_adapter"), "organ adapter")
        claims = _object(adapter.get("donor_claims"), "donor claims")
        if (
            not _valid_identity(crossing_id, "relatte-crossing-v0:")
            or crossing.get("schema") != "relatte.crossing-envelope/v0"
            or crossing.get("source_world") != SANCTUARY
            or crossing.get("source_particular") != req["spec"]["source_particular"]
            or crossing.get("declared_kind") != "OPAQUE_ORGAN_ARTIFACT"
            or crossing.get("payload_refs") != req["spec"]["payload_refs"]
            or crossing.get("requested_effect") != req["spec"]["requested_effect"]
            or adapter.get("family_ref") != DONOR_FAMILY
            or adapter.get("artifact_kind") != req["spec"]["artifact_kind"]
            or claims != req["spec"]["donor_claims"]
            or received.get("schema") != "relatte.receipt/v0"
            or disposition.get("schema") != "relatte.receipt/v0"
            or not _valid_identity(received.get("receipt_id"), "relatte-receipt-v0:")
            or not _valid_identity(disposition.get("receipt_id"), "relatte-receipt-v0:")
            or received.get("crossing_id") != crossing_id
            or disposition.get("crossing_id") != crossing_id
            or received.get("world_id") != ORCHARD
            or disposition.get("world_id") != ORCHARD
            or received.get("receiver_particular") != RECEIVER_PARTICULAR
            or disposition.get("receiver_particular") != RECEIVER_PARTICULAR
            or received.get("kind") != "RECEIVED"
            or received.get("semantic_effect") != "none"
            or disposition.get("kind") != "R3_" + policy
            or disposition.get("semantic_effect") != "none"
            or snapshot.get("schema") != "relatte.local-receiver-snapshot/v0"
            or snapshot.get("world_id") != ORCHARD
            or crossing_id in snapshot.get("admitted", [])
            or crossing_id not in snapshot.get("held" if policy == "HOLD" else "refused", [])
        ):
            raise WebzParcelError("reLATTE crossing or Orchard local disposition mismatch")
        return {
            "schema": "workbench.webz-parcel-result/v0",
            "kind": kind,
            "artifact_sha256": digest,
            "source_world_id": SANCTUARY,
            "destination_world_id": ORCHARD,
            "receiver_disposition": policy,
            "status": expected_status,
            "semantic_effect": "none",
            "admitted": False,
            "crossing_id": crossing_id,
            "receive_receipt_id": received["receipt_id"],
            "disposition_receipt_id": disposition["receipt_id"],
            "receiver_state_ref": snapshot.get("state_ref"),
            "relatte_revision": WEBZ_RELATTE_REVISION,
            "witness_scope": "signed-reLATTE-envelope-and-receipts-plus-local-byte-digest",
        }

    def _verify_stage(self, kind: str, digest: str, raw: bytes) -> None:
        path = self._staged_path(kind, digest)
        if path.exists() or path.is_symlink():
            staged = _read_exact(path, limit=4096)
            if hashlib.sha256(staged).hexdigest() != digest or staged != raw:
                raise WebzParcelError("staged parcel digest no longer matches the source")
        else:
            _atomic_bytes(path, raw)
            if hashlib.sha256(_read_exact(path, limit=4096)).hexdigest() != digest:
                raise WebzParcelError("staged parcel digest failed verification")

    def _stored(self, kind: str, digest: str, raw: bytes) -> dict | None:
        path = self._summary_path(kind)
        if not path.exists() and not path.is_symlink():
            return None
        row = _local_json(path, "stored parcel summary")
        expected = self._verify_summary(row, kind, digest, raw)
        return expected

    def _verify_summary(self, row: dict, kind: str, digest: str, raw: bytes) -> dict:
        staged = _read_exact(self._staged_path(kind, digest), limit=4096)
        if hashlib.sha256(staged).hexdigest() != digest or staged != raw:
            raise WebzParcelError("staged parcel digest no longer matches the source")
        policy = POLICY[kind][1]
        if (
            row.get("schema") != "workbench.webz-parcel-result/v0"
            or row.get("kind") != kind
            or row.get("artifact_sha256") != digest
            or row.get("source_world_id") != SANCTUARY
            or row.get("destination_world_id") != ORCHARD
            or row.get("receiver_disposition") != policy
            or row.get("status") != ("RECEIVED_THEN_HELD" if policy == "HOLD" else "RECEIVED_THEN_REFUSED")
            or row.get("admitted") is not False
            or row.get("semantic_effect") != "none"
            or not _valid_identity(row.get("crossing_id"), "relatte-crossing-v0:")
            or not _valid_identity(row.get("receive_receipt_id"), "relatte-receipt-v0:")
            or not _valid_identity(row.get("disposition_receipt_id"), "relatte-receipt-v0:")
            or row.get("relatte_revision") != WEBZ_RELATTE_REVISION
        ):
            raise WebzParcelError("stored Orchard receiver summary conflicts with the fixture")
        return row

    def send(self, kind: str, expected_sha256: str, confirmation: str, repos: list[RepoStatus]) -> dict:
        data, raw, digest, policy = self._fixture(kind)
        if (
            not isinstance(expected_sha256, str) or expected_sha256 != digest
            or confirmation != "SEND_TO_ORCHARD"
        ):
            raise WebzParcelError("parcel send requires exact preview digest and explicit confirmation")
        with self.lock:
            # No mutation if the owner is absent or the tracked worktree has changed.
            try:
                relatte = _find_pinned(
                    repos, "reLATTE", WEBZ_RELATTE_REVISION, "scripts/opaque-roundtrip.ts"
                )
            except FieldReseedCrossingError as exc:
                raise WebzParcelError(f"pinned reLATTE owner unavailable: {exc}") from exc
            if self._summary_path(kind).exists():
                saved = self._stored(kind, digest, raw)
                if saved is not None:
                    return saved
            created = self._intent(kind, digest)
            self._verify_stage(kind, digest, raw)
            request = self._request(kind, digest, created)
            try:
                result = _run_json(
                    ["node", "--experimental-strip-types", str(relatte / "scripts" / "opaque-roundtrip.ts")],
                    relatte,
                    request,
                    {**os.environ, "LC_ALL": "C"},
                    "reLATTE R14 webZ parcel",
                    timeout=30.0,
                )
            except (FieldReseedCrossingError, OSError) as exc:
                raise WebzParcelError(f"reLATTE parcel outcome not confirmed: {exc}") from exc
            summary = self._verify_result(result, request, kind, digest)
            _atomic_bytes(self._summary_path(kind), (json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
            return summary

    def inbox(self) -> list[dict]:
        """Read-only view. A missing result means no confirmed Orchard disposition."""
        with self.lock:
            entries: list[dict] = []
            for kind in POLICY:
                raw_path = self._summary_path(kind)
                if not raw_path.exists() and not raw_path.is_symlink():
                    continue
                _, raw, digest, _ = self._fixture(kind)
                row = self._stored(kind, digest, raw)
                if row is not None:
                    entries.append(row)
            return entries

    def proof(self, kind: str) -> dict:
        """Expose owner-produced *public* signature evidence for an offline verifier."""
        with self.lock:
            _, raw, digest, _ = self._fixture(kind)
            if self._stored(kind, digest, raw) is None:
                raise WebzParcelError("the Orchard has no confirmed parcel for this kind")
            path = self.root / "results" / f"{kind}-{digest}.json"
            result = _local_json(path, "owner proof", limit=256_000)
            intent = _local_json(self._intent_path(kind), "intent")
            request = self._request(kind, digest, intent["created_at"])
            self._verify_result(result, request, kind, digest)
            # The owner result contains only public JWKs, never local signing keys.
            return {
                "schema": "workbench.webz-parcel-proof/v0",
                "artifact": json.loads(raw),
                "artifact_sha256": digest,
                "crossing": result["crossing"],
                "receive_receipt": result["receive_receipt"],
                "disposition_receipt": result["disposition_receipt"],
                "receiver_snapshot": result["receiver_snapshot"],
                "scope": "cryptographically-verifiable-signed-owner-output;not-source-identity-proof",
            }
