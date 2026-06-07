# UnivOrch — Internal diagrams

> This document follows the **C4 model** (Context → Container → Component → Code,
> plus a supplementary **Deployment** view). The higher levels (Context,
> Container, Deployment) are the intended design; the lower levels (Component,
> Code) are **as-built** and grow with the code. For the full narrative design see
> [architecture.md](architecture.md).
>
> **Terminology note:** a C4 *container* is any independently runnable unit (a
> service, a database, the CLI) — **not** a Docker container. UnivOrch's daemon
> happens to run in a Docker container, but the word means different things.
>
> **Rendering note:** the diagrams follow the C4 *model*; for reliable layout
> they are drawn as Mermaid flowcharts and class diagrams (with C4 stereotypes
> like «Person» and «Container»), not Mermaid's experimental native C4 renderer.
>
> **Last updated:** 2026-06-07 — Sprint 3 closed. The daemon (`univorchd`) and
> the CLI client (`univorch`) are now two distinct binaries; everything goes
> through the REST API. The Resolver, connector type registry and live-session
> pool are in place. Real hypervisor connectors and the web GUI are still
> pending.

---

## 1. Context (C4 level 1)

The big picture: who uses UnivOrch and which external systems it talks to.

```mermaid
flowchart TB
    admin["«Person»<br/>Admin / Teacher<br/>Defines the tree, deploys and manages VMs"]:::person
    student["«Person»<br/>Student<br/>Operates and uses assigned VMs"]:::person
    integrator["«Person/System»<br/>External integration<br/>CI/CD, GitOps, scripts"]:::person
    univorch["«System»<br/>UnivOrch<br/>Universal VM orchestrator"]:::system
    vmware["«External System»<br/>VMware vSphere"]:::ext
    proxmox["«External System»<br/>Proxmox VE"]:::ext

    admin -->|"Manages / deploys (CLI, Web)"| univorch
    student -->|"Operates own VMs (Web)"| univorch
    integrator -->|"Automates (REST /api/v1)"| univorch
    univorch -->|"Clones and controls VMs (vSphere SOAP)"| vmware
    univorch -->|"Clones and controls VMs (Proxmox REST)"| proxmox
    student -.->|"Uses the VM (SSH / RDP / console)"| vmware

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef system fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef ext fill:#999999,color:#fff,stroke:#6b6b6b;
```

---

## 2. Containers (C4 level 2)

The independently runnable units that make up UnivOrch. **Note**: the daemon
(`univorchd`) and the CLI (`univorch`) are now two separate binaries, both
published as entry points of the same Python package. Every client speaks
HTTP to the daemon; nothing embeds the orchestrator in-process anymore.

```mermaid
flowchart TB
    admin["«Person»<br/>Admin / Teacher"]:::person
    student["«Person»<br/>Student"]:::person
    integrator["«Person/System»<br/>External integration"]:::person

    subgraph sys["UnivOrch system"]
        cli["«Container»<br/>CLI — univorch<br/>Python, cmd2 + httpx"]:::container
        web["«Container»<br/>Web GUI (Sprint 4)<br/>Python, NiceGUI"]:::container
        api["«Container»<br/>REST daemon — univorchd<br/>Python, FastAPI / uvicorn"]:::container
        db[("«Database»<br/>TinyDB (PoC) / MongoDB (future)<br/>JSON file or document store")]:::db
    end

    hv["«External System»<br/>Hypervisors (VMware / Proxmox / Mock)"]:::ext

    admin -->|"Uses (terminal)"| cli
    admin -->|"Uses (HTTPS)"| web
    student -->|"Uses (HTTPS)"| web
    integrator -->|"REST / HTTPS"| api
    cli -->|"REST /api/v1/*"| api
    web -->|"REST /api/v1/*"| api
    api -->|"Reads / writes"| db
    api -->|"Clones and controls (SOAP / REST / in-memory)"| hv

    classDef person fill:#08427b,color:#fff,stroke:#052e56;
    classDef container fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef db fill:#1168bd,color:#fff,stroke:#0b4884;
    classDef ext fill:#999999,color:#fff,stroke:#6b6b6b;
```

---

## 3. Deployment (C4 supplementary view)

How the containers map onto hosts and tiers. This is the **real** topology
since Sprint 3: a single Linux host running the daemon in a Docker container,
with the CLI either driven from the same container (via `docker exec`) or
from any external host that can reach the REST port.

- **Tier 1 — clients:** admins/teachers (CLI or browser) and students (browser).
- **Tier 2 — orchestrator host:** one Linux machine running Docker. The
  `univorchd` daemon lives in a container; the TinyDB JSON file persists on a
  named volume.
