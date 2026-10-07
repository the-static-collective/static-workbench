from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class KernelError(RuntimeError):
    """Base error for the bounded holographic-kernel specimen."""


class StalePreview(KernelError):
    pass


class AuthorityError(KernelError):
    pass


class HistoricalRewriteError(KernelError):
    pass


class InvalidCrossing(KernelError):
    pass


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any, size: int = 20) -> str:
    return sha256(_canon(value).encode("utf-8")).hexdigest()[:size]


@dataclass(frozen=True)
class Relation:
    source_state_id: str
    target_state_id: str
    kind: str
    rationale: str


@dataclass(frozen=True)
class WitnessedState:
    state_id: str
    content: str
    parent_state_id: str | None = None
    relation_kind: str | None = None
    rationale: str | None = None


@dataclass(frozen=True)
class ReturnAddress:
    kernel_id: str
    state_id: str
    unresolved: tuple[str, ...]
    residue: tuple[str, ...]
    continuations: tuple[str, ...]


@dataclass(frozen=True)
class Preview:
    preview_id: str
    kernel_id: str
    base_state_id: str
    operation: str
    candidate_content: str
    relation_kind: str
    rationale: str
    expected_delta: Mapping[str, Any]
    required_authority: str


@dataclass(frozen=True)
class Receipt:
    crossing_id: str
    preview_id: str
    kernel_id: str
    actor: str
    executor: str
    before_state_id: str
    after_state_id: str
    relation_kind: str
    observed_delta: Mapping[str, Any]
    return_address: ReturnAddress


@dataclass(frozen=True)
class Projection:
    projection_kind: str
    kernel_id: str
    state_id: str
    state_digest: str
    authority_owner: str
    affordances: tuple[str, ...]
    lineage_head: tuple[str, ...]
    return_address: ReturnAddress
    presentation: Mapping[str, Any]


