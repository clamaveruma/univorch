"""Integration tests for the OrchestratorService (machine operations)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.models import Descriptor, DescriptorState, JobStatus
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OperationError, OrchestratorService


@pytest.fixture
def db() -> TinyDB:
    return TinyDB(storage=MemoryStorage)


@pytest.fixture
def descriptors(db: TinyDB) -> DescriptorRepository:
    return DescriptorRepository(db)


@pytest.fixture
def jobs(db: TinyDB) -> JobRepository:
    return JobRepository(db)


@pytest.fixture
def service(
    db: TinyDB, descriptors: DescriptorRepository, jobs: JobRepository
) -> OrchestratorService:
    connectors = {"mock": MockConnector.with_templates(["linux-base"])}
    return OrchestratorService(FolderRepository(db), descriptors, jobs, connectors)


def _provisioned(repo: DescriptorRepository, **kwargs: object) -> None:
    base = {"path": "/lab/vm", "hypervisor": "mock", "base_vm": "linux-base"}
    repo.save(Descriptor(**(base | kwargs)))


def test_deploy_completes_and_marks_deployed(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    _provisioned(descriptors)
    job = service.deploy("/lab/vm")
    assert job.status == JobStatus.COMPLETED
    d = descriptors.get("/lab/vm")
    assert d is not None and d.state == DescriptorState.DEPLOYED


def test_full_lifecycle(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    _provisioned(descriptors)
    service.deploy("/lab/vm")
    assert service.start("/lab/vm").status == JobStatus.COMPLETED
    assert service.stop("/lab/vm").status == JobStatus.COMPLETED
    assert service.undeploy("/lab/vm").status == JobStatus.COMPLETED
    d = descriptors.get("/lab/vm")
    assert d is not None and d.state == DescriptorState.PROVISIONED


def test_unknown_path_rejected_without_job(
    service: OrchestratorService, jobs: JobRepository
) -> None:
    with pytest.raises(OperationError):
        service.deploy("/lab/nope")
    assert jobs.find_by_target("/lab/nope") == []  # no Job created


def test_unknown_hypervisor_rejected(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    _provisioned(descriptors, hypervisor="vmware")
    with pytest.raises(OperationError):
        service.deploy("/lab/vm")


def test_broken_descriptor_rejected(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    _provisioned(descriptors, state=DescriptorState.BROKEN)
    with pytest.raises(OperationError):
        service.deploy("/lab/vm")
