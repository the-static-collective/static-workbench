import hashlib
import sys
import types
from datetime import datetime, timezone

import pytest

from static_workbench.clockwork_sky import (
    hebrew_civil_utc_date, make_observation, observe_with_skyfield, parse_instant,
)


def provider():
    return {"name": "test fixture", "version": "fixture-1", "source": "synthetic",
            "coordinate_frame": "geocentric_apparent_ecliptic_of_date"}


def test_timezone_aware_instant_and_rejection():
    assert parse_instant("2026-09-20T09:22:00-05:00") == datetime(2026, 9, 20, 14, 22, tzinfo=timezone.utc)
    assert parse_instant("2026-09-20T14:22:00Z").isoformat() == "2026-09-20T14:22:00+00:00"
    for bad in ("2026-09-20", "2026-09-20T14:22:00", "bogus", "Z" * 90):
        with pytest.raises(ValueError):
            parse_instant(bad)


def test_cross_calendar_angulation_has_distinct_meanings():
    packet = make_observation(instant="2026-03-20T12:00:00Z", sun_longitude=0,
                              moon_longitude=6, ayanamsa=24, ayanamsa_name="fixture-only",
                              provider=provider())
    assert packet["chinese_solar"]["index_from_vernal_equinox_zero_based"] == 0
    assert packet["hindu_angular"]["tithi"] == 1
    assert packet["hindu_angular"]["karana"]["name"] == "Bava"
    assert packet["chinese_lunar_mansion"]["status"] == "not_calculated"
    assert "hebrew_civil_utc_date" not in packet
    assert "UTC" not in packet["kind"]
    assert packet["instant_utc"] == "2026-03-20T12:00:00Z"
    wrap = make_observation(instant="2026-03-20T12:00:00Z", sun_longitude=359.999,
                            moon_longitude=0, ayanamsa=24, ayanamsa_name="test", provider=provider())
    assert wrap["chinese_solar"]["index_from_vernal_equinox_zero_based"] == 23
    assert 1 <= wrap["hindu_angular"]["tithi"] <= 30


def test_provider_and_nan_inputs_rejected():
    args = dict(instant="2026-03-20T12:00:00Z", sun_longitude=0,
                moon_longitude=0, ayanamsa=24, ayanamsa_name="test", provider=provider())
    with pytest.raises(ValueError):
        make_observation(**(args | {"provider": {"name": "test"}}))
    with pytest.raises(ValueError):
        make_observation(**(args | {"provider": provider() | {"coordinate_frame": "topocentric"}}))
    with pytest.raises(ValueError):
        make_observation(**(args | {"moon_longitude": float("nan")}))


def test_hebrew_utc_civil_date_not_local_sunset():
    info = hebrew_civil_utc_date("2026-09-20T09:22:00-05:00")
    assert info["gregorian_utc_date"] == "2026-09-20"
    assert info["hebrew"] == {"year": 5787, "month_number": 7,
                              "month_name": "Tishrei", "day": 9}
    assert "not_local_sunset_day" in info["kind"]


def test_skyfield_adapter_requires_existing_bsp(tmp_path):
    with pytest.raises(FileNotFoundError):
        observe_with_skyfield(instant="2026-09-20T00:00:00Z", kernel_path=str(tmp_path / "no.bsp"),
                              ayanamsa=24, ayanamsa_name="fixture")
    text = tmp_path / "invalid.txt"
    text.write_text("test")
    with pytest.raises(ValueError):
        observe_with_skyfield(instant="2026-09-20T00:00:00Z", kernel_path=str(text),
                              ayanamsa=24, ayanamsa_name="fixture")


def test_offline_skyfield_provider_contract_with_test_double(tmp_path, monkeypatch):
    """Verifies adapter plumbing and hash, NOT accuracy of real ephemeris math."""
    sample = tmp_path / "synthetic.bsp"
    sample.write_bytes(b"synthetic fixture; NOT a real ephemeris")
    class Angle:
        def __init__(self, degrees):
            self.degrees = degrees
    class Observed:
        def __init__(self, degrees):
            self.degrees = degrees
        def apparent(self):
            return self
        def frame_latlon(self, frame):
            assert frame is fake_frame
            return None, Angle(self.degrees), None
    class Earth:
        def at(self, t):
            assert t == datetime(2026, 9, 20, tzinfo=timezone.utc)
            return self
        def observe(self, body):
            return Observed({"sun": 177.3, "moon": 190.1}[body])
    class Ephemeris:
        def __getitem__(self, key):
            return Earth() if key == "earth" else key
    class Scale:
        def from_datetime(self, date):
            return date
    class Loader:
        @staticmethod
        def timescale(builtin):
            assert builtin
            return Scale()
    fake_frame = object()
    sky = types.ModuleType("skyfield")
    sky.__version__ = "test-double"
    skyapi = types.ModuleType("skyfield.api")
    skyapi.load = Loader()
    skyapi.load_file = lambda path: Ephemeris()
    skyframe = types.ModuleType("skyfield.framelib")
    skyframe.ecliptic_frame = fake_frame
    monkeypatch.setitem(sys.modules, "skyfield", sky)
    monkeypatch.setitem(sys.modules, "skyfield.api", skyapi)
    monkeypatch.setitem(sys.modules, "skyfield.framelib", skyframe)
    packet = observe_with_skyfield(instant="2026-09-20T00:00:00Z", kernel_path=str(sample),
                                   ayanamsa=24.5, ayanamsa_name="fixture-only")
    assert packet["longitudes_degrees"]["sun_tropical"] == 177.3
    assert packet["provider"]["kernel_sha256"] == hashlib.sha256(sample.read_bytes()).hexdigest()
    assert packet["chinese_solar"]["index_from_vernal_equinox_zero_based"] == 11
    assert packet["hindu_angular"]["tithi"] == 2
    assert packet["provider"]["kernel_downloaded_by_adapter"] == "false"
