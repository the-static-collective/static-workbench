"""Experimental clock-of-clocks: pure transforms, never an astronomical authority.

No imported sacred text, no external code, no I/O except optional CLI display.
Tick is an abstract integer. A physical instant is NOT a tick unless a separate,
explicitly calibrated adapter maps between them.
"""
from __future__ import annotations

import argparse
import json
import math
import unicodedata
from typing import Any

STEMS = ("jia", "yi", "bing", "ding", "wu", "ji", "geng", "xin", "ren", "gui")
BRANCHES = ("zi", "chou", "yin", "mao", "chen", "si", "wu", "wei", "shen", "you", "xu", "hai")
FOUR = ("Osiris", "Isis", "Seth", "Nephthys")
DIRECTIONS = ("north", "east", "south", "west")
MOVING_KARANAS = ("Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti")
HEBREW_VALUES = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400)))
HEBREW_VALUES.update(dict(zip("ךםןףץ", (20, 40, 50, 80, 90))))


def lcm(*periods: int) -> int:
    """Joint return for fixed integer periods; no calendar-time claim."""
    if not periods or any(type(n) is not int or n <= 0 for n in periods):
        raise ValueError("periods must be positive integers")
    return math.lcm(*periods)


def tick_state(tick: int, *, jubilee_period: int = 50) -> dict[str, Any]:
    """Counter positions; gate is an INVENTED encoding, not King Wen order."""
    if type(tick) is not int or tick < 0:
        raise ValueError("tick must be a nonnegative integer")
    if jubilee_period not in (49, 50):
        raise ValueError("jubilee_period must be declared as 49 or 50")
    gate = tick % 64
    return {
        "kind": "experimental_abstract_tick",
        "tick": tick,
        "stem_branch": {"index": tick % 60, "stem": STEMS[tick % 10], "branch": BRANCHES[tick % 12]},
        "gate": {"index": gate, "binary": f"{gate:06b}", "source": FOUR[gate // 16],
                 "receiver": FOUR[(gate // 4) % 4], "direction": DIRECTIONS[gate % 4]},
        "jubilee_counter": {"period": jubilee_period, "index": tick % jubilee_period,
                            "boundary": tick > 0 and tick % jubilee_period == 0},
        "alignment": {"phase_class": tick % 4,
                      "sixty_sixtyfour_return": tick > 0 and tick % 960 == 0,
                      "joint_return": tick > 0 and tick % lcm(60, 64, jubilee_period) == 0},
        "non_claims": ["not an astronomical date", "not a traditional I Ching hexagram number",
                       "not a scriptural interpretation or permission to act"],
    }


def panchanga_coordinates(sun_longitude: float, moon_longitude: float,
                           ayanamsa: float) -> dict[str, Any]:
    """Instantaneous angular sectors only, NOT a full local daily Panchanga.

    Inputs must be geocentric tropical ecliptic longitudes in degrees and a
    declared ayanamsa in degrees from the SAME epoch/frame and provider.
    No ephemeris, sunrise, weekday, localization, or leap month is inferred.
    """
    values = (sun_longitude, moon_longitude, ayanamsa)
    if any(isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) for x in values):
        raise ValueError("angular inputs must be finite numbers")
    sun, moon = (sun_longitude % 360), (moon_longitude % 360)
    s_sid, m_sid = (sun - ayanamsa) % 360, (moon - ayanamsa) % 360
    elongation = (moon - sun) % 360
    half = min(59, int(elongation // 6))
    if half == 0:
        karana = "Kimstughna"
    elif half >= 57:
        karana = ("Shakuni", "Chatushpada", "Naga")[half - 57]
    else:
        karana = MOVING_KARANAS[(half - 1) % 7]
    return {"kind": "instantaneous_angular_sectors_not_daily_panchanga",
            "tithi": min(30, int(elongation // 12) + 1),
            "nakshatra": min(27, int(m_sid // (360 / 27)) + 1),
            "yoga": min(27, int(((s_sid + m_sid) % 360) // (360 / 27)) + 1),
            "karana": {"half_tithi_index": half, "name": karana},
            "vara": None, "sunrise": None, "ayanamsa_degrees": ayanamsa,
            "non_claims": ["not a verified ephemeris", "not a local sunrise-based almanac"]}


def hebrew_letters(text: str) -> str:
    """Strip Hebrew combining marks and spacing; reject unhandled letters."""
    if not isinstance(text, str):
        raise TypeError("text must be Unicode string")
    out = []
    for char in unicodedata.normalize("NFD", text):
        if char in HEBREW_VALUES:
            out.append(char)
        elif unicodedata.category(char) == "Mn" or char.isspace() or char in "־׀׃,.;:!?\"'":
            continue
        else:
            raise ValueError(f"unsupported character U+{ord(char):04X}")
    return "".join(out)


def gematria(text: str) -> int:
    """Standard Hebrew additive values; final letters use their ordinary values."""
    return sum(HEBREW_VALUES[c] for c in hebrew_letters(text))


def els_matches(corpus: str, term: str, *, max_skip: int = 20,
                max_results: int = 100) -> dict[str, Any]:
    """Bounded equidistant-letter search; a match is NOT evidence of a code."""
    if type(max_skip) is not int or not 1 <= max_skip <= 1000:
        raise ValueError("max_skip must be an integer in 1..1000")
    if type(max_results) is not int or not 1 <= max_results <= 10000:
        raise ValueError("max_results must be an integer in 1..10000")
    data, needle = hebrew_letters(corpus), hebrew_letters(term)
    if len(needle) < 2:
        raise ValueError("term must have at least two Hebrew letters")
    matches = []
    trials = 0
    for step in range(-max_skip, max_skip + 1):
        if step == 0:
            continue
        for start in range(len(data)):
            end = start + (len(needle) - 1) * step
            if not 0 <= end < len(data):
                continue
            trials += 1
            if all(data[start + i * step] == c for i, c in enumerate(needle)):
                if len(matches) < max_results:
                    matches.append({"start_zero_based": start, "step": step})
                else:
                    return {"matches": matches, "trials": trials, "truncated": True,
                            "normalization": "hebrew_consonants_only", "non_claim": "a match is not evidence of a hidden code"}
    return {"matches": matches, "trials": trials, "truncated": False,
            "normalization": "hebrew_consonants_only", "non_claim": "a match is not evidence of a hidden code"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimental abstract clock of clocks (no astronomical date implied)")
    parser.add_argument("--tick", type=int, default=960)
    parser.add_argument("--jubilee-period", type=int, choices=(49, 50), default=50)
    args = parser.parse_args()
    print(json.dumps(tick_state(args.tick, jubilee_period=args.jubilee_period), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
