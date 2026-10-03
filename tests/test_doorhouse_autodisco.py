from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict


def config_for(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def crossed_receipt(store: DoorHouse):
    state = store.enter()
    letter = state["letters"][0]
    store.open_letter(letter["id"])
    state = store.state()
    door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
    store.select(door["id"], 0)
    state = store.cross(door["id"], 0)
    return state["receipts"][0]


def relatte_result(receipt: dict):
    crossing_id = "relatte-crossing-v0:" + "a" * 64
    return {
        "schema": "relatte.opaque-roundtrip-result/v0",
        "request_id": "relatte-opaque-roundtrip-v0:" + "b" * 64,
        "crossing": {
            "crossing_id": crossing_id,
            "extensions": {
                "organ_adapter": {
                    "donor_claims": {
                        "local_receipt_id": receipt["id"],
                        "local_receipt_sha256": receipt["sha256"],
                    }
                }
            },
        },
        "transport_frame": {"transport_id": "relatte-transport-v0:" + "c" * 64},
        "receive_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "d" * 64,
            "kind": "RECEIVED",
            "semantic_effect": "none",
            "world_id": "world:doorhouse-relatte-hold",
        },
        "disposition_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "e" * 64,
            "kind": "R3_HOLD",
            "semantic_effect": "none",
        },
        "receiver_snapshot": {"state_ref": "relatte-local-state-v0:" + "f" * 64},
    }


def ghot_offer():
    return {
        "kind": "ghot.body-choice.offer",
        "version": "0",
        "offer_id": "ghot-body-offer-v0:" + "1" * 64,
        "capability": "creative.toaster.witness-sigil",
        "observed_at": "2026-10-03T03:00:00+00:00",
        "requester_node_id": "node-requester",
        "candidates": [{
            "node_id": "node-alpha",
            "location": "local",
            "hostname": "alpha",
            "eligible": True,
            "matching_offer": {
                "kind": "ghot.offer",
                "version": "0",
                "capability": "creative.toaster.witness-sigil",
                "available": True,
            },
            "rejected": [],
        }],
        "laws": ["OFFER != ASSIGNMENT"],
    }


def ghot_execution(receipt: dict):
    offer = ghot_offer()
    return {
        "kind": "ghot.body-choice.result",
        "version": "0",
        "assignment": {
            "kind": "ghot.assignment",
            "version": "0",
            "assignment_id": "assignment-creative-001",
            "offer_id": offer["offer_id"],
            "selected_node_id": "node-alpha",
            "capability": "creative.toaster.witness-sigil",
            "selection_source": "doorhouse-user-explicit",
        },
        "execution": {
            "receipt": {
                "kind": "ghot.receipt",
                "version": "0",
                "receipt_id": "receipt-ghot-creative-001",
                "executor_node_id": "node-alpha",
                "capability": "creative.toaster.witness-sigil",
                "status": "ok",
                "output_sha256": "7" * 64,
                "output": {
                    "kind": "ghot.external-adapter.result",
                    "version": "0",
                    "adapter_id": "haunted-toaster.witness-sigil",
                    "capability": "creative.toaster.witness-sigil",
                    "result": {
                        "kind": "haunted-toaster.ghot-adapter-result",
                        "version": "0",
                        "capability": "creative.toaster.witness-sigil",
                        "status": "ok",
                    },
                },
            },
        },
        "status": "ok",
        "workbench_materialized": {
            "kind": "workbench.materialized-toaster-artifact/v0",
            "svg_path": "/tmp/house.svg",
            "svg_sha256": "2" * 64,
            "recipe_path": "/tmp/house.recipe.json",
            "recipe_sha256": "3" * 64,
            "toaster_receipt_path": "/tmp/house.toaster.json",
            "toaster_receipt_sha256": "4" * 64,
            "instrument": "witness-sigil/v0.1",
            "source_digest_sha256": receipt["snapshot"]["artifact_sha256"],
        },
    }


def seed_creative(store: DoorHouse):
    receipt = crossed_receipt(store)
    store.record_relatte_witness(receipt["id"], relatte_result(receipt))
    offer = ghot_offer()
    store.record_ghot_offer(receipt["id"], offer)
    store.record_ghot_execution(
        receipt["id"],
        offer["offer_id"],
        "node-alpha",
        ghot_execution(receipt),
    )
    return receipt


