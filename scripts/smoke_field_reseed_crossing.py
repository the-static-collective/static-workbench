#!/usr/bin/env python3
"""Actual Workbench -> reLATTE R14 -> GHoT receiver metabolism smoke."""

from __future__ import annotations

import tempfile
from pathlib import Path

from static_workbench.field_reseed_crossing import (
    GHOT_REVISION,
    RELATTE_REVISION,
    admit_field_reseed,
    assign_field_reseed_intent,
    cross_field_reseed,
    offer_field_reseed_assignment,
)
from static_workbench.field_return import FieldReturnStore, compose_field_return
from static_workbench.field_station import compose_nearby_station_doors
from static_workbench.repos import RepoStatus


ROOT = Path(__file__).resolve().parent.parent
RELATTE = ROOT / ".compat" / "reLATTE"
GHOT = ROOT / ".compat" / "GHoT"


def repo(name: str, path: Path, head: str) -> RepoStatus:
    return RepoStatus(
        name=name,
        path=str(path),
        branch=None,
        detached=True,
        head=head[:7],
        dirty=False,
        ahead=None,
        behind=None,
    )


def house() -> dict:
    return {
        "entered": True,
        "world_version": 0,
        "letters": [],
        "doors": [],
        "receipts": [],
        "external_witnesses": [],
        "laws": [],
    }


def broadcast() -> dict:
    return {
        "checkout_present": False,
        "configured": False,
        "connection": "unconfigured",
        "open_url": None,
        "event": None,
        "broadcast_state": None,
        "recording": None,
        "stream": None,
        "authority": "static-live",
    }


def compose(receiver_state=None) -> dict:
    return compose_nearby_station_doors(
        house(),
        broadcast(),
        [],
        [],
        field_receivers=receiver_state or [],
    )


