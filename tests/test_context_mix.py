"""L BRANCH proposals remain deterministic, inert, bounded, and source-aware."""
from dataclasses import replace

import pytest

from static_workbench.context_mix import ContextLane, ContextMixError, Send, propose_mix

A = "a" * 64
B = "b" * 64


def song():
    return ContextLane("song", "local:song:v1", A, "human-supplied",
                       ("video", "draft", "live"), ("whole", "section:chorus"))


def lyrics():
    return ContextLane("lyrics", "local:lyrics:v3", B, "human-supplied",
                       ("video", "draft"), ("whole", "section:verse_1"))


def art():
    return ContextLane("art", "local:art:v1", A, "observed", ("video",))


def test_same_context_can_propose_distinct_replayable_listening_plans():
    bank = (song(), lyrics(), art())
    visual = (Send("song", "video", "whole", "strong", "reference", "follow"),
              Send("lyrics", "video", "section:verse_1", "light", "excerpt", "contrast"))
    narrative = (Send("lyrics", "draft", "whole", "strong", "summary", "accent"),)
    first = propose_mix(bank, visual)
    assert first == propose_mix(bank[::-1], visual[::-1])
    second = propose_mix(bank, narrative)
    assert first.context_sha256 == second.context_sha256
    assert first.plan_sha256 != second.plan_sha256
    assert first.used == ("lyrics", "song")
    assert first.ignored == ("art",)
    assert second.used == ("lyrics",)
    assert second.ignored == ("art", "song")
    assert first.status == "unrun_proposal_no_authority"


def test_missing_evidence_is_not_fabricated_or_consumed():
    bank = (song(), replace(art(), available=False))
    proposal = propose_mix(bank, (Send("song", "video"),))
    assert proposal.unavailable == ("art",)
    assert proposal.ignored == ()
    with pytest.raises(ContextMixError, match="unavailable"):
        propose_mix(bank, (Send("art", "video"),))


@pytest.mark.parametrize("invalid, error", [
    ((Send("missing", "video"),), "unknown lane"),
    ((Send("song", "not_declared"),), "destination not declared"),
    ((Send("song", "video", "section:verse_1"),), "scope not declared"),
    ((Send("song", "video", weight="arbitrary"),), "unsupported send"),
    ((Send("song", "video", response="invent"),), "unsupported send"),
    ((Send("song", "video"), Send("song", "video")), "duplicate lane/target/scope"),
])
def test_bad_routes_refuse(invalid, error):
    with pytest.raises(ContextMixError, match=error):
        propose_mix((song(),), invalid)


def test_source_revision_and_route_controls_affect_identity():
    bank = (song(), lyrics())
    base = propose_mix(bank, (Send("song", "video"),))
    assert base.context_sha256 != propose_mix(
        (replace(song(), source_sha256=B), lyrics()),
        (Send("song", "video"),)).context_sha256
    for send in [
        Send("song", "video", weight="strong"),
        Send("song", "video", response="contrast"),
        Send("song", "video", detail="summary"),
        Send("song", "video", scope="section:chorus"),
        Send("song", "draft"),
    ]:
        assert propose_mix(bank, (send,)).plan_sha256 != base.plan_sha256


def test_inferred_lane_is_separately_reported_not_promoted():
    inferred = ContextLane("vocal_salience", "analysis:sample:1", A, "inferred",
                           ("video",))
    proposal = propose_mix((inferred, song()), (Send("vocal_salience", "video"),))
    assert proposal.influence_only == ("vocal_salience",)
    assert proposal.ignored == ("song",)
    assert not hasattr(proposal, "authorized")
    assert not hasattr(proposal, "source_bytes")


def test_duplicate_lane_or_invalid_source_identity_refuses():
    with pytest.raises(ContextMixError, match="duplicate lane"):
        propose_mix((song(), song()), ())
    with pytest.raises(ContextMixError, match="source_sha256"):
        propose_mix((replace(song(), source_sha256="unknown"),), ())
    with pytest.raises(ContextMixError, match="declared target"):
        propose_mix((replace(song(), declared_targets=("video", "video")),), ())
    with pytest.raises(ContextMixError, match="bounded context"):
        propose_mix((song(),) * 33, ())


def test_empty_route_is_valid_observation_not_automatic_consumption():
    proposal = propose_mix((song(), art()), ())
    assert proposal.used == ()
    assert proposal.ignored == ("art", "song")
    assert proposal.sends == ()
