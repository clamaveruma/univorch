# UnivOrch — Product Vision

> Phase 1 deliverable: Problem Definition  
> Project: A virtual machine orchestrator for teaching and research environments. Proof of concept.

---

## 1. Problem

In the computer science school, virtual machines (VMs) are used for practical lab work across many courses. Each subject requires a set of VMs per student, all derived from base templates defined by the professor. The process sounds straightforward, but in practice it places a disproportionate burden on the system administrator.

When a professor wants to deploy a subject, they define the required VMs and request the administrator to create one set per student. The administrator runs custom scripts — written for a specific hypervisor platform — to clone base VMs, assign IP addresses, and make everything available. This works, but only as long as nothing changes. If a student stops a VM and cannot restart it, or corrupts the system and needs a fresh copy, the administrator must intervene again. If a new student joins after deployment, part of the process must be repeated by hand. If the hypervisor platform changes in the future, the scripts become useless and must be rewritten from scratch.

The core problems are:

- The administrator is the single point of contact for all VM operations, including trivial ones that students or professors could handle themselves.
- Students have no autonomy: they cannot start, stop, or restore their own VMs.
- Scripts are tightly coupled to a specific hypervisor; any platform change means rewriting everything.
- There is no unified interface for non-technical users — professors and students must go through the administrator for everything.
- The workload scales linearly: more subjects and students mean proportionally more administrative effort, with no mechanism to delegate.

---

## 2. Context

The system is designed for an academic environment, but the problem it addresses is not unique to universities. The same pattern appears in research labs, corporate training centres, and any other setting where groups of users need isolated, reproducible VM environments managed by a small team.

In the immediate context, the key characteristics are: multiple subjects running in parallel, each with its own set of VMs per student; a small number of administrators responsible for all hypervisors; professors who know their subject but are not hypervisor experts; and students who need to interact with their assigned machines, nothing more.

---

## 3. Proposed Solution

UnivOrch is a service that provides a unified abstraction layer over one or more hypervisors. Rather than interacting directly with VMware, Proxmox, or any other platform, users work through UnivOrch — which handles all communication with the underlying infrastructure.

The system is deliberately designed in two independent layers. The first is a generic orchestrator core that manages a tree of descriptors and folders, handles cascade inheritance of properties, and communicates with hypervisors through pluggable connectors. It has no knowledge of subjects, students, or academic concepts. The second layer is a teaching application built on top of the core, which interprets specific branches of the tree as subjects and student workspaces, and provides tools adapted to the teaching workflow.

This separation is important: the core is reusable for any environment — university, research lab, corporate training, or others — while the teaching logic stays contained in its own layer, without polluting the general-purpose engine.

---

## 4. Key Concepts

### Descriptor

The descriptor is the central object of the system. It represents a VM inside the orchestrator, in the same way that a file descriptor in an operating system points to a file without being the file itself. The descriptor holds the VM definition — hardware parameters, base template, hypervisor reference — and tracks its current state. From the user's perspective, the descriptor simply is the VM; the indirection is transparent.

One of the most useful properties of a descriptor is that it can exist in a *provisioned* state: the definition is stored in the orchestrator, but no VM has been created in the hypervisor yet. This allows a professor to define an entire subject's infrastructure before students need it, and students can deploy their own VMs on demand.

### Descriptor tree

Descriptors are organized in a hierarchical tree of folders. Each folder can hold a common definition that is inherited by all its children, recursively. This means that shared properties — hypervisor reference, base template, access permissions — can be defined once at a high level and inherited automatically by all descriptors below. Any property can be overridden at any level of the tree, which allows both consistency across large groups and flexibility for individual cases.

### Declarative model

The system follows a declarative approach: users describe the desired state, and the orchestrator is responsible for materializing it. This is the same philosophy used by tools like Terraform or Ansible. Instead of issuing step-by-step commands, a professor defines what the subject environment should look like, and the system takes care of the rest.

### Job

Every operation in the system generates a Job with a unique identifier and a lifecycle: pending → running → completed / failed. Batch operations — such as deploying all VMs for a subject at once — produce a parent Job with one child Job per VM. All Jobs are persisted and provide a full audit trail of everything that has happened in the system.

### Descriptor states

The orchestrator tracks its own set of states, independent of the hypervisor's runtime states. A descriptor can be *provisioned* (defined but not yet deployed), *deployed* (VM exists and matches the definition), *deployed with a drifted flag* (VM exists but its configuration was changed directly in the hypervisor, outside of UnivOrch), *broken* (an operation failed midway and left the state inconsistent), or *unreachable* (the hypervisor cannot be contacted). Runtime states such as running, stopped, or paused belong to the hypervisor and are queried on demand.

---

## 5. Users and Roles

The system defines three roles with fixed permissions:

| Role | Typical user | Scope |
|---|---|---|
| `superuser` | System administrator | Full tree; manages hypervisors, base templates, and global configuration |
| `manager` | Professor | Assigned branches of the tree; creates subjects and student folders; deploys and manages VMs |
| `end_user` | Student | Their own assigned folder only; can start, stop, and redeploy their own VMs |

Role assignment is defined per folder, not per user record. Each folder declares which users have access and with what role, and those assignments cascade downward through the tree. The same user can hold different roles in different branches, which makes the model flexible enough for contexts beyond the simple professor-student relationship.

From the student's perspective, none of this complexity is visible. They see only their own workspace — the set of VMs assigned by the professor — and can operate their machines without any administrator involvement.

---

## 6. Scope

### Version 1 — Proof of concept

The goal of v1 is to demonstrate that the concept works end to end. It includes the generic orchestrator core with descriptor tree, cascade inheritance, Jobs, and RBAC; connectors for a mock hypervisor (for development and testing), VMware ESXi, and Proxmox; a REST API and a web interface accessible to all roles; a command-line client; and a teaching application covering subject deployment and basic operational reports.

### Out of scope for v1

- Automatic reconciliation loop (state changes are applied on demand, not automatically).
- High availability and clustering.
- IP address management (IPAM).
- VM snapshot management through the orchestrator.
- Discovery of pre-existing VMs not created by UnivOrch.

---

## 7. Future Applications

The generic core of UnivOrch is not limited to teaching. Because the engine has no embedded domain logic, other applications can be built on top of it for different contexts: CTF and cybersecurity competitions with isolated environments per team; conference workshops where each attendee receives a VM for the duration of the event; practical exams with state captured at start and end for grading; on-demand development environments provisioned from a template; QA testing with identical VMs across different OS or software versions; research labs that need to replicate experiment environments exactly; and corporate IT training following the same model as academic teaching.

In all these cases, the orchestrator core remains unchanged. Only the application layer varies.

---

## 8. Non-Goals

UnivOrch is not a hypervisor management tool and does not replace platforms like vSphere or the Proxmox UI. It is not a monitoring or alerting system — it reports VM states on request but does not continuously watch for anomalies. It does not manage IP address assignment, which is out of scope for v1. And it is not a backup solution for VM data; it manages only its own operational data.
