"""OLD-GROWTH-002 pinned Git source verification and reviewed HOUSE GRAFT import."""
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
from static_workbench.graft_round import preview_round
from static_workbench.old_growth_import import preview as preview_sources, import_reviewed


def git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], check=True,
                            capture_output=True, text=True)
    return result.stdout.strip()


def make_checkout(root: Path, name: str, text: str) -> tuple[Path, str]:
    folder = root / name
    folder.mkdir()
    git(folder, "init", "-b", "main")
    git(folder, "remote", "add", "origin",
        f"https://github.com/the-static-collective/{name}.git")
    (folder / "old.txt").write_text(text, encoding="utf-8")
    git(folder, "add", "old.txt")
    git(folder, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "freeze source")
    return folder, git(folder, "rev-parse", "HEAD")


def fixture(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    a_dir, a_commit = make_checkout(root, "seedFORK", "α in an intact original.\n")
    b_dir, b_commit = make_checkout(root, "mundaneWORMHOLE", "a proposed seam\n")
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )
    def ref(name: str, commit: str, contents: str):
        return {
            "root_id": "static", "repo_path": name,
            "repository": f"the-static-collective/{name}",
            "commit": commit, "path": "old.txt",
            "start_byte": 0, "end_byte": len(contents.encode("utf-8")),
        }
    request = {
        "source_a": ref("seedFORK", a_commit, "α in an intact original.\n"),
        "source_b": ref("mundaneWORMHOLE", b_commit, "a proposed seam\n"),
        "keep": "Both original identities",
        "bend": "An intentionally provisional synthesis",
        "question": "What reversible experiment could compare these excerpts?",
        "relation_lane": "human_link",
        "move": "fuse",
    }
    return config, request, a_dir, b_dir


def token(client: TestClient) -> dict[str, str]:
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def test_verified_git_preview_is_inert_and_binds_exact_source_blobs(tmp_path):
    config, req, a_dir, b_dir = fixture(tmp_path)
    first = preview_sources(config, **req)
    assert first == preview_sources(config, **req)
    assert first["review"]["status"] == "review_required_before_import"
    assert all(s["origin_status"] == "verified_against_local_pinned_git_blob_only"
               and s["git_blob_sha"] == git(folder, "rev-parse", "HEAD:old.txt")
               for s, folder in zip(first["packet"]["sources"], (a_dir, b_dir)))
    assert first["packet"]["sources"][0]["excerpt"] == "α in an intact original.\n"
    assert first["packet"]["sources"][1]["repository"].endswith("/mundaneWORMHOLE")
    assert first["packet"]["authority"] == "none"
    assert first["packet"]["parallel_alternative"]["status"] == "LEFT_OPEN"
    assert first["receipt"]["status"] == "calculated_not_persisted"
    assert not (config.state_dir / "creator.sqlite3").exists()


