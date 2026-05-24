"""Tests for the Command pattern: DeployCommand (J2)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import RuntimeState
from univorch.jobs.commands import (
    DeployCommand,
    StartCommand,
    StopCommand,
    UndeployCommand,
)
from univorch.models import Descriptor, DescriptorState
from univorch.persistence.tinydb.repositories import DescriptorRepository


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
        assert cmd.validate() == ["descriptor not found: /lab/vm"]

    def test_broken_descriptor(
        self, descriptors: DescriptorRepository, connector: MockConnector
    ) -> None:
        _save(descriptors, state=DescriptorState.BROKEN)
        cmd = DeployCommand("/lab/vm", descriptors, connector)
        assert cmd.validate() == ["cannot deploy a broken descriptor: /lab/vm"]

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
