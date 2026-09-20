"""HOUSE-FLYWHEEL-002: read-only API and DOM-safety contract tests."""
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def make_app(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )
    return create_app(config)


def sample_report(return_id="local:flight-1:return-1"):
    return {
        "return_id": return_id,
        "flight_ref": "local:flight-1",
        "source_owner": "the-static-collective/static-workbench",
        "source_ref": "local:fixture@sha256:abc",
        "effect_state": "scope_uncertain",
        "parent_effect_ref": None,
        "artifacts": [
            {"artifact_ref": "fixture:one", "owner": "static-workbench",
             "kind": "test-fixture", "capability_state": "reported",
             "evidence_refs": ["local:unverified-test"]}
        ],
        "capability_delta": "Potential reuse only; not tested independently.",
        "evidence_refs": ["local:unverified-test"],
        "resource_costs": "unknown",
        "nonclaims": ["No source authentication, effect verification, or authorization."],
        "proposed_next": ["Human could inspect an independent reuse experiment."],
    }


def test_return_shelf_empty_and_no_implicit_operational_event_import(tmp_path):
    app = make_app(tmp_path)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        app.state.journal.append("flight.completed", {"return_id": "not-a-capability-return"})
        result = client.get("/api/house/returns")
        assert result.status_code == 200
        assert result.json()["format"] == "house.capability-return-shelf/v0"
        assert result.json()["verification"] == "not_evaluated"
        assert result.json()["records"] == []
        assert client.post("/api/house/returns", json=sample_report()).status_code == 405


def test_return_shelf_reads_existing_reports_persistently_and_preserves_nonclaims(tmp_path):
    app = make_app(tmp_path)
    original = sample_report()
    first = app.state.return_ledger.append(original)
    new = sample_report("local:flight-2:return-1")
    new["parent_effect_ref"] = first.packet["return_id"]
    app.state.return_ledger.append(new)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        result = client.get("/api/house/returns", params={"limit": 1})
        assert result.status_code == 200
        assert len(result.json()["records"]) == 1
        assert result.json()["records"][0]["packet"] == new
        assert result.json()["verification"] == "not_evaluated"
        detail = client.get("/api/house/returns/local:flight-1:return-1")
        assert detail.status_code == 200
        assert detail.json()["record"]["packet"] == original
        assert detail.json()["record"]["local_digest"] == first.local_digest
    reopened = make_app_from_existing(tmp_path)
    with TestClient(reopened, base_url="http://127.0.0.1") as client:
        assert len(client.get("/api/house/returns").json()["records"]) == 2


def make_app_from_existing(tmp_path):
    root = tmp_path / "root"
    return create_app(WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    ))


def test_return_shelf_rejects_invalid_limits_and_unknown_or_oversized_identity(tmp_path):
    app = make_app(tmp_path)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        for value in ("0", "101", "nan", "-1", "1.5"):
            assert client.get("/api/house/returns", params={"limit": value}).status_code == 422
        assert client.get("/api/house/returns/no-such-return").status_code == 404
        assert client.get("/api/house/returns/" + "a" * 513).status_code == 404


def test_return_shelf_displays_hostile_fields_only_as_text_and_never_exposes_write_controls(tmp_path):
    app = make_app(tmp_path)
    hostile = sample_report()
    hostile["capability_delta"] = "<img src=x onerror=alert(1)>"
    hostile["nonclaims"] = ["<script>window.unsafe=true</script>"]
    hostile["artifacts"][0]["artifact_ref"] = "javascript:alert(1)"
    app.state.return_ledger.append(hostile)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        script = client.get("/assets/return-shelf.js").text
        report = client.get("/api/house/returns").json()["records"][0]["packet"]
        assert report["capability_delta"] == hostile["capability_delta"]
        assert 'data-view="returns"' in html
        assert "/assets/return-shelf.js" in html
        assert "/api/house/returns?limit=50" in script
        assert "textContent" in script or "el(" in script
        assert "innerHTML" not in script
        assert "createElement('a')" not in script
        assert "fetch(" not in script
        assert "method: 'POST'" in script  # the separate, inert Loom preview only
        assert "'/api/house/loom/preview'" in script
        assert "'/api/house/returns'" not in script  # no import/write target
        assert 'REPORTED · NOT INDEPENDENTLY VERIFIED' in script
