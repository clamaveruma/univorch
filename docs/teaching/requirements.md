# Teaching Application — Requirements

> Phase 2 deliverable: Requirements Analysis (layer-2 teaching application)
> What the teaching application does, from the user's point of view.

This document builds on `docs/teaching/vision.md` (the problem) and on
the core requirements (`docs/requirements.md`). It describes the
behaviour of the teaching application for the proof of concept. The
vocabulary (subject, desktop, student, desk) is the one fixed in the
vision document.

---

## 1. Purpose and Scope

This document defines the functional and non-functional requirements of
the teaching application. It covers the `teach` subcommands and their
validations. It does not cover core behaviour (loading, deploying,
inheritance) except where the teaching layer relies on it.

The teaching application sits on top of the core and reaches it through
the same REST API as any other client.

---

## 2. Actors

| Actor | Description |
|---|---|
| **Administrator** (`superuser`) | Installs the application, prepares hypervisors and base templates, and decides where in the tree subjects live. Does not run the teaching workflow. |
| **Professor** (`manager`) | Runs the teaching workflow: loads subjects, loads student lists, exports both. |
| **Student** (`end_user`) | Operates their own machines through the desk view. Not an actor of the `teach` commands themselves. |
| **Core** | The UnivOrch daemon. Performs the actual tree operations the teaching application requests. |

---

## 3. Use Cases

Format: each use case has an ID, the actor, the goal and a short
description. Use cases are grouped by the workflow stage.

### 3.1 Subject definition

**UC-TEACH-1 — Load a subject**
*Actor:* professor. *Goal:* register a subject in the tree.
The professor provides a YAML file describing a subject (a folder marked
`kind: subject`, with template definitions and a desktop). The
application validates that the file is a well-formed subject (see
section 4.1) and, if valid, loads it into the tree at the chosen
destination using the core's `load`. If the validation fails, nothing is
loaded and the professor gets a clear list of reasons.

**UC-TEACH-2 — Export a subject**
*Actor:* professor. *Goal:* get a portable copy of a subject definition.
The professor exports a subject to a YAML file. The file contains the
subject definition only — templates and desktop — without any students or
runtime state. The exported file is a valid input to UC-TEACH-1, so the
same subject can be reused next term or shared with another professor.

### 3.2 Student management

**UC-TEACH-3 — Load a student list**
*Actor:* professor. *Goal:* create the per-student infrastructure of a
subject. The professor provides a subject (a path in the tree) and a
student list (a YAML file with usernames). The application checks that
the path is a valid subject, validates the list (no duplicates), and for
each student creates a folder named after the username and, inside it,
one descriptor per template of the subject's desktop. Descriptors are
created in `provisioned` state. Students already present are left
unchanged. The operation only adds; it never removes.

**UC-TEACH-4 — Export a student list**
*Actor:* professor. *Goal:* get the current list of students of a
subject. The application reads the student folders under the subject and
writes their usernames to a YAML file in the student-list format. The
exported file is a valid input to UC-TEACH-3.

### 3.3 Out of scope for the proof of concept

The following use cases are part of the model but not implemented in this
proof of concept. They are listed so the boundary is explicit.

- **UC-TEACH-X1 — Deploy a subject.** Deploy every provisioned machine
  of a subject in one batch operation. In the proof of concept the
  machines are deployed with ordinary core operations, per machine or
  per branch.
- **UC-TEACH-X2 — Update a student list with withdrawals.** When a
  student is no longer on the list, warn the professor that the student's
  folder and machines will be removed, let them confirm or cancel, and
  refuse if any machine is still deployed.
- **UC-TEACH-X3 — Notify students.** Send each student an email with the
  details of their desk when the subject is deployed.
- **UC-TEACH-X4 — Subject status report.** Show the professor the state
  of every student's machines in a subject at a glance.

---

## 4. Functional Requirements

### 4.1 Subject validation

A file or folder is a valid subject when all of the following hold. The
application checks them before any tree modification (fail-fast):

1. The root folder of the document carries the field `kind: subject`.
2. The folder declares a `desktop` field: a non-empty list of names.
3. Every name in the desktop resolves to a template that is available at
   the subject folder — either defined locally (`define templates:`) or
   inherited through `import:`. This check relies on the core resolver,
   which already validates references at load time.
4. The document has no child folders. A subject contains templates and a
   desktop, not nested folders; the student folders are added later by
   UC-TEACH-3.
5. No list in the document contains duplicate entries.

If any check fails, the load is rejected with a list of the specific
problems and the tree is not modified.

### 4.2 Student-list validation

A student list is valid when:

1. The document has `kind: student-list`.
2. The `students` field is a list of usernames.
3. The list has no duplicate usernames.

For the proof of concept the usernames are not checked against a user
registry; that check is a future concern tied to authentication.

### 4.3 Student-folder generation

For each username in a valid student list applied to a valid subject:

1. A folder named after the username is created under the subject folder,
   unless it already exists.
2. Inside the folder, one descriptor is created per template listed in
   the subject's desktop. Each descriptor is named after its template and
   carries `use template: <name>`, which the core resolves against the
   subject's definitions.
3. Descriptors are created in `provisioned` state. The application does
   not deploy them.

The generation only adds. A student already present and unchanged is a
no-op. Removing a student is out of scope (UC-TEACH-X2).

### 4.4 Interface

1. The teaching commands are exposed as a `teach` subcommand of the
   existing `univorch` CLI.
2. The commands are: `teach load-subject`, `teach save-subject`,
   `teach load-students`, `teach save-students`.
3. The commands talk to the daemon through the same REST API as the rest
   of the CLI. They add no new service and no new port.

### 4.5 Relationship to core operations

1. Loading a subject ends in a core `load`.
2. Generating student folders and descriptors ends in core
   create-folder and create-descriptor operations.
3. The teaching application performs no tree mutation directly; every
   mutation is a core operation requested through the API.

---

## 5. Non-Functional Requirements

| Quality | Target |
|---|---|
| Simplicity | The professor runs the whole workflow with a handful of subcommands, in the vocabulary of teaching. |
| Consistency | The teaching commands mirror the core commands (`load-subject` mirrors `load`; `save-*` mirrors a future core `save`). |
| Non-invasiveness | The application adds no new service, port or container. It is a client of the existing daemon. |
| Reusability | A subject definition is portable: it can be exported and re-loaded in another term or installation. |
| Separation | The core stays free of teaching vocabulary. The teaching logic lives entirely in the teaching module. |

---

## 6. Constraints and Assumptions

- The administrator has already set up the hypervisors, the base
  templates and a folder in the tree where subjects are loaded.
- The core daemon is running and reachable through its REST API.
- The proof of concept runs against the mock connector.
- Student usernames are taken at face value; no user registry check.
- Operations only add or update; they do not remove.

---

## 7. Out of Scope for the Proof of Concept

Traceable to the vision document and to the core's out-of-scope list:

- Deploying a whole subject in one command (UC-TEACH-X1).
- Student withdrawal with confirmation and deployed-machine checks
  (UC-TEACH-X2).
- Email notifications (UC-TEACH-X3).
- Subject status reports (UC-TEACH-X4).
- A dedicated web interface for the teaching workflow.
- Effective RBAC (the professor restricted to their own branches).
- Validation of usernames against a user registry.
- Multiple desktops per subject (the model allows it; the proof of
  concept assumes one).
