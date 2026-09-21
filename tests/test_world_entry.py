"""STATIC-ARG-002: source-pinned fictional rooms, guarded crossings and restart replay."""
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.first_door import ArgConflict, ArgMissing
from static_workbench.world_entry import WorldEntry


def fixture_world(store):
    store.enter()
    first = store.seed("The Bell", "A bell rings only when touched.")
    second = store.seed("The Door", "The missing corner is an opening.")
    fresh = store.seed("The Garden", "A small seed survives the crossing.")
    machine = store.machine("Bell Door", first["id"], second["id"])
    world = store.world("The Orchard", machine["id"], fresh["id"], "On each turn choose a door or rest.")
    return first, second, fresh, machine, world


def test_rooms_unlock_archive_only_after_three_source_linked_discoveries(tmp_path):
    store = WorldEntry(tmp_path / "state" / "static_arg.sqlite3")
    first, second, fresh, machine, world = fixture_world(store)
    state = store.play(world["id"])
    assert state["room_id"] == "threshold"
    assert state["discoveries"] == []
    assert state["archive_unlocked"] is False
    assert state["world"]["sha256"] == world["sha256"]
    try:
        store.act(world["id"], "travel", "threshold", "archive")
        assert False, "archive must begin locked"
    except ArgConflict:
        pass

    state = store.act(world["id"], "examine", "threshold", "rule")
    entry = next(room for room in state["rooms"] if room["id"] == "threshold")
    assert entry["object"]["revelation"] == "On each turn choose a door or rest."
    assert entry["object"]["source"] == {
        "id": world["id"], "sha256": world["sha256"], "kind": "world",
    }
    assert next(room for room in state["rooms"] if room["id"] == "workshop")["object"]["revelation"] is None

    store.act(world["id"], "travel", "threshold", "workshop")
    state = store.act(world["id"], "examine", "workshop", "machine")
    workshop = next(room for room in state["rooms"] if room["id"] == "workshop")
    assert workshop["object"]["source"]["sha256"] == machine["sha256"]
    assert first["snapshot"]["text"] in workshop["object"]["revelation"]
    assert second["snapshot"]["text"] in workshop["object"]["revelation"]
    assert store.play(world["id"])["room_id"] == "workshop"
    store.act(world["id"], "travel", "workshop", "threshold")
    store.act(world["id"], "travel", "threshold", "garden")
    state = store.act(world["id"], "examine", "garden", "seed")
    assert state["archive_unlocked"] is True
    assert state["discoveries"] == ["rule", "machine", "seed"]
    assert next(room for room in state["rooms"] if room["id"] == "garden")["object"]["source"]["id"] == fresh["id"]
    store.act(world["id"], "travel", "garden", "threshold")
    state = store.act(world["id"], "travel", "threshold", "archive")
    assert state["room_id"] == "archive"
    state = store.act(world["id"], "examine", "archive", "chronicle")
    assert state["discoveries"] == ["rule", "machine", "seed", "chronicle"]
    chronicle = next(room for room in state["rooms"] if room["id"] == "archive")
    assert first["snapshot"]["title"] in chronicle["object"]["revelation"]
    assert world["snapshot"]["play_rule"] in chronicle["object"]["revelation"]
    assert state["history"][0]["source_sha256"] == world["sha256"]
    assert state["history"][0]["action"] == "examine"
    reopened = WorldEntry(store.path).play(world["id"])
    assert reopened["room_id"] == "archive"
    assert reopened["discoveries"] == state["discoveries"]
    assert reopened["world"]["sha256"] == world["sha256"]


