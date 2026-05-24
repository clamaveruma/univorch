# UnivOrch — Internal diagrams

> **As-built view.** These diagrams reflect the **current code** and grow with it,
> updated roughly once a day. For the intended end-state design see
> [architecture.md](architecture.md); this document shows what actually exists.
>
> **Last updated:** 2026-05-24 — Sprint 1, connector contract + MockConnector + domain models.

**Legend:** solid = implemented · dashed/grey = designed, not yet implemented.

---

## 1. Component architecture

How the pieces fit together. Most of the engine is still pending; the connector
subsystem and the domain models are the first implemented parts.

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

## 2. Class diagram (implemented code)

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
