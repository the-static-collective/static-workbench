from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Iterable

from .holographic_kernel_001 import Projection


class FieldError(RuntimeError):
    """Base error for the bounded holographic-field specimen."""


class StaleFieldCheckpoint(FieldError):
    pass


class MissingDurableContext(FieldError):
    pass


class FieldIntegrityError(FieldError):
    pass


def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object, size: int = 24) -> str:
    return sha256(_canon(value).encode("utf-8")).hexdigest()[:size]


@dataclass(frozen=True)
class ContextAtom:
    atom_id: str
    kind: str
    text: str
    relevance: int
    ordinal: int

    @property
    def digest(self) -> str:
        return _digest(
            {
                "atom_id": self.atom_id,
                "kind": self.kind,
                "text": self.text,
                "relevance": self.relevance,
                "ordinal": self.ordinal,
            }
        )


@dataclass(frozen=True)
class ContextRef:
    """Coordination-plane reference. Deliberately contains no payload text."""

    atom_id: str
    digest: str
    kind: str
    relevance: int
    ordinal: int


@dataclass(frozen=True)
class FieldDoor:
    direction: str
    label: str
    target: str


@dataclass(frozen=True)
class ContextFrame:
    field_digest: str
    kernel_id: str
    state_id: str
    state_digest: str
    projection_kind: str
    capacity: int
    held: tuple[ContextAtom, ...]
    poured: tuple[ContextRef, ...]
    doors: tuple[FieldDoor, ...]

    @property
    def saturated(self) -> bool:
        return len(self.held) == self.capacity


@dataclass(frozen=True)
class FieldCheckpoint:
    """What survives field extinction outside the active context field."""

    field_digest: str
    kernel_id: str
    state_id: str
    state_digest: str
    capacity: int
    held_refs: tuple[ContextRef, ...]
    poured_refs: tuple[ContextRef, ...]
    doors: tuple[FieldDoor, ...]


class DurableContextStore:
    """X-plane specimen: durable payload memory, separate from live context."""

    def __init__(self) -> None:
        self._atoms: dict[str, ContextAtom] = {}
        self._ordinal = 0

    def receive(self, text: str, *, kind: str = "signal", relevance: int = 0) -> ContextAtom:
        if not text.strip():
            raise FieldIntegrityError("context text must not be empty")
        ordinal = self._ordinal
        self._ordinal += 1
        atom_id = "a_" + _digest(
            {"text": text, "kind": kind, "relevance": relevance, "ordinal": ordinal}
        )
        atom = ContextAtom(
            atom_id=atom_id,
            kind=kind,
            text=text,
            relevance=int(relevance),
            ordinal=ordinal,
        )
        self._atoms[atom_id] = atom
        return atom

    def all(self) -> tuple[ContextAtom, ...]:
        return tuple(self._atoms.values())

    def get(self, atom_id: str) -> ContextAtom:
        try:
            return self._atoms[atom_id]
        except KeyError as exc:
            raise MissingDurableContext(f"missing durable context: {atom_id}") from exc

    def remove_for_test(self, atom_id: str) -> None:
        self._atoms.pop(atom_id, None)


