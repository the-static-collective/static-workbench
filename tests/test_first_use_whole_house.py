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
