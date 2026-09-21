"""MADDLOOP-001 local pedal and hostile lift-gap acceptance tests."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.maddloop import MaddloopStore, LoopConflict


def config_for(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )


def layer(name="A", body="A first human-authored idea", **kw):
    return {"kind": "text", "label": name, "body": body, **kw}


def test_pedal_has_nav_and_serves_ui_assets(tmp_path):
    with TestClient(create_app(config_for(tmp_path)), base_url="http://127.0.0.1") as c:
        home = c.get("/")
        pedal = c.get("/maddloop")
        js = c.get("/assets/maddloop.js")
    assert 'href="/maddloop"' in home.text
    assert pedal.status_code == 200 and "MADDLOOP / 001" in pedal.text
    assert "PLAY · New preview encounter" in pedal.text
    assert js.status_code == 200 and "/api/maddloop/loops" in js.text


def test_two_replays_are_distinct_encounters_of_unchanged_source(tmp_path):
    store = MaddloopStore(tmp_path / "state" / "loop.sqlite3")
    original = store.create("First loop", layer())
    revision = original["head_revision_id"]
    source_id = original["layers"][0]["source_id"]
    first = store.encounter(original["id"], revision)
    second = store.encounter(original["id"], revision)
    assert first["id"] != second["id"]
    assert first["receipt"]["source_ids"] == second["receipt"]["source_ids"] == [source_id]
    assert first["receipt"]["snapshot_sha256"] == second["receipt"]["snapshot_sha256"]
    assert first["status"] == second["status"] == "composable_preview"
    assert "not execution" in first["receipt"]["nonclaims"][0]
    reopened = MaddloopStore(tmp_path / "state" / "loop.sqlite3").get(original["id"])
    assert len(reopened["encounters"]) == 2
    assert reopened["head_revision_id"] == revision


def test_overdub_is_immutable_branch_keeps_provenance_and_stale_edit_refuses(tmp_path):
    store = MaddloopStore(tmp_path / "loops.sqlite3")
    original = store.create("Loop", layer())
    old_revision = original["head_revision_id"]
    old_source = original["layers"][0]["source_id"]
    revised = store.overdub(original["id"], old_revision, layer("B", "Second voice"))
    assert revised["layers"][0]["source_id"] == old_source
    assert revised["layers"][1]["source_id"] != old_source
    assert revised["revisions"][1]["id"] == old_revision
    try:
        store.overdub(original["id"], old_revision, layer("STALE", "Should not be saved"))
        assert False, "stale write should refuse"
    except LoopConflict:
        pass
    branched = store.branch(original["id"], revised["head_revision_id"], "Fork")
    assert branched["id"] != original["id"]
    assert branched["parent_loop_id"] == original["id"]
    assert branched["revisions"][0]["parent_revision_id"] == revised["head_revision_id"]
    assert [x["source_id"] for x in branched["layers"]] == [
        x["source_id"] for x in revised["layers"]
    ]
    store.overdub(branched["id"], branched["head_revision_id"], layer("C", "Fork-only"))
    assert len(store.get(original["id"])["layers"]) == 2
    assert len(store.get(branched["id"])["layers"]) == 3


def test_abstract_edges_exist_without_concrete_lift_then_explicit_repair(tmp_path):
    store = MaddloopStore(tmp_path / "loops.sqlite3")
    start = store.create("Lift-gap specimen", layer(
        "P to Q_in", "Synthetic P -> Q_in",
        input_class="P", input_port="p", output_class="Q", output_port="q_in",
    ))
    blocked = store.overdub(start["id"], start["head_revision_id"], layer(
        "Q_out to R", "Synthetic Q_out -> R",
        input_class="Q", input_port="q_out", output_class="R", output_port="r",
    ))
    assert blocked["passage"]["status"] == "candidate_only"
    gap = blocked["passage"]["obstructions"][0]
    assert gap["reason"] == "concrete_lift_gap"
    assert gap["available"]["port"] == "q_in"
    assert gap["required"]["port"] == "q_out"
    encounter = store.encounter(blocked["id"], blocked["head_revision_id"])
    assert encounter["status"] == "blocked_route_preview"
    # Repairs are an explicit new arrangement, not a retroactive rewrite of the gap.
    repair = store.branch(start["id"], start["head_revision_id"], "Compatible alternative")
    solved = store.overdub(repair["id"], repair["head_revision_id"], layer(
        "Q_in to R", "Explicit compatible alternative",
        input_class="Q", input_port="q_in", output_class="R", output_port="r",
    ))
    assert solved["passage"]["status"] == "concrete_route_witnessed"
    assert not solved["passage"]["obstructions"]
    assert store.get(blocked["id"])["passage"]["status"] == "candidate_only"


def test_api_local_write_gate_revisions_and_restart(tmp_path):
    cfg = config_for(tmp_path)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as c:
        body = {"title": "Recorded", "layer": layer()}
        assert c.post("/api/maddloop/loops", json=body).status_code == 403
        token = c.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        assert c.post("/api/maddloop/loops", json=body, headers={
            **headers, "origin": "http://evil.example",
        }).status_code == 403
        result = c.post("/api/maddloop/loops", json=body, headers=headers)
        assert result.status_code == 200
        loop = result.json()
        revision = loop["head_revision_id"]
        overdub = c.post(
            "/api/maddloop/loops/" + loop["id"] + "/overdub", headers=headers,
            json={"expected_revision_id": revision, "layer": layer("new", "A second step")},
        )
        assert overdub.status_code == 200
        assert c.post(
            "/api/maddloop/loops/" + loop["id"] + "/encounters", headers=headers,
            json={"expected_revision_id": revision},
        ).status_code == 409
        encounter = c.post(
            "/api/maddloop/loops/" + loop["id"] + "/encounters", headers=headers,
            json={"expected_revision_id": overdub.json()["head_revision_id"]},
        )
        assert encounter.status_code == 200
        assert encounter.json()["kind"] == "local_preview"
        assert any(x["kind"] == "maddloop.preview_encounter" for x in
                   c.get("/api/events").json()["events"])
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as c:
        persisted = c.get("/api/maddloop/loops/" + loop["id"])
    assert persisted.status_code == 200
    assert len(persisted.json()["layers"]) == 2
    assert len(persisted.json()["encounters"]) == 1
