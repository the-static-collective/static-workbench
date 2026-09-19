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

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title must not be blank")
        return value


class CreatorPackSaveRequest(CreatorPackRequest):
    expected_pack_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
