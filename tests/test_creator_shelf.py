from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator import search_sources
from static_workbench.creator_shelf import CreatorConflict, CreatorShelf, preview_pack
from static_workbench.repos import discover_repositories


def fixture(tmp_path: Path):
    root = tmp_path / "root"
    for name in ("Dogram", "ALEX.2"):
        repo = root / name
        repo.mkdir(parents=True)
        subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
        (repo / "README.md").write_text("The house takes attendance.\n", encoding="utf-8")
    roots = (RootConfig("static", root),)
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=roots, max_repo_depth=2,
    )
    return config, root


def selection(config, repo_name):
    repos = discover_repositories(config.roots, config.max_repo_depth)
    result = search_sources(config.roots, repos, "static", repo_name, "house")
    assert len(result["hits"]) == 1
    hit = result["hits"][0]
    return {key: hit[key] for key in ("root_id", "repo_path", "source_path", "line", "file_sha256", "snippet")}


def headers(client):
    token = client.get("/api/bootstrap").json()["session_token"]
    return {"X-Workbench-Session": token}


def test_multi_repo_same_filename_remains_two_distinct_sources(tmp_path):
    config, _ = fixture(tmp_path)
    repos = discover_repositories(config.roots, 2)
    selections = [selection(config, "Dogram"), selection(config, "ALEX.2")]
    pack = preview_pack(config.roots, repos, selections)
    assert pack["source_count"] == 2
    assert pack["sources"][0]["source_path"] == pack["sources"][1]["source_path"] == "README.md"
    assert pack["sources"][0]["repo_path"] != pack["sources"][1]["repo_path"]
    assert pack["sources"][0]["file_sha256"] == hashlib.sha256(b"The house takes attendance.\n").hexdigest()
    assert pack["sources"][0]["source_kind"] == "local_worktree"
    with pytest.raises(ValueError, match="duplicate"):
        preview_pack(config.roots, repos, [selections[0], selections[0]])


def test_rejects_changed_source_and_symlink_even_if_target_is_inside_root(tmp_path):
    config, root = fixture(tmp_path)
    original = selection(config, "Dogram")
    file_path = root / "Dogram" / "README.md"
    file_path.write_text("The house was changed.\n", encoding="utf-8")
    with pytest.raises(CreatorConflict, match="changed"):
        preview_pack(config.roots, discover_repositories(config.roots, 2), [original])
    file_path.unlink()
    (root / "Dogram" / "other.md").write_text("The house takes attendance.\n", encoding="utf-8")
    file_path.symlink_to("other.md")
    with pytest.raises(ValueError, match="symlink"):
        preview_pack(config.roots, discover_repositories(config.roots, 2), [original])


def test_rejects_private_hidden_parent_and_oversized_source(tmp_path):
    config, root = fixture(tmp_path)
    base = selection(config, "Dogram")
    repos = discover_repositories(config.roots, 2)
    for source_path in ("../ALEX.2/README.md", ".git/config", "private-notes.md", "docs/.hidden.md"):
        bad = {**base, "source_path": source_path}
        with pytest.raises(ValueError):
            preview_pack(config.roots, repos, [bad])
    (root / "Dogram" / "huge.md").write_text("h" * 132000, encoding="utf-8")
    bad = {**base, "source_path": "huge.md"}
    with pytest.raises(ValueError):
        preview_pack(config.roots, repos, [bad])


def test_preview_and_persist_require_explicit_session_and_exact_digest(tmp_path):
    config, root = fixture(tmp_path)
    source = selection(config, "Dogram")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.post("/api/creator/packs/preview", json={"selections": [source]}).status_code == 403
        session = headers(client)
        assert client.post("/api/creator/packs/preview", headers={**session, "Origin": "http://evil.invalid"}, json={"selections": [source]}).status_code == 403
        preview = client.post("/api/creator/packs/preview", headers=session, json={"selections": [source]})
        assert preview.status_code == 200
        digest = preview.json()["pack_sha256"]
        mismatch = client.post("/api/creator/packs", headers=session, json={
            "selections": [source], "expected_pack_sha256": "0" * 64,
        })
        assert mismatch.status_code == 409
        assert client.get("/api/creator/packs").json()["packs"] == []
        (root / "Dogram" / "README.md").write_text("Modified between preview and save.\n", encoding="utf-8")
        stale = client.post("/api/creator/packs", headers=session, json={
            "selections": [source], "expected_pack_sha256": digest,
        })
        assert stale.status_code == 409
        assert client.get("/api/creator/packs").json()["packs"] == []


