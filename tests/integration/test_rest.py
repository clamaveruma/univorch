"""Integration tests for the REST interface (Sprint 3.1, read endpoints).

Drives FastAPI's TestClient against ``create_app`` with a real
``OrchestratorService`` backed by an in-memory TinyDB. No network, no
network namespace, no real uvicorn — just the WSGI/ASGI layer in process.
"""

import pytest
from fastapi.testclient import TestClient
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.interfaces.rest.app import create_app
from univorch.models import (
    DefinitionDocument,
    Descriptor,
    DescriptorDef,
    Folder,
    FolderDef,
    HypervisorDef,
)
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OrchestratorService


@pytest.fixture
def service() -> OrchestratorService:
    db = TinyDB(storage=MemoryStorage)
    folders = FolderRepository(db)
    descriptors = DescriptorRepository(db)
    jobs = JobRepository(db)
    folders.save(
        Folder(
            path="/lab",
            hypervisors={"mock": HypervisorDef(connector_type="mock")},
        )
    )
    return OrchestratorService(folders, descriptors, jobs, {"mock": MockConnector})


@pytest.fixture
def client(service: OrchestratorService) -> TestClient:
    return TestClient(create_app(service))


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestStatus:
    def test_status_of_provisioned_vm(
        self, client: TestClient, service: OrchestratorService
    ) -> None:
        service._descriptors.save(  # seed directly; load() endpoint comes in 3.1.b
            Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        )
        r = client.get("/api/v1/status", params={"path": "/lab/vm"})
        assert r.status_code == 200
        body = r.json()
        assert body["path"] == "/lab/vm"
        assert body["state"] == "provisioned"
        assert body["runtime_state"] is None
        assert body["vm_id"] is None

    def test_status_unknown_vm_is_400(self, client: TestClient) -> None:
        r = client.get("/api/v1/status", params={"path": "/lab/nope"})
        assert r.status_code == 400
        assert "errors" in r.json()
        assert any("not found" in e for e in r.json()["errors"])


class TestTree:
    def test_empty_root_returns_empty_list(self, client: TestClient) -> None:
        # The pre-seeded /lab is the only folder; the root listing shows it.
        r = client.get("/api/v1/tree", params={"path": "/"})
        assert r.status_code == 200
        paths = [entry["path"] for entry in r.json()]
        assert paths == ["/lab"]

    def test_recursive_listing(
        self, client: TestClient, service: OrchestratorService
    ) -> None:
        # seed a nested structure via the service to exercise recursive=True
        service.load(
            DefinitionDocument(
                folders={
                    "networks": FolderDef(
                        descriptors={
                            "vm1": DescriptorDef(
                                hypervisor="mock", base_vm="linux-base"
                            )
                        }
                    )
                }
            ),
            destination="/lab",
        )
        r = client.get("/api/v1/tree", params={"path": "/lab", "recursive": "true"})
        assert r.status_code == 200
        paths = sorted(entry["path"] for entry in r.json())
        assert paths == ["/lab/networks", "/lab/networks/vm1"]

    def test_missing_folder_returns_empty(self, client: TestClient) -> None:
        # Matches the CLI: no folder, no rows. Not an error condition.
        r = client.get("/api/v1/tree", params={"path": "/nope"})
        assert r.status_code == 200
        assert r.json() == []


