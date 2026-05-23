"""Shared value types that cross the connector boundary.

The common vocabulary every connector (mock, VMware, Proxmox) speaks with the
orchestrator core. ``RuntimeState`` is the hypervisor power state, distinct from
the descriptor state owned by the orchestrator. ``VMInfo`` is the full snapshot
returned by ``get_info()``; ``get_status()`` returns only the ``RuntimeState``.
"""

from enum import StrEnum

from pydantic import BaseModel


class RuntimeState(StrEnum):
    """Power state of a VM as reported by the hypervisor."""

    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    UNKNOWN = "unknown"  # reachable, but state not determinable


class VMInfo(BaseModel):
    """Full snapshot of a VM as it exists in the hypervisor.

    ``id`` is opaque to the core: only the connector that produced it knows how
    to interpret it (a VMware MoRef, a Proxmox VMID, ...).
    """

    id: str
    name: str
    runtime_state: RuntimeState
    cpu: int | None = None
    memory_mb: int | None = None
    disk_gb: int | None = None
