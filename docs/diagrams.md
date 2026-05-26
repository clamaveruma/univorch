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
> **Rendering note:** the diagrams follow the C4 *model*; for reliable layout
> they are drawn as Mermaid flowcharts and class diagrams (with C4 stereotypes
> like «Person» and «Container»), not Mermaid's experimental native C4 renderer.
>
> **Last updated:** 2026-05-26 — Sprint 1 closed: connectors, persistence, Jobs
> engine + Commands, `OrchestratorService` facade, YAML parser, and cmd2-based
> CLI with argparse help. Web GUI and real hypervisor connectors still pending.

---

## 1. Context (C4 level 1)

The big picture: who uses UnivOrch and which external systems it talks to.

```mermaid
flowchart TB
    admin["«Person»<br/>Admin / Teacher<br/>Defines the tree, deploys and manages VMs"]:::person
    student["«Person»<br/>Student<br/>Operates and uses assigned VMs"]:::person
    univorch["«System»<br/>UnivOrch<br/>Universal VM orchestrator"]:::system
    vmware["«External System»<br/>VMware vSphere"]:::ext
    proxmox["«External System»<br/>Proxmox VE"]:::ext

    admin -->|"Manages / deploys (REST, Web)"| univorch
    student -->|"Operates own VMs (Web)"| univorch
    univorch -->|"Clones and controls VMs (vSphere SOAP)"| vmware
    univorch -->|"Clones and controls VMs (Proxmox REST)"| proxmox
    student -.->|"Uses the VM (SSH / RDP / console)"| vmware

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef ext fill:#999999,color:#fff,stroke:#6b6b6b;
```

---

## 2. Containers (C4 level 2)

The independently runnable units that make up UnivOrch.

```mermaid
flowchart TB
    admin["«Person»<br/>Admin / Teacher"]:::person
    student["«Person»<br/>Student"]:::person

    subgraph sys["UnivOrch system"]
        cli["«Container»<br/>CLI<br/>Python, cmd2 + httpx"]:::container
        web["«Container»<br/>Web GUI<br/>Python, NiceGUI"]:::container
        api["«Container»<br/>Orchestrator service<br/>Python, FastAPI / uvicorn"]:::container
        db[("«Database»<br/>TinyDB<br/>JSON file")]:::db
    end

    hv["«External System»<br/>Hypervisors (VMware / Proxmox)"]:::ext

    admin -->|"Uses"| cli
    admin -->|"Uses (HTTPS)"| web
    student -->|"Uses (HTTPS)"| web
    cli -->|"Calls (REST / HTTPS)"| api
    web -->|"Calls"| api
    api -->|"Reads / writes"| db
    api -->|"Clones and controls (SOAP / REST)"| hv

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef container fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef db fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef ext fill:#999999,color:#fff,stroke:#6b6b6b;
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

Modules inside the orchestrator. After Sprint 1, the engine, persistence and the
CLI are in place; the web GUI and the real hypervisor connectors are still pending.

**Legend:** solid green = implemented · dashed/grey = designed, not yet implemented.

```mermaid
flowchart TD
    subgraph Interfaces
        CLI["CLI — cmd2 + argparse"]:::done
        Web["Web GUI — NiceGUI"]:::pending
    end

    Service["OrchestratorService (facade)"]:::done
    Parser["YAML parser — ruamel.yaml + Pydantic"]:::done
    Jobs["Jobs engine + Commands"]:::done

    subgraph Persistence
        Repos["Repositories<br/>Folder · Descriptor · Job"]:::done
        DB[("TinyDB — JSON file")]:::done
    end

    subgraph Connectors
        ABC["HypervisorConnector (ABC)"]:::done
        Mock["MockConnector"]:::done
        VMware["VMwareConnector"]:::pending
        Proxmox["ProxmoxConnector"]:::pending
    end

    Models["Models — Folder, Descriptor,<br/>Job, ApplyDocument, …"]:::done
    Resolver["Resolver (cascade inheritance)"]:::pending

    CLI --> Service
    Web --> Service
    CLI --> Parser
    Service --> Jobs
    Service --> Repos
    Service -.uses (Sprint 2).-> Resolver
    Jobs --> ABC
    Jobs --> Repos
    Repos --> DB
    Mock -.implements.-> ABC
    VMware -.implements.-> ABC
    Proxmox -.implements.-> ABC
    Service -.uses.-> Models
    Parser -.produces.-> Models
    Repos -.persist.-> Models

    classDef done fill:#cde7cd,stroke:#2e7d32,color:#000;
    classDef pending fill:#f0f0f0,stroke:#999,stroke-dasharray:4 4,color:#555;
