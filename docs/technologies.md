# UnivOrch — Technology Stack

> Phase 4 deliverable — technology selection and rationale
> Scope: proof of concept (v1)

This document records the technology choices for UnivOrch v1 and the reasoning
behind each one. Every choice is justified against the needs of the project as
defined in `requirements.md` and `architecture.md`. Decisions are tracked in the
internal decision index (DEC-033).

---

## 1. Language — Python 3.12

UnivOrch is written in **Python 3.12**.

Python was already established as the project language (the supervisor's
reference libraries are Python; the target audience builds on Python tooling).
The choice within Python is the version.

**Why 3.12 specifically:**

- **`@override` decorator (PEP 698).** Connectors are defined against an
  Abstract Base Class (DEC-029). `@override` makes the type checker fail early
  if a connector method does not actually correspond to a method in the base
  class — catching a whole class of mistakes (typos, signature drift) before
  runtime.
- **Performance.** The 3.12 interpreter is roughly 10–20% faster than 3.11 on
  typical workloads, at no cost to us.
- **Clearer error messages.** 3.12 continues the line of more precise
  tracebacks and error hints, which matters for an academic, open-source
  project that other developers will pick up.
- **Support window.** Python 3.12 receives security support until 2028,
  comfortably beyond the lifetime of the proof of concept.

Because UnivOrch ships as a container, the Python version is fixed by the image
and does not depend on the host operating system.

---

## 2. Testing — pytest + pytest-cov + Hypothesis

- **pytest** is the test runner. The decisive factor is integration: both
  **NiceGUI** (web GUI) and **cmd2** (CLI) publish their testing utilities as
  pytest plugins. Choosing pytest means the interface layers are testable with
  their own first-class tooling instead of fighting the framework.
- **pytest-cov** measures line and branch coverage. Branch coverage in
  particular surfaces untested error paths — valuable given how much of the
  design is about failure handling (states, drift, unreachable hypervisors).
  Coverage is treated as an indicator of what is *not* yet tested, not as a
  proof of correctness.
- **Hypothesis** (property-based testing) is used for the **Resolver**. The
  Resolver is modelled as a pure function `(ancestors, imports) → effective
  definition` (DEC-026). Pure functions with clear algebraic properties are the
  ideal target for property-based testing: instead of hand-picked examples,
  Hypothesis generates many inputs and checks invariants (e.g. scalar replaces,
  list accumulates, map merges).

---

## 3. Dependency manager — uv

Dependencies and the project environment are managed with **uv** (by Astral).

- uv is a **single Rust binary**, installed as a program rather than a Python
  module. It is significantly faster than pip/virtualenv-based workflows and
  resolves and locks dependencies deterministically.
- In the Docker build, uv is brought in with a multi-stage copy from its
  official image, pinning a fixed version for reproducibility:

  ```dockerfile
  COPY --from=ghcr.io/astral-sh/uv:<pinned-version> /uv /usr/local/bin/uv
  ```

  A pinned version (not `:latest`) guarantees that the same Dockerfile produces
  the same build over time.

### pyproject.toml

The project uses a single **`pyproject.toml`** as unified configuration. It
replaces `setup.py`, `requirements.txt`, and the several `*.ini` files older
projects accumulate. All tooling (uv, pytest, Ruff, mypy) reads its
configuration from this one file.

Dependencies are split so that nothing unnecessary ships to production:

```toml
[project]
dependencies = [
    # what UnivOrch needs to run
    "tinydb",
    "nicegui",
    "cmd2",
    "ruamel.yaml",
]

[project.optional-dependencies]
dev     = ["pytest", "pytest-cov", "hypothesis", "ruff", "mypy"]
vmware  = ["pyvmomi"]
proxmox = ["proxmoxer"]
```

---

## 4. Distribution — docker-compose + thin shell script

UnivOrch is distributed as a container image (published on **ghcr.io**),
orchestrated with **docker-compose** and wrapped by a **thin shell script**.

**Why docker-compose rather than a bare `docker run`:**

- It makes the **TinyDB persistence volume explicit and hard to forget**. This
  is a critical risk: without a mounted volume, recreating the container loses
  the entire database. Declaring it in `docker-compose.yml` makes persistence a
  visible, reviewed part of the deployment rather than a flag someone might
  omit.
- It **scales naturally to the future MongoDB setup** (DEC-030): MongoDB
  becomes an additional service in the same compose file, with no change in
  deployment philosophy.

**The shell script** is a thin convenience wrapper around
`docker compose up / down / restart` and the decision of whether UnivOrch
starts with the system. It contains no business logic — it exists so an
administrator does not have to remember compose invocations.

---

## 5. Code quality — Ruff + mypy

- **Ruff** (by Astral, same vendor as uv) is the linter *and* formatter, in a
  single Rust tool. It replaces the older stack of flake8 + isort + black with
  one fast tool, configured in `pyproject.toml`. It enforces PEP 8 style and
  catches common defects.
