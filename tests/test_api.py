from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def make_config(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    (root / "hello.txt").write_text("hello static\n", encoding="utf-8")
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
        max_repo_depth=2,
        preview_bytes=64,
    )


def client_for(config: WorkbenchConfig) -> TestClient:
    return TestClient(create_app(config), base_url="http://127.0.0.1")


def test_bootstrap_returns_root_contract_and_session_token(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        response = client.get("/api/bootstrap")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "0.2.0"
    assert body["roots"] == [{"id": "static", "path": str(config.roots[0].path)}]
    assert isinstance(body["session_token"], str)
    assert len(body["session_token"]) >= 20


def test_rejects_unapproved_host_header(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        response = client.get("/api/bootstrap", headers={"host": "evil.example"})

    assert response.status_code == 400


def test_object_inspection_rejects_traversal(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        response = client.get(
            "/api/objects/inspect",
            params={"root_id": "static", "path": "../outside.txt"},
        )

    assert response.status_code == 400
    assert "outside" in response.json()["detail"].lower() or "traversal" in response.json()["detail"].lower()


def test_object_inspection_returns_preview_and_emits_durable_event(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        response = client.get(
            "/api/objects/inspect",
            params={"root_id": "static", "path": "hello.txt"},
        )
        events = client.get("/api/events").json()["events"]

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "file"
    assert body["preview"] == "hello static\n"
    assert any(event["kind"] == "object.inspected" for event in events)

    with client_for(config) as client:
        reopened_events = client.get("/api/events").json()["events"]

    assert any(event["kind"] == "object.inspected" for event in reopened_events)


def test_repos_and_machine_endpoints_are_live(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        repos = client.get("/api/repos")
        machine = client.get("/api/machine")

    assert repos.status_code == 200
    assert "repos" in repos.json()
    assert machine.status_code == 200
    assert "cpu_percent" in machine.json()
    assert "temperatures" in machine.json()


def test_house_endpoint_separates_presence_from_readiness(tmp_path: Path):
    config = make_config(tmp_path)
    repo = config.roots[0].path / "static-live"
    repo.mkdir()
    import subprocess
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
    (repo / "package.json").write_text("{}\n", encoding="utf-8")

    with client_for(config) as client:
        response = client.get("/api/house")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["repos"] == 1
    static_live = next(item for item in body["organs"] if item["id"] == "static-live")
    assert static_live["present"] is True
    assert static_live["repo"]["stacks"] == ["node"]
    assert "present != ready" in body["laws"]


def test_aperture_analysis_preserves_ambiguity_then_narrows_as_child_cut(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        first = client.post(
            "/api/aperture/analyze",
            json={"raw_text": "The bank moved."},
        )
        assert first.status_code == 200
        first_body = first.json()
        assert first_body["analysis"]["status"] == "unresolved"
        assert [item["id"] for item in first_body["analysis"]["readings"]] == [
            "bank.financial",
            "bank.river",
            "bank.maneuver",
        ]

        second = client.post(
            "/api/aperture/analyze",
            json={
                "raw_text": "The bank moved.",
                "context_text": "After the flood, the bank moved six feet east.",
                "parent_id": first_body["id"],
            },
        )
        assert second.status_code == 200
        second_body = second.json()
        assert second_body["parent_id"] == first_body["id"]
        assert second_body["analysis"]["status"] == "narrowed"
        assert [item["id"] for item in second_body["analysis"]["readings"]] == ["bank.river"]

        history = client.get("/api/aperture/history").json()["sense_fields"]
        assert [item["id"] for item in history[:2]] == [second_body["id"], first_body["id"]]
        assert history[1]["analysis"]["status"] == "unresolved"
        assert any(event["kind"] == "aperture.analyzed" for event in client.get("/api/events").json()["events"])

    with client_for(config) as client:
        reopened = client.get("/api/aperture/history").json()["sense_fields"]

    assert [item["id"] for item in reopened[:2]] == [second_body["id"], first_body["id"]]
    assert reopened[1]["analysis"]["status"] == "unresolved"


def test_aperture_rejects_unknown_parent_and_cross_carrier_parent(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        unknown = client.post(
            "/api/aperture/analyze",
            json={"raw_text": "The bank moved.", "parent_id": 999},
        )
        assert unknown.status_code == 400

        first = client.post(
            "/api/aperture/analyze",
            json={"raw_text": "The bank moved."},
        ).json()
        mismatch = client.post(
            "/api/aperture/analyze",
            json={"raw_text": "A different carrier.", "parent_id": first["id"]},
        )
        assert mismatch.status_code == 400
        assert "same raw carrier" in mismatch.json()["detail"].lower()


def test_aperture_rejects_blank_or_oversized_input(tmp_path: Path):
    config = make_config(tmp_path)

    with client_for(config) as client:
        blank = client.post("/api/aperture/analyze", json={"raw_text": "   "})
        oversized = client.post("/api/aperture/analyze", json={"raw_text": "x" * 20001})

    assert blank.status_code == 422
    assert oversized.status_code == 422
