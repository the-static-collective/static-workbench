from __future__ import annotations

import json
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def git(path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def commit(path: Path, message: str) -> None:
    git(path, "add", ".")
    git(path, "-c", "user.name=House Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-m", message)


def setup(tmp_path: Path) -> tuple[WorkbenchConfig, Path, Path]:
    root = tmp_path / "root"
    repo = root / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    (repo / "pyproject.toml").write_text('[project]\nname="demo"\nversion="0.0.1"\n')
    (repo / "a.py").write_text("x = 1\n")
    commit(repo, "baseline")
    (repo / "b.py").write_text("from a import x\n")
    commit(repo, "candidate")

    dogram = root / "Dogram"
    dogram.mkdir()
    git(dogram, "init", "-b", "main")
    (dogram / ".gitignore").write_text("__pycache__/\n")
    package = dogram / "dogram"
    package.mkdir()
    (package / "__init__.py").write_text("")
    # Deliberately isolated contract fixture, not a claim to run upstream Dogram.
    (package / "repo_impact.py").write_text(
        "from pathlib import Path\n"
        "def build_repo_impact(baseline, candidate):\n"
        "    left = {p.relative_to(baseline).as_posix() for p in Path(baseline).rglob('*.py')}\n"
        "    right = {p.relative_to(candidate).as_posix() for p in Path(candidate).rglob('*.py')}\n"
        "    return {'graph_before_digest': 'fixture', 'graph_after_digest': 'fixture',\n"
        "            'node_delta': {'added': sorted(right-left), 'removed': sorted(left-right)},\n"
        "            'edge_delta': {'added': [], 'removed': []},\n"
        "            'reachability_delta': {'gained': [], 'lost': []}}\n"
    )
    commit(dogram, "test adapter")
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
        max_repo_depth=2,
    )
    return config, repo, dogram


def preview(client: TestClient, token: str):
    return client.post("/api/dogram/impact/preview",
                       headers={"x-workbench-session": token},
                       json={"root_id": "static", "repo_path": "demo"})


def run(client: TestClient, token: str, p: dict):
    return client.post(
        "/api/dogram/impact/run",
        headers={"x-workbench-session": token},
        json={
            "root_id": "static", "repo_path": "demo",
            "expected_input_sha256": p["input_sha256"],
            "expected_candidate_commit": p["candidate_commit"],
            "expected_dogram_commit": p["dogram"]["commit"],
        },
    )


def test_impact_preview_requires_session_and_fixes_two_commit_snapshots(tmp_path: Path):
    config, repo, _ = setup(tmp_path)
    (repo / "b.py").write_text("import os\n")  # uncommitted changes must be excluded
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        no_token = client.post("/api/dogram/impact/preview",
                               json={"root_id": "static", "repo_path": "demo"})
        token = client.get("/api/bootstrap").json()["session_token"]
        response = preview(client, token)
        unknown = client.post("/api/dogram/impact/preview",
                              headers={"x-workbench-session": token},
                              json={"root_id": "static", "repo_path": "../demo"})
    assert no_token.status_code == 403
    assert unknown.status_code == 409
    assert response.status_code == 200, response.text
    p = response.json()
    assert p["baseline_file_count"] == 1
    assert p["candidate_file_count"] == 2
    assert p["baseline_commit"] != p["candidate_commit"]
    assert p["working_tree_dirty"] is True
    assert p["working_tree_excluded"] is True
    assert p["dogram"]["available"] and p["dogram"]["clean"]


def test_impact_handoff_is_explicit_and_report_survives_restart(tmp_path: Path):
    config, repo, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        p = preview(client, token).json()
        receipt = run(client, token, p)
        assert receipt.status_code == 200, receipt.text
        result = receipt.json()
        assert result["report"]["dogram_internal_result"]["node_delta"]["added"] == ["b.py"]
        assert result["report"]["schema"] == "house.dogram-impact-report/v0.1"
        assert "not a dogram.receipt/v0 public operator receipt" in result["report"]["non_claims"]
        assert "b.py" in result["report"]["dogram_internal_result"]["node_delta"]["added"]
        assert any(e["kind"] == "dogram.impact.saved" for e in client.get("/api/events").json()["events"])

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        saved = client.get("/api/dogram/impact/reports/" + result["report_id"])
    assert saved.status_code == 200
    assert saved.json() == result
    path = config.state_dir / "dogram-impact" / (result["report_id"] + ".json")
    path.write_bytes(path.read_bytes() + b" ")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        corrupted = client.get("/api/dogram/impact/reports/" + result["report_id"])
    assert corrupted.status_code == 404


def test_impact_refuses_moved_head_and_changed_dogram(tmp_path: Path):
    config, repo, dogram = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        old = preview(client, token).json()
        (repo / "c.py").write_text("z = 3\n")
        commit(repo, "new candidate")
        assert run(client, token, old).status_code == 409
        fresh = preview(client, token).json()
        (dogram / "new.txt").write_text("dirty")
        refused = run(client, token, fresh)
        assert refused.status_code == 409
        assert "clean" in refused.json()["detail"].lower()


def test_impact_refuses_symlinked_python_source_in_committed_tree(tmp_path: Path):
    config, repo, _ = setup(tmp_path)
    (repo / "linked.py").symlink_to("a.py")
    commit(repo, "source symlink")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        response = preview(client, token)
    assert response.status_code == 409
    assert "unsafe" in response.json()["detail"].lower()


def test_impact_ui_asset_is_wired_without_automatic_invocation(tmp_path: Path):
    config, _, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        js = client.get("/assets/dogram-impact.js")
        app = client.get("/assets/app.js").text
    assert 'data-view="dogram-impact"' in html
    assert js.status_code == 200
    assert "Run exactly this Dogram comparison" in js.text
    assert "renderDogramImpactDesk" in app
