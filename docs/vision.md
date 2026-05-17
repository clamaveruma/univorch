# UniVorch — Product Vision

> Phase 1 deliverable: Problem Definition  
> Project: A virtual machine orchestrator for teaching and research environments. Proof of concept.

---

## 1. Problem

In the computer science school, virtual machines (VMs) are used for practical lab work across many courses. Each subject requires a set of VMs per student, all derived from base templates defined by the professor.

Today, the entire process is handled manually by the system administrator:

- A professor defines the VMs for a subject and requests deployment for every student.
- The administrator runs custom scripts, tightly coupled to VMware, to clone base VMs and assign IPs.
- IP addresses are managed through a workaround: the MAC address encodes the desired IP, which the DHCP server then assigns. This works, but it is fragile and hard to maintain.
- If a student stops a VM or corrupts it, the administrator must intervene to restart or recreate it.
- When a new student joins after deployment, the process must be repeated partially by hand.

The result is a heavy administrative burden, no autonomy for students or professors, and a system that breaks whenever the hypervisor platform changes.

**Core problems:**

- The administrator is the single point of contact for all VM operations, including trivial ones.
- Students cannot manage their own VMs: start, stop, restore from template.
- Scripts are tied to a specific hypervisor; a platform change means rewriting everything.
- There is no unified interface for non-technical users.
- Scaling is linear: more subjects and students mean proportionally more admin work.

---

## 2. Context

The system operates in an academic environment with the following characteristics:

- Multiple subjects running in parallel, each with its own set of VMs per student.
- A small number of administrators managing all hypervisors.
- Professors who understand their subject but are not hypervisor experts.
- Students who only need to interact with their assigned VMs, nothing more.
- VMware ESXi hypervisors today, with the possibility of adding Proxmox or others in the future.
- A need to scale without increasing the administrative workload proportionally.

---

## 3. Proposed Solution

UniVorch is a Linux service that provides a unified abstraction layer over one or more hypervisors. It allows administrators, professors, and students to manage VMs through a common interface, without direct access to the hypervisors.

The system is built on two layers:

**Layer 1 — Generic orchestrator (core)**  
Manages a tree of descriptors and folders. It handles cascade inheritance of properties, the job execution model, persistence, and connector interfaces to hypervisors. It has no knowledge of subjects, students, or teaching concepts. It is reusable for any environment: university, research lab, corporate training, or others.

**Layer 2 — Teaching application**  
Built on top of the core. It interprets specific branches of the tree as subjects and student workspaces. It provides the professor with tools to deploy a full subject from a template, and students with a simplified view of their own resources.

This separation keeps the core general-purpose while the teaching logic stays contained in its own layer.

---

## 4. Key Concepts

### Descriptor

A descriptor is the central object of the system. It represents a VM inside the orchestrator — analogous to a file descriptor in an operating system: it points to the real VM without being the VM itself.

A descriptor holds the VM definition (hardware parameters, base template, hypervisor reference) and its current state. From the user's perspective, the descriptor is the VM.

### Descriptor tree

Descriptors are organized in a hierarchical tree of folders. Each folder can hold a common definition that is inherited by all its children, recursively. This allows shared properties — hypervisor, base template, network configuration — to be defined once at a high level and inherited by all descriptors below.

Any property can be overridden at any level of the tree.

### Cascade inheritance

The effective definition of any descriptor is the result of combining all the definitions from root to that node, with each level being able to override properties from the level above. This makes it practical to manage hundreds of VMs: common parameters are defined once, and individual descriptors only specify what is different.

### Job

Every operation in the system generates a Job with a unique ID and a lifecycle: `pending → running → completed / failed`. Batch operations (deploy all VMs for a subject) produce a parent Job with one child Job per VM. Jobs are persisted in the database and provide a full audit trail.

### Descriptor states

The orchestrator tracks its own states, independent of the hypervisor's runtime states:

| State | Meaning |
|---|---|
| `provisioned` | Descriptor defined; no VM exists in the hypervisor yet |
| `deployed` | VM exists and matches the descriptor definition |
| `deployed` + `drifted` flag | VM exists but its configuration has been changed directly in the hypervisor |
| `broken` | A deploy or undeploy operation failed midway; state is inconsistent |
| `unreachable` | The hypervisor cannot be contacted |

Runtime states (running, stopped, paused) belong to the hypervisor and are queried on demand via `get_status`.

