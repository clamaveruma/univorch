"""Command pattern for orchestrator operations (DEC-028).

Each command encapsulates one operation on one target with two methods:
``validate()`` collects all precondition errors (empty list = OK) and doubles as
the plan/dry-run check; ``execute()`` performs the work and returns a result
message. ``execute()`` re-runs ``validate()`` first and raises if it fails, so it
is safe to call on its own; the Jobs engine wraps it to record the Job.
"""

from abc import ABC, abstractmethod
from typing import ClassVar, override

from univorch.connectors.base import HypervisorConnector
from univorch.models import DescriptorState, Operation
from univorch.persistence.tinydb.repositories import DescriptorRepository


class Command(ABC):
    """One operation on one target (DEC-028)."""

    operation: ClassVar[Operation]  # the kind of operation, set by each command
    target: str  # the path it acts on, set in __init__

    @abstractmethod
    def validate(self) -> list[str]:
        """Return all precondition errors; an empty list means it can run."""

    @abstractmethod
    def execute(self) -> str:
        """Perform the operation and return a result message."""


class DeployCommand(Command):
    """Deploy a descriptor: clone its base VM and mark it deployed."""

    operation = Operation.DEPLOY

    def __init__(
        self,
        path: str,
        descriptors: DescriptorRepository,
        connector: HypervisorConnector,
    ) -> None:
        self.target = path
        self._descriptors = descriptors
        self._connector = connector

    @override
    def validate(self) -> list[str]:
        descriptor = self._descriptors.get(self.target)
        if descriptor is None:
            return [f"descriptor not found: {self.target}"]
        if descriptor.state == DescriptorState.BROKEN:
            return [f"cannot deploy a broken descriptor: {self.target}"]
        return []

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        descriptor = self._descriptors.get(self.target)
        assert descriptor is not None  # validate() guaranteed it exists
        if descriptor.state == DescriptorState.DEPLOYED:
            return "already deployed (no change)"  # idempotent no-op (DEC-035)
        # name = full path; real connectors will sanitise it to their own rules
        vm_id = self._connector.clone(descriptor.base_vm, descriptor.path)
        descriptor.state = DescriptorState.DEPLOYED
        descriptor.vm_id = vm_id
        self._descriptors.save(descriptor)
        return f"deployed as {vm_id}"