def packet_result(status="packet-only"):
    packet = {
        "schema": "autodisco.first-encounter-packet/v0",
        "packet_id": "autodisco-first-encounter-v0:" + "5" * 64,
        "listener": {
            "role": "The New Listener",
            "memory_mode": "isolated-first-encounter",
        },
        "source": {
            "media_type": "image/svg+xml",
            "sha256": "2" * 64,
        },
        "content": "<svg/>",
        "prohibitions": [
            "NO CATALOG HISTORY",
            "NO PRIOR DJ TRANSCRIPTS",
            "NO HIDDEN HOUSE HISTORY",
        ],
    }
    base = {
        "schema": "autodisco.first-encounter-result/v0",
        "status": status,
        "packet": packet,
        "laws": ["STATION MEMORY != DJ MEMORY"],
    }
    if status == "packet-only":
        return {**base, "response": None, "model_used": None}
    return {
        **base,
        "response": {
            "observations": [
                {"mode": "OBSERVED", "text": "Sixteen geometric marks occupy a square field."},
                {"mode": "INTERPRETATION", "text": "It reads like a compact memory token."},
            ],
            "lingering_intrigue": True,
            "closing_line": "I want to know what changed before this shape arrived.",
        },
        "response_sha256": "6" * 64,
        "model_used": "gemini-test-real",
    }


def test_packet_only_is_preserved_without_fake_response(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)

    state = store.record_autodisco_first_encounter(receipt["id"], packet_result())
    packet = next(
        w for w in state["external_witnesses"] if w["kind"] == "autodisco_packet"
    )
    assert packet["snapshot"]["status"] == "packet-only"
    assert not any(
        w["kind"] == "autodisco_first_response"
        for w in state["external_witnesses"]
    )
    newest = state["letters"][0]
    assert newest["body"] is None
    assert "microphone stayed dark" in newest["title"].lower()


def test_real_first_response_is_sealed_separately_and_retry_is_idempotent(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    store.record_autodisco_first_encounter(receipt["id"], packet_result())

    responded = packet_result("responded")
    state = store.record_autodisco_first_encounter(receipt["id"], responded)
    response = next(
        w for w in state["external_witnesses"]
        if w["kind"] == "autodisco_first_response"
    )
    assert response["snapshot"]["model_used"] == "gemini-test-real"
    assert response["snapshot"]["packet_id"].startswith("autodisco-first-encounter-v0:")
    newest = state["letters"][0]
    assert newest["body"] is None
    assert newest["title"] == "Someone looked without knowing us."

    count = len(state["letters"])
    replay = store.record_autodisco_first_encounter(receipt["id"], responded)
    assert len(replay["letters"]) == count

    store.open_letter(newest["id"])
    opened = store.state()["letters"][0]
    assert "OBSERVED" in opened["body"]
    assert "CLOSING" in opened["body"]


def test_packet_must_bind_to_returned_svg(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    wrong = packet_result()
    wrong["packet"]["source"]["sha256"] = "0" * 64
    with pytest.raises(DoorHouseConflict):
        store.record_autodisco_first_encounter(receipt["id"], wrong)


def test_first_encounter_api_records_truthful_packet_only(monkeypatch, tmp_path):
    config = config_for(tmp_path)

    monkeypatch.setattr(
        app_module,
        "run_relatte_aperture",
        lambda receipt, state_dir, repos: relatte_result(receipt),
    )
    monkeypatch.setattr(
        app_module,
        "discover_ghot_bodies",
        lambda receipt, relatte, repos, state_dir: ghot_offer(),
    )
    monkeypatch.setattr(
        app_module,
        "assign_ghot_body",
        lambda receipt, relatte, offer, selected, repos, state_dir: ghot_execution(receipt),
    )
    monkeypatch.setattr(
        app_module,
        "run_first_encounter",
        lambda ghot, repos: packet_result(),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        state = client.post("/api/doorhouse/enter", json={}, headers=headers).json()
        first = state["letters"][0]
        state = client.post(
            f"/api/doorhouse/letters/{first['id']}/open",
            json={}, headers=headers,
        ).json()
        door = next(d for d in state["doors"] if d["letter_id"] == first["id"])
        client.post(
            f"/api/doorhouse/doors/{door['id']}/select",
            json={"expected_world_version": 0},
            headers=headers,
        )
        state = client.post(
            f"/api/doorhouse/doors/{door['id']}/cross",
            json={"expected_world_version": 0},
            headers=headers,
        ).json()
        receipt = state["receipts"][0]
        client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/relatte",
            json={}, headers=headers,
        )
        client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/offers",
            json={}, headers=headers,
        )
        client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/assign",
            json={
                "expected_offer_id": ghot_offer()["offer_id"],
                "selected_node_id": "node-alpha",
            },
            headers=headers,
        )

        result = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/first-encounter",
            json={}, headers=headers,
        )
        assert result.status_code == 200
        returned = result.json()
        packet = next(
            w for w in returned["external_witnesses"]
            if w["kind"] == "autodisco_packet"
        )
        assert packet["snapshot"]["status"] == "packet-only"
        assert not any(
            w["kind"] == "autodisco_first_response"
            for w in returned["external_witnesses"]
        )