def main() -> int:
    for path in (RELATTE, GHOT):
        if not path.is_dir():
            raise SystemExit(f"missing integration checkout: {path}")

    repos = [
        repo("reLATTE", RELATTE, RELATTE_REVISION),
        repo("GHoT", GHOT, GHOT_REVISION),
    ]

    with tempfile.TemporaryDirectory(prefix="field-reseed-crossing-") as raw:
        state_dir = Path(raw) / "state"
        store = FieldReturnStore(state_dir / "field_returns.sqlite3")

        observed = compose()
        source_door = observed["nearby_doors"][0]
        returned = compose_field_return(
            observed,
            source_door["door_id"],
            "take",
            "carry this exact witnessed aperture",
        )
        stored = store.save(returned)
        assert stored["reseed"]["status"] == "proposal-only"
        assert store.receiver(stored["receipt_id"]) is None

        crossing = cross_field_reseed(stored, state_dir, repos)
        assert crossing["status"] == "RECEIVED_THEN_HELD"
        assert crossing["semantic_effect"] == "none"
        assert crossing["pins"]["relatte"] == RELATTE_REVISION
        assert crossing["pins"]["ghot"] == GHOT_REVISION
        assert crossing["relatte"]["receive_receipt"]["kind"] == "RECEIVED"
        assert crossing["relatte"]["disposition_receipt"]["kind"] == "R3_HOLD"
        assert crossing["ghot_hold"]["status"] == "HOLD"
        assert crossing["ghot_hold"]["reseed_id"] == stored["reseed"]["reseed_id"]

        held = store.save_crossing(stored["receipt_id"], crossing)
        assert held["status"] == "RECEIVED_THEN_HELD"

        held_field = compose(store.receiver_field_state())
        held_door = next(
            door for door in held_field["nearby_doors"]
            if door["lane"] == "carried"
        )
        assert held_door["kind"] == "admit-ghot-field-reseed"
        assert held_door["effect"] == "none"
        assert held_field["field_state_id"] != observed["field_state_id"]

        admission = admit_field_reseed(
            held["crossing"],
            state_dir,
            repos,
        )
        assert admission["status"] == "ADMITTED_NOT_ASSIGNED"
        assert admission["semantic_effect"] == "local-inbox-only"
        intent = admission["ghot_admission"]["intent"]
        assert intent["schema"] == "ghot.carried-intent/v0"
        assert intent["status"] == "admitted-not-assigned"
        assert intent["effect"] == "local-inbox-only"

        admitted = store.save_admission(stored["receipt_id"], admission)
        assert admitted["status"] == "ADMITTED_NOT_ASSIGNED"

        admitted_field = compose(store.receiver_field_state())
        inspect = next(
            door for door in admitted_field["nearby_doors"]
            if door["lane"] == "carried"
        )
        assert inspect["kind"] == "offer-ghot-carried-intent-assignment"
        assert inspect["effect"] == "none"
        assert inspect["target"]["control"] == "ghot-field-intent-offer"
        assert admitted_field["field_state_id"] != held_field["field_state_id"]
        assert admitted_field["nearby_doors"][-1]["kind"] == "hold-silence"

        # Admission remains distinct from assignment. First open the exact
        # unranked current GHoT body/capability field.
        ghot_home = state_dir / "field-reseed-ghot"
        records = ghot_home / "records"
        before_execution_records = (
            sorted(
                path.name for path in records.iterdir()
                if "-task-" in path.name or "-receipt-" in path.name
            )
            if records.is_dir()
            else []
        )

        offered = offer_field_reseed_assignment(
            admitted["admission"],
            state_dir,
            repos,
        )
        assert offered["status"] == "OFFER_READY"
        assert offered["semantic_effect"] == "none"
        assert '"score"' not in __import__("json").dumps(offered)
        offered_state = store.save_assignment_offer(
            stored["receipt_id"],
            offered,
        )
        assert offered_state["status"] == "OFFER_READY"

        offer_field = compose(store.receiver_field_state())
        choose = next(
            door for door in offer_field["nearby_doors"]
            if door["lane"] == "carried"
        )
        assert choose["kind"] == "choose-ghot-carried-intent-assignment"
        assert choose["target"]["control"] == "ghot-field-intent-assign"

        ghot_offer = offered["ghot_offer"]
        local = next(
            body for body in ghot_offer["bodies"]
            if body.get("location") == "local"
        )
        selected = next(
            item for item in local["offers"]
            if item.get("capability") == "system.hash"
            and item.get("eligible") is True
        )
        assignment = assign_field_reseed_intent(
            admitted["admission"],
            offered,
            local["node_id"],
            selected["capability"],
            state_dir,
            repos,
        )
        assert assignment["status"] == "ASSIGNED_NOT_EXECUTED"
        assert assignment["semantic_effect"] == "receiver-assignment-only"
        ghot_assignment = assignment["ghot_assignment"]
        assert ghot_assignment["status"] == "ASSIGNED_NOT_EXECUTED"
        assert ghot_assignment["selected_node_id"] == local["node_id"]
        assert ghot_assignment["capability"] == "system.hash"

        assigned_state = store.save_assignment(
            stored["receipt_id"],
            assignment,
        )
        assert assigned_state["status"] == "ASSIGNED_NOT_EXECUTED"

        assigned_field = compose(store.receiver_field_state())
        inspect_assignment = next(
            door for door in assigned_field["nearby_doors"]
            if door["lane"] == "carried"
        )
        assert (
            inspect_assignment["kind"]
            == "inspect-ghot-carried-intent-assignment"
        )
        assert inspect_assignment["effect"] == "none"
        assert assigned_field["field_state_id"] != offer_field["field_state_id"]

        after_execution_records = (
            sorted(
                path.name for path in records.iterdir()
                if "-task-" in path.name or "-receipt-" in path.name
            )
            if records.is_dir()
            else []
        )
        assert after_execution_records == before_execution_records

        # The receiver consequences are durable state, not execution.
        assert (ghot_home / "field-reseed-inbox").is_dir()
        assert not (ghot_home / "executions").exists()

        print(
            "field reseed assignment metabolism smoke ok:",
            stored["receipt_id"],
            stored["reseed"]["reseed_id"],
            crossing["relatte"]["crossing"]["crossing_id"],
            crossing["ghot_hold"]["hold_id"],
            admission["ghot_admission"]["admission_id"],
            intent["intent_id"],
            ghot_offer["offer_id"],
            ghot_assignment["assignment_id"],
            ghot_assignment["selected_node_id"],
            ghot_assignment["capability"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
