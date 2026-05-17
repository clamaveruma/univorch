# UniVorch — Product Vision

> Phase 1 deliverable: Problem Definition  
> Project: A virtual machine orchestrator for teaching and research environments. Proof of concept.

---

## 1. Problem

In the computer science school, virtual machines (VMs) are used for practical lab work across many courses. Each subject requires a set of VMs per student, all derived from base templates defined by the professor.

Today, the entire process is handled manually by the system administrator:

- A professor defines the VMs for a subject and requests deployment for every student.
- The administrator runs custom scripts, tightly coupled to a specific hypervisor platform, to clone base VMs and assign IP addresses.
- If a student stops a VM or corrupts it, the administrator must intervene to restart or recreate it.
- When a new student joins after deployment, the process must be repeated partially by hand.

The result is a heavy administrative burden, no autonomy for students or professors, and a system that breaks whenever the hypervisor platform changes.

**Core problems:**

- The administrator is the single point of contact for all VM operations, including trivial ones.
- Students cannot manage their own VMs: start, stop, or restore from template.
- Scripts are tied to a specific hypervisor; a platform change means rewriting everything.
- There is no unified interface for non-technical users.
- Scaling is linear: more subjects and students mean proportionally more administrative work.

---

## 2. Context

The system operates in an academic environment with the following characteristics:

- Multiple subjects running in parallel, each with its own set of VMs per student.
- A small number of administrators managing all hypervisors.
- Professors who understand their subject but are not hypervisor experts.
- Students who only need to interact with their assigned VMs, nothing more.
- A need to scale without increasing the administrative workload proportionally.

---

## 3. Proposed Solution

UniVorch is a service that provides a unified abstraction layer over one or more hypervisors. It allows administrators, professors, and students to manage VMs through a common interface, without direct access to the hypervisors.

The system is built on two layers:

**Layer 1 — Generic orchestrator (core)**  
Manages a tree of descriptors and folders. It handles cascade inheritance of properties, operation execution, and communication with hypervisors through pluggable connectors. It has no knowledge of subjects, students, or teaching concepts. It is reusable for any environment: university, research lab, corporate training, or others.

**Layer 2 — Teaching application**  
Built on top of the core. It interprets specific branches of the tree as subjects and student workspaces, and provides tools adapted to the teaching workflow.

This separation keeps the core general-purpose while the teaching logic stays contained in its own layer.

---

## 4. Key Concepts

### Descriptor

A descriptor is the central object of the system. It represents a VM inside the orchestrator — analogous to a file descriptor in an operating system: it points to the real VM without being the VM itself.

A descriptor holds the VM definition (hardware parameters, base template, hypervisor reference) and tracks its current state. From the user's perspective, the descriptor is the VM.

### Descriptor tree

Descriptors are organized in a hierarchical tree of folders. Each folder can hold a common definition that is inherited by all its children, recursively. This allows shared properties — hypervisor reference, base template, access permissions — to be defined once at a high level and inherited by all descriptors below.

Any property can be overridden at any level of the tree.

### Cascade inheritance

The effective definition of any descriptor is the result of combining all definitions from root to that node, with each level able to override properties from the level above. This makes it practical to manage hundreds of VMs: common parameters are defined once, and individual descriptors only specify what is different.

### Declarative model

The system is declarative: users describe the desired state, and the orchestrator is responsible for materializing it. This is the same philosophy used by tools like Terraform or Ansible — the user does not issue step-by-step commands, but defines what should exist.

### Job

Every operation in the system generates a Job with a unique identifier and a lifecycle: pending → running → completed / failed. Batch operations produce a parent Job with one child Job per VM. Jobs are persisted and provide a full audit trail of all operations.

### Descriptor states

The orchestrator tracks its own states, independent of the hypervisor's runtime states:

- **provisioned** — the descriptor is defined but no VM exists in the hypervisor yet.
- **deployed** — the VM exists and matches the descriptor definition.
- **deployed + drifted** — the VM exists but its configuration has been changed directly in the hypervisor, outside of UniVorch.
- **broken** — an operation failed midway and left the state inconsistent.
- **unreachable** — the hypervisor cannot be contacted.

Runtime states (running, stopped, paused) belong to the hypervisor and are queried on demand.

---

## 5. Users and Roles

The system defines three roles with fixed permissions:

| Role | Typical user | Scope |
|---|---|---|
| `superuser` | System administrator | Full tree; manages hypervisors, base templates, and global configuration |
| `manager` | Professor | Assigned branches of the tree; creates subjects and student folders; deploys and manages VMs |
| `end_user` | Student | Their own assigned folder only; can start, stop, and redeploy their own VMs |

Role assignment is defined per folder, not per user. Each folder declares which users have access and with what role. Assignments cascade downward through the tree and can be overridden at any level.

**Student perspective**  
A student does not see the tree or folders. They see only their own workspace: the set of VMs assigned by the professor. They can operate their VMs without administrator intervention.

---

## 6. Scope

### Version 1 — Proof of concept

The goal of v1 is to demonstrate that the concept works end to end. It includes:

- The generic orchestrator core: descriptor tree, cascade inheritance, Jobs, RBAC.
- Connectors for a mock hypervisor (for development and testing), VMware ESXi, and Proxmox.
- A REST API and a web interface, accessible to all roles.
- A command-line client.
- A teaching application: subject deployment tool and basic operational reports.

### Out of scope for v1

- Automatic reconciliation loop (state changes are applied on demand, not automatically).
- High availability and clustering.
- IP address management (IPAM).
- VM snapshot management through the orchestrator.
- Discovery of pre-existing VMs not created by UniVorch.

---

## 7. Future Applications

The generic core of UniVorch is not limited to teaching. Other applications can be built on the same engine:

- CTF and cybersecurity competitions: isolated environments per team, time-limited.
- Conference workshops: one VM per attendee, very short lifecycle.
- Practical exams: isolated VM per student, with state captured at start and end.
- On-demand development environments: self-service from a template.
- QA and testing: identical VMs with different OS or software versions.
- Research labs: replicate experiment environments, snapshot at key points.
- Corporate IT training: same model as teaching, applied to enterprise environments.

In all cases, the generic orchestrator remains unchanged. Only the application layer varies.

---

## 8. Non-Goals

UniVorch is not:

- A hypervisor management tool. It does not replace vSphere, Proxmox UI, or similar platforms.
- A monitoring or alerting system. It reports VM states on request; it does not continuously watch for anomalies.
- A network management system. IP assignment is out of scope for v1.
- A backup solution for VM data. It manages only its own operational data.
