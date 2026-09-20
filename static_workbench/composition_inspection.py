"""Descriptor-only Founder Node -> HOUSE local checkout inspection.

This is an untrusted, human-pasted hint. Registry witness fields and claimed
project identities are not authenticated; no imported field grants execution.
"""
from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .repos import RepoStatus


SCHEMA = "static-collective.founder-node.workbench-inspection.v0.1"
ORG_REPOSITORY = re.compile(r"^the-static-collective/[A-Za-z0-9][A-Za-z0-9._-]{0,99}$", re.I)
PROJECT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class CompositionInspectionError(ValueError):
    pass


class RegistryWitnessEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    version: int = Field(ge=1)
    updated: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=512)


class RegistryWitness(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    projects: RegistryWitnessEntry
    invariants: RegistryWitnessEntry


class ProposedParticipant(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    projectId: str = Field(min_length=1, max_length=80)
    repository: str = Field(min_length=1, max_length=128)
    status: Literal["active", "seed"]
    role: str = Field(max_length=2000)
    owns: list[str] = Field(max_length=20)
    nonAuthority: list[str] = Field(max_length=20)
    evidence: list[dict[str, Any]] = Field(max_length=12)

    @field_validator("projectId")
    @classmethod
    def valid_project_id(cls, value: str) -> str:
        if not PROJECT_ID.fullmatch(value):
            raise ValueError("invalid participant project id")
        return value

    @field_validator("repository")
    @classmethod
    def valid_repository(cls, value: str) -> str:
        if not ORG_REPOSITORY.fullmatch(value) or value.endswith((".", "..")):
            raise ValueError("repository must be an ordinary the-static-collective GitHub slug")
        return value


class FounderInspectionDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema: Literal["static-collective.founder-node.workbench-inspection.v0.1"]
    mode: Literal["descriptor-only"]
    origin: Literal["founder-node"]
    proposedParticipants: list[ProposedParticipant] = Field(min_length=2, max_length=4)
    sourceRegistry: RegistryWitness
    localReadiness: Literal["unknown"]
    compatibility: Literal["unverified"]
    executionAuthorized: Literal[False]
    destinationAcceptance: Literal["not-requested"]
    requestedNextStep: str = Field(max_length=512)
    nonClaims: list[str] = Field(min_length=1, max_length=20)

    @field_validator("proposedParticipants")
    @classmethod
    def unique_participants(cls, participants: list[ProposedParticipant]) -> list[ProposedParticipant]:
        ids = [p.projectId.casefold() for p in participants]
        repos = [p.repository.casefold() for p in participants]
        if len(set(ids)) != len(ids) or len(set(repos)) != len(repos):
            raise ValueError("duplicate project ids or declared repositories")
        return participants


def inspect_composition(raw_json: str, repos: list[RepoStatus]) -> dict[str, Any]:
    if len(raw_json.encode("utf-8")) > 65536:
        raise CompositionInspectionError("descriptor exceeds 64 KiB")
    try:
        descriptor = FounderInspectionDescriptor.model_validate_json(raw_json)
    except ValidationError as exc:
        raise CompositionInspectionError("descriptor rejected: " + str(exc.errors()[0].get("msg", "invalid field"))) from exc

    participants: list[dict[str, Any]] = []
    for proposed in descriptor.proposedParticipants:
        # A repository name is only a local candidate identifier. It is NOT
        # an authenticated GitHub remote or a proof of the declared project ID.
        declared_slug = proposed.repository.rsplit("/", 1)[1].casefold()
        matches = [r for r in repos if r.name.casefold() == declared_slug]
        entry: dict[str, Any] = {
            "project_id_claimed": proposed.projectId,
            "repository_claimed": proposed.repository,
            "registry_status_claimed": proposed.status,
            "local_state": "missing" if not matches else "ambiguous" if len(matches) > 1 else "present",
            "project_identity_verified": False,
            "runtime_readiness": "unknown",
            "compatibility": "unverified",
            "admission": "not-requested",
            "execution_authorized": False,
            "checkouts": [],
        }
        if len(matches) == 1:
            repo = matches[0]
            entry["checkouts"] = [{
                "root_id": repo.root_id,
                "relative_path": repo.relative_path,
                "branch": repo.branch,
                "head": repo.head,
                "dirty": repo.dirty,
                "detached": repo.detached,
                "ahead": repo.ahead,
                "behind": repo.behind,
            }]
        participants.append(entry)

    return {
        "schema": "static-collective.house.composition-inspection.v0.1",
        "state": "inspection-only",
        "origin_claimed": descriptor.origin,
        "source_registry_claimed": descriptor.sourceRegistry.model_dump(),
        "source_authenticated": False,
        "participants": participants,
        "execution_authorized": False,
        "next_step": "Human review of each project-native identity, adapter contract and separate admission is required.",
        "non_claims": [
            "Pasted JSON and its registry witness are untrusted, not verified Founder Node output.",
            "Matching a local checkout basename does not authenticate its remote, contents, project ID, or runtime service.",
            "A local checkout is not proof of readiness, compatibility, admission or execution authority.",
            "No project process, installer, Git hook, adapter, or action was invoked.",
            "No imported descriptor or inspection result is persisted as project history.",
        ],
    }