def test_world_movement_is_adjacent_and_stale_context_refuses(tmp_path):
    store = WorldEntry(tmp_path / "arg.sqlite3")
    _, _, _, _, world = fixture_world(store)
    # Start in the Threshold: no remote object, no invented room, no nonadjacent archive.
    for action, expected, target in (
        ("examine", "threshold", "machine"),
        ("travel", "threshold", "archive"),
        ("travel", "threshold", "unknown"),
        ("invent", "threshold", "rule"),
    ):
        try:
            store.act(world["id"], action, expected, target)
            assert False, "invalid play must refuse"
        except ArgConflict:
            pass
    store.act(world["id"], "travel", "threshold", "garden")
    for action, expected, target in (
        ("examine", "threshold", "rule"),
        ("travel", "threshold", "workshop"),
        ("travel", "garden", "workshop"),
        ("examine", "garden", "machine"),
    ):
        try:
            store.act(world["id"], action, expected, target)
            assert False, "stale or disconnected action must refuse"
        except ArgConflict:
            pass
    assert len(store.play(world["id"])["history"]) == 1
    assert store.play(world["id"])["room_id"] == "garden"


def test_exact_source_lineage_refuses_tampering_and_nonworld(tmp_path):
    store = WorldEntry(tmp_path / "arg.sqlite3")
    first, _, _, _, world = fixture_world(store)
    try:
        store.play(first["id"])
        assert False
    except ArgConflict:
        pass
    try:
        store.play("0" * 32)
        assert False
    except ArgMissing:
        pass
    with sqlite3.connect(store.path) as db:
        db.execute("UPDATE arg_artifacts SET sha256=? WHERE id=?", ("a" * 64, first["id"]))
    try:
        store.play(world["id"])
        assert False, "a changed source digest must fail closed"
    except ArgConflict:
        pass


def test_world_page_and_post_guards_on_existing_workbench(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/arg/world")
        script = client.get("/assets/arg-world.js")
        style = client.get("/assets/arg-world.css")
        assert html.status_code == 200 and "The Threshold" in html.text
        assert "arg-world.js" in html.text and "arg-world.css" in html.text
        assert 'aria-label="World map and discoveries"' in html.text
        assert script.status_code == 200 and "textContent" in script.text
        assert "innerHTML" not in script.text
        assert "expected_room" in script.text
        assert style.status_code == 200 and "prefers-reduced-motion" in style.text
        assert "/arg/world?world=" in client.get("/assets/arg.js").text
        assert client.get("/api/arg/worlds/" + "0" * 32 + "/play").status_code == 409

        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        assert client.post("/api/arg/enter", json={}, headers=headers).status_code == 200
        a = client.post("/api/arg/seeds", json={"title": "A", "text": "A"}, headers=headers).json()
        b = client.post("/api/arg/seeds", json={"title": "B", "text": "B"}, headers=headers).json()
        c = client.post("/api/arg/seeds", json={"title": "C", "text": "C"}, headers=headers).json()
        m = client.post("/api/arg/machines", json={
            "title": "M", "first_id": a["id"], "second_id": b["id"],
        }, headers=headers).json()
        w = client.post("/api/arg/worlds", json={
            "title": "W", "machine_id": m["id"], "seed_id": c["id"], "rule": "Rest is allowed.",
        }, headers=headers).json()
        url = "/api/arg/worlds/" + w["id"] + "/play"
        assert client.get(url).json()["room_id"] == "threshold"
        payload = {"action": "examine", "expected_room": "threshold", "target": "rule"}
        assert client.post(url, json=payload).status_code == 403
        assert client.post(url, json=payload, headers={
            **headers, "origin": "http://invalid.example",
        }).status_code == 403
        assert client.post(url, json={
            "action": "travel", "expected_room": "threshold", "target": "archive",
        }, headers=headers).status_code == 409
        assert client.post(url, json=payload, headers=headers).status_code == 200
        assert client.post(url, json={
            "action": "travel", "expected_room": "threshold", "target": "garden",
        }, headers=headers).json()["room_id"] == "garden"
        assert client.post(url, json=payload, headers=headers).status_code == 409
        assert client.get(url).json()["discoveries"] == ["rule"]
        assert client.get("/api/arg/state").json()["artifacts"][0]["sha256"] == w["sha256"]
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        again = client.get(url).json()
        assert again["room_id"] == "garden"
        assert again["discoveries"] == ["rule"]
