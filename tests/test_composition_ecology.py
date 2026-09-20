"""COMPOSITION-ECOLOGY-001: deterministic lineage, refusal and read-only HTTP gates."""
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.capability_returns import CapabilityReturnLedger
from static_workbench.composition_ecology import preview_ecology
from static_workbench.config import RootConfig, WorkbenchConfig


def packet(name, ref):
    return {
        "return_id": "return-" + name,
        "flight_ref": "flight-" + name,
        "source_owner": "owner-" + name,
        "source_ref": "source-" + name,
        "effect_state": "scope_uncertain",
        "parent_effect_ref": None,
        "artifacts": [{
            "artifact_ref": ref, "owner": "owner-" + name, "kind": "example",
            "capability_state": "reported", "evidence_refs": ["self-report-" + name],
        }],
        "capability_delta": "reported, not independently verified",
        "evidence_refs": ["self-report-" + name],
        "resource_costs": "unknown",
        "nonclaims": ["No independently verified compatibility or permission."],
        "proposed_next": [],
    }


def fixture(tmp_path):
    ledger = CapabilityReturnLedger(tmp_path / "returns.sqlite3")
    rows = [ledger.append(packet(name, ref)) for name, ref in (
        ("one", "alpha"), ("two", "beta")
    )]
    request = {
        "question": "Could these artifacts support a new instrument?",
        "selections": [
            {"return_id": row.packet["return_id"], "local_digest": row.local_digest,
             "owner": row.packet["artifacts"][0]["owner"],
             "artifact_ref": row.packet["artifacts"][0]["artifact_ref"]}
            for row in rows
        ],
    }
    return ledger, request


def test_ecology_three_distinct_descendants_with_exact_unchanged_parents(tmp_path):
    ledger, request = fixture(tmp_path)
    before = ledger.latest()
    first = preview_ecology(ledger, request)
    assert preview_ecology(ledger, deepcopy(request)) == first
    assert ledger.latest() == before
    assert first["format"] == "house.composition-ecology/v0"
    assert first["execution"] == "not_attempted"
    assert first["human_continuation"] == "not_selected"
    assert [c["operator"] for c in first["candidates"]] == ["BRAID", "CROSS", "MUTATE"]
    assert len({c["candidate_digest"] for c in first["candidates"]}) == 3
    assert len({c["hypothesis"] for c in first["candidates"]}) == 3
    for card in first["candidates"]:
        assert card["parents"] == [p["identity"] for p in first["capability_packs"]]
        assert card["parent_loom_digest"] == first["source_loom_digest"]
        assert card["state"] == "inert_unrun"
        assert card["declared_effects"] == []
        assert card["execution"] == "not_attempted"
        assert card["compatibility"] == card["authorization"] == "not_evaluated"
        assert card["context_diet"]["unavailable"]
        assert all(0 <= parent < 2 for phase in card["phases"] for parent in phase["parents"])
    assert first["candidates"][2]["parent_roles"] == ["proposed_base", "influence_only"]
    assert first["candidates"][2]["inheritance"]["parent_1"] == "influence_only"
    assert all(p["input_contract"] == p["output_contract"] == "unknown"
               for p in first["capability_packs"])


@pytest.mark.parametrize("tamper", [
    lambda q: q.update({"execute": True}),
    lambda q: q["selections"][0].update({"authorized": True}),
    lambda q: q["selections"][0].update({"local_digest": "0" * 64}),
    lambda q: q["selections"].pop(),
    lambda q: q["selections"].append(deepcopy(q["selections"][0])),
    lambda q: q.update({"question": " "}),
])
def test_ecology_inherits_loom_refusals(tmp_path, tamper):
    ledger, request = fixture(tmp_path)
    tamper(request)
    with pytest.raises(ValueError):
        preview_ecology(ledger, request)


def test_http_requires_local_session_and_does_not_write_or_execute(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    ))
    ledger = app.state.return_ledger
    source, request = fixture(tmp_path / "other")
    for row in source.latest():
        ledger.append(row.packet)
    before = ledger.latest()
    with TestClient(app, base_url="http://127.0.0.1") as client:
        endpoint = "/api/house/ecology/preview"
        assert client.post(endpoint, json=request).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        assert client.post(endpoint, json=request, headers={
            **headers, "origin": "http://evil.example",
        }).status_code == 403
        response = client.post(endpoint, json=request, headers=headers)
        assert response.status_code == 200, response.text
        body = response.json()
        assert len(body["candidates"]) == 3
        assert body["declared_effects"] == []
        assert client.get(endpoint).status_code == 405
    assert ledger.latest() == before
    assert list(root.iterdir()) == []


def test_ecology_browser_is_opt_in_and_uses_safe_text_nodes(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    ))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        js = client.get("/assets/return-shelf.js").text
    assert "Preview three composition candidates" in js
    assert "/api/house/ecology/preview" in js
    assert "INERT / UNRUN / NOT AUTHORIZED" in js
    assert "textContent" in js
    assert "innerHTML" not in js
