"""HTTP client for the REST daemon (Sprint 3.2).

Implements ``OrchestratorAPI`` over an injected ``httpx.Client``. The CLI
uses this when ``UNIVORCH_REMOTE`` is set, so a single CLI binary serves
both local development (in-process service) and ``docker exec`` into the
production container (HTTP to the daemon at localhost:8080).

Why inject ``httpx.Client`` instead of building one internally: it lets
tests pass FastAPI's ``TestClient`` (which exposes the same interface but
routes requests to the ASGI app in-process). The tests therefore exercise
the real client AND the real server without a real socket, while
production passes an ``httpx.Client(base_url="...")`` that hits the daemon
over the network.
"""

import httpx

from univorch.interfaces.rest.app import InspectResult
from univorch.models import DefinitionDocument, Descriptor, Folder, Job
from univorch.service import (
    DescriptorStatus,
    LoadResult,
    OperationError,
    TreeEntry,
)


class HttpServiceClient:
    """Calls the REST daemon; cumple ``OrchestratorAPI``."""

    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    # --- Reads -------------------------------------------------------------

    def status(self, path: str) -> DescriptorStatus:
        r = self._raise_or_get("/api/v1/status", params={"path": path})
        return DescriptorStatus.model_validate(r.json())

    def list_tree(self, path: str = "/", recursive: bool = False) -> list[TreeEntry]:
        r = self._raise_or_get(
            "/api/v1/tree",
            params={"path": path, "recursive": str(recursive).lower()},
        )
        return [TreeEntry.model_validate(item) for item in r.json()]

    def folder_exists(self, path: str) -> bool:
        r = self._raise_or_get("/api/v1/folder_exists", params={"path": path})
        return bool(r.json()["exists"])

    def inspect(self, path: str, *, resolved: bool = True) -> Descriptor | Folder:
        r = self._raise_or_get(
            "/api/v1/inspect",
            params={"path": path, "local": str(not resolved).lower()},
        )
        wrapped = InspectResult.model_validate(r.json())
        # The discriminator tells us which field holds the payload; assert
        # for mypy and to fail loudly if the server ever sends garbage.
        if wrapped.kind == "folder":
            assert wrapped.folder is not None
            return wrapped.folder
        assert wrapped.descriptor is not None
        return wrapped.descriptor

    # --- Writes ------------------------------------------------------------

    def deploy(self, path: str) -> Job:
        return self._machine_op("deploy", path)

    def undeploy(self, path: str) -> Job:
        return self._machine_op("undeploy", path)

    def start(self, path: str) -> Job:
        return self._machine_op("start", path)

    def stop(self, path: str) -> Job:
        return self._machine_op("stop", path)

    def load(
        self, document: DefinitionDocument, destination: str = "/"
    ) -> list[LoadResult]:
        # by_alias=True so the YAML aliases (`define hypervisors`, `import`,
        # `define templates`) round-trip; the server's model_validator
        # accepts both forms but the aliased one is canonical on the wire.
        r = self._raise_or_post(
            "/api/v1/load",
            params={"destination": destination},
            json=document.model_dump(by_alias=True),
        )
        return [LoadResult.model_validate(item) for item in r.json()]

    # --- Helpers -----------------------------------------------------------

    def _machine_op(self, op: str, path: str) -> Job:
        r = self._raise_or_post(f"/api/v1/{op}", params={"path": path})
        return Job.model_validate(r.json())

    def _raise_or_get(
        self, url: str, *, params: dict[str, str] | None = None
    ) -> httpx.Response:
        return self._send("GET", url, params=params)

    def _raise_or_post(
        self,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: object = None,
    ) -> httpx.Response:
        return self._send("POST", url, params=params, json=json)

    def _send(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: object = None,
    ) -> httpx.Response:
        """Single place where transport errors and 400s are translated.

        Three buckets: cannot even reach the server (``ConnectError`` →
        actionable message naming the URL and how to start the daemon);
        any other transport problem (timeout, broken pipe, etc.); and a
        response that did arrive but the daemon rejected (400 → carries
        the same ``OperationError`` shape as the in-process facade).
        """
        try:
            response = self._http.request(method, url, params=params, json=json)
        except httpx.ConnectError as e:
            raise OperationError(
                [
                    f"cannot reach the UnivOrch daemon at {self._http.base_url}. "
                    "Is it running? Try: 'univorchd' "
                    "(or './univorch.sh start' in production)."
                ]
            ) from e
        except httpx.RequestError as e:
            raise OperationError(
                [f"transport error talking to the daemon: {e!s}"]
            ) from e
        if response.status_code == 400:
            raise OperationError(response.json()["errors"])
        response.raise_for_status()
        return response
