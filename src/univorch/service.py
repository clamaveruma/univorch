"""Orchestrator service: the single entry point for all interfaces (DEC-031).

CLI, web GUI and the teaching layer all go through this facade; none talk to the
repositories, the connectors or the Jobs engine directly. The facade validates a
request and rejects the invalid ones (raising ``OperationError``, no Job created),
then builds the Command and hands it to the Jobs engine.
"""

from univorch.connectors.base import HypervisorConnector
from univorch.jobs.commands import (
    Command,
    DeployCommand,
    StartCommand,
    StopCommand,
    UndeployCommand,
)
from univorch.jobs.engine import JobEngine
from univorch.models import Job
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


class OrchestratorService:
    """Single facade over repositories, connectors and the Jobs engine."""

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

    def _machine_command(self, command_cls: MachineCommand, path: str) -> Command:
        descriptor = self._descriptors.get(path)
        if descriptor is None:
            raise OperationError([f"descriptor not found: {path}"])
        connector = self._connectors.get(descriptor.hypervisor)
        if connector is None:
            raise OperationError([f"unknown hypervisor: {descriptor.hypervisor}"])
        return command_cls(path, self._descriptors, connector)

    def _run(self, command: Command) -> Job:
        errors = command.validate()
        if errors:
            raise OperationError(errors)  # rejected: no Job created
        return self._engine.run(command)
