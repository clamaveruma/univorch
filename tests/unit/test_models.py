"""Tests for the domain models: Folder, Descriptor and path validation."""

import pytest
from pydantic import ValidationError

from univorch.models import (
    Descriptor,
    DescriptorState,
    Folder,
    Job,
    JobStatus,
    OperationType,
)


class TestFolder:
    def test_minimal(self) -> None:
        folder = Folder(path="/lab")
        assert folder.path == "/lab"
        assert folder.description is None


class TestDescriptor:
    def test_defaults(self) -> None:
        d = Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        assert d.state == DescriptorState.PROVISIONED
        assert d.vm_id is None
        assert d.cpu is None

    def test_round_trips_through_model_dump(self) -> None:
        d = Descriptor(
            path="/lab/vm",
            hypervisor="mock",
            base_vm="linux-base",
            cpu=2,
            memory_mb=2048,
            disk_gb=20,
        )
        assert Descriptor.model_validate(d.model_dump()) == d

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            Descriptor.model_validate({"path": "/lab/vm", "hypervisor": "mock"})


class TestPathValidation:
    @pytest.mark.parametrize(
        "path", ["/", "/lab", "/lab/networks", "/lab/networks/student01"]
    )
    def test_valid_paths(self, path: str) -> None:
        assert Folder(path=path).path == path

    @pytest.mark.parametrize(
        "path", ["", "lab", "/lab/", "/lab//networks", "/lab/with space"]
    )
    def test_invalid_paths_raise(self, path: str) -> None:
        with pytest.raises(ValidationError):
            Folder(path=path)


class TestJob:
    def test_defaults(self) -> None:
        job = Job(operation_type=OperationType.DEPLOY, target="/lab/vm")
        assert job.status == JobStatus.PENDING
        assert job.finished_at is None
        assert job.message is None
        assert job.id  # auto-generated, non-empty
        assert job.created_at is not None

    def test_ids_are_unique(self) -> None:
        a = Job(operation_type=OperationType.START, target="/lab/vm")
        b = Job(operation_type=OperationType.START, target="/lab/vm")
        assert a.id != b.id

    def test_round_trips_through_model_dump(self) -> None:
        job = Job(operation_type=OperationType.DEPLOY, target="/lab/vm")
        assert Job.model_validate(job.model_dump(mode="json")) == job
