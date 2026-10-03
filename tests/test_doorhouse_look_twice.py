import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict, _digest, _encoded, _now


SVG_SHA = "2" * 64
PAIR_ID = "autodisco-look-twice-pair-v0:" + "3" * 64


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


def seed_creative(store: DoorHouse):
    receipt = crossed_receipt(store)
    snapshot = {
        "schema": "workbench.ghot-execution-witness/v1",
        "local_receipt_id": receipt["id"],
        "local_receipt_sha256": receipt["sha256"],
        "offer_id": "offer",
        "assignment_id": "assignment",
        "selected_node_id": "node-alpha",
        "capability": "creative.toaster.witness-sigil",
        "selection_source": "doorhouse-user-explicit",
        "ghot_receipt_id": "ghot-receipt",
        "executor_node_id": "node-alpha",
        "creative_artifact": {
            "kind": "workbench.materialized-toaster-artifact/v0",
            "svg_path": "/tmp/look-twice.svg",
            "svg_sha256": SVG_SHA,
            "recipe_path": "/tmp/look-twice.json",
            "recipe_sha256": "4" * 64,
            "toaster_receipt_path": "/tmp/toaster.json",
            "toaster_receipt_sha256": "5" * 64,
            "instrument": "witness-sigil/v0.1",
            "source_digest_sha256": receipt["snapshot"]["artifact_sha256"],
        },
        "status": "ok",
        "laws": [],
    }
    with store._db() as db:
        db.execute(
            "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
            (
                uuid4().hex,
                receipt["id"],
                "ghot_execution",
                _digest(snapshot),
                _encoded(snapshot),
                _now(),
            ),
        )
    return receipt


def pair():
    packets = []
    for listener_id, role in [("static-sam", "Static Sam"), ("juniper", "Juniper")]:
        packets.append({
            "schema": "autodisco.look-twice-first-packet/v0",
            "listener": {"id": listener_id, "role": role, "brief": "isolated"},
            "source": {"media_type": "image/svg+xml", "sha256": SVG_SHA},
            "content": "<svg/>",
            "prohibitions": ["NO OTHER LISTENER RESPONSE"],
            "packet_id": f"autodisco-look-twice-first-v0:{listener_id}-packet",
        })
    return {
        "schema": "autodisco.look-twice-pair/v0",
        "source": {"media_type": "image/svg+xml", "sha256": SVG_SHA},
        "packets": packets,
        "laws": ["FIRST RESPONSE PRECEDES CROSS-READ"],
        "pair_id": PAIR_ID,
    }


def sealed(listener_id: str, packet_id: str):
    return {
        "schema": "autodisco.look-twice-first-response/v0",
        "pair_id": PAIR_ID,
        "packet_id": packet_id,
        "listener": {
            "id": listener_id,
            "role": "Static Sam" if listener_id == "static-sam" else "Juniper",
            "brief": "isolated",
        },
        "source_sha256": SVG_SHA,
        "model_used": "gemini-real-test",
        "response_sha256": ("6" if listener_id == "static-sam" else "7") * 64,
        "response": {
            "observations": [
                {"mode": "OBSERVED", "text": "A bounded geometric field is visible."},
                {"mode": "INTERPRETATION", "text": f"{listener_id} finds it unresolved."},
            ],
            "lingering_intrigue": True,
            "closing_line": "Something remains open.",
        },
        "laws": ["SEALED != SHARED"],
        "first_response_id": (
            "autodisco-look-twice-response-v0:"
            + (("8" if listener_id == "static-sam" else "9") * 64)
        ),
    }


def encounter_result(status="two-first-responses-sealed"):
    p = pair()
    if status == "packets-only":
        return {
            "schema": "autodisco.look-twice-encounter-result/v0",
            "status": status,
            "pair_id": PAIR_ID,
            "first_responses": [],
            "model_used": None,
            "laws": ["SIMULATION != FIRST ENCOUNTER"],
        }
    return {
        "schema": "autodisco.look-twice-encounter-result/v0",
        "status": status,
        "pair_id": PAIR_ID,
        "first_responses": [
            sealed("static-sam", p["packets"][0]["packet_id"]),
            sealed("juniper", p["packets"][1]["packet_id"]),
        ],
        "model_used": "gemini-real-test",
        "laws": ["SEALED != SHARED"],
    }


def dialogue_packet():
    responses = encounter_result()["first_responses"]
    return {
        "schema": "autodisco.look-twice-dialogue-packet/v0",
        "pair_id": PAIR_ID,
        "source_sha256": SVG_SHA,
        "sealed_first_responses": [
            {
                "first_response_id": r["first_response_id"],
                "listener": r["listener"],
                "response_sha256": r["response_sha256"],
                "response": r["response"],
            }
            for r in responses
        ],
        "rules": ["ORIGINAL ARTIFACT IS NOT REOPENED"],
        "dialogue_packet_id": "autodisco-look-twice-dialogue-v0:" + "a" * 64,
    }


