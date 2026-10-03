import json

import pytest

from static_workbench.banana_fork import BananaForkStore
from static_workbench.field_return import FieldReturnStore
from static_workbench.field_station import compose_nearby_station_doors


def empty_house():
    return {
        "entered": True,
        "world_version": 0,
        "letters": [],
        "doors": [],
        "receipts": [],
        "external_witnesses": [],
        "laws": [],
    }


def broadcast():
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


def consequence_field():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:45:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "EXECUTED",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_offer_id": "ghot-carried-intent-offer-v0:" + "6" * 64,
        "assignment_id": "ghot-carried-intent-assignment-v0:" + "7" * 64,
        "selected_node_id": "node-local",
        "capability": "system.hash",
        "dispatch_crossing_id": "relatte-crossing-v0:" + "8" * 64,
        "task_id": "task-123",
        "execution_receipt_id": "receipt-123",
        "signed_receipt_id": "relatte-receipt-v0:" + "9" * 64,
        "execution_status": "ok",
        "output_sha256": "a" * 64,
    }]
    return compose_nearby_station_doors(
        empty_house(),
        broadcast(),
        [],
        [],
        field_receivers=receiver,
    )


def booth_by_label(fork, label):
    return next(item for item in fork["booths"] if item["label"] == label)


def door_by_facet(booth, facet):
    return next(
        door for door in booth["packet"]["doors"]
        if door.get("target", {}).get("facet") == facet
    )


def silence_door(booth):
    return next(
        door for door in booth["packet"]["doors"]
        if door.get("lane") == "silence"
    )


def test_fork_keeps_returns_sealed_until_every_booth_answers(tmp_path):
    store = BananaForkStore(tmp_path / "banana_forks.sqlite3")
    fork = store.create(
        consequence_field(),
        ["Human Friend", "Lumi", "Claude"],
    )
    assert fork["status"] == "collecting"
    assert fork["submitted_count"] == 0
    assert fork["returns"] == []
    assert fork["relation_field"] is None

    human = booth_by_label(fork, "Human Friend")
    ack = store.submit(
        fork["fork_id"],
        human["booth_id"],
        human["booth_token"],
        door_by_facet(human, "delightfuler")["door_id"],
        "take",
        "leave a tiny strange gift",
    )
    assert ack["sealed"] is True
    hidden = store.get(fork["fork_id"], include_tokens=True)
    assert hidden["status"] == "collecting"
    assert hidden["submitted_count"] == 1
    assert hidden["returns"] == []
    assert booth_by_label(hidden, "Human Friend")["submitted"] is True
    assert "response" not in booth_by_label(hidden, "Human Friend")

    lumi = booth_by_label(hidden, "Lumi")
    ack = store.submit(
        fork["fork_id"],
        lumi["booth_id"],
        lumi["booth_token"],
        door_by_facet(lumi, "curiouser")["door_id"],
        "take",
        "keep the weird residue visible",
    )
    assert ack["sealed"] is True
    assert store.get(fork["fork_id"])["returns"] == []

    waiting = store.get(fork["fork_id"], include_tokens=True)
    claude = booth_by_label(waiting, "Claude")
    ack = store.submit(
        fork["fork_id"],
        claude["booth_id"],
        claude["booth_token"],
        silence_door(claude)["door_id"],
        "hold",
        "let these stay adjacent for now",
    )
    assert ack["sealed"] is False
    assert ack["status"] == "revealed"

    revealed = store.get(fork["fork_id"], include_tokens=True)
    assert revealed["status"] == "revealed"
    assert len(revealed["returns"]) == 3
    assert len(revealed["take_descendants"]) == 2
    assert {
        item["returner_label"] for item in revealed["returns"]
    } == {"Human Friend", "Lumi", "Claude"}

    relation = revealed["relation_field"]
    relation_doors = [
        door for door in relation["nearby_doors"]
        if door["lane"] == "relation"
    ]
    assert len(relation_doors) == 1
    assert relation["nearby_doors"][-1]["lane"] == "silence"
    assert "Human Friend" in relation_doors[0]["label"]
    assert "Lumi" in relation_doors[0]["label"]
    assert relation_doors[0]["effect"] == "none"

    encoded = json.dumps(revealed).lower()
    assert '"winner"' not in encoded
    assert '"score"' not in encoded
    assert '"rank"' not in encoded
    assert "REVEAL != RANKING" in revealed["laws"]


