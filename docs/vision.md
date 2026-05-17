# UnivOrch — Product Vision

> Phase 1 deliverable: Problem Definition  
> Project: A virtual machine orchestrator for teaching and research environments. Proof of concept.

---

## 1. Problem

In the computer science school, virtual machines (VMs) are used for practical lab work in many courses. Each subject needs a set of VMs per student, all based on templates defined by the professor. Managing all this falls entirely on the system administrator.

When a professor wants to deploy a subject, they define the VMs and ask the administrator to create one set per student. The administrator runs custom scripts — written for a specific hypervisor — to clone the base VMs and assign IP addresses. If a student stops a VM or corrupts it, the administrator has to step in again. If a new student joins after deployment, part of the process has to be repeated by hand. If the hypervisor platform changes in the future, the scripts stop working and have to be rewritten.

The main problems are:

- The administrator handles all VM operations, including simple ones that students or professors could do themselves.
- Students cannot manage their own VMs: start, stop, or restore from template.
- Scripts are tied to one hypervisor; any platform change means rewriting everything.
- There is no interface for non-technical users — professors and students go through the administrator for everything.
- The workload grows with the number of subjects and students, with no way to delegate.

---

## 2. Context

The system is designed for an academic environment, but the problem is not unique to universities. The same situation appears in research labs, corporate training, and any setting where groups of users need isolated, reproducible VM environments managed by a small team.

The main characteristics of the target environment are:

- Multiple subjects running at the same time, each with its own set of VMs per student.
- A small number of administrators managing all hypervisors.
- Professors who know their subject but are not hypervisor experts.
- Students who only need to use their assigned VMs, nothing more.
- A need to scale without adding administrative work proportionally.

---

## 3. Proposed Solution

UnivOrch is a service that sits between users and hypervisors. Instead of interacting directly with VMware, Proxmox, or any other platform, users work through UnivOrch, which handles all communication with the underlying infrastructure.

The system is built on two layers:

- **Layer 1 — Generic orchestrator (core):** manages a tree of descriptors and folders, handles cascade inheritance of properties, and communicates with hypervisors through pluggable connectors. It has no knowledge of subjects, students, or academic concepts. It can be used in any environment.
- **Layer 2 — Teaching application:** built on top of the core. It provides tools for the teaching workflow — subject deployment, student management, reports — without modifying the core.

This separation keeps the core reusable while the teaching-specific logic stays in its own layer.

---

## 4. Key Concepts

### Descriptor

The descriptor is the main object of the system. It represents a VM inside the orchestrator, similar to how a file descriptor in an operating system points to a file without being the file itself. It holds the VM definition — hardware parameters, base template, hypervisor reference — and tracks its current state.

One important feature is that a descriptor can exist in a *provisioned* state: the definition is stored in the orchestrator, but no VM has been created in the hypervisor yet. This allows a professor to define the full infrastructure of a subject before students need it, and students can deploy their own VMs when they are ready.

### Descriptor tree

Descriptors are organized in a tree of folders. Each folder can hold a common definition that all its children inherit, recursively. This means shared properties — hypervisor reference, base template, access permissions — can be defined once at a high level and reused by all descriptors below. Any property can be overridden at any level of the tree.

### Declarative model

The system is declarative: users describe the desired state, and the orchestrator is responsible for making it happen. Instead of issuing step-by-step commands, a professor defines what the subject environment should look like, and the system does the rest.

### Job

Every operation generates a Job with a unique ID and a lifecycle:

```
pending → running → completed / failed
```

Batch operations — such as deploying all VMs for a subject at once — create a parent Job with one child Job per VM. All Jobs are stored and provide a full history of operations.

### Descriptor states

The orchestrator tracks its own states, separate from the hypervisor's runtime states:

| State | Meaning |
|---|---|
| `provisioned` | Descriptor defined; no VM exists in the hypervisor yet |
| `deployed` | VM exists and matches the descriptor definition |
| `deployed` + `drifted` | VM exists but was changed directly in the hypervisor, outside UnivOrch |
| `broken` | An operation failed midway; state is inconsistent |
| `unreachable` | The hypervisor cannot be contacted |

Runtime states (running, stopped, paused) belong to the hypervisor and are queried on demand.

---

## 5. Users and Roles

The system defines three roles:

| Role | Typical user | Scope |
|---|---|---|
| `superuser` | System administrator | Full tree; manages hypervisors, base templates, and global configuration |
| `manager` | Professor | Assigned branches of the tree; creates subjects and student folders; deploys and manages VMs |
| `end_user` | Student | Their own folder only; can start, stop, and redeploy their own VMs |

Role assignment is defined per folder, not per user. Each folder declares which users have access and with what role. Assignments cascade down the tree and can be overridden at any level.

From the student's perspective, none of this is visible. They see only their own workspace and can operate their VMs without any administrator involvement.

---

## 6. Scope

### Version 1 — Proof of concept

The goal of v1 is to show that the concept works end to end. It includes:

- Generic orchestrator core: descriptor tree, cascade inheritance, Jobs, RBAC.
- Hypervisor connectors: mock (for development and testing), VMware ESXi, Proxmox.
- REST API and web interface, accessible to all roles.
- Command-line client.
- Teaching application: subject deployment tool and basic operational reports.

### Out of scope for v1

- Automatic reconciliation loop (changes are applied on demand, not automatically).
- High availability and clustering.
- IP address management (IPAM).
- VM snapshot management through the orchestrator.
- Discovery of pre-existing VMs not created by UnivOrch.

---

## 7. Future Applications

The generic core is not limited to teaching. Other applications can be built on the same engine:

- CTF and cybersecurity competitions: isolated environments per team, time-limited.
- Conference workshops: one VM per attendee, short lifecycle.
- Practical exams: isolated VM per student, state captured at start and end for grading.
- On-demand development environments: self-service from a template.
- QA and testing: identical VMs with different OS or software versions.
- Research labs: replicate experiment environments, snapshot at key points.
- Corporate IT training: same model as academic teaching.

In all cases, the core stays the same. Only the application layer changes.

---

## 8. Non-Goals

UnivOrch is not:

- A hypervisor management tool. It does not replace platforms like vSphere or the Proxmox UI.
- A monitoring or alerting system. It reports VM states on request but does not watch for anomalies continuously.
- A network management system. IP assignment is out of scope for v1.
- A backup solution for VM data. It only manages its own operational data.