- **Tier 3 — hypervisor hosts + VMs:** VMware and Proxmox hosts running the
  VMs the orchestrator clones and controls.

```mermaid
flowchart LR
    subgraph Clients["Tier 1 — Client hosts"]
        Admin["Admin / teacher<br/>terminal + browser"]
        Student["Student<br/>browser"]
        Integ["External integration<br/>scripts, CI/CD"]
    end

    subgraph OrchHost["Tier 2 — Orchestrator host (Linux + Docker)"]
        subgraph Container["univorchd container (univorch image, ghcr.io)"]
            REST["FastAPI + uvicorn — REST :8080"]
            Core["Core<br/>service · resolver · jobs · pool"]
        end
        Vol[("TinyDB JSON<br/>named volume univorch_data")]
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

    Admin -->|REST / HTTPS<br/>or docker exec → CLI in container| REST
    Student -->|Web GUI / HTTPS| REST
    Integ -->|REST /api/v1| REST
    REST --> Core
    Core --> Vol
    Core -->|vSphere SOAP| ESX
    Core -->|Proxmox REST| PVE
    ESX --- VM1
    ESX --- VM2
    PVE --- VM3
    Student -. direct access by IP .-> VM1
```

In the **mock-driven demo**, the `MockConnector` replaces both hypervisor
tiers: the daemon runs the same Docker image, only the connector type
declared by the tree changes.

---

## 4. Components (C4 level 3) — as-built

Modules inside the daemon. After Sprint 3 the daemon (`univorchd`),
the CLI (`univorch`), the Resolver, the connector type registry and the
live-session pool are all in place. The web GUI and the real hypervisor
connectors are still pending.

**Legend:** solid green = implemented · dashed/grey = designed, not yet implemented.

```mermaid
flowchart TD
    subgraph Clients["Client binaries"]
        CLI["univorch CLI — cmd2 + argparse"]:::done
        Web["Web GUI — NiceGUI (Sprint 4)"]:::pending
        TA["Teaching app — layer 2 (Sprint 5+)"]:::pending
    end

    subgraph RESTLayer["REST boundary (inside univorchd)"]
        Http["HttpServiceClient<br/>(inside the CLI)"]:::done
        App["FastAPI app — create_app(service)"]:::done
        Main["__main__ — uvicorn entry point"]:::done
    end

    subgraph Core["Core (inside univorchd)"]
        Service["OrchestratorService (facade)"]:::done
        Resolver["Resolver<br/>cascade + lexical closure"]:::done
        Walker["_find_resource<br/>generic walker"]:::done
        Pool["Connection pool<br/>path → live connector"]:::done
        Registry["CONNECTOR_TYPES<br/>type → class"]:::done
        Parser["YAML parser — ruamel.yaml + Pydantic"]:::done
        Jobs["Jobs engine + Commands"]:::done
    end

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

    Models["Models — DefinitionDocument,<br/>Folder, Descriptor, Job,<br/>HypervisorDef, VMTemplateDef"]:::done

    CLI --> Http
    Http -->|HTTP /api/v1/*| App
    Web -.HTTP.-> App
    TA -.HTTP.-> App
    App --> Service
    Main --> App
    Service --> Resolver
    Service --> Jobs
    Service --> Pool
    Resolver --> Walker
    Pool --> Registry
    Service --> Parser
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

The classes that exist after Sprint 3. Optional fields (typed `X | None`,
default `None`) are omitted from the diagrams to keep them readable. Two
views, because one diagram with everything is unreadable: **5.1 Domain +
Connectors** and **5.2 Engine, Service, REST boundary**.

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
        +description str
        +imports list~str~
        +hypervisors dict~str, HypervisorDef~
        +vm_templates dict~str, VMTemplateDef~
    }
    class Descriptor {
        +path TreePath
        +hypervisor str
        +base_vm str
        +template str
        +state DescriptorState
        +vm_id str
    }
    class HypervisorDef {
        +connector_type str  // type:
        +description str
    }
    class VMTemplateDef {
        +hypervisor str  // use hypervisor:
        +base_vm str
        +cpu int
        +memory_mb int
        +disk_gb int
    }
    class FolderDef {
        +description str
        +imports list~str~
        +hypervisors dict~str, HypervisorDef~
        +vm_templates dict~str, VMTemplateDef~
        +folders dict~str, FolderDef~
        +descriptors dict~str, DescriptorDef~
    }
    class DescriptorDef {
        +hypervisor str
        +base_vm str
        +template str
        +cpu int
        +memory_mb int
        +disk_gb int
    }
    class DefinitionDocument {
        +kind: "definition"
        +version str
        +folders dict~str, FolderDef~
        +descriptors dict~str, DescriptorDef~
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
        -_templates set~str~
        -_deployed dict
        +empty() MockConnector
        +with_templates(templates) MockConnector
        +deployed_vms() list~VMInfo~
    }

    Descriptor ..> DescriptorState
    Job ..> JobStatus
    Job ..> OperationType
    Folder o-- HypervisorDef
    Folder o-- VMTemplateDef
    FolderDef o-- HypervisorDef
    FolderDef o-- VMTemplateDef
    FolderDef o-- DescriptorDef
    FolderDef o-- FolderDef : nested
    DefinitionDocument o-- FolderDef
    DefinitionDocument o-- DescriptorDef
    HypervisorConnector <|-- MockConnector
    HypervisorConnector ..> VMInfo : returns
    HypervisorConnector ..> RuntimeState : returns
    HypervisorConnector ..> CloneMode : uses
    VMInfo ..> RuntimeState
```

