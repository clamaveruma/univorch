"""FastAPI app for the REST interface.

Read endpoints first (this sub-piece of Sprint 3.1): ``GET /api/v1/health``,
``GET /api/v1/status``, ``GET /api/v1/tree``, ``GET /api/v1/inspect``. Writes
(deploy, undeploy, start, stop, load) come in the next sub-piece.

Tree paths are passed as **query parameters**, not URL segments. The
identifier of a folder or descriptor is a materialized path that contains
slashes (``/lab/networks/student01``); putting that inside a URL segment
turns into double-slashes and percent-encoding noise. As query string it
goes URL-encoded once and FastAPI hands it back as plain ``str``.

``OperationError`` from the service becomes HTTP 400 with a JSON body that
carries the error messages, so an HTTP client can render them the same way
the CLI does today.
"""

from typing import Literal

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from univorch.models import DefinitionDocument, Descriptor, Folder, Job
from univorch.service import (
    DescriptorStatus,
    LoadResult,
    OperationError,
    OrchestratorService,
    TreeEntry,
)


class InspectResult(BaseModel):
    """Discriminated wrapper around what ``inspect`` may return.

    ``kind`` tells the client whether ``data`` is a folder or a descriptor;
    each side has its own schema and the client picks the right one.
    """

    kind: Literal["folder", "descriptor"]
    folder: Folder | None = None
    descriptor: Descriptor | None = None


def create_app(service: OrchestratorService) -> FastAPI:
    """Build a FastAPI app bound to ``service``.

    Caller (typically ``__main__``) owns the service and its lifetime;
    ``create_app`` only wires routes to its methods. The same factory is
    used by integration tests with a service backed by an in-memory TinyDB.
    """
    app = FastAPI(
        title="UnivOrch REST API",
        version="0.1",
        description=(
            "Public HTTP API for the UnivOrch orchestrator. Sprint 3 scope: "
            "thin layer over OrchestratorService; no auth yet (Sprint 5+)."
        ),
    )

    @app.exception_handler(OperationError)
    async def _operation_error(_request: Request, exc: OperationError) -> JSONResponse:
        """The service rejected the request during validation; no Job created."""
        return JSONResponse(status_code=400, content={"errors": exc.errors})

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        """Liveness probe — returns ``{"status": "ok"}`` if the process is up."""
        return {"status": "ok"}

    @app.get("/api/v1/status")
    def status(path: str) -> DescriptorStatus:
        """Status of a single VM: orchestrator state + (if deployed) runtime."""
        return service.status(path)

    @app.get("/api/v1/tree")
    def tree(path: str = "/", recursive: bool = False) -> list[TreeEntry]:
        """List what lives under ``path``. ``recursive=False`` is ``ls`` style."""
        # The service raises only when the descriptor is unknown; an empty
        # listing for a missing folder is silent on purpose (matches CLI).
        return service.list_tree(path, recursive=recursive)

    @app.get("/api/v1/inspect", response_model=InspectResult)
    def inspect(path: str, local: bool = False) -> InspectResult:
        """Return the entity at ``path`` (folder or descriptor).

        ``local=True`` skips the cascade resolver for descriptors (raw local
        definition only). Folders are returned as-is in both modes.
        """
        result = service.inspect(path, resolved=not local)
        if isinstance(result, Folder):
            return InspectResult(kind="folder", folder=result)
        return InspectResult(kind="descriptor", descriptor=result)

    # --- Write endpoints ---------------------------------------------------
    # Each one wraps a single facade call. Return the Job verbatim — its
    # status (COMPLETED / FAILED) carries the outcome; an HTTP 200 means
    # "the Job exists, here it is", not "the operation succeeded". A 400
    # only ever comes from the OperationError handler above (rejected
    # before the Job was even created — DEC-027).

    @app.post("/api/v1/deploy")
    def deploy(path: str) -> Job:
        return service.deploy(path)

    @app.post("/api/v1/undeploy")
    def undeploy(path: str) -> Job:
        return service.undeploy(path)

    @app.post("/api/v1/start")
    def start(path: str) -> Job:
        return service.start(path)

    @app.post("/api/v1/stop")
    def stop(path: str) -> Job:
        return service.stop(path)

    @app.post("/api/v1/load")
    def load(document: DefinitionDocument, destination: str = "/") -> list[LoadResult]:
        """Load a YAML-shaped document into ``destination`` (default: root).

        Best-effort: each item is its own Job; rejected items are recorded
        in the result list while the rest continue (DEC-027).
        """
        return service.load(document, destination)

    return app
