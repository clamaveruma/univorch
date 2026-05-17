# UnivOrch — Requirements

> Phase 2 deliverable: Requirements Analysis  
> What the system does, from the user's point of view. Lightweight format.

This document builds on `vision.md` (the problem) and the design decisions recorded in `claude/decisiones.md`. It describes the expected behaviour of version 1 (proof of concept) and is meant to be precise enough for the architecture phase, without going into implementation.

---

## 1. Purpose and Scope

This document defines the functional and non-functional requirements of UnivOrch v1. It covers the generic orchestrator core and the teaching application built on top of it. It does not cover internal architecture, technology choices, or code structure — those belong to later phases.

The requirements are organized as:

- **Actors** — who interacts with the system.
- **Use cases** — what each actor wants to achieve, in plain language.
- **Functional requirements** — what the system does, grouped by area.
- **Non-functional requirements** — quality attributes the system must meet.
- **Constraints and assumptions** — fixed conditions the system works under.
- **Out of scope** — what v1 explicitly does not do.

---

## 2. Actors

| Actor | Description |
|---|---|
| **Administrator** (`superuser`) | Manages the whole system: hypervisors, base templates, users, the full tree, and global configuration. |
| **Manager** (`manager`) | A professor or similar. Manages assigned branches of the tree. Uses both the core and the teaching application. |
| **End user** (`end_user`) | A student or similar. Operates only their own assigned VMs. |
| **Hypervisor** | External system. UnivOrch communicates with it through connectors. It does not initiate actions; it responds. |
| **System** | UnivOrch acting on its own: running the operation engine and automatic tasks (backup, retention cleanup). |

A single person can hold different roles in different branches of the tree (see DEC-021).

---

## 3. Use Cases

Format: each use case has an ID, the actor, the goal, and a short description that includes the main flow and any notable alternatives or error situations.

Use cases are split into three groups: **core** (generic orchestrator), **teaching application** (layer 2, built on the core), and **system** (automatic behaviour).

### 3.1 Common — any authenticated user

**UC-AUTH-1 — Authenticate**  
*Actor:* any user. *Goal:* obtain access to the system.  
The user provides credentials. The system validates them and returns a session token (CLI) or establishes a session (web). Invalid credentials are rejected with a clear message. The token is required for all further operations.

**UC-AUTH-2 — View own resources**  
*Actor:* any user. *Goal:* see the current state of the resources they can access.  
The system shows the resources visible to the user according to their role and folder assignments, with the current state of each.

### 3.2 Core — Administrator

**UC-ADM-1 — Manage users**  
*Actor:* administrator. *Goal:* keep the user list up to date.  
The administrator creates, edits, or deletes users through the web interface. Each user has a username, password, display name, and email. Role assignment is not part of the user record — it is defined in each folder of the tree (see DEC-021). Only the administrator can manage users.

**UC-ADM-2 — Define hypervisors and datastores**  
*Actor:* administrator. *Goal:* register hypervisors and their storage so the system can use them.  
The administrator defines a hypervisor with an internal alias, type, address, and credentials. Within the hypervisor definition, datastores are also defined, each with its own alias. These definitions are placed in a folder and inherited in cascade. Both hypervisor details and datastore aliases can be referenced by templates and descriptors without exposing the underlying credentials (DEC-017).

**UC-ADM-3 — Define a base template**  
*Actor:* administrator. *Goal:* provide reusable VM definitions.  
The administrator defines a base template: the base VM it clones from, the hypervisor it lives on, hardware parameters, and the target datastore. Templates can be derived from other templates.

**UC-ADM-4 — Create and organize folders**  
*Actor:* administrator. *Goal:* structure the tree.  
The administrator creates folders anywhere in the tree and sets their common definition (what is available for child folders to import, see DEC-012).

**UC-ADM-5 — Assign users to roles**  
*Actor:* administrator. *Goal:* grant access.  
The administrator assigns users to roles in any folder. Assignments cascade down and can be overridden in subfolders.

**UC-ADM-6 — Restrict what a manager sees**  
*Actor:* administrator. *Goal:* limit a manager's visibility.  
The administrator restricts which templates and hypervisors a given manager can see. This is the only configurable permission in v1 (see DEC-011). A manager can use a resource without seeing its full definition.

**UC-ADM-7 — Configure global properties**  
*Actor:* administrator. *Goal:* tune system-wide settings.  
The administrator sets global properties, such as the Job retention period (default 90 days). These are not inherited in cascade.

