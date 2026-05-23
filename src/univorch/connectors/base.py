"""Hypervisor connector contract.

``HypervisorConnector`` is the Abstract Base Class (ABC) that every connector
implements (mock, VMware, Proxmox). An ABC defines a contract of methods a
subclass must implement; Python refuses to instantiate a subclass that leaves
any of them undefined, so an incomplete connector fails at construction rather
than at the first call. 
The connector exposes only hypervisor primitives and identifies VMs by an opaque
id. ``deploy``/``undeploy`` are orchestrator concepts built on ``clone``/
``delete``, not connector methods.
"""

from abc import ABC, abstractmethod

from univorch.connectors.types import CloneMode, RuntimeState, VMInfo


class HypervisorConnector(ABC):
    """Contract implemented by every hypervisor connector.

    Unless noted otherwise, every method raises ``ValueError`` if the id is
    unknown and ``ConnectionError`` if the hypervisor is unreachable.
    """

    @abstractmethod
    def clone(
        self, source_id: str, name: str, mode: CloneMode = CloneMode.LINKED
    ) -> str:
        """Clone template ``source_id`` into a new VM named ``name``; return its id.

        Raises:
            NotImplementedError: If mode is FULL (not supported in v1).
        """

    @abstractmethod
    def delete(self, vm_id: str) -> None:
        """Delete the VM and its virtual disk."""

    @abstractmethod
    def start(self, vm_id: str) -> None:
        """Power on the VM (idempotent)."""

    @abstractmethod
    def stop(self, vm_id: str) -> None:
        """Gracefully power off the VM (idempotent)."""

    @abstractmethod
    def force_stop(self, vm_id: str) -> None:
        """Forcibly power off the VM, like pulling the plug (idempotent)."""

    @abstractmethod
    def pause(self, vm_id: str) -> None:
        """Suspend the VM (idempotent)."""

    @abstractmethod
    def resume(self, vm_id: str) -> None:
        """Resume the VM (idempotent)."""

    @abstractmethod
    def get_status(self, vm_id: str) -> RuntimeState:
        """Return the VM's power state — cheap, frequent query."""

    @abstractmethod
    def get_info(self, vm_id: str) -> VMInfo:
        """Return a full snapshot of the VM."""