```

---

## 5. Code (C4 level 4) — as-built

The classes that exist after Sprint 1. Optional fields (typed `X | None`,
default `None`) are omitted from the diagrams to keep them readable. Two views,
because one diagram with everything is unreadable: **5.1 Domain + Connectors**
and **5.2 Engine, Persistence, Service, CLI**.

### 5.1 Domain models & connectors

```mermaid
classDiagram
    class DescriptorState {
        <<enumeration>>
        PROVISIONED
        DEPLOYED
        BROKEN
        UNREACHABLE
    }
    class JobStatus {
        <<enumeration>>
        PENDING
        RUNNING
        COMPLETED
        FAILED
    }
    class OperationType {
        <<enumeration>>
        DEPLOY
        UNDEPLOY
        START
        STOP
        CREATE_FOLDER
        CREATE_DESCRIPTOR
    }
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

    class Folder {
        +path TreePath
    }
    class Descriptor {
        +path TreePath
        +hypervisor str
        +base_vm str
        +state DescriptorState
        +vm_id str
    }
    class Job {
        +id str
        +operation_type OperationType
        +target str
        +status JobStatus
        +created_at datetime
        +finished_at datetime
        +message str
    }
    class ApplyDocument {
        +kind: "apply"
        +version str
        +folders list~Folder~
        +descriptors list~Descriptor~
    }

    class VMInfo {
        +id str
        +name str
        +runtime_state RuntimeState
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

    Descriptor ..> DescriptorState
    Job ..> JobStatus
    Job ..> OperationType
    ApplyDocument o-- Folder
    ApplyDocument o-- Descriptor
    HypervisorConnector <|-- MockConnector
    MockConnector "1" o-- "*" _MockVM : manages
    HypervisorConnector ..> VMInfo : returns
    HypervisorConnector ..> RuntimeState : returns
    HypervisorConnector ..> CloneMode : uses
    VMInfo ..> RuntimeState
    _MockVM ..> RuntimeState
```

### 5.2 Engine, persistence, service & CLI

```mermaid
classDiagram
    class Command {
        <<abstract>>
        +operation_type OperationType
        +target str
        +validate() list~str~
        +execute() str
    }
    class DeployCommand
    class UndeployCommand
    class StartCommand
    class StopCommand
    class CreateFolderCommand
    class CreateDescriptorCommand

    class JobEngine {
        +run(command) Job
    }

    class FolderRepository {
        +save(folder)
        +get(path) Folder
        +exists(path) bool
        +subtree(prefix) list~Folder~
        +delete(path)
    }
    class DescriptorRepository {
        +save(descriptor)
        +get(path) Descriptor
        +exists(path) bool
        +subtree(prefix) list~Descriptor~
        +delete(path)
    }
    class JobRepository {
        +save(job)
        +get(id) Job
        +find_by_target(target) list~Job~
        +find_by_status(status) list~Job~
    }

    class OrchestratorService {
        +deploy(path) Job
        +undeploy(path) Job
        +start(path) Job
        +stop(path) Job
        +status(path) DescriptorStatus
        +list_tree(path, recursive) list~TreeEntry~
        +folder_exists(path) bool
        +apply(document) list~ApplyResult~
    }
    class OperationError {
        +errors list~str~
    }
    class DescriptorStatus {
        +path str
        +state DescriptorState
        +runtime_state RuntimeState
        +vm_id str
    }
    class TreeEntry {
        +path str
        +kind: "folder" | "descriptor"
        +state DescriptorState
    }
    class ApplyResult {
        +path str
        +ok bool
        +message str
    }

    class UnivOrchShell {
        <<cmd2.Cmd>>
        +do_cd(args)
        +do_pwd(args)
        +do_list(args)
        +do_ls(args)
        +do_tree(args)
        +do_deploy(args)
        +do_undeploy(args)
        +do_start(args)
        +do_stop(args)
        +do_status(args)
        +do_apply(args)
    }

    Command <|-- DeployCommand
    Command <|-- UndeployCommand
    Command <|-- StartCommand
    Command <|-- StopCommand
    Command <|-- CreateFolderCommand
    Command <|-- CreateDescriptorCommand

    OrchestratorService --> JobEngine : owns
    OrchestratorService --> FolderRepository
    OrchestratorService --> DescriptorRepository
    OrchestratorService --> JobRepository
    OrchestratorService ..> OperationError : raises
    OrchestratorService ..> DescriptorStatus : returns
    OrchestratorService ..> TreeEntry : returns
    OrchestratorService ..> ApplyResult : returns

    JobEngine --> JobRepository
    DeployCommand --> DescriptorRepository
    DeployCommand --> HypervisorConnector
    UndeployCommand --> DescriptorRepository
    UndeployCommand --> HypervisorConnector
    StartCommand --> DescriptorRepository
    StartCommand --> HypervisorConnector
    StopCommand --> DescriptorRepository
    StopCommand --> HypervisorConnector
    CreateFolderCommand --> FolderRepository
    CreateDescriptorCommand --> DescriptorRepository
    CreateDescriptorCommand --> FolderRepository

    UnivOrchShell --> OrchestratorService
```

---

## How to view

GitHub renders Mermaid automatically — open this file in the repository. In
VSCode, the *Markdown Preview Mermaid Support* extension renders it in the
preview pane. For the final thesis, export to PNG/SVG/PDF with `mermaid-cli` or a
screenshot of the rendered diagram.
