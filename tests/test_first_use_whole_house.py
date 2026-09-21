"""First-use flight board: assembled surfaces remain observational until reviewed."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def test_first_use_board_and_arrival_are_read_only(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    root.mkdir()
    config = WorkbenchConfig("127.0.0.1", 13700, tmp_path / "state",
                             (RootConfig("static", root),))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        index = client.get("/")
        assert index.status_code == 200
        assert "/assets/creator-context-door.js" in index.text
        assert "/assets/creator-context-door.css" in index.text
        assert client.get("/assets/creator-context-door.js").status_code == 200
        board = client.get("/assets/launchpad.js")
        assert board.status_code == 200
        assert "WORKBENCH FIRST FLIGHT" in board.text
        assert "/api/arrival" in board.text
        assert "creatorV2Load()" in board.text
        response = client.get("/api/arrival")
        assert response.status_code == 200
        report = response.json()
        assert report["version"] == "house.arrival/v0.1"
        assert len(report["organs"]) >= 10
        assert all(o["installed"] == "not_evaluated" and o["ready"] == "not_evaluated"
                   and o["authorized"] is False for o in report["organs"])
        assert all(o["observed"] == "not_discovered" for o in report["organs"])
        assert client.post("/api/arrival", json={"execute": "sudo reboot"}).status_code == 405
        assert client.get("/api/launchpad").json()["automatic_actions"] == []
    assert list(root.iterdir()) == []


def test_real_creator_shelf_save_then_arrival_reentry(tmp_path: Path) -> None:
    """Cross the actual app/shelf boundary, not the synthetic ARRIVAL fixture."""
    import hashlib
    import subprocess

    from static_workbench.arrival import creator_reentry
    from static_workbench.creator import search_sources
    from static_workbench.repos import discover_repositories

    root = tmp_path / "projects"
    repo = root / "Dogram"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"],
                   check=True, capture_output=True)
    original = "The house takes attendance.\\n"
    (repo / "README.md").write_text(original, encoding="utf-8")
    config = WorkbenchConfig("127.0.0.1", 13700, tmp_path / "state",
                             (RootConfig("static", root),), max_repo_depth=2)
    repos = discover_repositories(config.roots, config.max_repo_depth)
    hit = search_sources(config.roots, repos, "static", "Dogram", "house")["hits"][0]
    selected = {key: hit[key] for key in
                ("root_id", "repo_path", "source_path", "line", "file_sha256", "snippet")}
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"X-Workbench-Session": token}
        preview = client.post("/api/creator/packs/preview", headers=headers,
                              json={"selections": [selected]})
        assert preview.status_code == 200
        saved = client.post("/api/creator/packs", headers=headers, json={
            "selections": [selected],
            "expected_pack_sha256": preview.json()["pack_sha256"],
        })
        assert saved.status_code == 200
        pack_id = saved.json()["id"]
        draft = client.post("/api/creator/drafts", headers=headers, json={
            "pack_id": pack_id, "expected_revision": 0, "title": "First flight",
            "kind": "lyric", "body": "A new song", "assumptions": "", "gaps": "",
        })
        assert draft.status_code == 200
        draft_id = draft.json()["id"]
    pointer = creator_reentry(config.state_dir, draft_id)
    assert pointer["draft_id"] == draft_id
    assert pointer["pack_id"] == pack_id
    assert pointer["pack_sha256"] == preview.json()["pack_sha256"]
    assert pointer["body_sha256"] == hashlib.sha256(b"A new song").hexdigest()
    assert pointer["source_current"] == "not_checked"
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get(f"/api/creator/drafts/{draft_id}").status_code == 200
    assert creator_reentry(config.state_dir, draft_id) == pointer
    assert (repo / "README.md").read_text(encoding="utf-8") == original
