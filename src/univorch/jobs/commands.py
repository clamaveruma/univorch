"""Command pattern for orchestrator operations (DEC-028).

Each command encapsulates one operation on one target with two methods:
``validate()`` collects all precondition errors (empty list = OK) and doubles as
the plan/dry-run check; ``execute()`` performs the work and returns a result
message. ``execute()`` re-runs ``validate()`` first and raises if it fails, so it
is safe to call on its own; the Jobs engine wraps it to record the Job.

Concepts: an ``OperationType`` is the *kind* of operation (an op-code). A
``Command`` and a ``Job`` are two views of the same operation instance — the
Command is its executable form (logic + dependencies, in memory), the Job its
persistent record (status, result, on disk). They share ``operation_type`` and
``target``; one Command execution produces one Job.
"""

from abc import ABC, abstractmethod
from typing import ClassVar, override

from univorch.connectors.base import HypervisorConnector
from univorch.connectors.types import RuntimeState
from univorch.models import Descriptor, DescriptorState, Folder, OperationType
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
)
from univorch.resolver import resolve_descriptor


class Command(ABC):
    """One operation on one target (DEC-028)."""

    operation_type: ClassVar[OperationType]  # set by each concrete command
    target: str  # the path it acts on, set in __init__

    @abstractmethod
    def validate(self) -> list[str]:
        """Return all precondition errors; an empty list means it can run."""

    @abstractmethod
    def execute(self) -> str:
        """Perform the operation and return a result message."""


class DeployCommand(Command):
    """Deploy a descriptor: clone its base VM and mark it deployed."""

    operation_type = OperationType.DEPLOY

    def __init__(
        self,
        path: str,
        descriptors_repo: DescriptorRepository,
        folders_repo: FolderRepository,
        hypervisor_connector: HypervisorConnector,
    ) -> None:
        self.target = path
        self._descriptors = descriptors_repo
        self._folders = folders_repo  # used by DeployCommand to resolve base_vm
        self._connector = hypervisor_connector

    @override
    def validate(self) -> list[str]:
        descriptor = self._descriptors.get(self.target)
        if descriptor is None:
            return [f"VM not found: {self.target}"]
        if descriptor.state == DescriptorState.BROKEN:
            return [f"cannot deploy a broken VM: {self.target}"]
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
        # Pieza 1.C: resolve template references to get the effective base_vm.
        # CreateDescriptorCommand.validate already guarantees this resolves at
        # load time; the defensive check below catches drift (e.g. a template
        # was changed after load) so the failure is clear and never silent.
        resolved, _ = resolve_descriptor(descriptor, self._folders)
        if resolved.base_vm is None:
            raise ValueError(f"VM has no effective base_vm: {self.target}")
        # name = full path; real connectors will sanitise it to their own rules
        vm_id = self._connector.clone(resolved.base_vm, descriptor.path)
        descriptor.state = DescriptorState.DEPLOYED
        descriptor.vm_id = vm_id
        # save only the runtime mutations; the local definition stays as the
        # user wrote it (the resolver re-runs on every access, so the resolved
        # values are never frozen into the persisted record)
        self._descriptors.save(descriptor)
        return f"deployed as {vm_id}"


class UndeployCommand(Command):
    """Undeploy: delete the VM and return the descriptor to provisioned."""

    operation_type = OperationType.UNDEPLOY

    def __init__(
        self,
        path: str,
        descriptors_repo: DescriptorRepository,
        folders_repo: FolderRepository,
        hypervisor_connector: HypervisorConnector,
    ) -> None:
        self.target = path
        self._descriptors = descriptors_repo
        self._folders = folders_repo  # used by DeployCommand to resolve base_vm
        self._connector = hypervisor_connector

    @override
    def validate(self) -> list[str]:
        descriptor = self._descriptors.get(self.target)
        if descriptor is None:
            return [f"VM not found: {self.target}"]
        if descriptor.state == DescriptorState.BROKEN:
            return [f"cannot undeploy a broken VM: {self.target}"]
        return []

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        descriptor = self._descriptors.get(self.target)
        assert descriptor is not None  # validate() guaranteed it exists
        if descriptor.state == DescriptorState.PROVISIONED:
            return "already undeployed (no change)"  # idempotent no-op (DEC-035)
        assert descriptor.vm_id is not None  # deployed → vm_id is set
        self._connector.delete(descriptor.vm_id)
        descriptor.state = DescriptorState.PROVISIONED
        descriptor.vm_id = None
        self._descriptors.save(descriptor)
        return "undeployed"


