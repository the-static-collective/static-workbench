from dataclasses import replace
import random

import pytest

from static_workbench.experimental.holographic_field_001 import (
    DurableContextStore,
    FieldIntegrityError,
    HolographicContextField,
    MissingDurableContext,
    StaleFieldCheckpoint,
    coordinator_payload,
)
from static_workbench.experimental.holographic_kernel_001 import Projection, ReturnAddress


def projection(kind="chat", state_id="s_1", state_digest="d_1"):
    ret = ReturnAddress(
        kernel_id="story-door/holographic-kernel-001",
        state_id=state_id,
        unresolved=("who rang it?",),
        residue=("danger reading remains",),
        continuations=("before", "after", "instead", "reinterpret", "inspect-lineage"),
    )
    return Projection(
        projection_kind=kind,
        kernel_id=ret.kernel_id,
        state_id=state_id,
        state_digest=state_digest,
        authority_owner="story-door-kernel",
        affordances=("before", "after", "instead", "reinterpret"),
        lineage_head=(state_id,),
        return_address=ret,
        presentation={"kind": kind},
    )


def seeded(capacity=4):
    field = HolographicContextField(capacity)
    atoms = [
        field.receive(f"signal-{i}", relevance=i % 3, kind="signal")
        for i in range(8)
    ]
    return field, atoms


def test_field_bat_01_receive_hold_pour_semantically_saturates_when_possible():
    field, _ = seeded(capacity=4)
    frame = field.now(projection())
    assert frame.saturated
    assert len(frame.held) == 4
    assert len(frame.poured) == 4


def test_field_bat_02_every_context_atom_is_held_or_poured_never_orphaned():
    field, atoms = seeded(capacity=3)
    frame = field.now(projection())
    addressed = {a.atom_id for a in frame.held} | {r.atom_id for r in frame.poured}
    assert addressed == {a.atom_id for a in atoms}


def test_field_bat_03_relevance_and_recency_shape_the_present_without_rewriting_memory():
    field = HolographicContextField(2)
    old = field.receive("old-high", relevance=9)
    field.receive("new-low", relevance=1)
    new = field.receive("new-high", relevance=9)
    held = field.hold()
    assert [a.atom_id for a in held] == [new.atom_id, old.atom_id]
    assert {a.text for a in field.store.all()} == {"old-high", "new-low", "new-high"}


def test_field_bat_04_poured_material_leaves_sideways_doors():
    field, _ = seeded(capacity=2)
    frame = field.now(projection())
    sideways = [d for d in frame.doors if d.direction == "sideways"]
    assert len(sideways) == len(frame.poured)
    assert {field.resolve_sideways(d).atom_id for d in sideways} == {r.atom_id for r in frame.poured}


def test_field_bat_05_forward_doors_come_from_kernel_return_address():
    field, _ = seeded(capacity=2)
    frame = field.now(projection())
    forward = {d.label for d in frame.doors if d.direction == "forward"}
    assert forward == set(projection().return_address.continuations)


def test_field_bat_06_second_now_has_backward_door_to_previous_field():
    field, _ = seeded(capacity=2)
    first = field.now(projection())
    field.receive("fresh", relevance=99)
    second = field.now(projection())
    backward = [d for d in second.doors if d.direction == "backward"]
    assert len(backward) == 1
    assert backward[0].target == f"field:{first.field_digest}"


def test_field_bat_07_projection_kind_does_not_change_underlying_field_digest():
    store = DurableContextStore()
    for i in range(5):
        store.receive(f"signal-{i}", relevance=i)
    chat = HolographicContextField(3, store=store).now(projection("chat"))
    world = HolographicContextField(3, store=store).now(projection("world"))
    assert chat.projection_kind != world.projection_kind
    assert chat.field_digest == world.field_digest
    assert [a.atom_id for a in chat.held] == [a.atom_id for a in world.held]


def test_field_bat_08_coordination_plane_contains_refs_not_context_payloads():
    field = HolographicContextField(1)
    marker = "THE-CONTEXT-PAYLOAD-IS-NOT-GLOCAL"
    field.receive(marker, relevance=1)
    field.receive("other", relevance=2)
    checkpoint = field.checkpoint(field.now(projection()))
    serialized = repr(coordinator_payload(checkpoint))
    assert marker not in serialized


def test_field_bat_09_strong_extinction_reconstructs_same_now_from_x_plus_relations():
    field, _ = seeded(capacity=3)
    original = field.now(projection("html"))
    checkpoint = field.checkpoint(original)
    persistent_store = field.store

    del field

    reinstantiated = HolographicContextField(3, store=persistent_store)
    recovered = reinstantiated.reconstruct(projection("world"), checkpoint)
    assert recovered.field_digest == original.field_digest
    assert recovered.projection_kind == "world"
    assert tuple(a.text for a in recovered.held) == tuple(a.text for a in original.held)
    assert recovered.doors == original.doors


def test_field_bat_10_extinction_cannot_reconstruct_missing_durable_payload_by_magic():
    field, _ = seeded(capacity=2)
    checkpoint = field.checkpoint(field.now(projection()))
    field.store.remove_for_test(checkpoint.held_refs[0].atom_id)
    reincarnated = HolographicContextField(2, store=field.store)
    with pytest.raises(MissingDurableContext):
        reincarnated.reconstruct(projection("cli"), checkpoint)


def test_field_bat_11_tampered_coordination_ref_refuses():
    field, _ = seeded(capacity=2)
    checkpoint = field.checkpoint(field.now(projection()))
    bad_ref = replace(checkpoint.held_refs[0], digest="tampered")
    bad_checkpoint = replace(
        checkpoint,
        held_refs=(bad_ref,) + checkpoint.held_refs[1:],
    )
    reincarnated = HolographicContextField(2, store=field.store)
    with pytest.raises(FieldIntegrityError):
        reincarnated.reconstruct(projection(), bad_checkpoint)


def test_field_bat_12_checkpoint_refuses_if_kernel_moved():
    field, _ = seeded(capacity=2)
    checkpoint = field.checkpoint(field.now(projection()))
    moved = projection(state_id="s_2", state_digest="d_2")
    with pytest.raises(StaleFieldCheckpoint):
        HolographicContextField(2, store=field.store).reconstruct(moved, checkpoint)


def test_field_bat_13_empty_input_refuses():
    field = HolographicContextField(2)
    with pytest.raises(FieldIntegrityError):
        field.receive("   ")


def test_field_bat_14_random_receive_hold_pour_swarm_keeps_bounded_now_and_addresses_all_elsewhere():
    rng = random.Random(917)
    field = HolographicContextField(7)
    for step in range(100):
        field.receive(
            f"signal-{step}-{rng.randrange(1_000_000)}",
            relevance=rng.randrange(0, 20),
            kind=rng.choice(("signal", "question", "residue", "lineage")),
        )
        frame = field.now(projection(rng.choice(("chat", "html", "cli", "world"))))
        all_ids = {a.atom_id for a in field.store.all()}
        held_ids = {a.atom_id for a in frame.held}
        poured_ids = {r.atom_id for r in frame.poured}
        assert held_ids.isdisjoint(poured_ids)
        assert held_ids | poured_ids == all_ids
        assert len(frame.held) <= field.capacity
        if len(all_ids) >= field.capacity:
            assert frame.saturated
