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

_CONTAINER_DATA_DIR = Path("/data")
_DEFAULT_PORT = 8080


def _default_db_path(container_dir: Path = _CONTAINER_DATA_DIR) -> Path:
    """Pick a sensible TinyDB path when ``UNIVORCH_DB_PATH`` is not set.

    Inside the production container, ``/data`` is the volume mount and the
    natural place — the docker-compose file binds the named volume there.
    Outside (devcontainer, host without Docker, CI runner…), ``/data`` does
    not exist and writing to it errors out; in that case fall back to the
    XDG Base Directory Specification: ``$XDG_DATA_HOME/univorch/db.json``
    (typically ``~/.local/share/univorch/db.json`` on Linux).

    Pure function: takes ``container_dir`` as a parameter so the choice is
    testable without touching the real filesystem at /data.
    """
    if container_dir.is_dir() and os.access(container_dir, os.W_OK):
        return container_dir / "univorch.json"
    xdg = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(xdg) / "univorch" / "db.json"


def _build_service() -> OrchestratorService:
    """Wire the service over a disk-backed TinyDB at ``UNIVORCH_DB_PATH``."""
    env = os.environ.get("UNIVORCH_DB_PATH")
    db_path = Path(env) if env else _default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
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
