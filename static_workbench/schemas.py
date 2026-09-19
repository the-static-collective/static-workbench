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