def test_two_phase_guarded_import_is_idempotent_and_reaches_existing_graft(tmp_path):
    config, req, a_dir, b_dir = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        path = "/api/house-maxhinal/old-growth/"
        assert client.post(path + "preview", json=req).status_code == 403
        header = token(client)
        assert client.post(path + "preview", json=req,
                           headers={**header, "Origin": "http://evil.invalid"}).status_code == 403
        preview = client.post(path + "preview", json=req, headers=header)
        assert preview.status_code == 200, preview.text
        packet = preview.json()
        assert client.get("/api/house-maxhinal/rides").json()["rides"] == []
        body = {
            **req,
            "expected_packet_sha256": packet["packet_sha256"],
            "reviewed_excerpt_sha256": packet["review"]["source_excerpt_sha256"],
            "human_confirmed": True,
        }
        assert client.post(path + "import", json=body).status_code == 403
        assert client.post(path + "import", json={**body, "human_confirmed": False},
                           headers=header).status_code == 409
        assert client.post(path + "import", json={
            **body, "expected_packet_sha256": "0" * 64
        }, headers=header).status_code == 409
        assert client.post(path + "import", json={
            **body, "reviewed_excerpt_sha256": ["0" * 64, body["reviewed_excerpt_sha256"][1]]
        }, headers=header).status_code == 409
        first = client.post(path + "import", json=body, headers=header)
        assert first.status_code == 200, first.text
        receipt = first.json()["receipt"]
        assert first.json()["status"] == "local_ride_saved_not_grafted"
        assert receipt["replayed"] is False
        native = client.get(f"/api/house-maxhinal/rides/{receipt['id']}").json()
        assert native["engine"] == "house.old-growth-pinned-import/v0.2"
        assert native["source_refs"][0]["content_sha256"] == hashlib.sha256(
            (a_dir / "old.txt").read_bytes()).hexdigest()
        assert native["source_refs"][1]["excerpt"] == "a proposed seam\n"
        assert native["authority"] == "none" and native["promotion"] == "NONE"
        again = client.post(path + "import", json=body, headers=header)
        assert again.status_code == 200 and again.json()["receipt"]["replayed"] is True
        assert again.json()["receipt"]["id"] == receipt["id"]
        assert len(client.get("/api/house-maxhinal/rides").json()["rides"]) == 1
        graft = preview_round(
            client.app.state.creator_shelf,
            ride_id=receipt["id"], ride_sha256=receipt["ride_sha256"],
            keep="Preserve both roots", bend="Experimental instrument",
            intruder="Second old archive", move="fuse", relation_lane="human_link",
            question="May these excerpts inform a reversible fixture?",
        )
        assert graft["round"]["source_refs"] == native["source_refs"]
        assert graft["round"]["authority"] == "none"
        events = client.get("/api/events").json()["events"]
        assert sum(e["kind"] == "house.old_growth.local_ride_imported" for e in events) == 1
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get(f"/api/house-maxhinal/rides/{receipt['id']}").json()["ride_sha256"] == receipt["ride_sha256"]
        assert client.post(path + "import", json=body, headers=token(client)).json()["receipt"]["replayed"] is True
    assert git(a_dir, "status", "--porcelain") == ""
    assert git(b_dir, "status", "--porcelain") == ""


def test_modified_worktree_does_not_change_pinned_source_or_import(tmp_path):
    config, req, a_dir, _ = fixture(tmp_path)
    expected = preview_sources(config, **req)
    (a_dir / "old.txt").write_text("a newer working tree\n", encoding="utf-8")
    assert preview_sources(config, **req) == expected
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    admitted = import_reviewed(config, shelf, **req,
        expected_packet_sha256=expected["packet_sha256"],
        reviewed_excerpt_sha256=expected["review"]["source_excerpt_sha256"],
        human_confirmed=True)
    assert admitted["ride"]["source_refs"][0]["excerpt"] == "α in an intact original.\n"
    assert (a_dir / "old.txt").read_text() == "a newer working tree\n"


def test_refuses_changed_review_pinned_commit_and_local_remote_mismatch(tmp_path):
    config, req, a_dir, _ = fixture(tmp_path)
    original = preview_sources(config, **req)
    changed = json.loads(json.dumps(req))
    changed["source_a"]["start_byte"] = 1  # Mid-codepoint split
    with pytest.raises(ValueError, match="UTF-8"):
        preview_sources(config, **changed)
    changed = json.loads(json.dumps(req))
    changed["source_a"]["commit"] = "f" * 40
    with pytest.raises(ValueError):
        preview_sources(config, **changed)
    changed = json.loads(json.dumps(req))
    changed["source_a"]["repository"] = "the-static-collective/Dogram"
    with pytest.raises(ValueError, match="origin"):
        preview_sources(config, **changed)
    git(a_dir, "remote", "set-url", "origin", "https://evil.invalid/fake")
    with pytest.raises(ValueError, match="origin"):
        preview_sources(config, **req)
    assert original["packet"]["sources"][0]["repository"].endswith("/seedFORK")


def test_symlink_source_binary_or_submodule_and_unknown_input_refuse(tmp_path):
    config, req, a_dir, _ = fixture(tmp_path)
    (a_dir / "link.txt").symlink_to("old.txt")
    git(a_dir, "add", "link.txt")
    git(a_dir, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "-m", "symlink")
    modified = json.loads(json.dumps(req))
    modified["source_a"]["commit"] = git(a_dir, "rev-parse", "HEAD")
    modified["source_a"]["path"] = "link.txt"
    with pytest.raises(ValueError, match="regular Git blob"):
        preview_sources(config, **modified)
    modified["source_a"]["path"] = "../escape"
    with pytest.raises(ValueError, match="safe relative"):
        preview_sources(config, **modified)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.post("/api/house-maxhinal/old-growth/preview",
             json={**req, "stealth_authority": "execute"},
             headers=token(client)).status_code == 422
