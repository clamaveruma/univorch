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
        assert folder.metadata == {}

    def test_metadata_is_stored_opaque(self) -> None:
        # DEC-038: the core keeps layer-2 metadata and never interprets it.
        folder = Folder(
            path="/lab/redes", metadata={"kind": "subject", "desktop": ["a"]}
        )
        assert folder.metadata["kind"] == "subject"
        assert folder.metadata["desktop"] == ["a"]
        assert Folder.model_validate(folder.model_dump()) == folder


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

    def test_unknown_field_rejected(self) -> None:
        # hypervisor and base_vm are optional now (can be inherited from a
        # template, Pieza 1.A onwards); what we still reject is typos
        with pytest.raises(ValidationError):
            Descriptor.model_validate(
                {"path": "/lab/vm", "hypevisor": "mock"}  # typo
            )


class TestPathValidation:
    @pytest.mark.parametrize(
        "path",
        [
            "/",
            "/lab",
            "/lab/networks",
            "/lab/networks/student01",
            "/redes-2026/juan@uma.es",  # email-as-username segment
            "/lab/v1.2",  # dot allowed mid-segment
        ],
    )
    def test_valid_paths(self, path: str) -> None:
        assert Folder(path=path).path == path

    @pytest.mark.parametrize(
        "path",
        [
            "",
            "lab",
            "/lab/",
            "/lab//networks",
            "/lab/with space",
            "/lab/.",  # segment must not start with a dot
            "/lab/..",
            "/lab/.hidden",
            "/lab/-dash",  # must start with a letter or digit
            "/lab/_under",
        ],
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
