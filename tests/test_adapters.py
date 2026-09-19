import pytest

from static_workbench.adapters import AdapterDescriptor, OperationDescriptor


def operation(operation_id: str = "observe.render") -> OperationDescriptor:
    return OperationDescriptor(
        operation_id=operation_id,
        input_schema_ref="toaster.render/v1",
        output_schema_ref="dogram.observation/v1",
        declared_effects=("creates-native-result",),
        authorization_requirements=("explicit-dispatch",),
        supports_cancel=False,
        supports_reconcile=True,
        retry_policy="reconcile-before-retry",
    )


def test_adapter_descriptor_retains_version_and_operation_contract():
    descriptor = AdapterDescriptor(
        adapter_id="toaster-dogram",
        adapter_version="0.1.0",
        owner_repository="the-static-collective/Dogram",
        pinned_commit="0123456789abcdef",
        dirty_worktree_status="clean",
        operations=(operation(),),
    )

    assert descriptor.operations[0].operation_id == "observe.render"
    assert descriptor.operations[0].supports_reconcile is True


def test_adapter_descriptor_rejects_duplicate_operation_ids():
    with pytest.raises(ValueError, match="duplicate"):
        AdapterDescriptor(
            adapter_id="bad",
            adapter_version="0.1.0",
            owner_repository="owner/repo",
            pinned_commit="abcdef0",
            dirty_worktree_status="unknown",
            operations=(operation("same"), operation("same")),
        )


def test_adapter_descriptors_do_not_expose_execution_methods():
    descriptor = AdapterDescriptor(
        adapter_id="descriptor-only",
        adapter_version="0.1.0",
        owner_repository="owner/repo",
        pinned_commit="abcdef0",
        dirty_worktree_status="dirty",
        operations=(operation(),),
    )

    for method in ("prepare", "execute", "inspect", "cancel", "reconcile"):
        assert not hasattr(descriptor, method)