class HolographicContextField:
    """
    HOLOGRAPHIC-FIELD-001 / RECEIVE-HOLD-POUR specimen.

    This is a semantic-slot model, not a claim that a production LLM should
    literally consume every available token. The field tries to keep its
    bounded active context maximally occupied by locally relevant material.

    TranchNOSE-inspired split:
      * X       -> DurableContextStore + durable kernel state outside this class
      * G_local -> ContextRef / FieldCheckpoint coordination metadata
      * G_field -> ContextFrame: the currently inhabited relational context

    G_local intentionally cannot reconstruct payload text without X.
    """

    def __init__(self, capacity: int, *, store: DurableContextStore | None = None) -> None:
        if capacity < 1:
            raise FieldIntegrityError("capacity must be positive")
        self.capacity = capacity
        self.store = store or DurableContextStore()
        self._previous_field_digest: str | None = None

    def receive(self, text: str, *, kind: str = "signal", relevance: int = 0) -> ContextAtom:
        return self.store.receive(text, kind=kind, relevance=relevance)

    @staticmethod
    def _ref(atom: ContextAtom) -> ContextRef:
        return ContextRef(
            atom_id=atom.atom_id,
            digest=atom.digest,
            kind=atom.kind,
            relevance=atom.relevance,
            ordinal=atom.ordinal,
        )

    def hold(self) -> tuple[ContextAtom, ...]:
        """Fill the active vessel with the highest-value local working set."""
        ranked = sorted(
            self.store.all(),
            key=lambda atom: (atom.relevance, atom.ordinal),
            reverse=True,
        )
        return tuple(ranked[: self.capacity])

    def pour(self, projection: Projection, held: Iterable[ContextAtom]) -> ContextFrame:
        """Externalize non-held material as addressable refs, never silent loss."""
        held = tuple(held)
        held_ids = {atom.atom_id for atom in held}
        all_atoms = self.store.all()
        all_ids = {atom.atom_id for atom in all_atoms}
        if any(atom.atom_id not in all_ids for atom in held):
            raise FieldIntegrityError("held context must originate in durable store")

        poured = tuple(self._ref(atom) for atom in all_atoms if atom.atom_id not in held_ids)
        doors: list[FieldDoor] = []
        if self._previous_field_digest is not None:
            doors.append(
                FieldDoor(
                    direction="backward",
                    label="previous-now",
                    target=f"field:{self._previous_field_digest}",
                )
            )
        doors.extend(
            FieldDoor(direction="forward", label=name, target=f"continuation:{name}")
            for name in projection.return_address.continuations
        )
        doors.extend(
            FieldDoor(
                direction="sideways",
                label=f"poured:{ref.kind}",
                target=f"context:{ref.atom_id}",
            )
            for ref in poured
        )

        constitutional_payload = {
            "kernel_id": projection.kernel_id,
            "state_id": projection.state_id,
            "state_digest": projection.state_digest,
            "capacity": self.capacity,
            "held": [asdict(self._ref(atom)) for atom in held],
            "poured": [asdict(ref) for ref in poured],
            "doors": [asdict(door) for door in doors],
        }
        field_digest = _digest(constitutional_payload, 32)
        frame = ContextFrame(
            field_digest=field_digest,
            kernel_id=projection.kernel_id,
            state_id=projection.state_id,
            state_digest=projection.state_digest,
            projection_kind=projection.projection_kind,
            capacity=self.capacity,
            held=held,
            poured=poured,
            doors=tuple(doors),
        )
        self._previous_field_digest = field_digest
        return frame

    def now(self, projection: Projection) -> ContextFrame:
        return self.pour(projection, self.hold())

    def checkpoint(self, frame: ContextFrame) -> FieldCheckpoint:
        return FieldCheckpoint(
            field_digest=frame.field_digest,
            kernel_id=frame.kernel_id,
            state_id=frame.state_id,
            state_digest=frame.state_digest,
            capacity=frame.capacity,
            held_refs=tuple(self._ref(atom) for atom in frame.held),
            poured_refs=frame.poured,
            doors=frame.doors,
        )

    def reconstruct(self, projection: Projection, checkpoint: FieldCheckpoint) -> ContextFrame:
        """
        Reinstantiate the field after extinction from durable payloads + refs.

        Refuses if the kernel moved, a ref was altered, or X no longer contains
        enough information. Reappearance is therefore not described as memory
        that lived only in the active field.
        """
        if (
            projection.kernel_id != checkpoint.kernel_id
            or projection.state_id != checkpoint.state_id
            or projection.state_digest != checkpoint.state_digest
        ):
            raise StaleFieldCheckpoint("kernel state changed after checkpoint")
        if checkpoint.capacity != self.capacity:
            raise FieldIntegrityError("checkpoint capacity does not match field capacity")

        held: list[ContextAtom] = []
        for ref in checkpoint.held_refs:
            atom = self.store.get(ref.atom_id)
            if self._ref(atom) != ref:
                raise FieldIntegrityError(f"held context ref failed integrity check: {ref.atom_id}")
            held.append(atom)
        for ref in checkpoint.poured_refs:
            atom = self.store.get(ref.atom_id)
            if self._ref(atom) != ref:
                raise FieldIntegrityError(f"poured context ref failed integrity check: {ref.atom_id}")

        frame = ContextFrame(
            field_digest=checkpoint.field_digest,
            kernel_id=checkpoint.kernel_id,
            state_id=checkpoint.state_id,
            state_digest=checkpoint.state_digest,
            projection_kind=projection.projection_kind,
            capacity=checkpoint.capacity,
            held=tuple(held),
            poured=checkpoint.poured_refs,
            doors=checkpoint.doors,
        )
        self._previous_field_digest = frame.field_digest
        return frame

    def resolve_sideways(self, door: FieldDoor) -> ContextAtom:
        if door.direction != "sideways" or not door.target.startswith("context:"):
            raise FieldIntegrityError("door is not a sideways context address")
        return self.store.get(door.target.removeprefix("context:"))


def coordinator_payload(checkpoint: FieldCheckpoint) -> dict[str, object]:
    """Serializable G_local view; intentionally excludes active payload text."""
    return asdict(checkpoint)
