"""OLD-GROWTH-001: source-selection, immutable-parent and authority-boundary tests."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest

from static_workbench.old_growth import OldGrowthError, compose


def source(text="The original archive stays.\nA new idea approaches.", *, name="seedFORK",
           start=0, end=None, commit="a" * 40):
    content = text.encode("utf-8")
    return {
        "repository": f"the-static-collective/{name}",
        "commit": commit,
        "path": "docs/original.txt",
        "content": text,
        "content_sha256": hashlib.sha256(content).hexdigest(),
        "start_byte": start,
        "end_byte": len(content) if end is None else end,
    }


def run(a=None, b=None, **overrides):
    params = {
        "keep": "Both source identities and unresolved questions",
        "bend": "A local creative workbench",
        "question": "Could these two excerpts suggest a bounded reversible test?",
        "relation_lane": "active_tension",
        "move": "fuse",
    }
    params.update(overrides)
    return compose(a if a is not None else source(),
                   b if b is not None else source(name="mundaneWORMHOLE"),
                   **params)


def test_deterministic_packet_preserves_two_distinct_source_identities_and_excerpts():
    a, b = source(), source(name="mundaneWORMHOLE")
    original_a, original_b = copy.deepcopy(a), copy.deepcopy(b)
    one, two = run(a, b), run(a, b)
    assert one == two
    packet = one["packet"]
    assert packet["sources"][0]["repository"].endswith("/seedFORK")
    assert packet["sources"][1]["repository"].endswith("/mundaneWORMHOLE")
    assert packet["sources"][0]["commit"] == a["commit"]
    assert packet["sources"][0]["excerpt"] == a["content"]
    assert packet["sources"][1]["content_sha256"] == b["content_sha256"]
    assert a == original_a and b == original_b
    assert packet["authority"] == "none" and packet["promotion"] == "NONE"
    assert packet["candidate"]["status"] == "PROPOSED_UNRUN"
    assert packet["parallel_alternative"]["status"] == "LEFT_OPEN"
    assert one["receipt"]["status"] == "calculated_not_persisted"
    assert hashlib.sha256(json.dumps(
        packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest() == one["packet_sha256"]


def test_output_contains_only_selected_excerpt_not_unselected_source_text():
    text = "private-unselected-prefix\npublic selected passage\nprivate-unselected-suffix"
    raw = text.encode("utf-8")
    selected = b"public selected passage"
    start = raw.index(selected)
    packet = run(source(text, start=start, end=start + len(selected)))["packet"]
    output = json.dumps(packet)
    assert packet["sources"][0]["excerpt"] == selected.decode()
    assert "private-unselected-prefix" not in output
    assert "private-unselected-suffix" not in output
    assert "content" not in packet["sources"][0]
    assert packet["sources"][0]["source_byte_length"] == len(raw)


def test_tampered_supplied_source_bytes_refuse_even_if_excerpt_unchanged():
    a = source("visible\nprotected parent")
    a["content"] = "visible\nchanged parent"
    with pytest.raises(OldGrowthError, match="do not match"):
        run(a)


def test_exact_utf8_byte_span_required():
    a = source("éclair", start=1, end=3)
    with pytest.raises(OldGrowthError, match="UTF-8 character"):
        run(a)
    good = source("éclair", start=0, end=2)
    assert run(good)["packet"]["sources"][0]["excerpt"] == "é"


@pytest.mark.parametrize("change", [
    {"commit": "not-a-commit"},
    {"path": "../outside"},
    {"path": "/absolute"},
    {"path": "a//b"},
    {"repository": "../../elsewhere"},
    {"start_byte": True},
    {"end_byte": 999999},
    {"content_sha256": "0" * 64},
    {"authority": "execute"},
])
def test_bad_or_authority_smuggling_source_refuses(change):
    with pytest.raises(OldGrowthError):
        run({**source(), **change})


def test_duplicate_locator_refuses_but_distinct_spans_of_same_file_allowed():
    a = source("alpha beta", start=0, end=5)
    with pytest.raises(OldGrowthError, match="distinct"):
        run(a, copy.deepcopy(a))
    b = source("alpha beta", start=6, end=10)
    output = run(a, b)
    assert [s["excerpt"] for s in output["packet"]["sources"]] == ["alpha", "beta"]


def test_human_declared_lane_does_not_imply_verified_relation():
    first = run(relation_lane="lineage")
    second = run(relation_lane="semantic")
    assert first["packet_sha256"] != second["packet_sha256"]
    assert first["packet"]["declarations"]["relation_status"] == "human_declared_not_inferred"
    assert "not inferred facts" in first["packet"]["non_claims"][2]
    with pytest.raises(OldGrowthError):
        run(relation_lane="automatic_authority")
    with pytest.raises(OldGrowthError):
        run(move="execute")
    with pytest.raises(OldGrowthError):
        run(question=" \n ")


def test_refuses_unbounded_sources_excerpts_and_invalid_unicode():
    with pytest.raises(OldGrowthError, match="131072"):
        run(source("x" * 131073))
    with pytest.raises(OldGrowthError, match="bounded byte span"):
        run(source("x" * 4097))
    with pytest.raises(OldGrowthError, match="UTF-8"):
        run(source("\ud800"))
