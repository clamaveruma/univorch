# UnivOrch — Glossary

This document is the reference vocabulary for UnivOrch. Two audiences:

- **Project authors and reviewers:** terms used in architecture, requirements,
  decisions and the TFG memoria.
- **Product users:** terms surfaced in the CLI help, error messages and the
  future user guide.

A small but important rule guides the choice of words by layer: **external
language is "VM"; internal language is "descriptor"** (DEC-005). See [The two
layers of vocabulary](#the-two-layers-of-vocabulary) at the end.

---

## The tree

**Folder.** A node of the orchestrator's tree that groups other folders and
VMs. A folder carries its own definitions (description, hypervisors and
templates declared inside, IP pool, permissions, imports from its parent…).
Folders form the tree rooted at `/` (DEC-005, DEC-026).

**Path / materialized path.** The full slash-separated path that identifies a
folder or VM uniquely, e.g. `/lab/networks/student01`. We store the path
explicitly on each persisted node — the *materialized path* pattern — so a
subtree is a path-prefix query (DEC-030).

**Descriptor.** The orchestrator's internal representation of a VM: a record
with definition (hypervisor, base VM, specs, description, permissions…) and a
small amount of runtime state (`state`, `vm_id`). The name pays homage to the
file descriptor of an OS — a handle that *represents* a resource without being
the resource (DEC-005). **In code, in this glossary and in the TFG memoria:
always "descriptor". In user-facing surfaces (CLI help, errors, the web GUI):
always "VM".**

**VM (virtual machine).** The actual virtual machine that lives inside a
hypervisor. Distinct from the descriptor: a `provisioned` descriptor has *no
VM* yet; a `deployed` descriptor is mapped to a VM identified by `vm_id`.

---

## The hypervisor side

**Hypervisor.** The external system that runs virtual machines (VMware
vSphere, Proxmox VE, our `mock`). UnivOrch is agnostic to which hypervisor a
descriptor uses: it talks to each via a connector that implements a common
contract. From Sprint 2 onwards a folder can `define hypervisors:` to register
named hypervisors visible to its subtree (DEC-010, DEC-016, DEC-029).

**Base VM.** The model VM that lives **in the hypervisor** and serves as the
source for `clone()`. It is not managed by the orchestrator; the orchestrator
references it by name (`base_vm`). The hypervisor admin is responsible for
creating and maintaining base VMs.

**Template** *(Sprint 2)*. An alias declared inside a folder (`define machine
templates:`) that names a configuration combining a `base_vm` with extra
parameters (CPU, memory, datastore aliases…). Templates can be derived from
other templates via `based on:`. **A template is an orchestrator artifact**,
*distinct* from the base VM that lives in the hypervisor. Templates flow down
the tree by cascade inheritance.

**Connector.** The Python class that adapts a hypervisor's API to the common
contract. The base contract is the `HypervisorConnector` abstract class
(`clone`, `delete`, `start`, `stop`, `pause`, `resume`, `force_stop`,
`get_status`, `get_info`). v1 ships `MockConnector` (in-memory); Sprint 3+
adds real connectors (`VMwareConnector` via pyvmomi, `ProxmoxConnector` via
proxmoxer). DEC-016, DEC-029.

---

## Definitions and the resolver

**Definition.** What is *written* inside a folder or a descriptor:
declarative configuration data (hypervisor name, base VM, specs, description,
imports, permissions, IP pool…). Distinct from *state*, which is what the
orchestrator observes or has done.

**Local definition.** A definition exactly as written at one specific node of
the tree (the YAML the user wrote, without considering any inheritance).

**Effective definition** *(Sprint 2)*. The definition of a descriptor after
applying cascade inheritance from all ancestors and the imports each one
declares. Computed by the `Resolver`.

**Cascade inheritance** *(Sprint 2, DEC-026)*. The mechanism by which a
folder's children take their definitions from the folder above (and that
folder's ancestors). Combination rules **by data type**:
- *Scalar* (string, int…) → child replaces parent.
- *List of strings* (e.g. `import`, `managers`, `end_users`) → child
  accumulates onto parent's list.
- *Map* → recursive merge by key, with declarable exceptions where the whole
  map is replaced instead (today: `ip_pool`).

Our schema has **no lists of collections**, which sidesteps the otherwise
thorny question of "are these two list items the same item?". Lists are
strings; collections are dicts keyed by name (folders, descriptors,
hypervisors, templates) where recursive merge is well-defined.

**Import** *(Sprint 2, DEC-012)*. A folder declares what it brings in from its
parent (`import: ALL` or `import: [linux-base, hyperv*]`). Only what is
imported is visible at this level and below. Whoever creates a sub-folder
decides what to import — at that moment they are the effective owner of the
parent.

**Resolver** *(Sprint 2)*. A pure function `(tree, path) → effective
definition`, modelled as `(ancestors, imports) → effective definition`. It is
called lazily by the service and by the future web GUI. The same resolver
will be used for permissions later (DEC-026: permissions and definitions are
the same problem).

**Annotated mode** *(future)*. A second mode of the resolver that returns,
for every field, both the value **and the node where it came from**. Drives
the web editor that shows inherited fields in another colour with a tooltip
to the source. Postponed past Sprint 2.

### Common syntax for inheritable resources

Every inheritable resource the user declares inside a folder follows the same
three-piece shape. Today this covers hypervisors and machine templates;
tomorrow datastores, IP pools, and more will plug into the same pattern
(specific quirks will be noted as exceptions, e.g. IP pools may be assigned
implicitly per folder rather than via `use`).

**Declare it** with `define <plural>:` in the folder where the resource lives:

```yaml
lab/:
  define hypervisors:
    mock01: { type: mock }
  define templates:
    linux-vm: { use hypervisor: mock01, base_vm: linux-base, cpu: 2 }
```

**Import it** into a descendant folder that uses it:

```yaml
networks/:
  import: [linux-vm]
```

**Reference it** with `use <singular>:` from a descriptor or another resource:

```yaml
student01: { use template: linux-vm }
```

**Closure (lexical environment).** A resource's internal references are
resolved from the folder where the resource is defined, not from the folder
where it is used. In the example above, `linux-vm` references `mock01`; that
reference resolves against `/lab` (where `linux-vm` lives), so
`/lab/networks` only needs to import `linux-vm`. It does not need to import
`mock01` as well. This matches how a function carries its lexical environment
in a language with closures.

**Combination rule.** When the same resource name is defined at multiple
levels, the cascade combination rule above applies (scalar replaces, list
accumulates, map merges recursively, with declarable exceptions). Today no
resource overrides itself in practice; the rule is in place for the future
when it does.

---

## State

UnivOrch tracks state on **two orthogonal axes** (DEC-022, DEC-032).

**Descriptor state** (the orchestrator's own state, stored in the DB):
- `provisioned` — definition exists, no VM in the hypervisor.
- `deployed` — a VM exists in the hypervisor, mapped through `vm_id`.
- `broken` — a lifecycle operation failed halfway leaving the
  descriptor↔VM mapping uncertain; needs `force-undeploy`.
- `unreachable` — last operation failed by communication with the hypervisor.

**Runtime state** (the VM's power state, lives in the hypervisor and is queried
on demand): `running`, `stopped`, `paused`, `unknown`.

The CLI's `list`/`ls` only shows the descriptor axis (cheap, DB-only). `status`
shows both axes (one query to the hypervisor). A future `list --live` would
combine the two with streaming.

---

## Operations

**Operation.** Any action the orchestrator performs: deploy, undeploy, start,
stop, create a folder, create a descriptor… Every operation has a target (a
path) and produces a record.

**OperationType.** The enum that names each kind of operation
(`DEPLOY`, `UNDEPLOY`, `START`, `STOP`, `CREATE_FOLDER`, `CREATE_DESCRIPTOR`,
…). Acts as an op-code.

**Command.** The *executable* form of an operation, in memory. Each Command
class encapsulates the logic for one operation type and exposes `validate()`
(returns the list of errors; empty = OK) and `execute()` (runs the work and
returns a result message). Command pattern (DEC-028).

**Job.** The *recorded* form of an operation, persisted to the database. Carries
the operation type, target, status (`pending → running → completed/failed`),
timestamps and result message. **A descriptor's state changes only as the
result of a Job.** A Command execution produces exactly one Job (DEC-014,
DEC-015, DEC-028, DEC-032).

---

## Actions

**Load.** The action of loading a YAML definition into a destination folder
of the tree. The YAML is relative (no paths inside); the destination is given
to the command (default: the current folder in REPL). `load` never modifies
the destination's own properties — only what goes inside (DEC-027 as
implemented after 2026-05-26).

**Save** *(future)*. The inverse of `load`: extract a folder's subtree to a
new YAML in relative form. Preserves local definitions, not effective
definitions (round-trip fidelity).

**Apply** *(deprecated)*. The previous name of `load`, when YAMLs carried
absolute paths. The CLI command and the document model both renamed in the
2026-05-26 refactor. The decision label `DEC-027 — Declarative apply/plan
flow` keeps its historical name.

**Plan / dry-run.** A `load` (or future bulk write) without execution: the
`validate()` of every Command is run, and the would-be results are reported,
without touching the system. Implementation detail of the same engine used
by `load`.

---

## Permissions

**RBAC** *(Sprint 5+, DEC-011, DEC-021, DEC-031)*. Role-based access control.
Three fixed roles in v1:
- **superuser** — full control. Assigned at the root.
- **manager** — defines and manages branches (typically professors).
- **end_user** — uses the VMs assigned to them (typically students).

A user can hold different roles in different branches of the tree. Roles flow
down with cascade inheritance just like definitions; the resolver computes
the effective set of roles for any (user, path) pair. Permissions checks
live in the facade (`OrchestratorService`), never in the interfaces.

---

## The two layers of vocabulary

The same concept may have two names: one for code and academic writing, one
for end users. The boundary is **the user-facing surface**.

| Concept | Internal (code, docs, TFG) | External (CLI, errors, web GUI) |
|---|---|---|
| The orchestrator's record for a VM | `descriptor` | `VM` |
| Anything else | same word in both | same word in both |

For the teaching application (Sprint final, layer 2) the boundary widens
further with DEC-009: the student sees **desks** ("mesa") and **computers**
("ordenador") instead of folders and VMs.

When in doubt: any text that appears in `help cd`, `perror`, the future web
UI or the user guide says **VM**; any text inside `.py` files, in `docs/` or
in `claude/` says **descriptor**.
