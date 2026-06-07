"""Web GUI built with NiceGUI — Sprint 4 (read-only v1).

The web interface runs **inside** the same process as the FastAPI daemon:
NiceGUI's ``ui.run_with(fastapi_app, ...)`` mounts its own ASGI sub-app
on the daemon's uvicorn, so a single port serves both ``/api/v1/*`` and
the web pages. This is a deliberate departure from the "every client is
an HTTP client" rule of Sprint 3.2 (DEC-031): the web is not an external
client of UnivOrch, it is part of the daemon itself. External clients
(CLI, future Teaching app, third-party integrations) still go through
the REST API.

The page handlers receive the service via closure of ``mount_web``,
not via DI on each request: NiceGUI's page decorators run at registration
time and capture the service reference once.
"""

from fastapi import FastAPI
from nicegui import ui

from univorch.service import OrchestratorService


def mount_web(app: FastAPI, service: OrchestratorService) -> None:
    """Register NiceGUI pages on ``app`` and mount them at ``/``.

    Args:
        app: the FastAPI app of the daemon, already configured with the
            REST routes under ``/api/v1/*``.
        service: the live orchestrator facade. Page handlers close over
            it for as long as the process is alive.

    Mounts NiceGUI at the root path; the REST API stays untouched under
    ``/api/v1/*`` because NiceGUI only claims the routes its own pages
    define.
    """

    @ui.page("/")
    def index() -> None:
        ui.label("UnivOrch").classes("text-h3 text-primary")
        ui.label("Universal VM orchestrator — read-only web view").classes(
            "text-subtitle1 text-grey-7"
        )
        ui.separator()

        entries = service.list_tree("/", recursive=True)
        ui.label(f"Tree contains {len(entries)} items.").classes("q-mt-md")
        ui.label("Detailed views: W2 (tree), W3 (descriptor).").classes("text-grey-7")

    ui.run_with(
        app,
        title="UnivOrch",
        favicon="🟦",
        storage_secret="univorch-web-dev",
    )