def dialogue_result(status="dialogue-sealed", intrigue=True):
    packet = dialogue_packet()
    if status == "dialogue-packet-only":
        return {
            "schema": "autodisco.look-twice-dialogue-result/v0",
            "status": status,
            "dialogue_packet": packet,
            "dialogue": None,
            "model_used": None,
            "laws": ["SIMULATION != DIALOGUE"],
        }
    dialogue = {
        "turns": [
            {"listener_id": "static-sam", "text": "Your unresolved edge matches mine differently."},
            {"listener_id": "juniper", "text": "The difference is what keeps pulling."},
        ],
        "convergences": ["Both notice unresolved direction."],
        "differences": ["They name its emotional weight differently."],
        "lingering_intrigue": intrigue,
        "intrigue_statement": "The disagreement itself points beyond the frame." if intrigue else "",
        "door_seed": "What changes when the shape is heard instead of seen?" if intrigue else None,
    }
    return {
        "schema": "autodisco.look-twice-dialogue-result/v0",
        "status": status,
        "dialogue_packet": packet,
        "dialogue": dialogue,
        "dialogue_sha256": "b" * 64,
        "model_used": "gemini-real-test",
        "laws": ["DOOR SEED != CROSSING"],
        "dialogue_id": "autodisco-look-twice-dialogue-result-v0:" + "c" * 64,
    }


def test_pair_and_two_first_responses_are_separate_durable_witnesses(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    state = store.record_look_twice_pair(receipt["id"], pair())
    assert any(w["kind"] == "look_twice_pair" for w in state["external_witnesses"])
    assert store.look_twice_first_responses(receipt["id"]) == []

    state = store.record_look_twice_encounters(receipt["id"], encounter_result())
    firsts = [w for w in state["external_witnesses"] if w["kind"].startswith("look_twice_first:")]
    assert len(firsts) == 2
    assert {w["snapshot"]["listener"]["id"] for w in firsts} == {"static-sam", "juniper"}
    assert not any(w["kind"] == "look_twice_dialogue" for w in state["external_witnesses"])
    newest = state["letters"][0]
    assert newest["body"] is None
    assert "Neither had seen the other's notes" in newest["title"]


def test_packets_only_does_not_invent_first_responses(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    store.record_look_twice_pair(receipt["id"], pair())
    before = len(store.state()["letters"])
    state = store.record_look_twice_encounters(
        receipt["id"], encounter_result("packets-only")
    )
    assert store.look_twice_first_responses(receipt["id"]) == []
    assert len(state["letters"]) == before


def test_dialogue_is_refused_before_two_first_responses(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    store.record_look_twice_pair(receipt["id"], pair())
    with pytest.raises(DoorHouseConflict, match="two sealed LOOK TWICE"):
        store.record_look_twice_dialogue(receipt["id"], dialogue_result())


def test_dialogue_packet_only_is_preserved_without_fake_exchange(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    store.record_look_twice_pair(receipt["id"], pair())
    store.record_look_twice_encounters(receipt["id"], encounter_result())
    state = store.record_look_twice_dialogue(
        receipt["id"], dialogue_result("dialogue-packet-only")
    )
    assert any(
        w["kind"] == "look_twice_dialogue_packet"
        for w in state["external_witnesses"]
    )
    assert not any(
        w["kind"] == "look_twice_dialogue"
        for w in state["external_witnesses"]
    )


def test_lingering_intrigue_opens_a_new_sealed_house_letter_idempotently(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_creative(store)
    store.record_look_twice_pair(receipt["id"], pair())
    store.record_look_twice_encounters(receipt["id"], encounter_result())
    result = dialogue_result()
    state = store.record_look_twice_dialogue(receipt["id"], result)
    dialogue = next(
        w for w in state["external_witnesses"]
        if w["kind"] == "look_twice_dialogue"
    )
    assert dialogue["snapshot"]["dialogue"]["lingering_intrigue"] is True
    newest = state["letters"][0]
    assert newest["body"] is None
    assert newest["title"] == "They looked twice. Something was still pulling."

    count = len(state["letters"])
    replay = store.record_look_twice_dialogue(receipt["id"], result)
    assert len(replay["letters"]) == count


def test_api_keeps_cross_read_locked_until_two_responses(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = seed_creative(store)

    monkeypatch.setattr(app_module, "prepare_look_twice", lambda ghot, repos: pair())
    monkeypatch.setattr(
        app_module,
        "run_look_twice_encounters",
        lambda pair_value, repos: encounter_result("packets-only"),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        prepared = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/look-twice/prepare",
            json={},
            headers=headers,
        )
        assert prepared.status_code == 200

        attempts = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/look-twice/encounters",
            json={},
            headers=headers,
        )
        assert attempts.status_code == 200
        assert not any(
            w["kind"].startswith("look_twice_first:")
            for w in attempts.json()["external_witnesses"]
        )

        dialogue = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/look-twice/dialogue",
            json={},
            headers=headers,
        )
        assert dialogue.status_code == 409
