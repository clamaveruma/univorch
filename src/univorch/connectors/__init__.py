"""Hypervisor connectors.

Each connector implements the HypervisorConnector ABC (base.py) and
talks to a specific hypervisor (VMware, Proxmox) or to the mock.
The orchestrator core only depends on the ABC — never on a concrete connector.

CONNECTOR_TYPES maps each ``type:`` name a YAML can declare (inside
``define hypervisors:``) to its connector class. A new connector is added in
two lines: an import and an entry here. The service receives this dict and
uses it to validate types at load time and to instantiate live sessions on
demand (Sprint 2 Pieza 3; DEC-029). Third-party connectors via Python entry
points are noted as future extension in DEC-029, not v1.
"""

from univorch.connectors.base import HypervisorConnector
from univorch.connectors.mock import MockConnector

CONNECTOR_TYPES: dict[str, type[HypervisorConnector]] = {
    "mock": MockConnector,
    # "vmware": VMwareConnector,    # when the connector lands
    # "proxmox": ProxmoxConnector,  # when the connector lands
}