class StoryDoorKernel:
    """
    HOLOGRAPHIC-KERNEL-001 specimen.

    Constitutional boundaries:
      * witnessed states are immutable;
      * meaning change is represented by a typed relation, never an in-place edit;
      * projections are pure views and never acquire execution authority;
      * execution consumes an exact preview against the current state;
      * every successful crossing emits a projection-agnostic return address.
    """

    KERNEL_ID = "story-door/holographic-kernel-001"
    AUTHORITY = "story-door-kernel"
    ALLOWED_OPERATIONS = ("after", "before", "instead", "reinterpret")
    ALLOWED_RELATIONS = {
        "after": "extends",
        "before": "preludes",
        "instead": "branches_from",
        "reinterpret": "reframes",
    }

    def __init__(self, opening: str, *, unresolved: Iterable[str] = ()) -> None:
        root_payload = {"kernel": self.KERNEL_ID, "root": opening}
        root_id = "s_" + _digest(root_payload)
        root = WitnessedState(state_id=root_id, content=opening)
        self._states: dict[str, WitnessedState] = {root_id: root}
        self._relations: list[Relation] = []
        self._head = root_id
        self._unresolved: tuple[str, ...] = tuple(unresolved)
        self._residue: tuple[str, ...] = ()
        self._receipts: list[Receipt] = []

    @property
    def head(self) -> WitnessedState:
        return self._states[self._head]

    @property
    def receipts(self) -> tuple[Receipt, ...]:
        return tuple(self._receipts)

    @property
    def relations(self) -> tuple[Relation, ...]:
        return tuple(self._relations)

    def witnessed_state(self, state_id: str) -> WitnessedState:
        return self._states[state_id]

    def history(self) -> tuple[WitnessedState, ...]:
        """Return ancestry from root to current head."""
        chain: list[WitnessedState] = []
        cursor: WitnessedState | None = self.head
        while cursor is not None:
            chain.append(cursor)
            cursor = self._states.get(cursor.parent_state_id) if cursor.parent_state_id else None
        return tuple(reversed(chain))

    def _continuations_for(self, state_id: str) -> tuple[str, ...]:
        if state_id not in self._states:
            raise InvalidCrossing(f"unknown state: {state_id}")
        return self.ALLOWED_OPERATIONS + ("inspect-lineage", "return-to-chat")

    def return_address(self) -> ReturnAddress:
        return ReturnAddress(
            kernel_id=self.KERNEL_ID,
            state_id=self._head,
            unresolved=self._unresolved,
            residue=self._residue,
            continuations=self._continuations_for(self._head),
        )

    def preview(
        self,
        operation: str,
        candidate_content: str,
        *,
        rationale: str,
    ) -> Preview:
        if operation not in self.ALLOWED_OPERATIONS:
            raise InvalidCrossing(f"unsupported operation: {operation}")
        if not candidate_content.strip():
            raise InvalidCrossing("candidate content must not be empty")
        relation_kind = self.ALLOWED_RELATIONS[operation]
        payload = {
            "kernel_id": self.KERNEL_ID,
            "base_state_id": self._head,
            "operation": operation,
            "candidate_content": candidate_content,
            "relation_kind": relation_kind,
            "rationale": rationale,
            "required_authority": self.AUTHORITY,
        }
        return Preview(
            preview_id="p_" + _digest(payload),
            kernel_id=self.KERNEL_ID,
            base_state_id=self._head,
            operation=operation,
            candidate_content=candidate_content,
            relation_kind=relation_kind,
            rationale=rationale,
            expected_delta={
                "creates_state": True,
                "rewrites_existing_state": False,
                "relation": relation_kind,
                "head_will_change": True,
            },
            required_authority=self.AUTHORITY,
        )

    def execute(
        self,
        preview: Preview,
        *,
        actor: str,
        executor: str,
        unresolved: Iterable[str] = (),
        residue: Iterable[str] = (),
    ) -> Receipt:
        if preview.kernel_id != self.KERNEL_ID:
            raise InvalidCrossing("preview belongs to another kernel")
        if executor != self.AUTHORITY:
            raise AuthorityError(
                f"{executor!r} cannot execute; required authority is {self.AUTHORITY!r}"
            )
        if preview.required_authority != self.AUTHORITY:
            raise AuthorityError("preview authority contract was altered")
        if preview.base_state_id != self._head:
            raise StalePreview(
                f"preview base {preview.base_state_id} is stale; current head is {self._head}"
            )

        expected_preview = self.preview(
            preview.operation, preview.candidate_content, rationale=preview.rationale
        )
        if expected_preview.preview_id != preview.preview_id:
            raise InvalidCrossing("preview identity does not match its inspected content")
        if expected_preview.relation_kind != preview.relation_kind:
            raise InvalidCrossing("preview relation was altered")

        before = self.head
        state_payload = {
            "kernel": self.KERNEL_ID,
            "parent": before.state_id,
            "content": preview.candidate_content,
            "relation": preview.relation_kind,
            "rationale": preview.rationale,
        }
        after_id = "s_" + _digest(state_payload)
        after = WitnessedState(
            state_id=after_id,
            content=preview.candidate_content,
            parent_state_id=before.state_id,
            relation_kind=preview.relation_kind,
            rationale=preview.rationale,
        )
        relation = Relation(
            source_state_id=before.state_id,
            target_state_id=after_id,
            kind=preview.relation_kind,
            rationale=preview.rationale,
        )
        self._states[after_id] = after
        self._relations.append(relation)
        self._head = after_id
        self._unresolved = tuple(unresolved)
        self._residue = tuple(residue)
        return_address = self.return_address()

        receipt_payload = {
            "preview": preview.preview_id,
            "actor": actor,
            "executor": executor,
            "before": before.state_id,
            "after": after_id,
            "relation": relation.kind,
            "return": asdict(return_address),
        }
        receipt = Receipt(
            crossing_id="x_" + _digest(receipt_payload),
            preview_id=preview.preview_id,
            kernel_id=self.KERNEL_ID,
            actor=actor,
            executor=executor,
            before_state_id=before.state_id,
            after_state_id=after_id,
            relation_kind=relation.kind,
            observed_delta={
                "created_state": after_id,
                "preserved_state": before.state_id,
                "relation": relation.kind,
                "head_changed": before.state_id != after_id,
            },
            return_address=return_address,
        )
        self._receipts.append(receipt)
        return receipt

    def rewrite_historical_state(self, state_id: str, new_content: str) -> None:
        """There is deliberately no lawful mutation path for witnessed meaning."""
        if state_id not in self._states:
            raise InvalidCrossing(f"unknown state: {state_id}")
        raise HistoricalRewriteError(
            "witnessed meaning cannot be rewritten; preview a typed reinterpretation instead"
        )

    def _state_digest(self) -> str:
        payload = {
            "kernel": self.KERNEL_ID,
            "head": asdict(self.head),
            "relations": [asdict(r) for r in self._relations],
            "return": asdict(self.return_address()),
        }
        return _digest(payload, 32)

    def project(self, kind: str) -> Projection:
        kind = kind.lower()
        head = self.head
        ret = self.return_address()
        lineage = tuple(s.state_id for s in self.history())
        common = dict(
            projection_kind=kind,
            kernel_id=self.KERNEL_ID,
            state_id=head.state_id,
            state_digest=self._state_digest(),
            authority_owner=self.AUTHORITY,
            affordances=self.ALLOWED_OPERATIONS,
            lineage_head=lineage,
            return_address=ret,
        )

        if kind == "chat":
            presentation = {
                "utterance": head.content,
                "choices": {
                    "before": "Explore what came before",
                    "after": "Continue from here",
                    "instead": "Open a sibling path",
                    "reinterpret": "Reframe without erasing this state",
                },
            }
        elif kind == "html":
            presentation = {
                "heading": "Story Door",
                "current": head.content,
                "buttons": ["BEFORE", "AFTER", "INSTEAD", "REINTERPRET"],
            }
        elif kind == "cli":
            presentation = {
                "prompt": f"story-door[{head.state_id}]>",
                "commands": [
                    "before <text>",
                    "after <text>",
                    "instead <text>",
                    "reinterpret <text>",
                ],
            }
        elif kind == "world":
            presentation = {
                "scene": "threshold",
                "inscription": head.content,
                "paths": {
                    "behind": "before",
                    "ahead": "after",
                    "side-trail": "instead",
                    "mirror": "reinterpret",
                },
            }
        else:
            raise InvalidCrossing(f"unknown projection kind: {kind}")

        return Projection(presentation=presentation, **common)


def prove_projection_equivalence(projections: Iterable[Projection]) -> bool:
    projections = tuple(projections)
    if not projections:
        return False
    first = projections[0]
    envelope = (
        first.kernel_id,
        first.state_id,
        first.state_digest,
        first.authority_owner,
        first.affordances,
        first.lineage_head,
        first.return_address,
    )
    return all(
        (
            p.kernel_id,
            p.state_id,
            p.state_digest,
            p.authority_owner,
            p.affordances,
            p.lineage_head,
            p.return_address,
        )
        == envelope
        for p in projections[1:]
    )
