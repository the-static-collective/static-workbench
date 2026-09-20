"""GRAFT 002: candidate identity, human review and separate Dogram linkage."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorConflict, CreatorShelf
from static_workbench.graft_round import get_candidate, preview_round
from static_workbench.graft_witness import GraftWitnessError


def fixture(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    dogram = root / "Dogram"
    dogram.mkdir()
    def git(*args):
        subprocess.run(["git", "-C", str(dogram), *args], check=True, capture_output=True)
    git("init", "-b", "main")
    (dogram / ".gitignore").write_text("__pycache__/\n")
    package = dogram / "dogram"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "repo_impact.py").write_text("# discovery fixture\n")
    (package / "engine.py").write_text(
        "import hashlib,json\n"
        "def evaluate_specimen(specimen):\n"
        "    raw=json.dumps(specimen,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()\n"
        "    return {'schema':'dogram.receipt/v0','status':'OK','operator':specimen['operator'],"
        "'operator_version':1,'input_digest':'sha256:'+hashlib.sha256(raw).hexdigest(),"
        "'result':{'fixture':True}}\n"
    )
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),), max_repo_depth=2)
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    ride = shelf.save_native_ride({
        "format": "house.native-maxhinal-ride/v0.1", "fuel_sha256": "a" * 64,
        "mode": "pressure", "outputs": [{"kind": "pressure_questions"}],
        "authority": "none", "promotion": "NONE",
    })
    request = {
        "ride_id": ride["id"], "ride_sha256": ride["ride_sha256"],
        "keep": "Exact provenance of a selected source",
        "bend": "An abandoned game interface",
        "intruder": "A human-confirmed participation basket",
        "move": "fuse", "relation_lane": "active_tension",
        "question": "How might one capability become a bounded local fixture?",
    }
    return config, shelf, ride, request


def token(client: TestClient) -> dict[str, str]:
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def test_round_review_save_three_distinct_candidates_persist_and_reject_stale(tmp_path):
    config, shelf, ride, request = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        path = "/api/house-maxhinal/graft/rounds"
        assert client.post(path + "/preview", json=request).status_code == 403
        headers = token(client)
        assert client.post(path + "/preview", headers={
            **headers, "Origin": "http://elsewhere.invalid",
        }, json=request).status_code == 403
        preview = client.post(path + "/preview", headers=headers, json=request)
        assert preview.status_code == 200, preview.text
        reviewed = preview.json()
        cards = reviewed["round"]["candidates"]
        assert [card["variant"] for card in cards] == ["clean_hit", "side_door", "wrong_turn"]
        assert len({card["candidate_sha256"] for card in cards}) == 3
        assert reviewed["round"]["source_refs"] == []
        assert reviewed["round"]["non_claims"]
        assert preview_round(shelf, **request)["round_sha256"] == reviewed["round_sha256"]
        stale = client.post(path, headers=headers, json={
            **request, "bend": "A changed implementation", "expected_round_sha256": reviewed["round_sha256"],
        })
        assert stale.status_code == 409
        saved = client.post(path, headers=headers, json={
            **request, "expected_round_sha256": reviewed["round_sha256"],
        })
        assert saved.status_code == 200, saved.text
        packet = saved.json()
        assert packet["round_sha256"] == reviewed["round_sha256"]
        repeat = client.post(path, headers=headers, json={
            **request, "expected_round_sha256": reviewed["round_sha256"],
        })
        assert repeat.json() == packet
        assert len(client.get(f"/api/house-maxhinal/graft/rides/{ride['id']}/rounds").json()["rounds"]) == 1
        assert client.get(f"{path}/{packet['round_sha256']}").json() == packet
        assert any(event["kind"] == "house.graft.round_saved" for event in client.get("/api/events").json()["events"])
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get(f"{path}/{packet['round_sha256']}").json() == packet
        for card in cards:
            assert get_candidate(shelf, ride["id"], ride["ride_sha256"],
                card["candidate_sha256"])["round_sha256"] == packet["round_sha256"]


def test_candidate_linkage_in_public_dogram_receipt_cannot_cross_ride(tmp_path):
    config, shelf, ride, request = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        h = token(client)
        proposed = client.post("/api/house-maxhinal/graft/rounds/preview", headers=h, json=request).json()
        saved = client.post("/api/house-maxhinal/graft/rounds", headers=h, json={
            **request, "expected_round_sha256": proposed["round_sha256"],
        }).json()
        card_sha = saved["round"]["candidates"][1]["candidate_sha256"]
        spec = {
            "ride_id": ride["id"], "ride_sha256": ride["ride_sha256"],
            "candidate_sha256": card_sha,
            "graph": {"nodes": ["seed", "candidate", "saved_proposal"],
                      "edges": [["seed", "candidate"]]},
            "operator": "reach",
            "change": {"op": "ADD_EDGE", "source": "candidate", "target": "saved_proposal"},
            "queries": [["seed", "saved_proposal"]],
        }
        p = client.post("/api/house-maxhinal/graft/preview", headers=h, json=spec)
        assert p.status_code == 200, p.text
        reviewed = p.json()
        assert reviewed["specimen"]["metadata"]["candidate_sha256"] == card_sha
        assert client.post("/api/house-maxhinal/graft/preview", headers=h,
            json={**spec, "candidate_sha256": "0" * 64}).status_code == 409
        wrong = shelf.save_native_ride({
            "format": "house.native-maxhinal-ride/v0.1", "fuel_sha256": "b" * 64,
            "mode": "braid", "outputs": [], "authority": "none", "promotion": "NONE",
        })
        assert client.post("/api/house-maxhinal/graft/preview", headers=h,
            json={**spec, "ride_id": wrong["id"], "ride_sha256": wrong["ride_sha256"]}).status_code == 409
        assert client.post("/api/house-maxhinal/graft/measure", headers=h,
            json={**spec, "candidate_sha256": None,
                  "expected_specimen_sha256": reviewed["specimen_sha256"],
                  "expected_dogram_commit": reviewed["dogram_commit"]}).status_code == 409
        run = client.post("/api/house-maxhinal/graft/measure", headers=h,
            json={**spec, "expected_specimen_sha256": reviewed["specimen_sha256"],
                  "expected_dogram_commit": reviewed["dogram_commit"]})
        assert run.status_code == 200, run.text
        witness = run.json()
        assert witness["witness"]["candidate_sha256"] == card_sha
        assert witness["witness"]["dogram_receipt"]["input_digest"] == (
            "sha256:" + reviewed["specimen_sha256"]
        )
        assert witness["witness"]["specimen"]["metadata"]["candidate_sha256"] == card_sha


def test_invalid_declarations_unknown_ride_and_tampered_round_refused(tmp_path):
    config, shelf, ride, request = fixture(tmp_path)
    for patch in [
        {"keep": ""}, {"intruder": " "}, {"move": "launch"},
        {"relation_lane": "secret_link"}, {"question": "q" * 401},
        {"ride_sha256": "0" * 64},
    ]:
        with pytest.raises(GraftWitnessError):
            preview_round(shelf, **{**request, **patch})
    reviewed = preview_round(shelf, **request)
    saved = shelf.save_graft_round(reviewed["round"])
    with shelf._connect() as db:
        db.execute("UPDATE house_graft_rounds SET payload_json=? WHERE round_sha256=?",
                   ('{"tampered":true}', saved["round_sha256"]))
    with pytest.raises(CreatorConflict):
        shelf.get_graft_round(saved["round_sha256"])


def test_browser_has_visible_candidate_table_before_dogram(tmp_path):
    config, _, _, _ = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        native = client.get("/assets/native-maxhinal.js").text
        round_ui = client.get("/assets/graft-round.js").text
        dogram_ui = client.get("/assets/graft-witness.js").text
    assert html.index("/assets/graft-round.js") < html.index("/assets/graft-witness.js")
    assert native.index("graftRoundRenderForRide(ride, host)") < native.index("graftRenderForRide(ride, host)")
    assert "Save this reviewed GRAFT round" in round_ui
    assert "candidate_sha256: candidateAtPreview" in dogram_ui
