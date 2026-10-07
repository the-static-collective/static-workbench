"""WEBZ-RELATTE-002: human-gated first-party parcel, pinned owner, destination policy."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench import webz_parcel as parcel_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.webz_parcel import WebzParcelError, WebzParcelGate


def config_for(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def fixture_result(request: dict) -> dict:
    spec = request["spec"]
    crossing_id = "relatte-crossing-v0:" + "b" * 64
    expected = request["disposition"]
    return {
        "schema": "relatte.opaque-roundtrip-result/v0",
        "request_id": "relatte-opaque-roundtrip-v0:" + "0" * 64,
        "crossing": {
            "schema": "relatte.crossing-envelope/v0",
            "crossing_id": crossing_id,
            "source_world": spec["source_world"],
            "source_particular": spec["source_particular"],
            "declared_kind": "OPAQUE_ORGAN_ARTIFACT",
            "payload_refs": spec["payload_refs"],
            "requested_effect": spec["requested_effect"],
            "extensions": {"organ_adapter": {
                "family_ref": spec["family_ref"],
                "artifact_kind": spec["artifact_kind"],
                "donor_claims": spec["donor_claims"],
            }},
        },
        "transport_frame": {"transport_id": "relatte-transport-v0:" + "f" * 64},
        "receive_receipt": {
            "schema": "relatte.receipt/v0",
            "receipt_id": "relatte-receipt-v0:" + "c" * 64,
            "crossing_id": crossing_id,
            "world_id": request["receiver"]["world_id"],
            "receiver_particular": request["receiver"]["receiver_particular"],
            "kind": "RECEIVED",
            "semantic_effect": "none",
        },
        "disposition_receipt": {
            "schema": "relatte.receipt/v0",
            "receipt_id": "relatte-receipt-v0:" + "d" * 64,
            "crossing_id": crossing_id,
            "world_id": request["receiver"]["world_id"],
            "receiver_particular": request["receiver"]["receiver_particular"],
            "kind": "R3_" + expected,
            "semantic_effect": "none",
        },
        "receiver_snapshot": {
            "schema": "relatte.local-receiver-snapshot/v0",
            "world_id": request["receiver"]["world_id"],
            "held": [crossing_id] if expected == "HOLD" else [],
            "refused": [crossing_id] if expected == "REFUSE" else [],
            "admitted": [],
            "state_ref": "relatte-local-state-v0:" + "e" * 64,
        },
        "laws": ["RECEIVED != ADMITTED"],
    }


def fake_pinned(monkeypatch, tmp_path: Path, calls: list[dict]):
    checkout = tmp_path / "pinned-relatte"
    checkout.mkdir(exist_ok=True)
    monkeypatch.setattr(parcel_module, "_find_pinned", lambda *a, **kw: checkout)
    def fake_run(command, cwd, payload, env, label, timeout=20.0):
        calls.append(payload)
        return fixture_result(payload)
    monkeypatch.setattr(parcel_module, "_run_json", fake_run)


def test_read_only_preview_is_declared_no_secret_or_dispatch(tmp_path, monkeypatch):
    gate = WebzParcelGate(tmp_path / "state")
    def never(*args, **kwargs):
        raise AssertionError("preview must not run the signer")
    monkeypatch.setattr(parcel_module, "_run_json", never)
    fruit = gate.preview("fruit")
    spore = gate.preview("spore")
    assert fruit["schema"] == "workbench.webz-parcel-preview/v0"
    assert fruit["kind"] == "fruit"
    assert fruit["policy"] == "HOLD"
    assert spore["policy"] == "REFUSE"
    assert fruit["source_world_id"] == "webz:the-static-collective/sanctuary"
    assert fruit["destination_world_id"] == "webz:the-static-collective/orchard-022100"
    assert len(fruit["artifact_sha256"]) == 64
    assert fruit["artifact_sha256"] != spore["artifact_sha256"]
    assert fruit["carry_mode"] == "explicit-synthetic-artifact"
    assert not (tmp_path / "state").exists()
    assert "private_key" not in json.dumps(fruit)


@pytest.mark.parametrize("kind", ["../fruit", "other", "", "fruit?disposition=ADMIT"])
def test_unknown_kind_never_reads_or_stages_arbitrary_file(tmp_path, kind):
    gate = WebzParcelGate(tmp_path / "state")
    with pytest.raises(WebzParcelError):
        gate.preview(kind)
    assert not (tmp_path / "state").exists()


def test_send_requires_approved_digest_confirmation_and_pinned_bridge(tmp_path, monkeypatch):
    gate = WebzParcelGate(tmp_path / "state")
    want = gate.preview("fruit")
    seen = []
    fake_pinned(monkeypatch, tmp_path, seen)
    for digest, confirmation in [
        ("0" * 64, "SEND_TO_ORCHARD"),
        (want["artifact_sha256"], "no"),
        (want["artifact_sha256"], ""),
    ]:
        with pytest.raises(WebzParcelError):
            gate.send("fruit", digest, confirmation, [])
    assert seen == []
    assert not (tmp_path / "state").exists()
    monkeypatch.setattr(parcel_module, "_find_pinned", lambda *args: (_ for _ in ()).throw(
        parcel_module.FieldReseedCrossingError("no pinned owner")
    ))
    with pytest.raises(WebzParcelError, match="pinned"):
        gate.send("fruit", want["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert seen == []


def test_explicit_send_preserves_signed_ids_and_receiver_local_hold(tmp_path, monkeypatch):
    calls = []
    fake_pinned(monkeypatch, tmp_path, calls)
    gate = WebzParcelGate(tmp_path / "state")
    preview = gate.preview("fruit")
    saved = gate.send("fruit", preview["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert saved["schema"] == "workbench.webz-parcel-result/v0"
    assert saved["status"] == "RECEIVED_THEN_HELD"
    assert saved["admitted"] is False
    assert saved["semantic_effect"] == "none"
    assert saved["receiver_disposition"] == "HOLD"
    assert saved["source_world_id"] == preview["source_world_id"]
    assert saved["destination_world_id"] == preview["destination_world_id"]
    assert saved["artifact_sha256"] == preview["artifact_sha256"]
    assert saved["crossing_id"].startswith("relatte-crossing-v0:")
    assert saved["receive_receipt_id"].startswith("relatte-receipt-v0:")
    assert len(calls) == 1
    req = calls[0]
    assert req["disposition"] == "HOLD"
    assert req["spec"]["source_world"] == preview["source_world_id"]
    assert req["spec"]["payload_refs"][0]["address"] == "sha256:" + preview["artifact_sha256"]
    staged = (tmp_path / "state" / "webz-relatte" / "v0" / "staged"
              / ("fruit-" + preview["artifact_sha256"] + ".json"))
    assert staged.is_file()
    assert hashlib.sha256(staged.read_bytes()).hexdigest() == preview["artifact_sha256"]
    again = gate.send("fruit", preview["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert again == saved
    assert len(calls) == 1
    assert gate.inbox() == [saved]


def test_receiver_policy_refuses_uninvited_spore_without_admission(tmp_path, monkeypatch):
    calls = []
    fake_pinned(monkeypatch, tmp_path, calls)
    gate = WebzParcelGate(tmp_path / "state")
    preview = gate.preview("spore")
    result = gate.send("spore", preview["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert calls[0]["disposition"] == "REFUSE"
    assert result["status"] == "RECEIVED_THEN_REFUSED"
    assert result["receiver_disposition"] == "REFUSE"
    assert result["admitted"] is False
    assert result["semantic_effect"] == "none"
    assert len(gate.inbox()) == 1


def test_tampered_relatte_result_and_staged_bytes_refuse(tmp_path, monkeypatch):
    calls = []
    fake_pinned(monkeypatch, tmp_path, calls)
    original = fixture_result
    def forged(*args, **kwargs):
        value = original(args[2])
        value["disposition_receipt"]["kind"] = "R3_ADMIT"
        return value
    monkeypatch.setattr(parcel_module, "_run_json", forged)
    gate = WebzParcelGate(tmp_path / "state")
    want = gate.preview("fruit")
    with pytest.raises(WebzParcelError):
        gate.send("fruit", want["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert gate.inbox() == []
    monkeypatch.setattr(parcel_module, "_run_json", lambda *args, **kw: original(args[2]))
    good = gate.send("fruit", want["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert good["status"] == "RECEIVED_THEN_HELD"
    staged = (tmp_path / "state" / "webz-relatte" / "v0" / "staged"
              / ("fruit-" + want["artifact_sha256"] + ".json"))
    staged.write_bytes(b"tampered")
    with pytest.raises(WebzParcelError, match="digest"):
        gate.send("fruit", want["artifact_sha256"], "SEND_TO_ORCHARD", [])
    with pytest.raises(WebzParcelError, match="digest"):
        gate.inbox()


def test_api_read_is_pure_and_signed_offer_requires_workbench_session(tmp_path, monkeypatch):
    config = config_for(tmp_path)
    calls = []
    fake_pinned(monkeypatch, tmp_path, calls)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        p = client.get("/api/webz/parcels/fruit/preview")
        assert p.status_code == 200
        preview = p.json()
        assert client.get("/api/webz/parcels/inbox").json() == {"parcels": []}
        assert client.get("/webz/world/sanctuary").status_code == 200
        assert not config.state_dir.joinpath("webz-relatte").exists()
        payload = {
            "expected_sha256": preview["artifact_sha256"],
            "confirmation": "SEND_TO_ORCHARD",
        }
        url = "/api/webz/parcels/fruit/send"
        assert client.post(url, json=payload).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        assert client.post(url, json=payload, headers={
            **headers, "origin": "http://untrusted.test",
        }).status_code == 403
        assert client.post(url, json={**payload, "disposition": "ADMIT"}, headers=headers).status_code == 422
        assert client.post(url, json=payload, headers=headers).status_code == 200
        assert len(calls) == 1
        assert client.get("/api/webz/parcels/inbox").json()["parcels"][0]["status"] == "RECEIVED_THEN_HELD"
        assert client.get("/api/webz/parcels/bad/preview").status_code == 404
        assert client.get("/").status_code == 200
        assert client.get("/arg").status_code == 200


def test_world_pages_have_explicit_parcel_instrument_and_owner_receipt_inspection(tmp_path):
    config = config_for(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        sanctuary = client.get("/webz/world/sanctuary").text
        orchard = client.get("/webz/world/orchard").text
        script = client.get("/assets/webz-parcel.js")
        assert 'id="webz-parcel-inspect"' in sanctuary
        assert 'id="webz-parcel-send"' in sanctuary
        assert 'id="webz-parcel-kind"' in sanctuary
        assert 'id="webz-parcel-preview"' in sanctuary
        assert 'id="webz-parcel-status"' in sanctuary
        assert 'type="module" src="/assets/webz-parcel.js"' in sanctuary
        assert 'id="webz-parcel-inbox"' in orchard
        assert 'id="webz-parcel-refresh"' in orchard
        assert 'type="module" src="/assets/webz-parcel.js"' in orchard
        assert script.status_code == 200
        assert "/api/webz/parcels/" in script.text
        assert "SEND_TO_ORCHARD" in script.text
        assert "textContent" in script.text
        assert "innerHTML" not in script.text
        assert "eval(" not in script.text
        assert "api/bootstrap" in script.text
        assert 'id="webz-cross"' in sanctuary  # existing no-carry door remains
        assert 'id="webz-cross"' in orchard


def test_corrupt_persisted_intent_and_summary_fail_closed(tmp_path, monkeypatch):
    calls = []
    fake_pinned(monkeypatch, tmp_path, calls)
    gate = WebzParcelGate(tmp_path / "state")
    proposal = gate.preview("fruit")
    intent = gate.root / "intents" / "fruit.json"
    intent.parent.mkdir(parents=True)
    intent.write_text("{bad")
    with pytest.raises(WebzParcelError, match="intent"):
        gate.send("fruit", proposal["artifact_sha256"], "SEND_TO_ORCHARD", [])
    assert calls == []
    intent.unlink()
    gate.send("fruit", proposal["artifact_sha256"], "SEND_TO_ORCHARD", [])
    summary = gate.root / "summaries" / "fruit.json"
    summary.write_text("{broken")
    with pytest.raises(WebzParcelError, match="summary"):
        gate.inbox()
