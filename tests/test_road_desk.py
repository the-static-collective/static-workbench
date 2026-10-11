import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.road_desk import road_desk_status


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def make_house(tmp_path: Path) -> Path:
    root = tmp_path / "roadkit-house"
    identity = {
        "schema": "static.house-identity/v0",
        "house_id": "static-house:test",
        "world_id": "static-world:test",
        "label": "Test House",
        "signing_public_key": {"kty": "EC", "crv": "P-256", "x": "x", "y": "y"},
        "created_at": "2026-10-01T00:00:00.000Z",
        "authority": "self-asserted-local",
    }
    identity_bytes = _json_bytes(identity)
    digest = hashlib.sha256(identity_bytes).hexdigest()
    identity_ref = f"sha256:{digest}"
    identity_path = (
        root / "tranchnode" / "objects" / "sha256" / digest[:2] / digest[2:4] / digest
    )
    identity_path.parent.mkdir(parents=True, exist_ok=True)
    identity_path.write_bytes(identity_bytes)

    _write_json(
        root / "house.json",
        {
            "schema": "static.roadkit-house/v0",
            "house_id": "static-house:test",
            "world_id": "static-world:test",
            "label": "Test House",
            "identity_ref": identity_ref,
            "authority": "local",
        },
    )
    _write_json(
        root / "relatte-receiver" / "receiver.json",
        {
            "schema": "relatte.local-receiver-config/v0",
            "world_id": "static-world:test",
            "receiver_particular": "static-house:test",
            "contract_ref": "static:roadkit-001",
        },
    )

    foreign_id = "relatte-crossing-v0:foreign"
    local_id = "relatte-crossing-v0:local"
    journal = [
        {
            "event_type": "DISPOSITION",
            "crossing_id": foreign_id,
            "receipt": {
                "receipt_id": "relatte-receipt-v0:hold",
                "crossing_id": foreign_id,
                "kind": "R3_HOLD",
                "semantic_effect": "none",
                "created_at": "2026-10-01T00:00:01.000Z",
            },
        },
        {
            "event_type": "DISPOSITION",
            "crossing_id": local_id,
            "receipt": {
                "receipt_id": "relatte-receipt-v0:admit",
                "crossing_id": local_id,
                "kind": "R3_ADMIT",
                "semantic_effect": "index-roadkit-specimen",
                "created_at": "2026-10-01T00:00:02.000Z",
            },
        },
    ]
    journal_path = root / "relatte-receiver" / "journal.jsonl"
    journal_path.write_text(
        "".join(json.dumps(item) + "\n" for item in journal),
        encoding="utf-8",
    )

    _write_json(
        root / "inbox" / "foreign.json",
        {
            "schema": "relatte.crossing-envelope/v0",
            "crossing_id": foreign_id,
            "source_particular": "static-house:source",
            "source_world": "static-world:source",
            "declared_kind": "static.roadkit-specimen/v0",
            "requested_effect": "index-roadkit-specimen",
            "payload_refs": [{"address": identity_ref}],
            "return_address": "http://127.0.0.1:45111/roadkit/v0/artifacts/",
        },
    )
    _write_json(root / "outbox" / "local.json", {"crossing_id": local_id})
    _write_json(root / "crossing-key.json", {"private_jwk": "DO NOT READ"})
    return root


def make_config(tmp_path: Path, roadkit_root: Path | None) -> WorkbenchConfig:
    source_root = tmp_path / "repos"
    source_root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", source_root),),
        roadkit_house_root=roadkit_root,
    )


def test_road_desk_reports_identity_holds_and_admits_without_execution(tmp_path: Path):
    house_root = make_house(tmp_path)
    status = road_desk_status(house_root)

    assert status["configured"] is True
    assert status["present"] is True
    assert status["identity"]["address_verified"] is True
    assert status["identity"]["matches_house"] is True
    assert status["summary"] == {
        "inbox": 1,
        "outbox": 1,
        "foreign_holds": 1,
        "admits": 1,
    }
    assert status["foreign_crossings"][0]["crossing_id"] == "relatte-crossing-v0:foreign"
    assert status["foreign_hold_receipts"][0]["semantic_effect"] == "none"
    assert "UI != ROADKIT EXECUTION" in status["laws"]
    assert "receipt_signatures_not_reverified" in status["verification"]


def test_road_desk_unconfigured_is_explicit(tmp_path: Path):
    status = road_desk_status(None)
    assert status["configured"] is False
    assert status["present"] is False
    assert status["verification"] == "not_evaluated"


def test_api_is_get_only_and_observational(tmp_path: Path):
    house_root = make_house(tmp_path)
    with TestClient(
        create_app(make_config(tmp_path, house_root)),
        base_url="http://127.0.0.1",
    ) as client:
        response = client.get("/api/roadkit")
        refused_write = client.post("/api/roadkit", json={"action": "accept"})

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["foreign_holds"] == 1
    assert body["summary"]["admits"] == 1
    assert body["operator_note"].startswith("Road Desk is observational")
    assert refused_write.status_code == 405