class StartCommand(Command):
    """Power on the VM (runtime state only; descriptor state unchanged)."""

    operation_type = OperationType.START

    def __init__(
        self,
        path: str,
        descriptors_repo: DescriptorRepository,
        folders_repo: FolderRepository,
        hypervisor_connector: HypervisorConnector,
    ) -> None:
        self.target = path
        self._descriptors = descriptors_repo
        self._folders = folders_repo  # used by DeployCommand to resolve base_vm
        self._connector = hypervisor_connector

    @override
    def validate(self) -> list[str]:
        descriptor = self._descriptors.get(self.target)
        if descriptor is None:
            return [f"VM not found: {self.target}"]
        if descriptor.state != DescriptorState.DEPLOYED:
            return [f"cannot start a VM that is not deployed: {self.target}"]
        return []

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        descriptor = self._descriptors.get(self.target)
        assert descriptor is not None and descriptor.vm_id is not None
        if self._connector.get_status(descriptor.vm_id) == RuntimeState.RUNNING:
            return "already running (no change)"  # idempotent no-op (DEC-035)
        self._connector.start(descriptor.vm_id)
        return "started"


class StopCommand(Command):
    """Power off the VM (runtime state only; descriptor state unchanged)."""

    operation_type = OperationType.STOP

    def __init__(
        self,
        path: str,
        descriptors_repo: DescriptorRepository,
        folders_repo: FolderRepository,
        hypervisor_connector: HypervisorConnector,
    ) -> None:
        self.target = path
        self._descriptors = descriptors_repo
        self._folders = folders_repo  # used by DeployCommand to resolve base_vm
        self._connector = hypervisor_connector

    @override
    def validate(self) -> list[str]:
        descriptor = self._descriptors.get(self.target)
        if descriptor is None:
            return [f"VM not found: {self.target}"]
        if descriptor.state != DescriptorState.DEPLOYED:
            return [f"cannot stop a VM that is not deployed: {self.target}"]
        return []

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        descriptor = self._descriptors.get(self.target)
        assert descriptor is not None and descriptor.vm_id is not None
        if self._connector.get_status(descriptor.vm_id) == RuntimeState.STOPPED:
            return "already stopped (no change)"  # idempotent no-op (DEC-035)
        self._connector.stop(descriptor.vm_id)
        return "stopped"


class CreateFolderCommand(Command):
    """Create or update a folder (definition operation; no hypervisor)."""

    operation_type = OperationType.CREATE_FOLDER

    def __init__(self, folder: Folder, folders_repo: FolderRepository) -> None:
        self.target = folder.path
        self._folder = folder
        self._folders = folders_repo

    @override
    def validate(self) -> list[str]:
        parent = self.target.rsplit("/", 1)[0]
        if parent and not self._folders.exists(parent):
            return [f"parent folder does not exist: {parent}"]
        return []

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        existing = self._folders.get(self.target)
        if existing == self._folder:
            return f"folder {self.target} unchanged (no change)"
        self._folders.save(self._folder)
        verb = "updated" if existing else "created"
        return f"folder {self.target} {verb}"


class CreateDescriptorCommand(Command):
    """Create or update a descriptor's definition (definition operation).

    A descriptor mixes definition (hypervisor, base_vm, specs) with runtime state
    (state, vm_id). Re-applying only touches the definition: an existing
    descriptor that is not provisioned can only be redefined if the definition is
    unchanged (otherwise it must be undeployed first), so its runtime state is
    never clobbered.
    """

    operation_type = OperationType.CREATE_DESCRIPTOR

    def __init__(
        self,
        descriptor: Descriptor,
        descriptors_repo: DescriptorRepository,
        folders_repo: FolderRepository,
    ) -> None:
        self.target = descriptor.path
        self._descriptor = descriptor
        self._descriptors = descriptors_repo
        self._folders = folders_repo

    @override
    def validate(self) -> list[str]:
        errors: list[str] = []
        parent = self.target.rsplit("/", 1)[0]
        # an empty parent means the target sits at the root, which is implicit
        if parent and not self._folders.exists(parent):
            errors.append(f"parent folder does not exist: {parent}")
        existing = self._descriptors.get(self.target)
        if (
            existing is not None
            and existing.state != DescriptorState.PROVISIONED
            and self._differs(existing)
        ):
            errors.append(f"cannot redefine a non-provisioned VM: {self.target}")
        # Pieza 1.C: fail-fast at load time if the descriptor's references don't
        # resolve. Skipped when the structure is already broken — there's no
        # point resolving against a parent we know doesn't exist.
        if not errors:
            try:
                resolved, _ = resolve_descriptor(self._descriptor, self._folders)
            except ValueError as resolver_error:
                errors.append(str(resolver_error))
            else:
                if resolved.hypervisor is None:
                    errors.append(f"VM has no effective hypervisor: {self.target}")
                if resolved.base_vm is None:
                    errors.append(f"VM has no effective base_vm: {self.target}")
        return errors

    @override
    def execute(self) -> str:
        errors = self.validate()
        if errors:
            raise ValueError("; ".join(errors))
        existing = self._descriptors.get(self.target)
        if existing is not None and not self._differs(existing):
            return f"descriptor {self.target} unchanged (no change)"
        self._descriptors.save(self._descriptor)
        verb = "updated" if existing else "created"
        return f"descriptor {self.target} {verb}"

    def _differs(self, existing: Descriptor) -> bool:
        """True if the definition (ignoring runtime state) differs from existing."""
        runtime = {"state", "vm_id"}
        return existing.model_dump(exclude=runtime) != self._descriptor.model_dump(
            exclude=runtime
        )
