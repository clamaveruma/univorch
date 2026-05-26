# UnivOrch — Sprint 1 demo guide

> **Status:** this guide describes the Sprint 1 demo. It will be fully
> functional when Sprint 1 development is complete.

UnivOrch is a proof-of-concept virtual machine orchestrator. This demo
shows the core workflow using a **mock connector** — no real hypervisor
is needed. The mock simulates VM operations in memory.

---

## Prerequisites

- Docker Engine ≥ 24 and Docker Compose ≥ 2.20
- The repository cloned locally

---

## Start the service

```bash
chmod +x univorch.sh
./univorch.sh start     # builds the image and starts the container
./univorch.sh status    # confirm it is running
```

---

## Demo walkthrough

Open an interactive CLI session:

```bash
./univorch.sh cli
```

You will see the UnivOrch prompt. Run these commands in order:

### 1. Apply the example setup

```
univorch> apply demo/setup.yml
```

This creates two folders (`/lab`, `/lab/networks`) and three descriptors,
each in `provisioned` state. A descriptor in `provisioned` means the
definition exists in the orchestrator but no VM has been created yet in
the hypervisor.

### 2. Inspect the tree

```
univorch> tree /
```

`tree` shows the whole subtree: the two folders and the three descriptors,
each with a state glyph (`□` provisioned, `■` deployed, `✗` broken,
`▲` unreachable). `list` shows only one level, like `ls`.

### 3. Navigate into the subject folder

```
univorch> cd /lab/networks
univorch /lab/networks>
```

The prompt changes to show your current folder. You can now use relative
paths.

### 4. Deploy a VM

```
univorch /lab/networks> deploy student01
```

The orchestrator creates a Job, asks the mock connector to clone the
`linux-base` template, and updates the descriptor state to `deployed`.
The mock simulates the clone in memory — instant, no real hardware needed.

### 5. Check the descriptor state

```
univorch /lab/networks> status student01
```

You should see:
- **Orchestrator state:** `deployed`
- **Runtime state (hypervisor):** `stopped`
- **VM id:** the mock VM identifier

### 6. Start the VM

```
univorch /lab/networks> start student01
```

The orchestrator sends a start command to the mock connector. The runtime
state changes to `running`.

### 7. Check state again

```
univorch /lab/networks> status student01
```

Now runtime state is `running`.

### 8. Stop and undeploy

```
univorch /lab/networks> stop student01
univorch /lab/networks> undeploy student01
```

`undeploy` deletes the VM from the mock connector and returns the
descriptor to `provisioned`. The definition remains — you can deploy again.

### 9. Batch: deploy all three students

```
univorch /lab/networks> deploy student01
univorch /lab/networks> deploy student02
univorch /lab/networks> deploy student03
univorch /lab/networks> list
```

`list` without a path shows the contents of the current folder.

### 10. Exit the REPL

```
univorch /lab/networks> exit
```

---

## Same commands in bash mode (for scripts)

All commands work without the REPL. Useful for shell scripts:

```bash
./univorch.sh cli apply demo/setup.yml
./univorch.sh cli deploy /lab/networks/student01
./univorch.sh cli status /lab/networks/student01
./univorch.sh cli start  /lab/networks/student01
```

---

## What is happening inside

- **Descriptor tree:** the orchestrator stores folders and descriptors in
  a TinyDB JSON file (a document database in a single file). Each node
  has a full path as its key — a pattern called *materialized path*.

- **Jobs:** every operation (deploy, start, stop, undeploy) creates a
  Job record in the database with a unique ID and a lifecycle:
  `pending → running → completed / failed`. The Job history is the audit
  trail of everything the orchestrator has done.

- **Mock connector:** implements the same interface (`HypervisorConnector`
  ABC) as the real VMware and Proxmox connectors. The orchestrator core
  does not know or care which connector is in use — it only calls the
  common interface. This is the extensibility point for real hypervisors.

- **Descriptor states:** `provisioned` (definition exists, no VM),
  `deployed` (VM exists and matches the definition), `broken` (failed
  operation), `unreachable` (hypervisor not reachable).
