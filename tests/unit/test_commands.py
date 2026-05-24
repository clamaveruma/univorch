"""Tests for the Command pattern: DeployCommand (J2)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.jobs.commands import DeployCommand
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
