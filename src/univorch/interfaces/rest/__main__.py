"""Daemon entry point: ``python -m univorch.interfaces.rest``.

Reads ``UNIVORCH_DB_PATH`` and ``UNIVORCH_PORT`` from the environment,
builds the ``OrchestratorService`` on a disk-backed TinyDB, and runs
uvicorn serving the REST app. This is the ``CMD`` of the production
Docker image (Sprint 3.1.c) — it is what keeps the container alive and
makes the public API reachable.

For development inside the devcontainer, the daemon can also be run
directly with ``uv run python -m univorch.interfaces.rest`` without
Docker.
"""

import os
from pathlib import Path

import uvicorn
from tinydb import TinyDB

from univorch.interfaces.rest.app import create_app
from univorch.persistence.tinydb.repositories import (
    DescriptorRepository,
    FolderRepository,
    JobRepository,
)
from univorch.service import OrchestratorService

_DEFAULT_DB = "/data/univorch.json"
_DEFAULT_PORT = 8080


def _build_service() -> OrchestratorService:
    """Wire the service over a disk-backed TinyDB at ``UNIVORCH_DB_PATH``."""
    db_path = os.environ.get("UNIVORCH_DB_PATH", _DEFAULT_DB)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    db = TinyDB(db_path)
    return OrchestratorService(
        FolderRepository(db),
        DescriptorRepository(db),
        JobRepository(db),
    )


def main() -> None:
    """Start uvicorn bound to ``0.0.0.0:UNIVORCH_PORT``.

    ``0.0.0.0`` inside the container is reachable from the host via the
    port mapping in ``docker-compose.yml``; uvicorn handles SIGTERM/SIGINT
    cleanly for ``docker stop`` and Ctrl-C.
    """
    port = int(os.environ.get("UNIVORCH_PORT", _DEFAULT_PORT))
    service = _build_service()
    app = create_app(service)
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