class TestInspect:
    def test_inspect_folder(self, client: TestClient) -> None:
        r = client.get("/api/v1/inspect", params={"path": "/lab"})
        assert r.status_code == 200
        body = r.json()
        assert body["kind"] == "folder"
        assert body["folder"]["path"] == "/lab"
        assert "mock" in body["folder"]["hypervisors"]

    def test_inspect_descriptor_resolved(
        self, client: TestClient, service: OrchestratorService
    ) -> None:
        # Seed: a template in /lab, descriptor in /lab uses it (no import needed
        # at /lab since the resource is defined locally).
        service.load(
            DefinitionDocument(
                folders={
                    "demo": FolderDef(
                        descriptors={
                            "vm": DescriptorDef(
                                hypervisor="mock", base_vm="linux-base", cpu=2
                            )
                        }
                    )
                }
            ),
            destination="/lab",
        )
        r = client.get("/api/v1/inspect", params={"path": "/lab/demo/vm"})
        assert r.status_code == 200
        body = r.json()
        assert body["kind"] == "descriptor"
        assert body["descriptor"]["path"] == "/lab/demo/vm"
        assert body["descriptor"]["hypervisor"] == "mock"

    def test_inspect_unknown_path_is_400(self, client: TestClient) -> None:
        r = client.get("/api/v1/inspect", params={"path": "/nowhere"})
        assert r.status_code == 400
        assert "errors" in r.json()


class TestMachineOps:
    """Write endpoints: deploy/undeploy/start/stop. Each returns a Job
    serialised; HTTP 200 means "Job exists", check Job.status for outcome."""

    def _seed_vm(self, service: OrchestratorService) -> None:
        service._descriptors.save(
            Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        )

    def test_deploy_full_lifecycle(
        self, client: TestClient, service: OrchestratorService
    ) -> None:
        self._seed_vm(service)
        r = client.post("/api/v1/deploy", params={"path": "/lab/vm"})
        assert r.status_code == 200
        assert r.json()["status"] == "completed"
        # status now shows deployed + stopped (freshly cloned)
        s = client.get("/api/v1/status", params={"path": "/lab/vm"}).json()
        assert s["state"] == "deployed"
        assert s["runtime_state"] == "stopped"
        # start → running
        assert (
            client.post("/api/v1/start", params={"path": "/lab/vm"}).json()["status"]
            == "completed"
        )
        s = client.get("/api/v1/status", params={"path": "/lab/vm"}).json()
        assert s["runtime_state"] == "running"
        # stop → stopped
        client.post("/api/v1/stop", params={"path": "/lab/vm"})
        # undeploy → back to provisioned
        assert (
            client.post("/api/v1/undeploy", params={"path": "/lab/vm"}).json()["status"]
            == "completed"
        )
        s = client.get("/api/v1/status", params={"path": "/lab/vm"}).json()
        assert s["state"] == "provisioned"

    def test_deploy_unknown_vm_is_400(self, client: TestClient) -> None:
        r = client.post("/api/v1/deploy", params={"path": "/lab/nope"})
        assert r.status_code == 400
        assert "errors" in r.json()


class TestLoad:
    def test_load_creates_tree(
        self, client: TestClient, service: OrchestratorService
    ) -> None:
        # Document shaped as it would arrive via JSON (normalised form).
        body = {
            "kind": "definition",
            "version": "1",
            "folders": {
                "networks": {
                    "descriptors": {
                        "vm1": {"hypervisor": "mock", "base_vm": "linux-base"}
                    }
                }
            },
        }
        r = client.post("/api/v1/load", params={"destination": "/lab"}, json=body)
        assert r.status_code == 200
        results = r.json()
        assert all(item["ok"] for item in results)
        # the descriptor is actually there
        assert service._descriptors.get("/lab/networks/vm1") is not None

    def test_load_missing_destination_is_400(self, client: TestClient) -> None:
        body = {"kind": "definition", "version": "1", "folders": {}}
        r = client.post("/api/v1/load", params={"destination": "/nope"}, json=body)
        assert r.status_code == 400
        assert any("destination" in e for e in r.json()["errors"])

    def test_load_invalid_document_is_422(self, client: TestClient) -> None:
        # FastAPI validates the body against DefinitionDocument; an unknown
        # field at the top → 422 Unprocessable Entity (Pydantic validation),
        # distinct from 400 (service-level rejection).
        r = client.post(
            "/api/v1/load",
            params={"destination": "/lab"},
            json={"kind": "definition", "version": "1", "garbage_field": 1},
        )
        assert r.status_code == 422