def test_pack_snapshot_and_draft_revisions_survive_restart_without_touching_repo(tmp_path):
    config, root = fixture(tmp_path)
    original = (root / "Dogram" / "README.md").read_bytes()
    source = selection(config, "Dogram")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        session = headers(client)
        preview = client.post("/api/creator/packs/preview", headers=session, json={"selections": [source]}).json()
        saved = client.post("/api/creator/packs", headers=session, json={
            "selections": [source], "expected_pack_sha256": preview["pack_sha256"],
        })
        assert saved.status_code == 200
        pack_id = saved.json()["id"]
        payload = {
            "pack_id": pack_id, "expected_revision": 0, "title": "The House",
            "kind": "lyric", "body": "First take", "assumptions": "Metaphor, not evidence",
            "gaps": "Unresolved ending",
        }
        draft = client.post("/api/creator/drafts", headers=session, json=payload)
        assert draft.status_code == 200
        draft_id = draft.json()["id"]
        assert draft.json()["revision"] == 1
        assert client.post("/api/creator/drafts/" + str(draft_id) + "/revisions",
            headers=session, json={**payload, "expected_revision": 0, "body": "stale"}).status_code == 409
        second = client.post("/api/creator/drafts/" + str(draft_id) + "/revisions",
            headers=session, json={**payload, "expected_revision": 1, "body": "Second take"})
        assert second.status_code == 200 and second.json()["revision"] == 2
        assert client.post("/api/creator/drafts/" + str(draft_id) + "/revisions",
            headers=session, json={**payload, "expected_revision": 2, "pack_id": 999}).status_code == 409

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        latest = client.get("/api/creator/drafts/" + str(draft_id)).json()
        assert latest["body"] == "Second take"
        assert latest["revision"] == 2 and latest["status"] == "local_draft"
        assert latest["assumptions"] == "Metaphor, not evidence"
        assert client.get("/api/creator/drafts/" + str(draft_id) + "/revisions").json()["revisions"][0]["revision"] == 2
        assert client.get("/api/creator/packs/" + str(pack_id)).json()["pack_sha256"] == preview["pack_sha256"]
        assert client.get("/api/creator/packs").json()["packs"][0]["id"] == pack_id
        assert client.get("/api/creator/drafts").json()["drafts"][0]["id"] == draft_id
    assert (root / "Dogram" / "README.md").read_bytes() == original


def test_draft_failed_write_preserves_previous_revision(tmp_path):
    shelf = CreatorShelf(tmp_path / "state" / "creator.sqlite3")
    pack = {"pack_sha256": "a" * 64, "source_count": 1, "sources": []}
    pack_id = shelf.save_pack(pack)["id"]
    payload = {"pack_id": pack_id, "title": "Title", "kind": "brief", "body": "original", "assumptions": "", "gaps": ""}
    saved = shelf.save_revision(None, 0, payload)
    with pytest.raises(ValueError):
        shelf.save_revision(saved["id"], 1, {**payload, "body": "X" * 33000})
    assert shelf.get_draft(saved["id"])["body"] == "original"
    assert len(shelf.revisions(saved["id"])) == 1


def test_creator_ui_assets_and_manual_export_boundary(tmp_path):
    config, _ = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        js = client.get("/assets/creator-v02.js")
    assert js.status_code == 200
    assert "/assets/creator-v02.js" in html
    assert "Preview selected source pack" in js.text
    assert "Save exactly this pack locally" in js.text
    assert "Copy draft + source references (manual handoff)" in js.text
    assert "navigator.clipboard" in js.text
    assert "publish(" not in js.text
