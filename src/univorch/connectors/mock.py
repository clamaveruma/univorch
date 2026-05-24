"""In-memory mock connector for development and tests.

Implements the ``HypervisorConnector`` contract without a real hypervisor, so the
whole orchestrator can be exercised with TDD. State lives in memory: a set of
base templates (sources for ``clone``) and a dict of deployed VMs.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self, override

from univorch.connectors.base import HypervisorConnector
from univorch.connectors.types import CloneMode, RuntimeState, VMInfo


@dataclass
class _MockVM:
    """A VM that exists in the mock hypervisor (a clone produced by ``clone``)."""

    id: str
    name: str
    runtime_state: RuntimeState
    metadata: dict[str, str] = field(default_factory=dict)


class MockConnector(HypervisorConnector):
    """Hypervisor connector that simulates VMs in memory."""

    def __init__(self, templates: Iterable[str] = ()) -> None:
        self._templates: set[str] = set(templates)
        self._deployed: dict[str, _MockVM] = {}
        self._counter = 0

    @classmethod
    def empty(cls) -> Self:
        return cls()

    @classmethod
    def with_demo_templates(cls) -> Self:
        return cls(["linux-base", "windows-base"])

    @classmethod
    def with_templates(cls, templates: Iterable[str]) -> Self:
        return cls(templates)

    @override
    def clone(
        self, source_id: str, name: str, mode: CloneMode = CloneMode.LINKED
    ) -> str:
        if mode is not CloneMode.LINKED:
            raise NotImplementedError("only linked clone is supported in v1")
        if source_id not in self._templates:
            raise ValueError(f"unknown template: {source_id}")
        self._counter += 1
        vm_id = f"mock-vm-{self._counter}"
        self._deployed[vm_id] = _MockVM(
            id=vm_id, name=name, runtime_state=RuntimeState.STOPPED
        )
        return vm_id

    @override
    def get_status(self, vm_id: str) -> RuntimeState:
        return self._get(vm_id).runtime_state

    def _get(self, vm_id: str) -> _MockVM:
        """Return the deployed VM, or raise ValueError if the id is unknown."""
        try:
            return self._deployed[vm_id]
        except KeyError:
            raise ValueError(f"unknown vm: {vm_id}") from None

    @override
    def start(self, vm_id: str) -> None:
        self._get(vm_id).runtime_state = RuntimeState.RUNNING

    @override
    def stop(self, vm_id: str) -> None:
        self._get(vm_id).runtime_state = RuntimeState.STOPPED

    @override
    def force_stop(self, vm_id: str) -> None:
        self._get(vm_id).runtime_state = RuntimeState.STOPPED

    @override
    def pause(self, vm_id: str) -> None:
        vm = self._get(vm_id)
        if vm.runtime_state is RuntimeState.STOPPED:
            raise ValueError(f"cannot pause a stopped vm: {vm_id}")
        vm.runtime_state = RuntimeState.PAUSED

    @override
    def resume(self, vm_id: str) -> None:
        vm = self._get(vm_id)
        if vm.runtime_state is RuntimeState.STOPPED:
            raise ValueError(f"cannot resume a stopped vm: {vm_id}")
        vm.runtime_state = RuntimeState.RUNNING

    @override
    def delete(self, vm_id: str) -> None:
        try:
            del self._deployed[vm_id]
        except KeyError:
            raise ValueError(f"unknown vm: {vm_id}") from None

    @override
    def get_info(self, vm_id: str) -> VMInfo:
        return self._to_info(self._get(vm_id))

    def deployed_vms(self) -> list[VMInfo]:
        """Snapshot of every deployed VM. Test-only; not part of the ABC."""
        return [self._to_info(vm) for vm in self._deployed.values()]

    @staticmethod
    def _to_info(vm: _MockVM) -> VMInfo:
        return VMInfo(id=vm.id, name=vm.name, runtime_state=vm.runtime_state)
