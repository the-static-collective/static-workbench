from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OperationDescriptor:
    operation_id: str
    input_schema_ref: str
    output_schema_ref: str
    declared_effects: tuple[str, ...]
    authorization_requirements: tuple[str, ...]
    supports_cancel: bool
    supports_reconcile: bool
    retry_policy: str

    def __post_init__(self) -> None:
        for field_name in ("operation_id", "input_schema_ref", "output_schema_ref", "retry_policy"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True)
class AdapterDescriptor:
    adapter_id: str
    adapter_version: str
    owner_repository: str
    pinned_commit: str
    dirty_worktree_status: str
    operations: tuple[OperationDescriptor, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "adapter_id",
            "adapter_version",
            "owner_repository",
            "pinned_commit",
            "dirty_worktree_status",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must not be empty")
        ids = [operation.operation_id for operation in self.operations]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate operation_id in adapter descriptor")
