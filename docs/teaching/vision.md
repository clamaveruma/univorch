# Teaching Application — Product Vision

> Phase 1 deliverable: Problem Definition (layer-2 teaching application)
> Project: A virtual machine orchestrator for teaching and research environments. Proof of concept.

This document defines the problem that the **teaching application**
solves. The teaching application is the layer-2 application built on top
of the generic UnivOrch orchestrator (see `docs/vision.md` for the
core). It does not replace any core concept; it gives the core a
teaching-specific vocabulary and automates the workflow a professor
follows when running a subject.

---

## 1. Problem

The generic orchestrator manages a tree of folders and descriptors. It
is powerful but neutral: it knows nothing about subjects, students or
courses. Operating it directly means thinking in terms of folders,
descriptors, templates and imports.

A professor does not think that way. A professor thinks in terms of:

- "My subject needs every student to have the same set of machines."
- "These are the students enrolled this term."
- "Deploy a workstation and a server for each of them."
- "Next term I want to reuse the same setup with a new list of students."

Without a teaching layer, the professor has to translate all of this by
hand into core operations: create one folder per student, create the
right descriptors inside each, wire the templates, keep the structure
consistent as students join or leave. This is tedious and error-prone,
and it pushes the professor back towards asking the administrator to do
it — exactly the dependency the core was built to remove.

The teaching application closes that last gap. It lets the professor
work in the vocabulary of teaching and does the translation to core
operations automatically.

---

## 2. Context

The teaching application targets the same academic environment as the
core, but it serves a narrower, more concrete workflow: setting up and
maintaining the virtual infrastructure of a university subject.

The defining characteristics of this workflow are:

- A subject is a **template for an environment**: every student gets the
  same set of machines (a *desktop*), built from the same definitions.
- The set of students changes over time (enrolment, withdrawal) but the
  environment definition stays mostly stable across a term.
- The same environment definition is often **reused across terms** with
  a different list of students.
- The professor is the operator, not the administrator. The professor
  should be able to run the whole workflow without touching the
  hypervisor or asking the administrator for anything beyond the initial
  setup (templates, hypervisors, a place in the tree).

The teaching application is one possible layer-2 application. Others
(CTF competitions, conference workshops, research labs) would follow the
same pattern over the same core, with their own vocabulary. The teaching
case is the one this project implements as a proof of concept.

---

## 3. Proposed Solution

The teaching application is a thin layer that translates two
teaching-specific inputs into core operations:

1. **A subject definition** — what every student's environment looks
   like. It is an ordinary core definition (a folder with templates),
   marked as a subject and carrying one extra concept: the *desktop*,
   the list of templates that make up a student's set of machines.

2. **A student list** — who is enrolled. A simple list of usernames.

From these two inputs the application:

- Loads the subject definition into the tree (after checking it is a
  valid subject).
- Creates one folder per student under the subject.
- Creates, inside each student folder, one descriptor per template in
  the desktop.

The result is a tree the core already understands. From that point on,
deploying, starting and stopping the machines are ordinary core
operations. The teaching application does not re-implement any of that;
it only builds the structure.

The application is distributed as a set of `teach` subcommands inside
the existing `univorch` CLI. It talks to the orchestrator daemon through
the same REST API every other client uses. It is not a separate service
and adds no new infrastructure.

---

## 4. Key Concepts

### Subject

A subject is a folder in the tree, marked with `kind: subject`. It
defines (or imports) the templates its students will use, and it
declares a *desktop*. The core stores the `kind` and `desktop` fields as
opaque metadata; only the teaching application interprets them.

### Desktop

A desktop is the list of templates that make up a single student's set
of machines. A subject whose desktop is `[workstation, server]` gives
every student two machines: a `workstation` and a `server`. A subject is
normally one desktop; the model allows more than one as a natural
extension.

### Student

A student is a folder under the subject, named after the student's
username. The folder *is* the student's identity in the tree. Creating a
student means creating the folder and its descriptors; removing a
student means removing the folder (with the appropriate safeguards — a
future concern).

The student's personal data (full name, email) lives in the user
registry, separate from the tree, exactly as the core defines it
(see core DEC-021). For this proof of concept the student list is just a
list of usernames.

### Desk (the student's view)

The student never sees the tree, the templates or the folders. The
student sees a *desk* with *computers* on it — the simplified metaphor
the core defines for end users (core DEC-009). The teaching application
is where this metaphor is given meaning: a student's desk is the set of
machines deployed under their folder.

---

## 5. Users and Roles

The teaching application serves the same three roles as the core, with a
teaching reading of each:

| Role | Teaching reading | What they do |
|---|---|---|
| `superuser` | Administrator | Sets up hypervisors, base templates and the place in the tree where subjects live. Installs the application. |
| `manager` | Professor | Runs the teaching workflow: loads subjects, loads student lists, manages the deployment of their subjects. |
| `end_user` | Student | Operates their own machines through the desk view. |

The administrator installs the application and prepares the ground; they
do not run the day-to-day teaching workflow. The professor does. The
student only uses their own machines. This is the delegation the whole
project is built to enable.

---

## 6. Scope

### Proof of concept

The proof of concept implements the minimum that demonstrates the model
end to end:

- Load a subject definition, with validation that it is a well-formed
  subject.
- Load a student list and generate the per-student folders and
  descriptors.
- Export the subject definition and the student list back out
  (`save-subject`, `save-students`).

All of this runs against the mock connector; no real hypervisor is
required.

### Out of scope for the proof of concept

- Deploying a whole subject in one command (`deploy-subject`). The
  descriptors are created in `provisioned` state; deploying them is an
  ordinary core operation, applied per machine or per branch.
- Student withdrawal (removing a student no longer on the list), which
  needs a confirmation step and a check for deployed machines.
- A dedicated web interface for the teaching workflow.
- Email notifications to students.
- Effective role-based access control (the professor seeing only their
  own branches).

These are documented as natural extensions, not as missing pieces of the
model.

---

## 7. Relationship to the Core

The teaching application is deliberately thin. Everything it does ends in
a core operation:

- A subject is loaded with the core `load`, after a teaching-level
  validation.
- Student folders and descriptors are created with the core's
  create-folder and create-descriptor operations.
- The references in the generated descriptors (`use template: …`) are
  resolved and validated by the core's resolver, with the same
  fail-fast behaviour as any other load.

The application contributes the teaching vocabulary and the workflow; the
core contributes the engine. This keeps the core reusable for other
domains and keeps the teaching logic in one place.

---

## 8. Non-Goals

The teaching application is not:

- A replacement for the core. It cannot do anything the core cannot;
  it only makes a specific workflow convenient.
- A student information system. It does not manage enrolment, grades or
  any academic record beyond the list of usernames it needs to create
  folders.
- A separate service. It is a set of subcommands of the existing CLI,
  talking to the existing daemon.
