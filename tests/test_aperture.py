from static_workbench.aperture import analyze_aperture


def test_ambiguous_bank_sentence_preserves_multiple_readings():
    result = analyze_aperture("The bank moved.")

    assert result.raw_text == "The bank moved."
    assert result.status == "unresolved"
    assert len(result.readings) == 3
    assert {reading.id for reading in result.readings} == {
        "bank.financial",
        "bank.river",
        "bank.maneuver",
    }
    assert any(gap.code == "ambiguous_bank" for gap in result.gaps)
    assert [candidate.kind for candidate in result.triad] == ["fact_candidate", "idea", "relation_candidate"]


def test_later_flood_context_narrows_current_field_without_changing_raw():
    result = analyze_aperture(
        "The bank moved.",
        "After the flood, the bank moved six feet east.",
    )

    assert result.raw_text == "The bank moved."
    assert [reading.id for reading in result.readings] == ["bank.river"]
    assert result.status == "narrowed"
    assert result.context[0].source == "supplied_context"


def test_unknown_text_refuses_to_invent_semantics():
    result = analyze_aperture("Purple kettle theorem.")

    assert result.raw_text == "Purple kettle theorem."
    assert result.status == "unresolved"
    assert [reading.id for reading in result.readings] == ["literal.carrier"]
    assert any(gap.code == "no_deterministic_fixture" for gap in result.gaps)
    assert result.triad == ()
