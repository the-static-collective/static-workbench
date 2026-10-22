"""CLOCKWORK-002: read-only, provenance-bearing astronomical composition.

Every observation is UTC and geocentric. A longitude observation never implies a
local sunrise-based Hindu day, a traditional Chinese lunisolar date, or a Hebrew
religious day (which can start at local sunset). No I/O beyond explicit local
kernel read and optional CLI output; no network, system clock, or project effect.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .clockwork import panchanga_coordinates


def parse_instant(value: str) -> datetime:
    """Require an ISO-8601 timestamp with explicit UTC offset; normalize to UTC."""
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("instant must be a bounded ISO-8601 timestamp with UTC offset")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid ISO-8601 instant") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def make_observation(*, instant: str, sun_longitude: float, moon_longitude: float,
                     ayanamsa: float, ayanamsa_name: str,
                     provider: dict[str, str]) -> dict[str, Any]:
    """Pure composition of supplied ephemeris coordinates; does not validate their origin."""
    date = parse_instant(instant)
    if not isinstance(ayanamsa_name, str) or not ayanamsa_name.strip() or len(ayanamsa_name) > 128:
        raise ValueError("a named ayanamsa convention is required")
    if not isinstance(provider, dict) or not all(
        isinstance(provider.get(key), str) and provider[key].strip()
        for key in ("name", "version", "source", "coordinate_frame")
    ):
        raise ValueError("provider must identify name, version, source and coordinate_frame")
    if provider["coordinate_frame"] != "geocentric_apparent_ecliptic_of_date":
        raise ValueError("longitude coordinate frame must be geocentric apparent ecliptic of date")
    coordinates = panchanga_coordinates(sun_longitude, moon_longitude, ayanamsa)
    sun = sun_longitude % 360
    moon = moon_longitude % 360
    return {
        "kind": "experimental_astronomical_coordinate_packet",
        "instant_utc": date.isoformat().replace("+00:00", "Z"),
        "observer": "geocenter",
        "provider": dict(provider),
        "longitudes_degrees": {"sun_tropical": sun, "moon_tropical": moon,
                               "sun_sidereal": (sun - ayanamsa) % 360,
                               "moon_sidereal": (moon - ayanamsa) % 360},
        "ayanamsa": {"name": ayanamsa_name, "degrees": ayanamsa,
                     "status": "caller_supplied_not_astronomically_validated"},
        "hindu_angular": coordinates,
        "chinese_solar": {"index_from_vernal_equinox_zero_based": int(sun // 15),
                          "segment_degrees": 15, "kind": "instantaneous_24_solar_term_sector_not_exact_transition_time"},
        "chinese_lunar_mansion": {"status": "not_calculated", "reason": "traditional 28-mansion boundaries are not uniform zodiac sectors"},
        "non_claims": ["longitude source is caller-provided unless a kernel adapter establishes it",
                       "not a full local Panchanga or Chinese lunisolar date",
                       "no astronomy-derived Jubilee, Egyptian, or I Ching correspondence",
                       "no automatic synchronization with abstract counter ticks"],
    }


def hebrew_civil_utc_date(instant: str) -> dict[str, Any]:
    """A Hebrew date for the UTC Gregorian *civil* date, NOT a local sunset day."""
    date = parse_instant(instant)
    try:
        import pyluach
        from pyluach import dates
    except ImportError as exc:
        raise RuntimeError("optional dependency pyluach is required for Hebrew civil-date conversion") from exc
    result = dates.GregorianDate(date.year, date.month, date.day).to_heb()
    return {"kind": "hebrew_date_of_utc_civil_date_not_local_sunset_day",
            "gregorian_utc_date": date.date().isoformat(),
            "hebrew": {"year": result.year, "month_number": result.month,
                       "month_name": result.month_name(), "day": result.day},
            "provider": {"name": "pyluach", "version": pyluach.__version__,
                         "conversion_basis": "UTC civil date; local sunset NOT calculated"}}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def observe_with_skyfield(*, instant: str, kernel_path: str,
                          ayanamsa: float, ayanamsa_name: str) -> dict[str, Any]:
    """Actual geocentric Sun/Moon longitudes from an explicit LOCAL .bsp file.

    No implicit kernel download. The exact kernel is hashed and library version
    recorded. The caller must choose/justify the sidereal ayanamsa convention.
    """
    date = parse_instant(instant)
    if not isinstance(kernel_path, str) or not kernel_path.strip():
        raise ValueError("an explicit local BSP kernel file is required")
    path = Path(kernel_path).expanduser().resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".bsp":
        raise ValueError("kernel_path must point to a local .bsp file")
    try:
        import skyfield
        from skyfield.api import load, load_file
        from skyfield.framelib import ecliptic_frame
    except ImportError as exc:
        raise RuntimeError("optional dependency skyfield is required for astronomical computation") from exc
    kernel_hash = _sha256_file(path)
    ephemeris = load_file(str(path))
    t = load.timescale(builtin=True).from_datetime(date)
    earth = ephemeris["earth"].at(t)
    def longitude(body: str) -> float:
        _, angle, _ = earth.observe(ephemeris[body]).apparent().frame_latlon(ecliptic_frame)
        return float(angle.degrees % 360)
    return make_observation(
        instant=date.isoformat(), sun_longitude=longitude("sun"),
        moon_longitude=longitude("moon"), ayanamsa=ayanamsa,
        ayanamsa_name=ayanamsa_name,
        provider={"name": "Skyfield", "version": skyfield.__version__,
                  "source": str(path), "kernel_sha256": kernel_hash,
                  "coordinate_frame": "geocentric_apparent_ecliptic_of_date",
                  "timescale": "Skyfield built-in timescale tables",
                  "kernel_downloaded_by_adapter": "false"})


def main() -> None:
    parser = argparse.ArgumentParser(description="CLOCKWORK-002: read-only UTC astronomical observation")
    parser.add_argument("--instant", required=True, help="ISO-8601 timestamp with explicit offset")
    parser.add_argument("--kernel", required=True, help="existing local .bsp ephemeris file; never downloaded")
    parser.add_argument("--ayanamsa-degrees", required=True, type=float)
    parser.add_argument("--ayanamsa-name", required=True)
    parser.add_argument("--hebrew-utc-date", action="store_true", help="UTC civil date, NOT sunset-based")
    args = parser.parse_args()
    packet = observe_with_skyfield(instant=args.instant, kernel_path=args.kernel,
                                  ayanamsa=args.ayanamsa_degrees, ayanamsa_name=args.ayanamsa_name)
    if args.hebrew_utc_date:
        packet["hebrew_civil_utc_date"] = hebrew_civil_utc_date(args.instant)
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
