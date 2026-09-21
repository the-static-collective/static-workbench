import json
import sys

import pytest

from static_workbench.clockwork import (
    els_matches, gematria, hebrew_letters, lcm, panchanga_coordinates, tick_state,
)


def test_periods_and_boundaries():
    assert lcm(10, 12) == 60
    assert lcm(60, 64) == 960
    assert lcm(60, 64, 50) == 4800
    assert lcm(60, 64, 49) == 47040
    assert tick_state(960)["alignment"] == {"phase_class": 0, "sixty_sixtyfour_return": True, "joint_return": False}
    assert tick_state(4800)["alignment"]["joint_return"] is True
    assert tick_state(49, jubilee_period=49)["jubilee_counter"]["boundary"] is True
    assert tick_state(0)["jubilee_counter"]["boundary"] is False


def test_gate_is_bijective():
    states = [tick_state(i)["gate"] for i in range(64)]
    assert len({(s["source"], s["receiver"], s["direction"]) for s in states}) == 64
    assert states[0]["binary"] == "000000"
    assert states[-1]["binary"] == "111111"
    assert tick_state(64)["gate"] == states[0]


def test_sectors_and_karana_boundaries():
    new = panchanga_coordinates(0.0, 0.0, 24.0)
    assert new["tithi"] == 1 and new["karana"]["name"] == "Kimstughna"
    assert panchanga_coordinates(0.0, 6.0, 24.0)["karana"]["name"] == "Bava"
    assert panchanga_coordinates(0.0, 342.0, 24.0)["karana"]["name"] == "Shakuni"
    assert panchanga_coordinates(0.0, 348.0, 24.0)["karana"]["name"] == "Chatushpada"
    assert panchanga_coordinates(0.0, 354.0, 24.0)["karana"]["name"] == "Naga"
    assert panchanga_coordinates(0.0, 359.999, 24.0)["tithi"] == 30
    assert panchanga_coordinates(0.0, 0.0, 24.0)["vara"] is None


def test_reject_bad_inputs():
    for bad in (-1, 1.2, True):
        with pytest.raises(ValueError):
            tick_state(bad)
    with pytest.raises(ValueError):
        panchanga_coordinates(float("nan"), 0, 24)
    with pytest.raises(ValueError):
        lcm(60, 0)


def test_text_arithmetic_and_explicit_search_limits():
    assert hebrew_letters("שָׁלוֹם") == "שלום"
    assert gematria("שלום") == 376
    assert gematria("מלך") == 90  # final kaf=20, not the alternative 500 mapping
    assert {"start_zero_based": 0, "step": 2} in els_matches("אבגדאבגד", "אג", max_skip=2)["matches"]
    with pytest.raises(ValueError):
        gematria("ABC")
    with pytest.raises(ValueError):
        els_matches("אבגד", "א", max_skip=2)


def test_cli_clicks_three_abstract_ticks(monkeypatch, capsys):
    from static_workbench.clockwork import main
    monkeypatch.setattr(sys, "argv", ["clockwork", "--tick", "960", "--steps", "3"])
    main()
    states = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [s["tick"] for s in states] == [960, 961, 962]
    assert sum(s["alignment"]["sixty_sixtyfour_return"] for s in states) == 1
