from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def test_living_main_preview_is_session_guarded_and_read_only(tmp_path: Path):
    root = tmp_path / "root"
    repo = root / "sample"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("one\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    sha = git(repo, "rev-parse", "HEAD")
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),), max_repo_depth=2, preview_bytes=64,
    )
    payload = {"selections": [{
        "root_id": "static", "relative_path": "sample", "expected_sha": sha,
    }]}
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        denied = client.post("/api/living-main/preview", json=payload)
        assert denied.status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token, "origin": "http://127.0.0.1"}
        accepted = client.post("/api/living-main/preview", headers=headers, json=payload)
        assert accepted.status_code == 200
        assert accepted.json()["execution"] == "NOT_ATTEMPTED"
        assert accepted.json()["members"][0]["source_sha"] == sha
        invalid = client.post("/api/living-main/preview", headers=headers, json={**payload, "authority": "present"})
        assert invalid.status_code == 400
        cross_origin = client.post(
            "/api/living-main/preview", headers={**headers, "origin": "http://evil.example"}, json=payload
        )
        assert cross_origin.status_code == 403
    assert git(repo, "rev-parse", "HEAD") == sha
    assert not git(repo, "status", "--porcelain")