- **mypy** is the static type checker, kept separate from Ruff. It validates
  the things that matter most structurally in this codebase: the ABC connector
  contracts (DEC-029) and the Resolver function signatures (DEC-026).

**Where they live:** these are **development tools only**. They are declared
under `[project.optional-dependencies] dev` and are **not** installed in the
production container — the production image runs only what UnivOrch needs to
execute. They are used in two places:

- **Locally**, integrated into VSCode via official extensions (inline
  diagnostics, format-on-save for Ruff, type-error highlighting for mypy).
- **In CI/CD** (GitHub Actions) as an automated quality gate: each push runs
  `ruff check`, `ruff format --check`, and `mypy`. A failure stops the change
  before it reaches the main branch — a safety net independent of any
  developer's local setup.

---

## 6. Hypervisor client libraries

Hypervisor SDKs are **dependencies of each concrete connector, not of the
core** (DEC-029). The core never imports them. They are modelled as optional
extras in `pyproject.toml`, so an operator who only uses Proxmox does not
install the VMware library, and the mock works with neither.

### VMware — pyvmomi

**pyvmomi** is VMware's **official Python SDK**, maintained by VMware. It speaks
the vSphere SOAP API (the long-standing management API of vCenter/ESXi) and
covers everything UnivOrch needs: clone, delete, start/stop, status.

The vSphere API is verbose and carries VMware-specific concepts (managed
objects, `vim` types). Hiding that complexity behind the connector ABC is
precisely the purpose of the connector layer. The more recent REST-based
vSphere Automation SDK was considered but does not cover the full set of VM
management operations and is less mature; for a proof of concept pyvmomi is the
safe choice — and it is what the supervisor's `esxobjects` uses, which makes the
final comparative evaluation (DEC-029) more direct.

### Proxmox — proxmoxer

Proxmox publishes **no official Python SDK**, only a documented REST API.
**proxmoxer** is the community's de-facto library: a thin, well-maintained
wrapper over that REST API, recommended by the Proxmox documentation itself.
Using it instead of hand-calling the REST API avoids reinventing proxmoxer,
worse.

### Mock — no dependency

The mock connector talks to nothing external. It is pure Python implementing
the same `HypervisorConnector` ABC, with **in-memory state**. It enables TDD of
the entire orchestrator and error-handling logic without a real hypervisor
(DEC-029).

Its in-memory structure has two parts:

- **Base templates** — preloaded by an initialisation function. These are the
  sources for linked clones; without at least one, `clone()` has nothing to
  clone from.
- **Deployed VMs** — initially empty; populated as the orchestrator calls
  `clone()` and removed by `delete()`. This is where runtime state
  (running/stopped/paused) and simulated drift live.

Initialisation comes in variants for different scenarios:

```python
MockConnector.empty()                  # bare hypervisor, no templates
MockConnector.with_defaults()          # sensible templates preloaded (common TDD case)
MockConnector.with_templates([...])    # explicit templates for a specific test
```

The mock additionally exposes test-only inspection and injection methods that
real connectors do not have and that are **not part of the ABC**
(`deployed_vms()`, `inject_drift()`, `make_unreachable()`). These let tests
control exactly what to simulate without hacks.

A mock-as-REST-service variant (out-of-process) was considered. It would
exercise the out-of-process seam — serialisation, real network errors, latency
— more faithfully, but it is deliberately deferred: v1 connectors are
in-process, so an in-process mock is consistent with what actually needs
testing in v1. The variant is recorded as future work for when a connector is
externalised to a separate service.

---

## 7. Summary

| Concern | Choice | Key reason |
|---|---|---|
| Language | Python 3.12 | `@override` for ABC connectors; faster; supported to 2028 |
| Test runner | pytest | NiceGUI and cmd2 ship pytest plugins |
| Coverage | pytest-cov | surfaces untested error/branch paths |
| Property testing | Hypothesis | ideal for the pure-function Resolver |
| Dependency manager | uv | fast, reproducible, single binary |
| Project config | pyproject.toml | one unified file, all tools read it |
| Distribution | docker-compose + thin script | makes TinyDB volume explicit; scales to MongoDB |
| Linter + formatter | Ruff | one Rust tool replacing flake8/isort/black |
| Type checker | mypy | validates ABC contracts and Resolver signatures |
| VMware client | pyvmomi | official SDK; matches supervisor's library |
| Proxmox client | proxmoxer | de-facto community wrapper; no official SDK |
| Mock | none (in-memory) | TDD without a real hypervisor |

Development-only tooling (pytest, pytest-cov, Hypothesis, Ruff, mypy) is
isolated under `[project.optional-dependencies] dev` and never reaches the
production container. Hypervisor SDKs are optional extras tied to their
connector, never to the core.