def test_identical_independent_returns_remain_distinct_by_booth(tmp_path):
    store = BananaForkStore(tmp_path / "banana_forks.sqlite3")
    fork = store.create(consequence_field(), ["A", "B"])
    a = booth_by_label(fork, "A")
    b = booth_by_label(fork, "B")
    door_a = door_by_facet(a, "helpfuler")
    door_b = door_by_facet(b, "helpfuler")

    first = store.submit(
        fork["fork_id"],
        a["booth_id"],
        a["booth_token"],
        door_a["door_id"],
        "take",
        "remove the same snag",
    )
    second = store.submit(
        fork["fork_id"],
        b["booth_id"],
        b["booth_token"],
        door_b["door_id"],
        "take",
        "remove the same snag",
    )
    assert first["submission_id"] != second["submission_id"]

    revealed = store.get(fork["fork_id"])
    takes = revealed["take_descendants"]
    assert len(takes) == 2
    # The underlying Field Return can be identical while the attributable
    # sealed return remains distinct because booth identity is preserved.
    assert (
        takes[0]["field_return"]["receipt_id"]
        == takes[1]["field_return"]["receipt_id"]
    )
    assert takes[0]["submission_id"] != takes[1]["submission_id"]
    assert len([
        door for door in revealed["relation_field"]["nearby_doors"]
        if door["lane"] == "relation"
    ]) == 1


def test_bad_token_and_outside_door_are_refused(tmp_path):
    store = BananaForkStore(tmp_path / "banana_forks.sqlite3")
    field = consequence_field()
    fork = store.create(field, ["A", "B"])
    a = booth_by_label(fork, "A")
    door = door_by_facet(a, "delightfuler")

    with pytest.raises(ValueError, match="token mismatch"):
        store.submit(
            fork["fork_id"],
            a["booth_id"],
            "wrong",
            door["door_id"],
            "take",
            "",
        )

    outside = next(
        door for door in field["nearby_doors"]
        if door["lane"] not in {"delight", "silence"}
    )
    with pytest.raises(ValueError, match="not part of this frozen"):
        store.submit(
            fork["fork_id"],
            a["booth_id"],
            a["booth_token"],
            outside["door_id"],
            "take",
            "",
        )


def test_relation_take_becomes_normal_proposal_only_reseed(tmp_path):
    forks = BananaForkStore(tmp_path / "banana_forks.sqlite3")
    returns = FieldReturnStore(tmp_path / "field_returns.sqlite3")
    fork = forks.create(consequence_field(), ["A", "B"])

    for label, facet in [("A", "delightfuler"), ("B", "curiouser")]:
        current = forks.get(fork["fork_id"], include_tokens=True)
        booth = booth_by_label(current, label)
        forks.submit(
            fork["fork_id"],
            booth["booth_id"],
            booth["booth_token"],
            door_by_facet(booth, facet)["door_id"],
            "take",
            label + " independent return",
        )

    relation = forks.relation_field(fork["fork_id"])
    relation_door = next(
        door for door in relation["nearby_doors"]
        if door["lane"] == "relation"
    )
    receipt = forks.compose_relation_return(
        fork["fork_id"],
        relation["field_state_id"],
        relation_door["door_id"],
        "take",
        "let the independent descendants make a third thing",
    )
    stored = returns.save(receipt)

    assert stored["schema"] == "workbench.field-return/v0"
    assert stored["disposition"] == "take"
    assert stored["selected_door"]["lane"] == "relation"
    assert stored["reseed"]["status"] == "proposal-only"
    assert stored["reseed"]["effect"] == "none"
    assert stored["reseed"]["door"]["target"]["move"] == "let-meet-without-merging"
    assert returns.receiver(stored["receipt_id"]) is None


def test_fork_requires_exact_banana_elf_consequence_field(tmp_path):
    store = BananaForkStore(tmp_path / "banana_forks.sqlite3")
    ordinary = compose_nearby_station_doors(
        empty_house(), broadcast(), [], []
    )
    with pytest.raises(ValueError, match="requires exactly"):
        store.create(ordinary, ["A", "B"])

    with pytest.raises(ValueError, match="2-6"):
        store.create(consequence_field(), ["A"])

    with pytest.raises(ValueError, match="unique"):
        store.create(consequence_field(), ["A", "a"])
