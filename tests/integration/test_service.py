"""Integration tests for the OrchestratorService (machine operations)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import RuntimeState
from univorch.models import (
    ApplyDocument,
    Descriptor,
    DescriptorState,
    Folder,
    JobStatus,
)
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
    def test_recursive_lists_whole_subtree_sorted_with_states(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        folders.save(Folder(path="/lab"))
        folders.save(Folder(path="/lab/networks"))
        _provisioned(descriptors, path="/lab/networks/vm")
        entries = service.list_tree("/", recursive=True)
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

    def test_default_lists_direct_children_only(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        folders.save(Folder(path="/lab"))
        folders.save(Folder(path="/lab/networks"))  # a folder one level down
        _provisioned(descriptors, path="/lab/vm")  # a descriptor one level down
        _provisioned(descriptors, path="/lab/networks/deep")  # two levels down
        # only the direct children of /lab, never the deeper /lab/networks/deep
        assert sorted(e.path for e in service.list_tree("/lab")) == [
            "/lab/networks",
            "/lab/vm",
        ]

    def test_scopes_to_subtree(
        self, service: OrchestratorService, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab"))
        folders.save(Folder(path="/lab/x"))
        folders.save(Folder(path="/other"))  # a sibling subtree, must be excluded
        assert [e.path for e in service.list_tree("/lab")] == ["/lab/x"]


class TestApply:
    def test_creates_folders_and_descriptors(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        doc = ApplyDocument(
            folders=[Folder(path="/lab"), Folder(path="/lab/networks")],
            descriptors=[
                Descriptor(
                    path="/lab/networks/vm1", hypervisor="mock", base_vm="linux-base"
                )
            ],
        )
        results = service.apply(doc)
        assert all(r.ok for r in results)
        assert folders.exists("/lab") and folders.exists("/lab/networks")
        assert descriptors.get("/lab/networks/vm1") is not None

    def test_orders_parents_first(
        self, service: OrchestratorService, folders: FolderRepository
    ) -> None:
        # child listed before parent in the document → sorted, so both succeed
        doc = ApplyDocument(folders=[Folder(path="/lab/networks"), Folder(path="/lab")])
        assert all(r.ok for r in service.apply(doc))
        assert folders.exists("/lab/networks")

    def test_best_effort_records_rejection(
        self, service: OrchestratorService, folders: FolderRepository
    ) -> None:
        doc = ApplyDocument(folders=[Folder(path="/lab"), Folder(path="/x/y")])
        by_path = {r.path: r for r in service.apply(doc)}
        assert by_path["/lab"].ok
        assert not by_path["/x/y"].ok  # parent /x missing
        assert folders.exists("/lab")  # the valid one was still applied
        assert not folders.exists("/x/y")

    def test_idempotent(self, service: OrchestratorService) -> None:
        doc = ApplyDocument(folders=[Folder(path="/lab")])
        service.apply(doc)
        results = service.apply(doc)
        assert results[0].ok and "no change" in results[0].message
