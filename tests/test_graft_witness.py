from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorShelf
from static_workbench.graft_witness import GraftWitnessError, preview


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def setup(tmp_path: Path) -> tuple[WorkbenchConfig, CreatorShelf, dict]:
    root = tmp_path / "root"
    root.mkdir()
    dogram = root / "Dogram"
    dogram.mkdir()
    git(dogram, "init", "-b", "main")
    (dogram / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    package = dogram / "dogram"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "repo_impact.py").write_text("# Discovery fixture\n", encoding="utf-8")
    (package / "engine.py").write_text(
        "import hashlib,json\n"
        "def evaluate_specimen(specimen):\n"
        "    raw=json.dumps(specimen,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()\n"
        "    return {'schema':'dogram.receipt/v0','status':'OK','operator':specimen['operator'],"
        "'operator_version':1,'input_digest':'sha256:'+hashlib.sha256(raw).hexdigest(),"
        "'result':{'fixture':True}}\n", encoding="utf-8"
    )
    git(dogram, "add", ".")
    git(dogram, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-m", "fixture")
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
        max_repo_depth=2,
    )
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    ride = shelf.save_native_ride({
        "format": "house.native-maxhinal-ride/v0.1", "fuel_sha256": "a" * 64,
        "mode": "pressure", "outputs": [{"kind": "pressure_questions"}],
        "authority": "none", "promotion": "NONE",
    })
    return config, shelf, ride


def specimen(ride: dict) -> dict:
    return {
        "ride_id": ride["id"], "ride_sha256": ride["ride_sha256"],
        "graph": {"nodes": ["seed", "candidate", "saved_proposal"],
                  "edges": [["seed", "candidate"]]},
        "operator": "reach",
        "change": {"op": "ADD_EDGE", "source": "candidate", "target": "saved_proposal"},
        "queries": [["seed", "saved_proposal"]],
    }


def token(client: TestClient) -> dict:
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def test_witness_requires_reviewed_ride_exact_graph_session_and_persists(tmp_path: Path):
    config, _, ride = setup(tmp_path)
    request = specimen(ride)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.post("/api/house-maxhinal/graft/preview", json=request).status_code == 403
        headers = token(client)
        assert client.post("/api/house-maxhinal/graft/preview", headers={
            **headers, "Origin": "http://evil.example"
        }, json=request).status_code == 403
        p = client.post("/api/house-maxhinal/graft/preview", headers=headers, json=request)
        assert p.status_code == 200, p.text
        reviewed = p.json()
        assert reviewed["specimen"]["operator"] == "reach"
        assert reviewed["specimen"]["metadata"]["ride_sha256"] == ride["ride_sha256"]
        assert reviewed["authority"] == "none"
        bad = client.post("/api/house-maxhinal/graft/measure", headers=headers,
                          json={**request, "expected_specimen_sha256": "f" * 64,
                                "expected_dogram_commit": reviewed["dogram_commit"]})
        assert bad.status_code == 409
        run = client.post("/api/house-maxhinal/graft/measure", headers=headers,
                          json={**request, "expected_specimen_sha256": reviewed["specimen_sha256"],
                                "expected_dogram_commit": reviewed["dogram_commit"]})
        assert run.status_code == 200, run.text
        data = run.json()
        assert data["witness"]["dogram_receipt"]["schema"] == "dogram.receipt/v0"
        assert data["witness"]["dogram_receipt"]["result"]["fixture"] is True
        assert data["witness"]["non_claims"]
        assert client.get("/api/house-maxhinal/graft/rides/1/witnesses").json()["witnesses"][0]["witness_sha256"] == data["witness_sha256"]
        assert any(x["kind"] == "house.graft.dogram_witness_saved" for x in client.get("/api/events").json()["events"])
        second = client.post("/api/house-maxhinal/graft/measure", headers=headers,
                             json={**request, "expected_specimen_sha256": reviewed["specimen_sha256"],
                                   "expected_dogram_commit": reviewed["dogram_commit"]})
        assert second.status_code == 200
        assert second.json()["witness_sha256"] == data["witness_sha256"]
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        fetched = client.get("/api/house-maxhinal/graft/witnesses/" + data["witness_sha256"])
        assert fetched.status_code == 200
        assert fetched.json() == data
        assert len(client.get("/api/house-maxhinal/graft/rides/1/witnesses").json()["witnesses"]) == 1


def test_graph_refusals_and_changed_ride_or_dogram(tmp_path: Path):
    config, shelf, ride = setup(tmp_path)
    base = specimen(ride)
    for patch in [
        {"graph": {"nodes": ["a", "a"], "edges": []}},
        {"graph": {"nodes": ["a", "b"], "edges": [["a", "missing"]]}},
        {"graph": {"nodes": ["a", "b"], "edges": [["a", "b"], ["a", "b"]]}},
        {"graph": {"nodes": [str(i) for i in range(13)], "edges": []}},
        {"queries": [["seed", "not-a-node"]]},
        {"operator": "exec"},
        {"change": {"op": "ADD_EDGE", "source": "seed", "target": "candidate"}},
        {"ride_sha256": "0" * 64},
    ]:
        with pytest.raises(GraftWitnessError):
            preview(config, shelf, **{**base, **patch})
    reviewed = preview(config, shelf, **base)
    root = config.roots[0].path
    (root / "Dogram" / "dirty.txt").write_text("untracked")
    with pytest.raises(GraftWitnessError, match="dirty"):
        preview(config, shelf, **base)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        bad = client.post("/api/house-maxhinal/graft/measure", headers=token(client), json={
            **base, "expected_specimen_sha256": reviewed["specimen_sha256"],
            "expected_dogram_commit": reviewed["dogram_commit"],
        })
        assert bad.status_code == 409


def test_ablate_preview_has_correct_public_schema(tmp_path: Path):
    config, shelf, ride = setup(tmp_path)
    request = specimen(ride)
    request["operator"] = "ablate"
    request["change"] = {"kind": "edge", "source": "seed", "target": "candidate"}
    reviewed = preview(config, shelf, **request)
    assert reviewed["specimen"]["operator"] == "ablate"
    assert reviewed["specimen"]["inputs"]["target"]["kind"] == "edge"
    with pytest.raises(GraftWitnessError):
        preview(config, shelf, **{**request, "change": {
            "kind": "edge", "source": "candidate", "target": "saved_proposal",
        }})


def test_graft_witness_tampering_is_detected(tmp_path: Path):
    config, shelf, ride = setup(tmp_path)
    request = specimen(ride)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        headers = token(client)
        reviewed = client.post("/api/house-maxhinal/graft/preview",
                               headers=headers, json=request).json()
        result = client.post("/api/house-maxhinal/graft/measure",
                             headers=headers, json={
                                 **request,
                                 "expected_specimen_sha256": reviewed["specimen_sha256"],
                                 "expected_dogram_commit": reviewed["dogram_commit"],
                             }).json()
    with shelf._connect() as db:
        db.execute("UPDATE house_graft_witnesses SET payload_json=? WHERE witness_sha256=?",
                   ('{"changed":true}', result["witness_sha256"]))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.get("/api/house-maxhinal/graft/witnesses/" + result["witness_sha256"])
    assert response.status_code == 409


def test_graft_is_inside_native_ride_browser_without_background_execution(tmp_path: Path):
    config, _, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        js = client.get("/assets/graft-witness.js")
        native = client.get("/assets/native-maxhinal.js").text
    assert js.status_code == 200
    assert 'src="/assets/graft-witness.js"' in html
    assert "Preview declared GRAFT graph" in js.text
    assert "graftRenderForRide(ride, host)" in native
