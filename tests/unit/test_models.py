"""Tests for the domain models: Folder, Descriptor and path validation."""

import pytest
from pydantic import ValidationError

from univorch.models import Descriptor, DescriptorState, Folder


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
