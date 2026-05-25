"""Orchestrator service: the single entry point for all interfaces (DEC-031).

CLI, web GUI and the teaching layer all go through this facade; none talk to the
repositories, the connectors or the Jobs engine directly. The facade validates a
request and rejects the invalid ones (raising ``OperationError``, no Job created),
then builds the Command and hands it to the Jobs engine.
"""

from typing import Literal

from pydantic import BaseModel

from univorch.connectors.base import HypervisorConnector
from univorch.connectors.types import RuntimeState
from univorch.jobs.commands import (
    Command,
    CreateDescriptorCommand,
    CreateFolderCommand,
    DeployCommand,
    StartCommand,
    StopCommand,
    UndeployCommand,
)
from univorch.jobs.engine import JobEngine
from univorch.models import ApplyDocument, DescriptorState, Job, JobStatus
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)

# the four machine commands share the same constructor (path, repo, connector)
type MachineCommand = type[DeployCommand | UndeployCommand | StartCommand | StopCommand]


class OperationError(Exception):
    """A request rejected during validation; no Job is created.

    Carries all the validation messages so the interface can show them.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class DescriptorStatus(BaseModel):
    """Read result for one descriptor: orchestrator state + hypervisor runtime."""

    path: str
    state: DescriptorState
    runtime_state: RuntimeState | None = None  # None unless deployed
    vm_id: str | None = None


class TreeEntry(BaseModel):
    """One node in a tree listing (a folder or a descriptor)."""

    path: str
    kind: Literal["folder", "descriptor"]
    state: DescriptorState | None = None  # None for folders


class ApplyResult(BaseModel):
    """Per-item outcome of an ``apply`` (best-effort report)."""

    path: str
    ok: bool
    message: str


class OrchestratorService:
    """Single facade over repositories, connectors and the Jobs engine.

    Folders and descriptors are identified by their ``path``: the full
    materialized path in the tree (e.g. ``/lab/networks/student01``). A
    ``hypervisor_connector`` is the live adapter that talks to a hypervisor;
    ``hypervisor_connectors`` maps each hypervisor name to its connector (DEC-029).
    """

    def __init__(
        self,
        folders_repo: FolderRepository,
        descriptors_repo: DescriptorRepository,
        jobs_repo: JobRepository,
        hypervisor_connectors: dict[str, HypervisorConnector],
    ) -> None:
        self._folders = folders_repo
        self._descriptors = descriptors_repo
        self._connectors = hypervisor_connectors
        self._engine = JobEngine(jobs_repo)

    def deploy(self, path: str) -> Job:
        return self._run(self._machine_command(DeployCommand, path))

    def undeploy(self, path: str) -> Job:
        return self._run(self._machine_command(UndeployCommand, path))

    def start(self, path: str) -> Job:
        return self._run(self._machine_command(StartCommand, path))

    def stop(self, path: str) -> Job:
        return self._run(self._machine_command(StopCommand, path))

    def status(self, path: str) -> DescriptorStatus:
        """Report a descriptor's status: its orchestrator state and, only when it
        is deployed, the live runtime state queried from its hypervisor.

        A read — creates no Job. Raises OperationError if the path is unknown.
        """
        descriptor = self._descriptors.get(path)
        if descriptor is None:
            raise OperationError([f"descriptor not found: {path}"])
        runtime: RuntimeState | None = None
        # runtime state only exists for a deployed VM — ask its hypervisor
        if descriptor.state == DescriptorState.DEPLOYED and descriptor.vm_id:
            connector = self._connectors.get(descriptor.hypervisor)
            runtime = (
                connector.get_status(descriptor.vm_id)
                if connector is not None
                else RuntimeState.UNKNOWN
            )
        return DescriptorStatus(
            path=path,
            state=descriptor.state,
            runtime_state=runtime,
            vm_id=descriptor.vm_id,
        )

    def list_tree(self, path: str = "/") -> list[TreeEntry]:
        """List the subtree rooted at ``path`` as one listing sorted by path.

        Folders and descriptors live in separate tables, so this reads each one's
        subtree and merges them. Reads the DB only (no hypervisor calls) and
        creates no Job.
        """
        entries: list[TreeEntry] = [
            TreeEntry(path=folder.path, kind="folder")
            for folder in self._folders.subtree(path)
        ]
        entries += [
            TreeEntry(path=d.path, kind="descriptor", state=d.state)
            for d in self._descriptors.subtree(path)
        ]
        return sorted(entries, key=lambda entry: entry.path)

    def apply(self, document: ApplyDocument) -> list[ApplyResult]:
        """Create/update the folders and descriptors in ``document``.

        Best-effort (DEC-027): items run in dependency order — folders shallowest
        first, then descriptors — and a rejected item is recorded while the rest
        continue. Each item is its own Job. (Batch all-or-reject and a parent Job
        for the whole apply are future work, DEC-028.)
        """
        results: list[ApplyResult] = []
        # shallowest paths first so a parent folder is created before its children
        for folder in sorted(document.folders, key=lambda f: f.path.count("/")):
            results.append(self._apply_one(CreateFolderCommand(folder, self._folders)))
        for descriptor in document.descriptors:
            command = CreateDescriptorCommand(
                descriptor, self._descriptors, self._folders
            )
            results.append(self._apply_one(command))
        return results

    def _machine_command(self, command_cls: MachineCommand, path: str) -> Command:
        """Build a machine command for ``path``.

        Loads the descriptor (rejects if missing) and resolves its hypervisor's
        connector (rejects if unknown), then constructs the command with both.
        """
        descriptor = self._descriptors.get(path)
        if descriptor is None:
            raise OperationError([f"descriptor not found: {path}"])
        connector = self._connectors.get(descriptor.hypervisor)
        if connector is None:
            raise OperationError([f"unknown hypervisor: {descriptor.hypervisor}"])
        return command_cls(path, self._descriptors, connector)

    def _run(self, command: Command) -> Job:
        """Run an already-built command.

        Validates first — any error raises OperationError and creates no Job —
        then hands it to the engine, which records and returns the Job.
        """
        errors = command.validate()
        if errors:
            raise OperationError(errors)  # rejected: no Job created
        return self._engine.run(command)

    def _apply_one(self, command: Command) -> ApplyResult:
        """Run one apply item, turning a rejection into a result instead of raising."""
        try:
            job = self._run(command)
            return ApplyResult(
                path=command.target,
                ok=job.status == JobStatus.COMPLETED,
                message=job.message or "",
            )
        except OperationError as error:
            return ApplyResult(
                path=command.target, ok=False, message="; ".join(error.errors)
            )
