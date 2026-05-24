# UnivOrch — Internal diagrams

> This document collects the project's diagrams: the intended **deployment
> topology** (the general philosophy) and **as-built** views of the code, which
> grow with it and are updated roughly once a day. For the full intended design
> see [architecture.md](architecture.md).
>
> **Last updated:** 2026-05-24 — Sprint 1, connector contract + MockConnector + domain models.

---

## 1. Deployment topology

The general philosophy across hosts and tiers. This is the **target** scenario,
largely future — it shows how the pieces are meant to be deployed, not what is
built yet.

- **Tier 1 — clients:** admins/teachers (CLI + browser) and students (browser).
- **Tier 2 — orchestrator:** a single Linux host running UnivOrch in a Docker
  container; TinyDB persists on a host-managed named volume mounted into it.
- **Tier 3 — hypervisors + VMs:** VMware/Proxmox hosts running the VMs. The
  orchestrator's connectors talk to each hypervisor's management API.

```mermaid
flowchart LR
    subgraph Clients["Tier 1 — Client hosts"]
        Admin["Admin / teacher<br/>CLI + browser"]
        Student["Student<br/>browser"]
    end

    subgraph OrchHost["Tier 2 — Orchestrator host (Linux + Docker)"]
        subgraph Container["UnivOrch container"]
            API["FastAPI + uvicorn<br/>REST API + Web GUI :8080"]
            Core["Core<br/>service · jobs · connectors"]
        end
        Vol[("TinyDB<br/>named volume")]
    end

    subgraph HV1["Tier 3 — Hypervisor host (VMware ESXi)"]
        ESX["vSphere API"]
        VM1["VM"]
        VM2["VM"]
    end

    subgraph HV2["Tier 3 — Hypervisor host (Proxmox)"]
        PVE["Proxmox API"]
        VM3["VM"]
    end

    Admin -->|REST / HTTPS| API
    Student -->|Web GUI / HTTPS| API
    API --> Core
    Core --> Vol
    Core -->|vSphere SOAP| ESX
    Core -->|Proxmox REST| PVE
    ESX --- VM1
    ESX --- VM2
    PVE --- VM3
    Student -. direct access by IP .-> VM1
```

In **development and the demo**, the `MockConnector` stands in for the hypervisor
tier: no real ESXi/Proxmox hosts are needed, and the orchestrator runs directly
with `uv run` (no container).

---

## 2. Component architecture

How the pieces fit together inside the orchestrator. Most of the engine is still
pending; the connector subsystem and the domain models are the first implemented
parts.

**Legend:** solid = implemented · dashed/grey = designed, not yet implemented.

```mermaid
flowchart TD
    subgraph Interfaces
        CLI["CLI — cmd2"]:::pending
        Web["Web GUI — NiceGUI"]:::pending
    end

    Service["OrchestratorService (facade)"]:::pending
    Jobs["Jobs engine + Commands"]:::pending

    subgraph Persistence
        Repos["Repositories"]:::pending
        DB[("TinyDB — JSON file")]:::pending
    end

    subgraph Connectors
        ABC["HypervisorConnector (ABC)"]:::done
        Mock["MockConnector"]:::done
        VMware["VMwareConnector"]:::pending
        Proxmox["ProxmoxConnector"]:::pending
    end

    Models["Models — Folder, Descriptor"]:::done

    CLI --> Service
    Web --> Service
    Service --> Jobs
    Service --> Repos
    Jobs --> ABC
    Jobs --> Repos
    Repos --> DB
    Mock -.implements.-> ABC
    VMware -.implements.-> ABC
    Proxmox -.implements.-> ABC
    Service -.uses.-> Models
    Repos -.persist.-> Models

    classDef done fill:#cde7cd,stroke:#2e7d32,color:#000;
    classDef pending fill:#f0f0f0,stroke:#999,stroke-dasharray:4 4,color:#555;
```

---

## 3. Class diagram (implemented code)

The classes that exist today, in `connectors/` and `models.py`. Fields typed
`X | None` (`description`, `cpu`, `memory_mb`, `disk_gb`, `vm_id`) are optional
and default to `None`.

```mermaid
classDiagram
    class RuntimeState {
        <<enumeration>>
        RUNNING
        STOPPED
        PAUSED
        UNKNOWN
    }

    class CloneMode {
        <<enumeration>>
        LINKED
        FULL
    }

    class VMInfo {
        +id str
        +name str
        +runtime_state RuntimeState
        +cpu int
        +memory_mb int
        +disk_gb int
    }

    class HypervisorConnector {
        <<abstract>>
        +clone(source_id, name, mode) str
        +delete(vm_id)
        +start(vm_id)
        +stop(vm_id)
        +force_stop(vm_id)
        +pause(vm_id)
        +resume(vm_id)
        +get_status(vm_id) RuntimeState
        +get_info(vm_id) VMInfo
    }

    class MockConnector {
        +empty() MockConnector
        +with_demo_templates() MockConnector
        +with_templates(templates) MockConnector
        +deployed_vms() list~VMInfo~
    }

    class _MockVM {
        +id str
        +name str
        +runtime_state RuntimeState
        +metadata dict
    }

    class DescriptorState {
        <<enumeration>>
        PROVISIONED
        DEPLOYED
        BROKEN
        UNREACHABLE
    }

    class Folder {
        +path str
        +description str
    }

    class Descriptor {
        +path str
        +description str
        +hypervisor str
        +base_vm str
        +cpu int
        +memory_mb int
        +disk_gb int
        +state DescriptorState
        +vm_id str
    }

    HypervisorConnector <|-- MockConnector
    MockConnector "1" o-- "*" _MockVM : manages
    HypervisorConnector ..> VMInfo : returns
    HypervisorConnector ..> RuntimeState : returns
    HypervisorConnector ..> CloneMode : uses
    VMInfo ..> RuntimeState
    _MockVM ..> RuntimeState
    Descriptor ..> DescriptorState
```

---

## How to view

GitHub renders Mermaid automatically — open this file in the repository. In
VSCode, the *Markdown Preview Mermaid Support* extension renders it in the
preview pane. For the final thesis, export to PNG/SVG/PDF with `mermaid-cli` or a
screenshot of the rendered diagram.
