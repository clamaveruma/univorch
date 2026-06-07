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

from posixpath import basename
from typing import Any

from fastapi import FastAPI
from nicegui import ui

from univorch.models import Descriptor
from univorch.service import OperationError, OrchestratorService, TreeEntry


def _build_tree_nodes(entries: list[TreeEntry]) -> list[dict[str, Any]]:
    """Turn a flat list of ``TreeEntry`` into a Quasar-style nested tree.

    Args:
        entries: descendants of ``/`` as returned by
            ``service.list_tree("/", recursive=True)``. Each entry carries
            its absolute materialized path; the function builds the
            parent/child links from the path itself.

    Returns:
        The list of top-level nodes (children of ``/``). Each node has
        ``id`` (absolute path), ``label`` (basename), ``kind`` (folder or
        descriptor), ``state`` (``DescriptorState`` or ``None``) and
        ``children`` (list of the same shape).
    """
    by_path: dict[str, dict[str, Any]] = {}
    for entry in sorted(entries, key=lambda e: e.path):
        by_path[entry.path] = {
            "id": entry.path,
            "label": basename(entry.path),
            "kind": entry.kind,
            "state": entry.state,
            "children": [],
        }

    roots: list[dict[str, Any]] = []
    for path, node in by_path.items():
        parent_path = path.rsplit("/", 1)[0] or "/"
        if parent_path == "/" or parent_path not in by_path:
            roots.append(node)
        else:
            by_path[parent_path]["children"].append(node)
    return roots


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
        with ui.header().classes("bg-primary text-white"):
            ui.label("UnivOrch").classes("text-h5 q-mr-md")
            ui.label("Universal VM orchestrator").classes("text-subtitle2 self-center")

        entries = service.list_tree("/", recursive=True)
        nodes = _build_tree_nodes(entries)
        descriptor_paths = {e.path for e in entries if e.kind == "descriptor"}

        with ui.card().classes("q-ma-md").style("min-width: 480px"):
            ui.label("Descriptor tree").classes("text-h6 q-mb-sm")
            if not nodes:
                ui.label("The tree is empty. Load a YAML definition first.").classes(
                    "text-grey-7"
                )
                return
            tree = ui.tree(
                nodes,
                label_key="label",
                children_key="children",
                node_key="id",
                on_select=lambda e: (
                    ui.navigate.to(f"/descriptor?path={e.value}")
                    if e.value in descriptor_paths
                    else None
                ),
            )
            tree.add_slot(
                "default-header",
                r"""
                <span :class="props.node.kind === 'folder'
                    ? 'text-blue-7 text-weight-medium'
                    : 'text-body1'">
                  <q-icon :name="props.node.kind === 'folder'
                    ? 'folder'
                    : props.node.state === 'deployed' ? 'check_box'
                    : props.node.state === 'broken' ? 'error'
                    : props.node.state === 'unreachable' ? 'cloud_off'
                    : 'crop_square'"
                    :class="props.node.kind === 'folder'
                      ? 'text-blue-7'
                      : props.node.state === 'deployed' ? 'text-primary'
                      : props.node.state === 'broken' ? 'text-negative'
                      : props.node.state === 'unreachable' ? 'text-warning'
                      : 'text-grey-6'"
                    class="q-mr-xs" />
                  {{ props.node.label }}
                  <q-badge v-if="props.node.kind === 'descriptor'"
                    :color="props.node.state === 'deployed' ? 'primary'
                      : props.node.state === 'broken' ? 'negative'
                      : props.node.state === 'unreachable' ? 'warning'
                      : 'grey-6'"
                    class="q-ml-sm">
                    {{ props.node.state }}
                  </q-badge>
                </span>
                """,
            )

    @ui.page("/descriptor")
    def descriptor_detail(path: str = "/") -> None:
        with ui.header().classes("bg-primary text-white"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat round"
            )
            ui.label("Descriptor detail").classes("text-h5 q-ml-sm")

        try:
            entity = service.inspect(path, resolved=True)
            descriptor_status = service.status(path)
        except OperationError as exc:
            with ui.card().classes("q-ma-md"):
                ui.label("Error").classes("text-h6 text-negative")
                ui.label("; ".join(exc.errors)).classes("text-body1")
            return

        if not isinstance(entity, Descriptor):
            with ui.card().classes("q-ma-md"):
                ui.label(f"{path} is a folder, not a descriptor.").classes(
                    "text-grey-7"
                )
            return

        rt = descriptor_status.runtime_state
        fields: list[tuple[str, str]] = [
            ("Path", entity.path),
            ("Description", entity.description or "—"),
            ("State", descriptor_status.state.value),
            ("Runtime state", rt.value if rt is not None else "—"),
            ("VM id (hypervisor)", descriptor_status.vm_id or "—"),
            ("Hypervisor", entity.hypervisor or "—"),
            ("Base VM", entity.base_vm or "—"),
            ("Template (use template)", entity.template or "—"),
            ("CPU", str(entity.cpu) if entity.cpu is not None else "—"),
            (
                "Memory (MB)",
                str(entity.memory_mb) if entity.memory_mb is not None else "—",
            ),
            ("Disk (GB)", str(entity.disk_gb) if entity.disk_gb is not None else "—"),
        ]

        with ui.card().classes("q-ma-md").style("min-width: 540px"):
            ui.label(basename(entity.path)).classes("text-h6")
            ui.label(
                "Effective definition (resolved through cascade + closure)"
            ).classes("text-grey-7 text-caption")
            ui.separator().classes("q-my-sm")
            with ui.grid(columns=2).classes("q-gutter-sm"):
                for label, value in fields:
                    ui.label(label).classes("text-grey-7")
                    ui.label(value).classes("text-body1")

    ui.run_with(
        app,
        title="UnivOrch",
        favicon="🟦",
        storage_secret="univorch-web-dev",
    )
