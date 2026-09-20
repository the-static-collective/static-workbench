"""BRANCH-DECK-004 synthetic public API: no network or project execution."""
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from static_workbench.app import create_app
from static_workbench.branch_radar import CollectiveRadar
from static_workbench.branch_remote import RemoteDiscoveryError
from static_workbench.config import RootConfig, WorkbenchConfig


def owner_repo(name: str):
    return {"name": name, "full_name": "the-static-collective/" + name,
            "owner": {"login": "the-static-collective"}, "fork": False,
            "archived": False}


def test_baseline_then_new_branch_and_updated_commit_are_distinct(monkeypatch, tmp_path: Path):
    fixture = {"refs": [
        {"name": "main", "commit": {"sha": "a" * 40}},
        {"name": "feat/first", "commit": {"sha": "b" * 40}},
    ], "calls": []}
    def github(path: str):
        fixture["calls"].append(path)
        if path.startswith("/users/"):
            return [owner_repo("demo")]
        if path.startswith("/repos/the-static-collective/demo/branches?"):
            return fixture["refs"]
        raise AssertionError(path)
    monkeypatch.setattr("static_workbench.branch_radar._github_json", github)
    radar = CollectiveRadar(tmp_path / "state")
    first = radar.scan_once()
    snapshot = radar.snapshot()
    assert first["repos_scanned"] == ["the-static-collective/demo"]
    assert snapshot["all_repositories_observed"] is True
    assert all(item["baseline"] for item in snapshot["branches"])
    assert all(item["readiness"] == "not_tested" for item in snapshot["branches"])
    assert snapshot["branches"][0]["url"].startswith("https://github.com/the-static-collective/demo/tree/")
    fixture["refs"][1]["commit"]["sha"] = "c" * 40
    fixture["refs"].append({"name": "feat/new", "commit": {"sha": "d" * 40}})
    radar.scan_once()
    cards = {row["name"]: row for row in radar.snapshot()["branches"]}
    assert cards["feat/new"]["baseline"] is False
    assert cards["feat/first"]["baseline"] is True
    assert cards["feat/first"]["commit"] == "c" * 40
    assert CollectiveRadar(tmp_path / "state").snapshot()["branches"]
    assert len(fixture["calls"]) == 4  # one repo-list and one branch-list per cycle


def test_bounded_rotation_across_six_repositories(monkeypatch, tmp_path: Path):
    calls = []
    def github(path: str):
        calls.append(path)
        if path.startswith("/users/"):
            return [owner_repo(f"repo-{index}") for index in range(6)]
        return [{"name": "main", "commit": {"sha": "a" * 40}}]
    monkeypatch.setattr("static_workbench.branch_radar._github_json", github)
    radar = CollectiveRadar(tmp_path / "state")
    a = radar.scan_once()
    assert len(a["repos_scanned"]) == 5
    assert a["cursor"] == "5"
    assert len(calls) == 6
    assert radar.snapshot()["all_repositories_observed"] is False
    b = radar.scan_once()
    assert len(b["repos_scanned"]) == 5
    assert "the-static-collective/repo-5" in b["repos_scanned"]
    assert radar.snapshot()["all_repositories_observed"] is True


def test_failed_repo_preserves_prior_observation_and_exposes_gap(monkeypatch, tmp_path: Path):
    enabled = {"ok": True}
    def github(path: str):
        if path.startswith("/users/"):
            return [owner_repo("demo")]
        if enabled["ok"]:
            return [{"name": "feat/live", "commit": {"sha": "a" * 40}}]
        raise RemoteDiscoveryError("github_http_403")
    monkeypatch.setattr("static_workbench.branch_radar._github_json", github)
    radar = CollectiveRadar(tmp_path / "state")
    radar.scan_once()
    enabled["ok"] = False
    result = radar.scan_once()
    assert result["errors"]
    snapshot = radar.snapshot()
    assert snapshot["branches"][0]["commit"] == "a" * 40
    assert "github_http_403" in snapshot["last_error"]


def test_one_full_branch_page_is_explicitly_incomplete(monkeypatch, tmp_path: Path):
    def github(path: str):
        if path.startswith("/users/"):
            return [owner_repo("demo")]
        return [{"name": f"feat/n-{index}", "commit": {"sha": "a" * 40}}
                for index in range(100)]
    monkeypatch.setattr("static_workbench.branch_radar._github_json", github)
    radar = CollectiveRadar(tmp_path / "state")
    radar.scan_once()
    assert radar.snapshot()["branches"][0]["scan_complete"] is False


def test_disabled_api_never_starts_public_scan(monkeypatch, tmp_path: Path):
    monkeypatch.setattr("static_workbench.branch_radar._github_json",
                        lambda path: pytest.fail("disabled radar must not make network calls"))
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        snapshot = client.get("/api/branches/radar")
        js = client.get("/assets/branch-deck.js")
    assert snapshot.status_code == 200
    assert snapshot.json()["enabled"] is False
    assert "/api/branches/radar" in js.text
