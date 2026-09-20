from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class RootInfo(BaseModel):
    id: str
    path: str


class BootstrapResponse(BaseModel):
    version: str
    roots: list[RootInfo]
    session_token: str


class ObjectResponse(BaseModel):
    root_id: str
    path: str
    kind: str
    size: int | None
    mtime_ns: int
    preview: str | None = None
    preview_truncated: bool = False
    entries: list[str] | None = None


class ApertureAnalyzeRequest(BaseModel):
    raw_text: str = Field(min_length=1, max_length=20_000)
    context_text: str | None = Field(default=None, max_length=20_000)
    parent_id: int | None = Field(default=None, ge=1)

    @field_validator("raw_text")
    @classmethod
    def raw_text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("raw_text must not be blank")
        return value


class ApertureRecordResponse(BaseModel):
    id: int
    created_at: str
    raw_text: str
    parent_id: int | None
    analysis: dict[str, Any]


class ApertureHistoryResponse(BaseModel):
    sense_fields: list[ApertureRecordResponse]


class CreatorSelection(BaseModel):
    root_id: str = Field(min_length=1, max_length=64)
    repo_path: str = Field(min_length=1, max_length=256)
    source_path: str = Field(min_length=1, max_length=512)
    line: int = Field(ge=1, le=200000)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    snippet: str = Field(max_length=240)


class CreatorPackRequest(BaseModel):
    selections: list[CreatorSelection] = Field(min_length=1, max_length=8)


class CreatorDraftRequest(BaseModel):
    pack_id: int = Field(ge=1)
    expected_revision: int = Field(ge=0)
    title: str = Field(min_length=1, max_length=160)
    kind: str = Field(pattern=r"^(lyric|podcast|post|brief|other)$")
    body: str = Field(max_length=32768)
    assumptions: str = Field(default="", max_length=4000)
    gaps: str = Field(default="", max_length=4000)
    maxhinal_ride_id: int | None = Field(default=None, ge=1)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class CreatorPackSaveRequest(CreatorPackRequest):
    expected_pack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class MaxhinalRideRequest(BaseModel):
    pack_id: int = Field(ge=1)
    raw_json: str = Field(min_length=1, max_length=131072)


class MaxhinalRideSaveRequest(MaxhinalRideRequest):
    expected_ride_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class NativeFuelItem(BaseModel):
    kind: str = Field(pattern=r"^(file|source_pack)$")
    root_id: str | None = Field(default=None, max_length=64)
    path: str | None = Field(default=None, max_length=512)
    pack_id: int | None = Field(default=None, ge=1)

    @field_validator("path")
    @classmethod
    def reject_absolute_input(cls, value: str | None) -> str | None:
        if value is not None and ("\\x00" in value or value.startswith(("/", "\\\\"))):
            raise ValueError("only root-relative paths may be selected")
        return value


class NativeFuelRequest(BaseModel):
    fuels: list[NativeFuelItem] = Field(min_length=1, max_length=4)


class NativeSpinRequest(NativeFuelRequest):
    expected_fuel_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mode: str = Field(pattern=r"^(discontinuity|braid|compose|pressure|shuffle)$")
    seed: str = Field(default="0", max_length=100)
    question: str = Field(default="", max_length=400)


class DogramImpactRequest(BaseModel):
    root_id: str = Field(min_length=1, max_length=64)
    repo_path: str = Field(min_length=1, max_length=256)


class DogramImpactRunRequest(DogramImpactRequest):
    expected_input_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_candidate_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    expected_dogram_commit: str = Field(pattern=r"^[0-9a-f]{40}$")


class GraftRoundPreviewRequest(BaseModel):
    ride_id: int = Field(ge=1)
    ride_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    keep: str = Field(min_length=1, max_length=400)
    bend: str = Field(min_length=1, max_length=400)
    intruder: str = Field(min_length=1, max_length=400)
    move: str = Field(pattern=r"^(fuse|invert|continue|wildcard)$")
    relation_lane: str = Field(
        pattern=r"^(semantic|lineage|active_tension|human_link|rejected_parallel)$"
    )
    question: str = Field(default="", max_length=400)


class GraftRoundSaveRequest(GraftRoundPreviewRequest):
    expected_round_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class GraftWitnessPreviewRequest(BaseModel):
    ride_id: int = Field(ge=1)
    ride_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    candidate_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    graph: dict[str, Any]
    operator: str = Field(pattern=r"^(reach|ablate)$")
    change: dict[str, Any]
    queries: list[list[str]] = Field(default_factory=list, max_length=8)


class GraftWitnessRunRequest(GraftWitnessPreviewRequest):
    expected_specimen_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_dogram_commit: str = Field(pattern=r"^[0-9a-f]{40}$")


class CompositionInspectRequest(BaseModel):
    raw_json: str = Field(min_length=1, max_length=65536)


class GraftExperimentPlan(BaseModel):
    input: str = Field(min_length=1, max_length=1200)
    procedure: str = Field(min_length=1, max_length=1200)
    observable: str = Field(min_length=1, max_length=1200)
    stop_condition: str = Field(min_length=1, max_length=1200)


class GraftDraftSaveRequest(BaseModel):
    candidate_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expected_revision: int = Field(ge=0)
    expected_draft_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=8192)
    experiment: GraftExperimentPlan
    assumptions: str = Field(min_length=1, max_length=2000)
    unresolved: str = Field(min_length=1, max_length=2000)
