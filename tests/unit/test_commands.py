"""Tests for the Command pattern: DeployCommand (J2)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import RuntimeState
from univorch.jobs.commands import (
    CreateDescriptorCommand,
    CreateFolderCommand,
    DeployCommand,
    StartCommand,
    StopCommand,
    UndeployCommand,
)
from univorch.models import Descriptor, DescriptorState, Folder
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
)


@pytest.fixture
def folders() -> FolderRepository:
    return FolderRepository(TinyDB(storage=MemoryStorage))


@pytest.fixture
def descriptors() -> DescriptorRepository:
    return DescriptorRepository(TinyDB(storage=MemoryStorage))


@pytest.fixture
def connector() -> MockConnector:
    return MockConnector.with_templates(["linux-base"])


def _save(repo: DescriptorRepository, **kwargs: object) -> None:
    base = {"path": "/lab/vm", "hypervisor": "mock", "base_vm": "linux-base"}
    repo.save(Descriptor(**(base | kwargs)))


def _deploy(repo: DescriptorRepository, connector: MockConnector) -> str:
    """Set up a deployed descriptor at /lab/vm; return its vm_id."""
    vm_id = connector.clone("linux-base", "/lab/vm")
    _save(repo, state=DescriptorState.DEPLOYED, vm_id=vm_id)
    return vm_id


class TestDeployCommandValidate:
    def test_missing_descriptor(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        cmd = DeployCommand("/lab/vm", descriptors, connector)
        assert cmd.validate() == ["VM not found: /lab/vm"]

    def test_broken_descriptor(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors, state=DescriptorState.BROKEN)
        cmd = DeployCommand("/lab/vm", descriptors, connector)
        assert cmd.validate() == ["cannot deploy a broken VM: /lab/vm"]

    def test_ok(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors)
        cmd = DeployCommand("/lab/vm", descriptors, connector)
        assert cmd.validate() == []


class TestDeployCommandExecute:
    def test_deploys(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors)
        msg = DeployCommand("/lab/vm", descriptors, connector).execute()
        d = descriptors.get("/lab/vm")
        assert d is not None
        assert d.state == DescriptorState.DEPLOYED
        assert d.vm_id is not None
        assert "deployed" in msg

    def test_idempotent_when_already_deployed(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors)
        cmd = DeployCommand("/lab/vm", descriptors, connector)
        cmd.execute()
        msg = cmd.execute()
        assert "no change" in msg
        assert len(connector.deployed_vms()) == 1  # not cloned twice

    def test_raises_when_invalid(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        cmd = DeployCommand("/lab/vm", descriptors, connector)  # no descriptor
        with pytest.raises(ValueError):
            cmd.execute()

    def test_names_the_vm_with_full_path(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors)
        DeployCommand("/lab/vm", descriptors, connector).execute()
        assert connector.deployed_vms()[0].name == "/lab/vm"


class TestUndeployCommand:
    def test_undeploys(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _deploy(descriptors, connector)
        msg = UndeployCommand("/lab/vm", descriptors, connector).execute()
        d = descriptors.get("/lab/vm")
        assert d is not None
        assert d.state == DescriptorState.PROVISIONED
        assert d.vm_id is None
        assert connector.deployed_vms() == []
        assert "undeployed" in msg

    def test_idempotent_when_provisioned(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors)  # provisioned by default
        msg = UndeployCommand("/lab/vm", descriptors, connector).execute()
        assert "no change" in msg

    def test_validate_rejects_broken(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors, state=DescriptorState.BROKEN)
        assert UndeployCommand("/lab/vm", descriptors, connector).validate() != []


class TestStartStopCommands:
    def test_start_runs_the_vm(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        vm_id = _deploy(descriptors, connector)
        msg = StartCommand("/lab/vm", descriptors, connector).execute()
        assert connector.get_status(vm_id) == RuntimeState.RUNNING
        assert "started" in msg

    def test_start_idempotent(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _deploy(descriptors, connector)
        StartCommand("/lab/vm", descriptors, connector).execute()
        msg = StartCommand("/lab/vm", descriptors, connector).execute()
        assert "no change" in msg

    def test_stop_stops_the_vm(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        vm_id = _deploy(descriptors, connector)
        StartCommand("/lab/vm", descriptors, connector).execute()
        msg = StopCommand("/lab/vm", descriptors, connector).execute()
        assert connector.get_status(vm_id) == RuntimeState.STOPPED
        assert "stopped" in msg

    def test_stop_idempotent(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _deploy(descriptors, connector)  # deployed; the VM is stopped after clone
        msg = StopCommand("/lab/vm", descriptors, connector).execute()
        assert "no change" in msg


@pytest.mark.parametrize("command_cls", [UndeployCommand, StartCommand, StopCommand])
def test_execute_raises_on_missing_descriptor(
    descriptors: DescriptorRepository,
    connector: MockConnector,
    command_cls: type,
) -> None:
    cmd = command_cls("/lab/vm", descriptors, connector)
    assert cmd.validate() != []
    with pytest.raises(ValueError):
        cmd.execute()


@pytest.mark.parametrize("command_cls", [StartCommand, StopCommand])
def test_start_stop_require_deployed(
    descriptors: DescriptorRepository,
    connector: MockConnector,
    command_cls: type,
) -> None:
    _save(descriptors)  # provisioned, no VM
    assert command_cls("/lab/vm", descriptors, connector).validate() != []


class TestCreateFolderCommand:
    def test_creates(self, folders: FolderRepository) -> None:
        msg = CreateFolderCommand(Folder(path="/lab"), folders).execute()
        assert folders.get("/lab") is not None
        assert "created" in msg

    def test_top_level_needs_no_parent(self, folders: FolderRepository) -> None:
        assert CreateFolderCommand(Folder(path="/lab"), folders).validate() == []

    def test_requires_parent(self, folders: FolderRepository) -> None:
        cmd = CreateFolderCommand(Folder(path="/lab/networks"), folders)
        assert cmd.validate() != []

    def test_execute_raises_without_parent(self, folders: FolderRepository) -> None:
        cmd = CreateFolderCommand(Folder(path="/lab/networks"), folders)
        with pytest.raises(ValueError):
            cmd.execute()

    def test_idempotent(self, folders: FolderRepository) -> None:
        CreateFolderCommand(Folder(path="/lab"), folders).execute()
        msg = CreateFolderCommand(Folder(path="/lab"), folders).execute()
        assert "no change" in msg

    def test_updates_existing(self, folders: FolderRepository) -> None:
        CreateFolderCommand(Folder(path="/lab", description="old"), folders).execute()
        msg = CreateFolderCommand(
            Folder(path="/lab", description="new"), folders
        ).execute()
        assert "updated" in msg


class TestCreateDescriptorCommand:
    def _desc(self, **kwargs: object) -> Descriptor:
        base = {"path": "/lab/vm", "hypervisor": "mock", "base_vm": "linux-base"}
        return Descriptor(**(base | kwargs))

    def test_creates_when_parent_exists(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        msg = CreateDescriptorCommand(self._desc(), descriptors, folders).execute()
        assert descriptors.get("/lab/vm") is not None
        assert "created" in msg

    def test_requires_parent_folder(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        cmd = CreateDescriptorCommand(self._desc(), descriptors, folders)  # no /lab
        assert cmd.validate() != []

    def test_execute_raises_without_parent_folder(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        with pytest.raises(ValueError):
            CreateDescriptorCommand(self._desc(), descriptors, folders).execute()

    def test_idempotent(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        CreateDescriptorCommand(self._desc(), descriptors, folders).execute()
        msg = CreateDescriptorCommand(self._desc(), descriptors, folders).execute()
        assert "no change" in msg

    def test_updates_provisioned(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        descriptors.save(self._desc(description="old"))
        msg = CreateDescriptorCommand(
            self._desc(description="new"), descriptors, folders
        ).execute()
        assert "updated" in msg

    def test_rejects_redefining_deployed(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        descriptors.save(self._desc(state=DescriptorState.DEPLOYED, vm_id="mock-vm-1"))
        cmd = CreateDescriptorCommand(self._desc(base_vm="other"), descriptors, folders)
        assert cmd.validate() != []

    def test_reapply_same_on_deployed_is_noop(
        self, descriptors: DescriptorRepository, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        descriptors.save(self._desc(state=DescriptorState.DEPLOYED, vm_id="mock-vm-1"))
        msg = CreateDescriptorCommand(self._desc(), descriptors, folders).execute()
        assert "no change" in msg
        d = descriptors.get("/lab/vm")
        assert d is not None and d.state == DescriptorState.DEPLOYED  # runtime kept