**UC-ADM-8 — Force-undeploy a broken descriptor**  
*Actor:* administrator. *Goal:* recover from an inconsistent state.  
For a descriptor in `broken` state, the administrator triggers a force-undeploy. The system removes whatever exists in the hypervisor and returns the descriptor to `provisioned`.

**UC-ADM-9 — View Job history**  
*Actor:* administrator. *Goal:* audit operations.  
The administrator views the history of Jobs, with their state, result, and error message if any. This is also how the reason for a `broken` state is found.

**UC-ADM-10 — Restore the database from a backup**  
*Actor:* administrator. *Goal:* recover after data loss or corruption.  
In v1 this is manual: the administrator replaces the database file with a previous backup copy. The system offers the available backups for reference.

**UC-ADM-11 — View operational reports**  
*Actor:* administrator. *Goal:* get an overview of system state.  
The administrator views an operational report, such as the state of all VMs grouped by folder.

### 3.3 Core — Manager

**UC-MGR-1 — Create and organize folders in own branches**  
*Actor:* manager. *Goal:* structure their own area.  
Within the branches assigned to them, the manager creates folders. When creating a folder, the creator chooses which definitions to import from the parent (or imports all with `*`). The manager sets the folder's own common definition, which child folders can in turn import.

**UC-MGR-2 — Create descriptors**  
*Actor:* manager. *Goal:* define VMs.  
The manager creates descriptors based on the templates allowed to them. The descriptor only specifies what differs from the inherited definition.

**UC-MGR-3 — Derive templates**  
*Actor:* manager. *Goal:* adapt templates for a subject.  
The manager derives new templates from the base templates allowed to them. The manager can see the full template definition — hardware parameters, base VM name, target datastore — but not the hypervisor's address or credentials, which are hidden as sensitive information (DEC-011). Templates are referenced by their alias.

**UC-MGR-4 — Assign users to roles in own folders**  
*Actor:* manager. *Goal:* grant access to students or other managers.  
In their own folders, the manager assigns end users (students) and may assign other managers.

**UC-MGR-5 — Batch operations on descriptors**  
*Actor:* manager. *Goal:* operate on many VMs or descriptors at once.  
The manager can trigger the following operations on a set of descriptors at once: deploy, undeploy, start, stop, pause, resume. The system creates a parent Job with one child Job per VM. The manager can follow progress and see which ones failed.  
The manager can also create multiple descriptors at once by uploading a YAML file with several descriptor definitions. *(Note: the exact mechanism for passing structured data to the orchestrator — CLI file argument, web upload, or other — is a design decision deferred to Phase 3.)*

**UC-MGR-6 — View Job history for own scope**  
*Actor:* manager. *Goal:* check what happened in their area.  
The manager views the Job history limited to their assigned branches.

**UC-MGR-7 — View subject status report**  
*Actor:* manager. *Goal:* see the state of a subject at a glance.  
The manager views a report with the state of all student VMs in a subject.

### 3.4 Teaching application — Manager (layer 2)

These use cases run on top of the core. They translate a teaching workflow into core operations.

**UC-TEACH-1 — Deploy a subject**  
*Actor:* manager. *Goal:* set up a full subject from a model.  
The manager defines a model desk (the set of VMs every student gets) and provides a student list. The application creates one desk per student, creates the descriptors in `provisioned` state, assigns each student as end user of their desk, applies the IP policy, sends a notification email to each student, and produces a deployment report for the manager.

**UC-TEACH-2 — Update the student list**  
*Actor:* manager. *Goal:* keep the subject in sync with enrolment.  
The manager provides an updated student list. The application creates desks for new students and flags students no longer on the list. Removal behaviour follows the configured policy.

**UC-TEACH-3 — Change a model VM**  
*Actor:* manager. *Goal:* update the subject definition.  
The manager changes a VM in the model desk. The application updates the descriptors. Changes to running VMs apply on the next recreation, consistent with the descriptor state machine (DEC-022).

### 3.5 Core — End user (student)

The student sees the metaphor of **desks** (DEC-009). They never see folders or the tree.

**UC-USR-1 — View own desks**  
*Actor:* end user. *Goal:* see their assigned VMs.  
The student opens the application and sees their desks. Each desk shows its VMs and their current state.

**UC-USR-2 — Deploy own VM**  
*Actor:* end user. *Goal:* create a VM that is only provisioned.  
The student deploys a VM from `provisioned`. The system clones it from the assigned template and reports progress through a Job.

**UC-USR-3 — Undeploy own VM**  
*Actor:* end user. *Goal:* remove a VM.  
The student undeploys one of their VMs. The system deletes the VM and its virtual disk completely; the descriptor returns to `provisioned`.

