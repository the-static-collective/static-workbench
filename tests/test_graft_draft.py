"""GRAFT 003: source-bound human working drafts, unrun experiments and revisions."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorConflict, CreatorShelf
from static_workbench.graft_draft import candidate_context, open_draft, prepare, starter
from static_workbench.graft_round import preview_round
from static_workbench.graft_witness import GraftWitnessError


def setup(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),))
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    ride = shelf.save_native_ride({
        "format": "house.native-maxhinal-ride/v0.1", "fuel_sha256": "a" * 64,
        "source_refs": [{"kind": "file", "path": "chosen-only.txt", "sha256": "b" * 64}],
        "mode": "pressure", "outputs": [{"kind": "pressure_questions"}],
        "authority": "none", "promotion": "NONE",
    })
    request = dict(
        ride_id=ride["id"], ride_sha256=ride["ride_sha256"],
        keep="Preserve the selected source digest",
        bend="Standalone game interface", intruder="A local experiment queue",
        move="fuse", relation_lane="human_link",
        question="Which explicitly tested bridge might be reusable?",
    )
    round_data = preview_round(shelf, **request)["round"]
    shelf.save_graft_round(round_data)
    candidate = round_data["candidates"][1]["candidate_sha256"]
    return config, shelf, ride, candidate


def h(client: TestClient) -> dict:
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def draft_fields(document: dict) -> dict:
    return {key: document[key] for key in
            ("title", "body", "experiment", "assumptions", "unresolved")}


def test_candidate_starter_keeps_exact_source_and_plan_is_explicitly_unrun(tmp_path):
    _, shelf, ride, candidate = setup(tmp_path)
    opened = open_draft(shelf, candidate)
    draft = opened["draft"]
    assert opened["revision"] == 0 and opened["draft_sha256"] is None
    assert draft["ride_id"] == ride["id"] and draft["ride_sha256"] == ride["ride_sha256"]
    assert draft["candidate_sha256"] == candidate
    assert draft["source_refs"][0]["path"] == "chosen-only.txt"
    assert draft["status"] == "PROPOSED_UNRUN"
    assert "two-part handoff" in draft["body"]
    assert all(draft["experiment"][name] for name in
               ("input", "procedure", "observable", "stop_condition"))
    assert "not an implementation" in draft["non_claims"][0]


def test_guarded_revision_chain_conflict_history_restart_and_other_candidates(tmp_path):
    config, shelf, ride, candidate = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        path = f"/api/house-maxhinal/graft/candidates/{candidate}/draft"
        opened = client.get(path)
        assert opened.status_code == 200, opened.text
        initial = opened.json()
        form = {"candidate_sha256": candidate, "expected_revision": 0,
                "expected_draft_sha256": None, **draft_fields(initial["draft"])}
        assert client.post("/api/house-maxhinal/graft/drafts", json=form).status_code == 403
        headers = h(client)
        assert client.post("/api/house-maxhinal/graft/drafts", headers={
            **headers, "Origin": "http://elsewhere.invalid",
        }, json=form).status_code == 403
        save = client.post("/api/house-maxhinal/graft/drafts", headers=headers, json=form)
        assert save.status_code == 200, save.text
        one = save.json()
        assert one["revision"] == 1 and one["saved"]
        assert one["draft"]["status"] == "PROPOSED_UNRUN"
        assert one["draft"]["source_refs"] == initial["draft"]["source_refs"]
        assert one["draft"]["parent_draft_sha256"] is None
        stale = client.post("/api/house-maxhinal/graft/drafts", headers=headers, json=form)
        assert stale.status_code == 409
        two_form = {**form, "expected_revision": 1, "expected_draft_sha256": one["draft_sha256"],
                    "body": form["body"] + "\nOne further bounded, reversible seam to examine."}
        save_two = client.post("/api/house-maxhinal/graft/drafts", headers=headers, json=two_form)
        assert save_two.status_code == 200, save_two.text
        two = save_two.json()
        assert two["revision"] == 2 and two["draft_sha256"] != one["draft_sha256"]
        assert two["draft"]["parent_draft_sha256"] == one["draft_sha256"]
        assert client.get(path).json() == two
        history = client.get(path + "/revisions").json()["revisions"]
        assert [row["revision"] for row in history] == [2, 1]
        assert client.get(path + "/revisions/1").json() == one
        assert client.get(path + "/revisions/2").json() == two
        assert client.get(path + "/revisions/30").status_code == 404
        assert any(row["kind"] == "house.graft.draft_revision_saved"
                   for row in client.get("/api/events").json()["events"])
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get(path).json() == two
        assert client.get(path + "/revisions/1").json() == one

    # No mutation of immutable source ride or original candidate on draft revision.
    assert shelf.get_native_ride(ride["id"])["ride_sha256"] == ride["ride_sha256"]
    resolved = candidate_context(shelf, candidate)
    assert resolved["candidate"]["candidate_sha256"] == candidate


def test_invalid_plan_cross_candidate_and_tampered_revision_refused(tmp_path):
    config, shelf, _, candidate = setup(tmp_path)
    initial = starter(shelf, candidate)
    with pytest.raises(GraftWitnessError):
        prepare(shelf, "0" * 64, **initial)
    with pytest.raises(GraftWitnessError):
        prepare(shelf, candidate, **{**initial, "experiment": {
            **initial["experiment"], "unexpected": "extra",
        }})
    with pytest.raises(GraftWitnessError):
        prepare(shelf, candidate, **{**initial, "experiment": {
            **initial["experiment"], "observable": "  ",
        }})
    with pytest.raises(GraftWitnessError):
        prepare(shelf, candidate, **{**initial, "body": " "})
    with pytest.raises(GraftWitnessError):
        prepare(shelf, candidate, **{**initial, "title": "x" * 161})
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        form = {"candidate_sha256": candidate, "expected_revision": 0,
                "expected_draft_sha256": None, **initial}
        h0 = h(client)
        assert client.post("/api/house-maxhinal/graft/drafts", headers=h0, json={
            **form, "candidate_sha256": "0" * 64,
        }).status_code == 409
        saved = client.post("/api/house-maxhinal/graft/drafts", headers=h0, json=form)
        assert saved.status_code == 200, saved.text
        digest = saved.json()["draft_sha256"]
    with shelf._connect() as db:
        db.execute("""UPDATE house_graft_draft_revisions SET payload_json=?
                      WHERE candidate_sha256=? AND revision=1""",
                   ('{"tampered":true}', candidate))
    with pytest.raises(CreatorConflict):
        shelf.latest_graft_draft(candidate)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get(f"/api/house-maxhinal/graft/candidates/{candidate}/draft").status_code == 409


def test_browser_places_editor_inside_saved_candidate_and_not_background_execution(tmp_path):
    config, _, _, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        rounds = client.get("/assets/graft-round.js").text
        editor = client.get("/assets/graft-draft.js").text
    assert html.index("/assets/graft-draft.js") < html.index("/assets/graft-round.js")
    assert "Open working draft + bounded experiment" in rounds
    assert "graftDraftOpen(candidate.candidate_sha256, draftHost)" in rounds
    assert "Save explicit local draft revision" in editor
    assert "PROPOSED" in editor
