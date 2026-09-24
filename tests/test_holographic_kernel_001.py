from dataclasses import replace

import pytest

from static_workbench.experimental.holographic_kernel_001 import (
    AuthorityError,
    HistoricalRewriteError,
    InvalidCrossing,
    StalePreview,
    StoryDoorKernel,
    prove_projection_equivalence,
)


def kernel() -> StoryDoorKernel:
    return StoryDoorKernel(
        "The bell means danger.",
        unresolved=("Who rang it?",),
    )


def test_bat_01_four_projections_are_holographically_equivalent():
    k = kernel()
    projections = [k.project(kind) for kind in ("chat", "html", "cli", "world")]
    assert prove_projection_equivalence(projections)
    assert len({repr(p.presentation) for p in projections}) == 4


def test_bat_02_projection_is_not_authority():
    k = kernel()
    preview = k.preview(
        "reinterpret",
        "The bell means invitation.",
        rationale="New witnessed context changes the reading.",
    )
    with pytest.raises(AuthorityError):
        k.execute(preview, actor="human", executor="world-projection")


def test_bat_03_successful_crossing_requires_kernel_authority():
    k = kernel()
    preview = k.preview(
        "reinterpret",
        "The bell means invitation.",
        rationale="New witnessed context changes the reading.",
    )
    receipt = k.execute(
        preview,
        actor="human",
        executor=k.AUTHORITY,
        unresolved=("Who invited us?",),
        residue=("danger-reading remains historically witnessed",),
    )
    assert receipt.relation_kind == "reframes"
    assert receipt.before_state_id != receipt.after_state_id
    assert receipt.observed_delta["preserved_state"] == receipt.before_state_id


def test_bat_04_witnessed_meaning_cannot_be_silently_rewritten():
    k = kernel()
    root_id = k.head.state_id
    with pytest.raises(HistoricalRewriteError):
        k.rewrite_historical_state(root_id, "The bell means invitation.")
    assert k.witnessed_state(root_id).content == "The bell means danger."


def test_bat_05_reinterpretation_creates_typed_edge_and_preserves_source():
    k = kernel()
    root_id = k.head.state_id
    preview = k.preview(
        "reinterpret",
        "The bell means invitation.",
        rationale="The host explicitly identifies it as a welcome bell.",
    )
    receipt = k.execute(preview, actor="human", executor=k.AUTHORITY)

    assert k.witnessed_state(root_id).content == "The bell means danger."
    assert k.head.content == "The bell means invitation."
    assert k.relations[-1].source_state_id == root_id
    assert k.relations[-1].target_state_id == receipt.after_state_id
    assert k.relations[-1].kind == "reframes"


def test_bat_06_stale_preview_refuses_after_any_intervening_crossing():
    k = kernel()
    stale = k.preview(
        "after",
        "A door opens.",
        rationale="Candidate continuation.",
    )
    current = k.preview(
        "before",
        "Someone tied the bell before dawn.",
        rationale="Add an incoming scene.",
    )
    k.execute(current, actor="human", executor=k.AUTHORITY)

    with pytest.raises(StalePreview):
        k.execute(stale, actor="human", executor=k.AUTHORITY)


def test_bat_07_tampered_preview_identity_refuses():
    k = kernel()
    preview = k.preview(
        "after",
        "A door opens.",
        rationale="Candidate continuation.",
    )
    tampered = replace(preview, candidate_content="A trapdoor opens.")
    with pytest.raises(InvalidCrossing):
        k.execute(tampered, actor="human", executor=k.AUTHORITY)


def test_bat_08_tampered_relation_refuses():
    k = kernel()
    preview = k.preview(
        "reinterpret",
        "The bell means invitation.",
        rationale="Reframed reading.",
    )
    tampered = replace(preview, relation_kind="deletes")
    with pytest.raises(InvalidCrossing):
        k.execute(tampered, actor="human", executor=k.AUTHORITY)


def test_bat_09_return_address_survives_projection_swap():
    k = kernel()
    preview = k.preview(
        "after",
        "A door opens.",
        rationale="Continue from the witnessed opening.",
    )
    receipt = k.execute(
        preview,
        actor="human",
        executor=k.AUTHORITY,
        unresolved=("What is behind the door?",),
        residue=("bell remains audible",),
    )

    world = k.project("world")
    chat = k.project("chat")
    cli = k.project("cli")

    assert receipt.return_address == world.return_address
    assert world.return_address == chat.return_address == cli.return_address
    assert world.return_address.state_id == k.head.state_id
    assert "inspect-lineage" in world.return_address.continuations
    assert "return-to-chat" in world.return_address.continuations


def test_bat_10_each_new_projection_reconstructs_full_current_lineage():
    k = kernel()
    first = k.head.state_id

    p1 = k.preview("after", "A door opens.", rationale="Continuation.")
    r1 = k.execute(p1, actor="human", executor=k.AUTHORITY)

    p2 = k.preview(
        "reinterpret",
        "The open door is an invitation.",
        rationale="Later context changes the meaning of the opening.",
    )
    r2 = k.execute(p2, actor="human", executor=k.AUTHORITY)

    projection = k.project("html")
    assert projection.lineage_head == (first, r1.after_state_id, r2.after_state_id)


def test_bat_11_projection_presentations_can_differ_without_state_drift():
    k = kernel()
    chat = k.project("chat")
    world = k.project("world")
    assert chat.presentation != world.presentation
    assert chat.state_digest == world.state_digest
    assert chat.state_id == world.state_id
    assert chat.authority_owner == world.authority_owner


def test_bat_12_projection_object_tampering_does_not_mutate_kernel():
    k = kernel()
    projection = k.project("world")
    fake = replace(
        projection,
        authority_owner="world-projection",
        state_id="s_fake",
    )
    assert fake.state_id == "s_fake"
    assert k.head.state_id != fake.state_id
    assert k.project("world").authority_owner == k.AUTHORITY


def test_bat_13_unknown_projection_refuses_instead_of_guessing():
    k = kernel()
    with pytest.raises(InvalidCrossing):
        k.project("telepathy")


def test_bat_14_unknown_operation_refuses_instead_of_inventing_affordance():
    k = kernel()
    with pytest.raises(InvalidCrossing):
        k.preview("erase-history", "Nothing happened.", rationale="Nope.")


def test_bat_15_return_address_tracks_current_unresolved_and_residue():
    k = kernel()
    preview = k.preview(
        "reinterpret",
        "The bell means invitation.",
        rationale="New evidence.",
    )
    receipt = k.execute(
        preview,
        actor="human",
        executor=k.AUTHORITY,
        unresolved=("Invitation from whom?",),
        residue=("danger interpretation preserved in lineage",),
    )
    ret = receipt.return_address
    assert ret.unresolved == ("Invitation from whom?",)
    assert ret.residue == ("danger interpretation preserved in lineage",)
