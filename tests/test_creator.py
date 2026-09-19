from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator import creator_desk_status, search_sources
from static_workbench.repos import discover_repositories


def setup_repo(tmp_path: Path):
    root = tmp_path / "root"
    repo = root / "the-autodisco"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
    (repo / "README.md").write_text("The house takes attendance.\nOriginal lines stay attributable.\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "study.md").write_text("A research receipt is not an authority.\n", encoding="utf-8")
    (repo / "notes").mkdir()
    (repo / "notes" / "credentials.md").write_text("Secret phrase house, never index this.\n", encoding="utf-8")
    roots = (RootConfig("static", root),)
    repos = discover_repositories(roots, max_depth=2)
    return root, repo, roots, repos


def test_creator_routes_show_local_presence_without_claiming_execution(tmp_path: Path):
    _, _, _, repos = setup_repo(tmp_path)
    desk = creator_desk_status(repos)
    recall = next(item for item in desk["workflows"] if item["id"] == "recall")
    assert recall["status"] == "inspectable"
    assert [item["name"] for item in recall["local_sources"]] == ["the-autodisco"]
    assert desk["workflows"][2]["status"] == "not_discovered"
    assert "plugin route != local plugin execution" in desk["laws"]


def test_source_search_has_attributable_lines_and_excludes_sensitive_names(tmp_path: Path):
    _, repo, roots, repos = setup_repo(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("The house is outside the configured root.\n", encoding="utf-8")
    (repo / "docs" / "leak.md").symlink_to(outside)
    (repo / "docs" / ".private.md").write_text("The house is hidden.\n", encoding="utf-8")

    result = search_sources(roots, repos, "static", "the-autodisco", "house")

    assert result["source_kind"] == "local_worktree"
    assert result["authority"] == "none"
    assert [(hit["source_path"], hit["line"]) for hit in result["hits"]] == [("README.md", 1)]
    assert result["hits"][0]["snippet"] == "The house takes attendance."
    assert result["hits"][0]["dirty"] is True
    assert result["files_examined"] == 2


def test_search_requires_chosen_discovered_repo_and_bounded_query(tmp_path: Path):
    _, _, roots, repos = setup_repo(tmp_path)
    for root_id, repo_path, query in [
        ("static", "../outside", "house"),
        ("absent", "the-autodisco", "house"),
        ("static", "the-autodisco", "x"),
        ("static", "the-autodisco", "x" * 101),
    ]:
        with pytest.raises(ValueError):
            search_sources(roots, repos, root_id, repo_path, query)


def test_creator_api_and_navigation_are_read_only_and_available(tmp_path: Path):
    root, _, roots, _ = setup_repo(tmp_path)
    config = WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=roots,
        max_repo_depth=2,
    )
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        desk = client.get("/api/creator/desk")
        matches = client.get("/api/creator/sources", params={
            "root_id": "static", "repo_path": "the-autodisco", "query": "research receipt",
        })
        bad = client.get("/api/creator/sources", params={
            "root_id": "static", "repo_path": "../outside", "query": "research",
        })
        html = client.get("/").text
        js = client.get("/assets/app.js").text
    assert desk.status_code == 200
    assert matches.status_code == 200
    assert matches.json()["hits"][0]["source_path"] == "docs/study.md"
    assert bad.status_code == 400
    assert 'data-view="creator"' in html
    assert "/api/creator/desk" in js
    assert "/api/creator/sources" in js
    assert "Copy source handoff" in js
