"""HOUSE-FLYWHEEL-003: exact-reference, no-effect composition preview."""
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.capability_loom import preview_composition
from static_workbench.capability_returns import CapabilityReturnLedger
from static_workbench.config import RootConfig, WorkbenchConfig


def reported_return(name, artifact_name):
    return {
        "return_id": f"local:{name}:return",
        "flight_ref": f"local:{name}",
        "source_owner": "static-workbench",
        "source_ref": f"local:ref:{name}",
        "effect_state": "scope_uncertain",
        "parent_effect_ref": None,
        "artifacts": [
            {"artifact_ref": artifact_name, "owner": "static-workbench",
             "kind": "test-fixture", "capability_state": "reported",
             "evidence_refs": [f"local:reported:{name}"]}
        ],
        "capability_delta": "Possible fixture reuse, not independently verified.",
        "evidence_refs": [f"local:reported:{name}"],
        "resource_costs": "unmeasured",
        "nonclaims": ["No source verification or effect authorization."],
        "proposed_next": ["Explore an inert composition proposal."],
    }


def setup(tmp_path: Path):
    ledger = CapabilityReturnLedger(tmp_path / "returns.sqlite3")
    first = ledger.append(reported_return("one", "fixture-one"))
    second = ledger.append(reported_return("two", "fixture-two"))
    selections = [
        {"return_id": item.packet["return_id"], "local_digest": item.local_digest,
         "owner": item.packet["artifacts"][0]["owner"],
         "artifact_ref": item.packet["artifacts"][0]["artifact_ref"]}
        for item in (first, second)
    ]
    return ledger, {"selections": selections, "question": "Could these fixtures share a bounded test?"}


def test_preview_is_stable_and_preserves_unverified_distinct_sources(tmp_path: Path):
    ledger, request = setup(tmp_path)
    before = ledger.latest()
    a = preview_composition(ledger, request)
    b = preview_composition(ledger, request)
    assert a == b
    assert a["format"] == "house.capability-loom-proposal/v0"
    assert a["state"] == "inert_unrun"
    assert a["execution"] == "not_attempted"
    assert a["authorization"] == a["compatibility"] == a["verification"] == "not_evaluated"
    assert a["declared_effects"] == []
    assert [item["artifact_ref"] for item in a["inputs"]] == ["fixture-one", "fixture-two"]
    assert all(item["reported_capability_state"] == "reported" for item in a["inputs"])
    assert all(item["reported_effect_state"] == "scope_uncertain" for item in a["inputs"])
    assert ledger.latest() == before  # preview does not write anything


@pytest.mark.parametrize("change", [
    lambda q: q["selections"].pop(),
    lambda q: q["selections"].append(deepcopy(q["selections"][0])),
    lambda q: q["selections"][1].update({"local_digest": "0" * 64}),
    lambda q: q["selections"][1].update({"return_id": "missing"}),
    lambda q: q["selections"][0].update({"artifact_ref": "missing"}),
    lambda q: q["selections"][1].update({"artifact_ref": q["selections"][0]["artifact_ref"],
                                         "return_id": q["selections"][0]["return_id"],
                                         "local_digest": q["selections"][0]["local_digest"]}),
    lambda q: q["selections"][0].update({"execute": True}),
    lambda q: q.update({"authorize": True}),
    lambda q: q.update({"question": " "}),
    lambda q: q.update({"question": "x" * 513}),
])
def test_rejects_unresolved_or_mutated_or_authority_smuggling_selections(tmp_path: Path, change):
    ledger, request = setup(tmp_path)
    change(request)
    with pytest.raises(ValueError):
        preview_composition(ledger, request)


def test_two_returns_reporting_same_owner_artifact_are_not_distinct_capabilities(tmp_path: Path):
    ledger, request = setup(tmp_path)
    duplicate = reported_return("three", "fixture-one")
    record = ledger.append(duplicate)
    request["selections"][1] = {
        "return_id": duplicate["return_id"], "local_digest": record.local_digest,
        "owner": "static-workbench", "artifact_ref": "fixture-one"
    }
    with pytest.raises(ValueError, match="same project-owned artifact"):
        preview_composition(ledger, request)


def test_inert_preview_requires_session_and_uses_no_project_or_ledger_write(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    ))
    first = app.state.return_ledger.append(reported_return("one", "fixture-one"))
    second = app.state.return_ledger.append(reported_return("two", "fixture-two"))
    request = {
        "question": "Could these be tested together?",
        "selections": [
            {"return_id": row.packet["return_id"], "local_digest": row.local_digest,
             "owner": row.packet["artifacts"][0]["owner"],
             "artifact_ref": row.packet["artifacts"][0]["artifact_ref"]}
            for row in (first, second)
        ],
    }
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.post("/api/house/loom/preview", json=request).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        assert client.post("/api/house/loom/preview", json=request,
                           headers={**headers, "origin": "http://evil.example"}).status_code == 403
        ok = client.post("/api/house/loom/preview", json=request, headers=headers)
        assert ok.status_code == 200
        proposal = ok.json()
        assert proposal["execution"] == "not_attempted"
        assert proposal["inputs"][0]["return_digest"] == first.local_digest
        assert len(app.state.return_ledger.latest()) == 2
        assert client.get("/api/events").json()["events"] == [{"id": 1, "created_at": client.get("/api/events").json()["events"][0]["created_at"], "kind": "workbench.started", "payload": {"version": "0.2.0"}}]
        assert client.get("/api/house/loom/preview").status_code == 405


def test_loom_ui_is_explicit_and_uses_text_not_html(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    app = create_app(WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    ))
    with TestClient(app, base_url="http://127.0.0.1") as client:
        js = client.get("/assets/return-shelf.js").text
    assert "Select this exact reported artifact" in js
    assert "selected.size !== 2" in js
    assert "method: 'POST'" in js
    assert "'/api/house/loom/preview'" in js
    assert "X-Workbench-Session" in js
    assert "innerHTML" not in js
    assert "createElement('a')" not in js
    assert "textContent" in js or "el(" in js
