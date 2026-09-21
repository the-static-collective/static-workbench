from copy import deepcopy
from pathlib import Path

import pytest

from static_workbench.capability_returns import CapabilityReturnLedger, validate_packet


def packet():
    return {
        "return_id": "workbench:flight-001:return-001",
        "flight_ref": "workbench:flight-001",
        "source_owner": "the-static-collective/static-workbench",
        "source_ref": "repo@0123456789abcdef",
        "effect_state": "scoped_complete",
        "parent_effect_ref": None,
        "artifacts": [{"artifact_ref": "repo@0123456789abcdef:fixture", "owner": "static-workbench",
                       "kind": "test-fixture", "capability_state": "reported", "evidence_refs": ["local:test-run:1"]}],
        "capability_delta": "A fixture was supplied for reuse; no independent validation is claimed.",
        "evidence_refs": ["local:test-run:1"],
        "resource_costs": "not measured",
        "nonclaims": ["Workbench did not authenticate source, effect, or authorization."],
        "proposed_next": ["Consider an independently authorized fixture-reuse test."],
    }


def test_roundtrip_reopen_and_identical_replay(tmp_path: Path):
    path = tmp_path / "workbench.sqlite3"
    ledger = CapabilityReturnLedger(path)
    first = ledger.append(packet())
    again = CapabilityReturnLedger(path).append(packet())
    assert again.id == first.id
    assert again.local_digest == first.local_digest
    assert ledger.latest()[0].packet == packet()
    assert ledger.get(packet()["return_id"]).id == first.id
    assert ledger.get("unknown") is None


def test_different_return_id_is_a_new_record_not_revision(tmp_path: Path):
    ledger = CapabilityReturnLedger(tmp_path / "ledger.sqlite3")
    first = ledger.append(packet())
    new = packet()
    new["return_id"] = "workbench:flight-002:return-001"
    new["parent_effect_ref"] = first.packet["return_id"]
    second = ledger.append(new)
    assert [r.id for r in ledger.latest()] == [second.id, first.id]
    assert ledger.get(first.packet["return_id"]).packet["parent_effect_ref"] is None


def test_conflicting_replay_refuses_without_overwriting(tmp_path: Path):
    ledger = CapabilityReturnLedger(tmp_path / "ledger.sqlite3")
    before = ledger.append(packet())
    changed = packet()
    changed["effect_state"] = "partial"
    with pytest.raises(ValueError, match="different content"):
        ledger.append(changed)
    assert ledger.get(packet()["return_id"]) == before


@pytest.mark.parametrize("mutate", [
    lambda p: p.update({"authorization": True}),
    lambda p: p.update({"effect_state": "proved"}),
    lambda p: p.update({"nonclaims": []}),
    lambda p: p.update({"artifacts": p["artifacts"] * 33}),
    lambda p: p["artifacts"][0].update({"capability_state": "proven"}),
    lambda p: p["artifacts"][0].update({"run_command": "rm -rf /"}),
    lambda p: p["artifacts"].append(deepcopy(p["artifacts"][0])),
    lambda p: p.update({"resource_costs": "a" * 513}),
])
def test_invalid_or_authority_smuggling_refused(mutate):
    candidate = packet()
    mutate(candidate)
    with pytest.raises(ValueError):
        validate_packet(candidate)


def test_list_is_bounded(tmp_path: Path):
    ledger = CapabilityReturnLedger(tmp_path / "ledger.sqlite3")
    for limit in (0, 101, True, 1.1):
        with pytest.raises(ValueError):
            ledger.latest(limit)
