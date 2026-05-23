"""Tests for the connector boundary value types."""

import pytest
from pydantic import ValidationError

from univorch.connectors.types import RuntimeState, VMInfo


class TestRuntimeState:
    def test_has_the_four_expected_states(self) -> None:
        assert {state.value for state in RuntimeState} == {
            "running",
            "stopped",
            "paused",
            "unknown",
        }

    def test_member_is_its_string_value(self) -> None:
        assert RuntimeState.RUNNING == "running"


class TestVMInfo:
    def test_minimal_construction_leaves_optionals_none(self) -> None:
        info = VMInfo(id="vm-1", name="student01", runtime_state=RuntimeState.STOPPED)
        assert info.cpu is None
        assert info.memory_mb is None
        assert info.disk_gb is None

    def test_round_trips_through_model_dump(self) -> None:
        info = VMInfo(
            id="vm-1",
            name="student01",
            runtime_state=RuntimeState.RUNNING,
            cpu=2,
            memory_mb=2048,
            disk_gb=20,
        )
        assert VMInfo.model_validate(info.model_dump()) == info

    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            VMInfo.model_validate({"id": "vm-1", "name": "student01"})