**UC-USR-4 — Start, stop, pause, or resume own VM**  
*Actor:* end user. *Goal:* control a deployed VM.  
The student performs the operation. The system forwards it to the hypervisor and reports the result.

**UC-USR-5 — Recreate own VM**  
*Actor:* end user. *Goal:* get a clean copy.  
The student recreates a VM (undeploy followed by deploy). This is the way to recover from a corrupted system without administrator help.

**UC-USR-6 — View status and connection info**  
*Actor:* end user. *Goal:* know how to connect.  
The student views the state of a VM and its connection data (such as the IP), queried from the hypervisor on demand.

### 3.6 System — automatic behaviour

**UC-SYS-1 — Run the operation engine**  
*Actor:* system. *Goal:* execute operations.  
The system takes operations from the pending queue, executes them, and records the result (completed or failed) in the Job history. In v1 operations are synchronous; the Job model is designed so an asynchronous queue can be added later without redesign (DEC-014, DEC-015).

**UC-SYS-2 — Back up the database**  
*Actor:* system. *Goal:* protect data.  
The system periodically copies the database following a GFS retention policy (DEC-024).

**UC-SYS-3 — Clean up old Jobs**  
*Actor:* system. *Goal:* limit data growth.  
The system removes Jobs older than the configured retention period (DEC-023).

**UC-SYS-4 — Detect an unreachable hypervisor**  
*Actor:* system. *Goal:* reflect reality.  
When communication with a hypervisor fails, the system marks the affected descriptors as `unreachable`.

---

## 4. Functional Requirements

Grouped by area. Each item is a clear statement of what the system does.

### 4.1 Tree and folders

- The system stores descriptors and folders in a hierarchical tree.
- A folder has a common definition that its children can import and use.
- A parent folder makes definitions available; child folders choose what to import (DEC-012).
- Folders can be created, viewed, and organized by users with the right role in that branch.

### 4.2 Cascade inheritance

- The effective definition of a descriptor is the combination of all definitions from root to that node, with each level able to override properties from the level above (DEC-010).
- Hypervisors, templates, datastores, and role assignments are all inherited this way.
- When a folder is created, its creator declares which definitions to import from the parent folder. The creator can import a specific list or use `*` to import everything available. What is not imported is not visible below (DEC-012).
- A user can see the full resolved definition of the elements imported into their folder (local definition plus everything inherited from above), but can only modify definitions at their own level. Parent definitions are read-only.
- Only hypervisor credentials and address are hidden from managers; all other template and descriptor properties are visible to those who import them (DEC-011).
- Ownership of a folder is not an explicit system concept. It emerges naturally from role assignment: the users assigned as `manager` of a folder are effectively its owners. The administrator is manager of all; a student is end user of their final folder. No separate ownership mechanism is needed (DEC-021).
- Inheritance is mandatory in v1; it is not optional.

### 4.3 Descriptors and states

