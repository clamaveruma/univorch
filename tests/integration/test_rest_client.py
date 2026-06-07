"""Integration tests for the REST HTTP client (Sprint 3.2).

Each test exercises the **full slice**: HttpServiceClient → httpx →
FastAPI app → real OrchestratorService over an in-memory TinyDB. No
network, no socket, no uvicorn — FastAPI's TestClient routes httpx
calls straight to the ASGI app in-process. If the client and the
server disagree on a field name or a type, the test fails here.

Why this beats mocking the transport: an httpx.MockTransport would
need a hand-rolled fake of every response, and that fake can silently
drift from the real server. With TestClient the server *is* the real
code.

For transport-error translation (pendiente 5.2) we DO use MockTransport
deliberately: we cannot make TestClient refuse a connection because it
never opens one. ``httpx.MockTransport`` is the right tool for "the
network said no" tests.
"""

import httpx
import pytest
from fastapi.testclient import TestClient
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from univorch.connectors.mock import MockConnector
from univorch.interfaces.rest.app import create_app
from univorch.interfaces.rest.client import HttpServiceClient
from univorch.models import (
    DefinitionDocument,
    Descriptor,
    DescriptorDef,
    Folder,
    FolderDef,
    HypervisorDef,
    JobStatus,
)
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import (
    DescriptorStatus,
    OperationError,
    OrchestratorService,
    TreeEntry,
)


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
def http(service: OrchestratorService) -> HttpServiceClient:
    """The HTTP client wired to a TestClient that drives the real app."""
    return HttpServiceClient(TestClient(create_app(service)))


class TestReads:
    def test_status_returns_descriptor_status(
        self, http: HttpServiceClient, service: OrchestratorService
    ) -> None:
        service._descriptors.save(
            Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        )
        result = http.status("/lab/vm")
        assert isinstance(result, DescriptorStatus)
        assert result.path == "/lab/vm"
        assert result.state.value == "provisioned"
        assert result.runtime_state is None

    def test_status_unknown_path_raises_OperationError(
        self, http: HttpServiceClient
    ) -> None:
        with pytest.raises(OperationError) as excinfo:
            http.status("/nope")
        assert any("not found" in e for e in excinfo.value.errors)

    def test_list_tree_returns_typed_entries(self, http: HttpServiceClient) -> None:
        entries = http.list_tree("/")
        assert all(isinstance(e, TreeEntry) for e in entries)
        assert [e.path for e in entries] == ["/lab"]

    def test_folder_exists_returns_bool(self, http: HttpServiceClient) -> None:
        assert http.folder_exists("/lab") is True
        assert http.folder_exists("/nowhere") is False
        assert http.folder_exists("/") is True  # root is implicit

    def test_inspect_returns_folder(self, http: HttpServiceClient) -> None:
        result = http.inspect("/lab")
        assert isinstance(result, Folder)
        assert result.path == "/lab"
        assert "mock" in result.hypervisors

    def test_inspect_returns_descriptor_resolved(
        self, http: HttpServiceClient, service: OrchestratorService
    ) -> None:
        service._descriptors.save(
            Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        )
        result = http.inspect("/lab/vm")
        assert isinstance(result, Descriptor)
        assert result.hypervisor == "mock"


class TestWrites:
    def test_full_lifecycle_via_client(
        self, http: HttpServiceClient, service: OrchestratorService
    ) -> None:
        # deploy → start → stop → undeploy, all through the HTTP client.
        # If any layer (client, server, service) drifts on the schema, one
        # of these fails. That is the value of TestClient over a mock.
        service._descriptors.save(
            Descriptor(path="/lab/vm", hypervisor="mock", base_vm="linux-base")
        )
        assert http.deploy("/lab/vm").status == JobStatus.COMPLETED
        assert http.start("/lab/vm").status == JobStatus.COMPLETED
        assert http.status("/lab/vm").runtime_state is not None  # is running
        assert http.stop("/lab/vm").status == JobStatus.COMPLETED
        assert http.undeploy("/lab/vm").status == JobStatus.COMPLETED
        assert http.status("/lab/vm").state.value == "provisioned"

    def test_load_creates_tree_via_client(
        self, http: HttpServiceClient, service: OrchestratorService
    ) -> None:
        document = DefinitionDocument(
            folders={
                "networks": FolderDef(
                    descriptors={
                        "vm1": DescriptorDef(hypervisor="mock", base_vm="linux-base")
                    }
                )
            }
        )
        results = http.load(document, destination="/lab")
        assert all(item.ok for item in results)
        assert service._descriptors.get("/lab/networks/vm1") is not None

    def test_load_missing_destination_raises(self, http: HttpServiceClient) -> None:
        with pytest.raises(OperationError):
            http.load(DefinitionDocument(), destination="/nope")


class TestTransportErrors:
    """Pendiente 5.2: when httpx itself cannot deliver a request (daemon
    down, timeout, network), the client raises ``OperationError`` with an
    actionable message — same shape the CLI already knows how to render.
    """

    def test_connect_error_becomes_actionable_operation_error(self) -> None:
        def refuse(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        http = HttpServiceClient(
            httpx.Client(
                transport=httpx.MockTransport(refuse),
                base_url="http://localhost:8080",
            )
        )
        with pytest.raises(OperationError) as excinfo:
            http.status("/lab/vm")
        message = "; ".join(excinfo.value.errors)
        assert "cannot reach the UnivOrch daemon" in message
        assert "http://localhost:8080" in message
        assert "univorchd" in message  # tells the user how to fix it

    def test_timeout_becomes_operation_error(self) -> None:
        def timeout(_request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("read timeout")

        http = HttpServiceClient(
            httpx.Client(
                transport=httpx.MockTransport(timeout),
                base_url="http://localhost:8080",
            )
        )
        with pytest.raises(OperationError) as excinfo:
            http.status("/lab/vm")
        assert "transport error" in "; ".join(excinfo.value.errors)


class TestProtocolConformance:
    """The HttpServiceClient cumple ``OrchestratorAPI``.

    This is what mypy verifies statically; here we just exercise the
    assignment at runtime so a future refactor that breaks conformance
    blows up the test, not only mypy.
    """

    def test_http_client_satisfies_orchestrator_api(
        self, http: HttpServiceClient
    ) -> None:
        from univorch.service import OrchestratorAPI

        api: OrchestratorAPI = http  # mypy enforces; runtime sanity check
        assert api.folder_exists("/lab") is True
