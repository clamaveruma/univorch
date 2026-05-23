"""Tests for the HypervisorConnector ABC contract."""

import pytest

from univorch.connectors.base import HypervisorConnector
from univorch.connectors.types import CloneMode, RuntimeState, VMInfo


class CompleteConnector(HypervisorConnector):
    """Minimal connector implementing every abstract method."""

    def clone(
        self, source_id: str, name: str, mode: CloneMode = CloneMode.LINKED
    ) -> str:
        return "vm-1"

    def delete(self, vm_id: str) -> None: ...
    def start(self, vm_id: str) -> None: ...
    def stop(self, vm_id: str) -> None: ...
    def force_stop(self, vm_id: str) -> None: ...
    def pause(self, vm_id: str) -> None: ...
    def resume(self, vm_id: str) -> None: ...

    def get_status(self, vm_id: str) -> RuntimeState:
        return RuntimeState.STOPPED

    def get_info(self, vm_id: str) -> VMInfo:
        return VMInfo(id=vm_id, name="vm", runtime_state=RuntimeState.STOPPED)


def test_complete_subclass_can_be_instantiated() -> None:
    assert isinstance(CompleteConnector(), HypervisorConnector)


def test_abc_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        HypervisorConnector()


def test_incomplete_subclass_cannot_be_instantiated() -> None:
    class IncompleteConnector(HypervisorConnector):
        def clone(
            self, source_id: str, name: str, mode: CloneMode = CloneMode.LINKED
        ) -> str:
            return "vm-1"

        # the other eight abstract methods are intentionally left unimplemented

    with pytest.raises(TypeError):
        IncompleteConnector()
