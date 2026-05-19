"""Hypervisor connectors.

Each connector implements the HypervisorConnector ABC (base.py) and
talks to a specific hypervisor (VMware, Proxmox) or to the mock.
The orchestrator core only depends on the ABC — never on a concrete connector.
"""