### 5.2 Engine, service & REST boundary

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

    class OrchestratorAPI {
        <<Protocol>>
        +deploy(path) Job
        +undeploy(path) Job
        +start(path) Job
        +stop(path) Job
        +status(path) DescriptorStatus
        +list_tree(path, recursive) list~TreeEntry~
        +folder_exists(path) bool
        +inspect(path, resolved) Descriptor or Folder
        +load(document, destination) list~LoadResult~
    }
    class OrchestratorService {
        -_connector_types dict
        -_connection_pool dict
        +deploy(path) Job
        +undeploy(path) Job
        +start(path) Job
        +stop(path) Job
        +status(path) DescriptorStatus
        +list_tree(path, recursive) list~TreeEntry~
        +folder_exists(path) bool
        +inspect(path, resolved) Descriptor or Folder
        +load(document, destination) list~LoadResult~
        -_resolve_hypervisor(original, resolved, origin) HypervisorConnector
    }
    class HttpServiceClient {
        -_http httpx.Client
        +deploy(path) Job
        +undeploy(path) Job
        +start(path) Job
        +stop(path) Job
        +status(path) DescriptorStatus
        +list_tree(path, recursive) list~TreeEntry~
        +folder_exists(path) bool
        +inspect(path, resolved) Descriptor or Folder
        +load(document, destination) list~LoadResult~
        -_send(method, url, ...) Response
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
    class LoadResult {
        +path str
        +ok bool
        +message str
    }
    class InspectResult {
        +kind: "folder" | "descriptor"
        +folder Folder
        +descriptor Descriptor
    }

    class create_app {
        <<function>>
        +create_app(service) FastAPI
    }
    class univorchd {
        <<entry point>>
        +main()
    }

    class UnivOrchShell {
        <<cmd2.Cmd>>
        -_service OrchestratorAPI
        -_remote str
        +do_cd(args)
        +do_pwd(args)
        +do_list(args)
        +do_tree(args)
        +do_inspect(args)
        +do_deploy(args)
        +do_undeploy(args)
        +do_start(args)
        +do_stop(args)
        +do_status(args)
        +do_load(args)
        +do_connect(args)
    }

    Command <|-- DeployCommand
    Command <|-- UndeployCommand
    Command <|-- StartCommand
    Command <|-- StopCommand
    Command <|-- CreateFolderCommand
    Command <|-- CreateDescriptorCommand

    OrchestratorService ..|> OrchestratorAPI : implements (structural)
    HttpServiceClient ..|> OrchestratorAPI : implements (structural)

    OrchestratorService --> JobEngine : owns
    OrchestratorService --> FolderRepository
    OrchestratorService --> DescriptorRepository
    OrchestratorService --> JobRepository
    OrchestratorService ..> OperationError : raises
    OrchestratorService ..> DescriptorStatus : returns
    OrchestratorService ..> TreeEntry : returns
    OrchestratorService ..> LoadResult : returns
    OrchestratorService ..> HypervisorConnector : pool of

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

    create_app --> OrchestratorService : injects
    create_app ..> InspectResult : wraps inspect
    univorchd --> create_app
    univorchd ..> OrchestratorService : composes

    HttpServiceClient ..> OperationError : raises on 400 or ConnectError
    UnivOrchShell --> OrchestratorAPI
    UnivOrchShell ..> HttpServiceClient : default backend
```

---

## How to view

GitHub renders Mermaid automatically — open this file in the repository. In
VSCode, the *Markdown Preview Mermaid Support* extension renders it in the
preview pane. The thesis embeds these diagrams as PDF figures generated from
the Mermaid sources with `mermaid-cli` (`mmdc`); see
`docs/memoria/figures/mermaid/` and the CI workflow for the build pipeline.
