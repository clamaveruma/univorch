# UnivOrch — Internal diagrams

> This document follows the **C4 model** (Context → Container → Component → Code,
> plus a supplementary **Deployment** view). The higher levels (Context,
> Container, Deployment) are the intended design; the lower levels (Component,
> Code) are **as-built** and grow with the code. For the full narrative design see
> [architecture.md](architecture.md).
>
> **Terminology note:** a C4 *container* is any independently runnable unit (a
> service, a database, the CLI) — **not** a Docker container. UnivOrch's service
> happens to run in a Docker container, but the word means different things.
>
> **Mermaid note:** Context and Container use Mermaid's native C4 renderer, which
> is experimental; if they render poorly they can be redrawn as plain flowcharts.
>
> **Last updated:** 2026-05-24 — Sprint 1, connector contract + MockConnector + domain models.

---

## 1. Context (C4 level 1)

The big picture: who uses UnivOrch and which external systems it talks to.

```mermaid
C4Context
    title System context — UnivOrch

    Person(admin, "Admin / Teacher", "Defines the tree, deploys and manages VMs")
    Person(student, "Student", "Starts, stops and uses assigned VMs")

    System(univorch, "UnivOrch", "Universal VM orchestrator")

    System_Ext(vmware, "VMware vSphere", "Hypervisor platform")
    System_Ext(proxmox, "Proxmox VE", "Hypervisor platform")

    Rel(admin, univorch, "Manages / deploys", "REST, Web")
    Rel(student, univorch, "Operates own VMs", "Web")
    Rel(univorch, vmware, "Clones & controls VMs", "vSphere SOAP")
    Rel(univorch, proxmox, "Clones & controls VMs", "Proxmox REST")
    Rel(student, vmware, "Uses the VM", "SSH / RDP / console")
```

---

## 2. Containers (C4 level 2)

The independently runnable units that make up UnivOrch.

```mermaid
C4Container
    title Containers — UnivOrch

    Person(admin, "Admin / Teacher")
    Person(student, "Student")

    System_Boundary(s1, "UnivOrch") {
        Container(cli, "CLI", "Python · cmd2 + httpx", "Scriptable command line")
        Container(web, "Web GUI", "Python · NiceGUI", "Browser interface for all roles")
        Container(api, "Orchestrator service", "Python · FastAPI / uvicorn", "Facade, jobs, connectors")
        ContainerDb(db, "TinyDB", "JSON file", "Folders, descriptors, jobs, sessions")
    }

    System_Ext(hv, "Hypervisors", "VMware / Proxmox")

    Rel(admin, cli, "Uses")
    Rel(admin, web, "Uses", "HTTPS")
    Rel(student, web, "Uses", "HTTPS")
    Rel(cli, api, "Calls", "REST / HTTPS")
    Rel(web, api, "Calls")
    Rel(api, db, "Reads / writes")
    Rel(api, hv, "Clones & controls VMs", "SOAP / REST")
```

---

## 3. Deployment (C4 supplementary view)

How the containers map onto hosts and tiers. This is the **target** topology —
largely future; it shows how the pieces are meant to be deployed.

- **Tier 1 — clients:** admins/teachers (CLI + browser) and students (browser).
- **Tier 2 — orchestrator:** one Linux host running UnivOrch in a Docker
  container; TinyDB persists on a host-managed named volume mounted into it.
- **Tier 3 — hypervisors + VMs:** VMware/Proxmox hosts running the VMs; the
  connectors talk to each hypervisor's management API.

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

## 4. Components (C4 level 3) — as-built

Modules inside the orchestrator. Most of the engine is still pending; the
connector subsystem and the domain models are the first implemented parts.

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

## 5. Code (C4 level 4) — as-built

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
