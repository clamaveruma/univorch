"""Integration tests for the OrchestratorService (machine operations)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import RuntimeState
from univorch.models import Descriptor, DescriptorState, Folder, JobStatus
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
def folders(db: TinyDB) -> FolderRepository:
    return FolderRepository(db)


@pytest.fixture
def descriptors(db: TinyDB) -> DescriptorRepository:
    return DescriptorRepository(db)


@pytest.fixture
def jobs(db: TinyDB) -> JobRepository:
    return JobRepository(db)


@pytest.fixture
def service(
    folders: FolderRepository,
    descriptors: DescriptorRepository,
    jobs: JobRepository,
) -> OrchestratorService:
    connectors = {"mock": MockConnector.with_templates(["linux-base"])}
    return OrchestratorService(folders, descriptors, jobs, connectors)


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


class TestStatus:
    def test_provisioned_has_no_runtime(
        self, service: OrchestratorService, descriptors: DescriptorRepository
    ) -> None:
        _provisioned(descriptors)
        s = service.status("/lab/vm")
        assert s.state == DescriptorState.PROVISIONED
        assert s.runtime_state is None
        assert s.vm_id is None

    def test_deployed_reports_runtime(
        self, service: OrchestratorService, descriptors: DescriptorRepository
    ) -> None:
        _provisioned(descriptors)
        service.deploy("/lab/vm")
        s = service.status("/lab/vm")
        assert s.state == DescriptorState.DEPLOYED
        assert s.runtime_state == RuntimeState.STOPPED  # freshly cloned
        assert s.vm_id is not None

    def test_unknown_path_rejected(self, service: OrchestratorService) -> None:
        with pytest.raises(OperationError):
            service.status("/lab/nope")


class TestListTree:
    def test_lists_subtree_sorted_with_states(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        folders.save(Folder(path="/lab"))
        folders.save(Folder(path="/lab/networks"))
        _provisioned(descriptors, path="/lab/networks/vm")
        entries = service.list_tree("/")
        assert [e.path for e in entries] == [
            "/lab",
            "/lab/networks",
            "/lab/networks/vm",
        ]
        by_path = {e.path: e for e in entries}
        assert by_path["/lab"].kind == "folder"
        assert by_path["/lab"].state is None
        assert by_path["/lab/networks/vm"].kind == "descriptor"
        assert by_path["/lab/networks/vm"].state == DescriptorState.PROVISIONED

    def test_scopes_to_subtree(
        self, service: OrchestratorService, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        folders.save(Folder(path="/other"))
        assert [e.path for e in service.list_tree("/lab")] == ["/lab"]