- A descriptor holds the VM definition and a reference to the real VM (the VM's name or ID as used by the hypervisor), and tracks its own state.
- The descriptor states are: `provisioned`, `deployed` (with an optional `drifted` flag), `broken`, and `unreachable` (DEC-022).
- Runtime states (running, stopped, paused) are not stored; they are queried from the hypervisor on demand.
- A descriptor in `broken` exposes its Job history so the reason can be seen, and can only leave that state through force-undeploy.
- v1 supports only normal descriptors. Reference-only descriptors are out of scope (DEC-005b).

### 4.4 Deployment and hypervisor connectors

- Every connector implements a common interface: `deploy`, `undeploy`, `start`, `stop`, `force_stop`, `pause`, `resume`, `get_status`, `get_info` (DEC-016).
- `deploy` clones the base VM (linked clone preferred). `undeploy` deletes the VM and its virtual disk completely.
- The system routes each operation to the correct connector using two pieces of information: the hypervisor definition (resolved from cascade inheritance) and the VM reference stored in the descriptor (the name or ID that the hypervisor uses to identify the VM uniquely).
- v1 includes connectors for a mock hypervisor, VMware ESXi, and Proxmox.
- The system does not interfere with normal hypervisor operation (non-invasive principle, DEC-016).

### 4.5 Jobs and the operation engine

- Every operation creates a Job with a unique ID and a lifecycle: `pending → running → completed / failed` (DEC-014).
- Jobs cover all types of operations: VM operations (deploy, start, stop...), tree operations (create folder, move...), permission changes, and any other system action.
- Batch operations create a parent Job with one child Job per VM.
- Jobs are persisted in the database (DEC-015).
- In v1 operations are synchronous; the model supports an asynchronous queue in the future.
- The Job history is available to users for their scope and is the source for diagnosing failures.

### 4.6 Users and access control

- Users are stored in a YAML file and managed by the administrator through the web interface (DEC-021).
- In v1 passwords are stored in plain text (acceptable for the proof of concept; must move to hashing before any real deployment).
- The system uses three fixed roles: `superuser`, `manager`, `end_user` (DEC-011).
- Role assignment is defined per folder and inherited in cascade; it can be overridden in subfolders.
- The user store is accessed through an abstraction layer so it can be replaced later (for example, by LDAP) without affecting the rest of the system.

### 4.7 Teaching application

- The teaching application is a layer on top of the core; the core has no knowledge of subjects or students (DEC-004).
- It deploys a subject from a model desk and a student list, creating one desk per student.
- It assigns each student as end user of their desk, applies the IP policy, and sends notification emails.
- It produces a deployment report for the manager.
- It supports updating the student list and changing a model VM.

### 4.8 Reports

- The system provides at least one operational report (VM state grouped by folder) and one teaching report (subject status for a manager).
- The catalogue of possible reports is recorded for the future; v1 implements these two as examples.

### 4.9 Interfaces

- The system exposes a REST API used by external clients.
- It provides a command-line client that works both as single commands and as an interactive shell, with session-token authentication and script support (DEC-018).
- It provides a web interface for all roles, designed especially for the student.
- The web interface is part of the service and uses the core directly; the CLI uses the REST API.

### 4.10 Persistence, logging, and backup

- The tree, descriptors, Jobs, and users are persisted; the system stays consistent across restarts.
- Persistence is accessed through an abstraction (Repository pattern) so the storage engine can change later (DEC-007).
- System logs use the standard Python logging facility and go to the system log (DEC-023).
- Operation logs are the persisted Job history, with configurable retention (default 90 days).
- The database is backed up periodically with a GFS retention policy; restore is manual in v1 (DEC-024).

---

## 5. Non-Functional Requirements

### 5.1 Usability

- A non-technical user (student) can operate their VMs without knowing anything about hypervisors.
- The student only sees their desks, never the tree or internal structure.
- Error messages are clear and tell the user what happened and, when possible, what to do.

### 5.2 Security

- All operations require authentication.
- Users can only see and act on resources allowed by their role and folder assignments.
- Authentication uses the standard mechanisms provided by the web and API frameworks.
- The plain-text password store is a known limitation of the proof of concept and is documented as such.

### 5.3 Performance and scalability

- The system handles a realistic teaching load: hundreds of VMs across several subjects.
- Cascade inheritance keeps configuration manageable at that scale without repeating definitions.
- Batch operations report progress so large deployments are observable.

### 5.4 Reliability and recovery

- The system stays consistent across restarts.
- A failed operation never leaves the system without a record; the Job history always reflects what happened.
- An inconsistent descriptor goes to `broken` rather than to an undefined state.
- The database can be restored from a backup after corruption.

### 5.5 Maintainability and extensibility

- New hypervisor types can be added by implementing the common connector interface, without changing the core.
- New applications can be built on the core without modifying it (the two-layer design).
- Design patterns are used only when they simplify the project, not by default (DEC-008).
- The code is kept at a basic-to-intermediate level; advanced features are discussed before being introduced.

### 5.6 Portability

- The system runs as a Linux service.
- It does not require the hypervisors to be on the same host.
- It does not interfere with the hypervisors' normal operation; they keep working if UnivOrch is stopped.

---

## 6. Constraints and Assumptions

- The implementation language is Python (recent version, chosen in Phase 4).
- The system runs as a service on Linux.
- The hypervisors already exist and are not part of UnivOrch. Base VMs are created directly on the hypervisor by the administrator.
- v1 operations are synchronous.
- v1 stores passwords in plain text (proof of concept only).
- IP assignment is not managed by UnivOrch in v1; the existing approach (such as encoding the IP in the MAC) stays in place.

---

## 7. Out of Scope for v1

Traceable to `vision.md` and the design decisions:

- Automatic reconciliation loop (changes are applied on demand) — DEC-006.
- High availability and clustering.
- IPAM integration — DEC-013.
- Snapshot management through the orchestrator.
- Reference-only descriptors and discovery of pre-existing VMs — DEC-005b, DEC-020.
- LDAP / Active Directory integration — DEC-021.
- TUI monitor — DEC-018.
- Web interface for backup restore — DEC-024.
- Per-folder fine-grained permission customization — DEC-011.