---

## 5. Users and Roles

The system defines three roles with fixed permissions:

| Role | Typical user | Scope |
|---|---|---|
| `superuser` | System administrator | Full tree; manages hypervisors, base templates, and global configuration |
| `manager` | Professor | Assigned branches of the tree; creates subjects and student folders; deploys and manages VMs for their subjects |
| `end_user` | Student | Their own assigned folder only; can start, stop, and redeploy their own VMs |

Role assignment is defined per folder, not per user. Each folder declares which users have access and with what role. Assignments cascade downward through the tree and can be overridden at any level.

**User perspective — the student**  
A student does not see the tree or folders. They see only their own workspace: a set of VMs assigned by the professor. The student can start, stop, and redeploy their VMs without admin intervention.

---

## 6. System Architecture (overview)

UniVorch runs as a Linux service on a host. It exposes a REST API used by external clients. The web interface is embedded in the same service.

**Main components:**

- **REST API** — the primary interface for CLI clients and external integrations (FastAPI).
- **Web GUI** — embedded in the service, used by all roles, especially students (NiceGUI).
- **Core engine** — processes operations, manages the descriptor tree, executes Jobs.
- **Hypervisor connectors** — pluggable modules that translate generic operations (deploy, undeploy, start, stop, pause, resume, get_status) to the specific API of each hypervisor type.
- **Persistence layer** — stores the descriptor tree, Jobs, and user data (TinyDB for v1, MongoDB for future HA).

**Non-invasive principle**  
The hypervisors continue to operate normally. UniVorch is an additional layer. If the service is stopped or unavailable, the hypervisors are not affected.

**Clients:**

- **CLI** (cmd2): supports both single commands and an interactive REPL shell. Communicates with the service via the REST API.
- **Web GUI**: accessible to all roles. The primary interface for students.

---

## 7. Scope of Version 1

**Included:**

- Descriptor tree with cascade inheritance.
- RBAC with three roles: superuser, manager, end_user.
- Full Job model with persistence.
- Descriptor state machine: provisioned, deployed, broken, unreachable.
- Hypervisor connectors: mock (for development and testing), VMware ESXi, Proxmox.
- REST API (FastAPI).
- Web GUI (NiceGUI).
- CLI client (cmd2).
- User management: YAML file, editable by superuser via web GUI.
- Teaching application: subject deployment tool (template desk + student list → individual desks, email notifications, deployment report).
- Basic reports: operational status per folder, subject status for professors.
- System logs via standard Python `logging` to syslog/journald.
- Operation history (Jobs) persisted in database with configurable retention (default: 90 days).
- Database backup with GFS rotation policy; manual restore in v1.

**Out of scope for v1:**

- Automatic reconciliation loop (changes are applied on demand).
- High availability / active-passive clustering.
- IPAM integration (IP management remains manual or via existing MAC trick).
- Snapshots managed through the orchestrator (hypervisor snapshots exist but are not tracked by UniVorch).
- Reference descriptors for pre-existing VMs (non-invasive discovery).
- TUI monitor (Textual).
- LDAP / Active Directory integration.
- Web UI for backup restore.

---

## 8. Future Applications

The generic core of UniVorch is not limited to teaching. Other applications can be built on the same engine by implementing a different layer 2:

- CTF and cybersecurity competitions: isolated environments per team, time-limited.
- Conference workshops: one VM per attendee, very short lifecycle.
- Practical exams: isolated VM per student, snapshots at start and end for grading.
- On-demand development environments: self-service from a template.
- QA and testing: identical VMs with different OS or software versions.
- Demo environments: deploy for a client, destroy after.
- Research labs: replicate experiment environments, snapshot at key points.
- Corporate training: same model as teaching, applied to IT training.
- MSPs: each client is a branch; one UniVorch instance manages multiple clients.
- Disaster recovery testing: periodic automated deployment of a production replica.

In all cases, the generic orchestrator remains unchanged. Only the application layer changes.

---

## 9. Non-Goals

UniVorch is not:

- A hypervisor management tool. It does not replace vSphere, Proxmox UI, or similar tools.
- A monitoring or alerting platform. It reports VM states on request; it does not continuously watch for anomalies.
- A network management system. IP assignment is out of scope for v1.
- A backup solution for VM data. It manages the orchestrator's own database backups, not VM disk backups.
