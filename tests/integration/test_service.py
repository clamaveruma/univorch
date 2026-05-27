"""Integration tests for the OrchestratorService (machine operations)."""

import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.connectors.types import RuntimeState
from univorch.models import (
    DefinitionDocument,
    Descriptor,
    DescriptorDef,
    DescriptorState,
    Folder,
    FolderDef,
    JobStatus,
    VMTemplateDef,
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


def test_deploy_descriptor_without_any_hypervisor_rejected(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    # No hypervisor inline AND no template → the Resolver has nothing to find,
    # the service rejects the deploy with 'no effective hypervisor'.
    descriptors.save(Descriptor(path="/lab/vm"))
    with pytest.raises(OperationError, match="no effective hypervisor"):
        service.deploy("/lab/vm")


def test_deploy_descriptor_with_unresolvable_template_rejected(
    service: OrchestratorService, descriptors: DescriptorRepository
) -> None:
    # Template name referenced but no folder defines it / no import lets it in.
    descriptors.save(Descriptor(path="/lab/vm", template="missing"))
    with pytest.raises(OperationError, match="template not accessible"):
        service.deploy("/lab/vm")


def test_template_based_descriptor_load_then_deploy(
    service: OrchestratorService,
    folders: FolderRepository,
    descriptors: DescriptorRepository,
) -> None:
    """End-to-end: load a YAML with template+import, deploy resolves OK.

    Mirrors the demo's shape: a folder defines a template, a subfolder imports
    it, and a descriptor in the subfolder uses it. The Resolver (Pieza 1.C
    wiring) makes deploy succeed: the resolved hypervisor 'mock' picks the
    connector and the resolved base_vm 'linux-base' clones into a VM.
    """
    doc = DefinitionDocument(
        folders={
            "lab": FolderDef(
                vm_templates={
                    "linux-vm": VMTemplateDef(
                        hypervisor="mock", base_vm="linux-base", cpu=2
                    )
                },
                folders={
                    "networks": FolderDef(
                        imports=["linux-vm"],
                        descriptors={"vm": DescriptorDef(template="linux-vm")},
                    )
                },
            )
        }
    )
    results = service.load(doc)
    assert all(r.ok for r in results), [r.message for r in results if not r.ok]
    # the persisted descriptor still has its local definition only
    raw = descriptors.get("/lab/networks/vm")
    assert raw is not None
    assert raw.template == "linux-vm"
    assert raw.hypervisor is None  # NOT frozen at load
    # and deploy works because the Resolver fills in the gaps at access time
    job = service.deploy("/lab/networks/vm")
    assert job.status == JobStatus.COMPLETED
    raw_after = descriptors.get("/lab/networks/vm")
    assert raw_after is not None and raw_after.state == DescriptorState.DEPLOYED


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

    def test_inspect_returns_resolved_descriptor_by_default(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        # Template defined in /lab; descriptor in /lab uses it (no import needed
        # — local folder defines it).
        folders.save(
            Folder(
                path="/lab",
                vm_templates={
                    "linux-vm": VMTemplateDef(hypervisor="mock", base_vm="linux-base")
                },
            )
        )
        descriptors.save(Descriptor(path="/lab/vm", template="linux-vm"))
        result = service.inspect("/lab/vm")
        assert isinstance(result, Descriptor)
        assert result.hypervisor == "mock"  # filled by resolver
        assert result.base_vm == "linux-base"

    def test_inspect_local_does_not_resolve(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        folders.save(
            Folder(
                path="/lab",
                vm_templates={
                    "linux-vm": VMTemplateDef(hypervisor="mock", base_vm="linux-base")
                },
            )
        )
        descriptors.save(Descriptor(path="/lab/vm", template="linux-vm"))
        result = service.inspect("/lab/vm", resolved=False)
        assert isinstance(result, Descriptor)
        assert result.hypervisor is None  # local: no resolution
        assert result.base_vm is None

    def test_inspect_folder(
        self, service: OrchestratorService, folders: FolderRepository
    ) -> None:
        folders.save(Folder(path="/lab", description="The lab"))
        result = service.inspect("/lab")
        assert isinstance(result, Folder)
        assert result.description == "The lab"

    def test_inspect_unknown_path_raises(
        self, service: OrchestratorService
    ) -> None:
        with pytest.raises(OperationError):
            service.inspect("/nope")

    def test_status_tolerates_unresolvable_template(
        self,
        service: OrchestratorService,
        descriptors: DescriptorRepository,
    ) -> None:
        # Edge case: a descriptor 'deployed' in the DB (manually injected here)
        # but its template no longer resolves. status must not raise; runtime
        # stays None. State reporting is still authoritative.
        descriptors.save(
            Descriptor(
                path="/lab/vm",
                template="missing",
                state=DescriptorState.DEPLOYED,
                vm_id="mock-vm-X",
            )
        )
        s = service.status("/lab/vm")
        assert s.state == DescriptorState.DEPLOYED
        assert s.runtime_state is None  # resolver failed, runtime stays None
        assert s.vm_id == "mock-vm-X"


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


class TestLoad:
    def _vm_def(self) -> DescriptorDef:
        return DescriptorDef(hypervisor="mock", base_vm="linux-base")

    def test_creates_nested_tree_at_root(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        doc = DefinitionDocument(
            folders={
                "lab": FolderDef(
                    folders={"networks": FolderDef(descriptors={"vm1": self._vm_def()})}
                )
            }
        )
        results = service.load(doc)  # default destination = root
        assert all(r.ok for r in results)
        assert folders.exists("/lab") and folders.exists("/lab/networks")
        assert descriptors.get("/lab/networks/vm1") is not None

    def test_loads_into_destination(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        folders.save(Folder(path="/lab"))  # destination must exist
        doc = DefinitionDocument(descriptors={"vm": self._vm_def()})
        results = service.load(doc, destination="/lab")
        assert all(r.ok for r in results)
        assert descriptors.get("/lab/vm") is not None  # hung under destination

    def test_top_level_folder_and_descriptor(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        # a folder and a VM at the same (top) level of the document
        doc = DefinitionDocument(
            folders={"lab": FolderDef()},
            descriptors={"shared_vm": self._vm_def()},
        )
        assert all(r.ok for r in service.load(doc))
        assert folders.exists("/lab")
        assert descriptors.get("/shared_vm") is not None

    def test_rejects_missing_destination(self, service: OrchestratorService) -> None:
        doc = DefinitionDocument(descriptors={"vm": self._vm_def()})
        with pytest.raises(OperationError):
            service.load(doc, destination="/nope")

    def test_best_effort_records_failure(
        self,
        service: OrchestratorService,
        folders: FolderRepository,
        descriptors: DescriptorRepository,
    ) -> None:
        # /lab/vm already exists DEPLOYED → cannot be redefined with a different
        # base_vm without undeploying first (DEC-027)
        folders.save(Folder(path="/lab"))
        descriptors.save(
            Descriptor(
                path="/lab/vm",
                hypervisor="mock",
                base_vm="linux-base",
                state=DescriptorState.DEPLOYED,
                vm_id="mock-vm-99",
            )
        )
        doc = DefinitionDocument(
            descriptors={"shared_vm": self._vm_def()},  # this one works
            folders={
                "lab": FolderDef(
                    descriptors={
                        "vm": DescriptorDef(hypervisor="mock", base_vm="other-base")
                    }
                )
            },
        )
        results = service.load(doc)
        by_path = {r.path: r for r in results}
        assert by_path["/shared_vm"].ok  # unrelated item still applied
        assert not by_path["/lab/vm"].ok  # redefinition rejected

    def test_idempotent(self, service: OrchestratorService) -> None:
        doc = DefinitionDocument(folders={"lab": FolderDef()})
        service.load(doc)
        results = service.load(doc)
        assert results[0].ok and "no change" in results[0].message
