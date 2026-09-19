from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SignalItem:
    kind: str
    text: str


@dataclass(frozen=True)
class ContextItem:
    source: str
    text: str


@dataclass(frozen=True)
class GapItem:
    code: str
    text: str


@dataclass(frozen=True)
class ReadingCandidate:
    id: str
    text: str
    basis: str


@dataclass(frozen=True)
class TriadCandidate:
    kind: str
    text: str
    reading_id: str | None = None


@dataclass(frozen=True)
class ApertureResult:
    raw_text: str
    signal: tuple[SignalItem, ...]
    context: tuple[ContextItem, ...]
    gaps: tuple[GapItem, ...]
    readings: tuple[ReadingCandidate, ...]
    triad: tuple[TriadCandidate, ...]
    status: str


_BANK_READINGS = (
    ReadingCandidate(
        id="bank.financial",
        text="A financial institution changed location or organizational position.",
        basis="lexical ambiguity fixture: bank",
    ),
    ReadingCandidate(
        id="bank.river",
        text="A river bank physically shifted position.",
        basis="lexical ambiguity fixture: bank",
    ),
    ReadingCandidate(
        id="bank.maneuver",
        text="A vehicle or aircraft performed a banking maneuver.",
        basis="lexical ambiguity fixture: bank",
    ),
)


def _contains_bank(text: str) -> bool:
    tokens = text.lower().replace(".", " ").replace(",", " ").split()
    return "bank" in tokens


def _context_selects_river(context_text: str) -> bool:
    lowered = context_text.lower()
    return any(token in lowered for token in ("flood", "river", "feet east", "shore", "water"))


def analyze_aperture(raw_text: str, context_text: str | None = None) -> ApertureResult:
    raw = raw_text
    signal = (SignalItem(kind="raw_text", text=raw),)
    context = () if not context_text else (ContextItem(source="supplied_context", text=context_text),)

    if _contains_bank(raw):
        readings = _BANK_READINGS
        status = "unresolved"
        gaps: tuple[GapItem, ...] = (
            GapItem(
                code="ambiguous_bank",
                text="The token 'bank' admits multiple deterministic fixture readings under the present cut.",
            ),
        )
        if context_text and _context_selects_river(context_text):
            readings = (_BANK_READINGS[1],)
            status = "narrowed"
            gaps = ()

        triad = (
            TriadCandidate(
                kind="fact_candidate",
                text="The raw carrier states that a bank moved.",
            ),
            TriadCandidate(
                kind="idea",
                text="The intended sense of 'bank' remains a semantic question unless attributable context narrows it.",
            ),
            TriadCandidate(
                kind="relation_candidate",
                text="bank --moved--> unspecified_position_or_state",
            ),
        )
        return ApertureResult(
            raw_text=raw,
            signal=signal,
            context=context,
            gaps=gaps,
            readings=readings,
            triad=triad,
            status=status,
        )

    return ApertureResult(
        raw_text=raw,
        signal=signal,
        context=context,
        gaps=(
            GapItem(
                code="no_deterministic_fixture",
                text="No deterministic APERTURE fixture is declared for this carrier; semantics remain unresolved.",
            ),
        ),
        readings=(
            ReadingCandidate(
                id="literal.carrier",
                text=raw,
                basis="literal carrier only; no semantic inference",
            ),
        ),
        triad=(),
        status="unresolved",
    )
