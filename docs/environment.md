# UnivOrch — Development and Deployment Environment

> Phase 5 deliverable — environment configuration

---

## Prerequisites

### Production deployment

- Docker Engine ≥ 24 and Docker Compose ≥ 2.20
- No other software required — UnivOrch and all its dependencies run inside the container

### Development

- Docker Engine ≥ 24
- Visual Studio Code with the following extensions:
  - **Remote - SSH** (if working on a remote server)
  - **Dev Containers**
  - **Claude Code** (`anthropic.claude-code`) — installed automatically inside the container

---

## Quick start — production

```bash
git clone https://github.com/clamaveruma/univorch.git
cd univorch
chmod +x univorch.sh
./univorch.sh start
```

Available commands:

| Command | Effect |
|---|---|
| `./univorch.sh start` | Start UnivOrch in the background |
| `./univorch.sh stop` | Stop UnivOrch |
| `./univorch.sh restart` | Restart (picks up config changes) |
| `./univorch.sh status` | Show container status |
| `./univorch.sh logs` | Follow live logs |
| `./univorch.sh cli` | Open an interactive CLI session |

### Configuration

Override defaults with environment variables before calling `univorch.sh`:

```bash
UNIVORCH_PORT=9090 ./univorch.sh start   # use port 9090 instead of 8080
```

| Variable | Default | Description |
|---|---|---|
| `UNIVORCH_PORT` | `8080` | Web GUI port (Sprint 2+) |
| `UNIVORCH_DB_PATH` | `/data/univorch.json` | TinyDB file path inside container |

### Data persistence

UnivOrch stores all data in a single TinyDB JSON file, mounted into the container
as a Docker named volume (`univorch_data`). This volume **must not be removed** while
the service holds data. To back up:

```bash
# Find the volume path on the host
docker volume inspect univorch_univorch_data

# Copy the JSON file to a safe location
cp <volume-mountpoint>/univorch.json ~/univorch-backup-$(date +%F).json
```

---

## Development environment

The repository includes a `.devcontainer/devcontainer.json` that defines a
fully reproducible development environment. The same file works in three setups:

### Option A — VSCode + local Docker

1. Install Docker Desktop (Mac/Windows) or Docker Engine (Linux)
2. Open the repo folder in VSCode
3. When prompted, click **Reopen in Container**

All tools (Python 3.12, uv, Ruff, mypy, pytest, Claude Code) are installed
automatically inside the container.

### Option B — VSCode + SSH remote server (recommended for Phase 6)

This option places the development container on a Linux server in your network.
Advantages: no hour limits, direct network access to VMware/Proxmox hypervisors
on the same network for testing with real connectors.

1. Install the **Remote - SSH** extension in your local VSCode
2. On the server: install Docker Engine and clone the repository
3. In VSCode: connect to the server via Remote - SSH → open the repo folder
4. When prompted, click **Reopen in Container**

The container runs on the server; your VSCode UI runs locally. The terminal
you see in VSCode is inside the container on the server.

### Option C — GitHub Codespaces

1. Open the repository on GitHub
2. Click **Code → Codespaces → Create codespace on main**

The same `devcontainer.json` is used. Note: the free GitHub plan provides
approximately 60 hours of compute per month on a 2-core Codespace — suitable
for documentation and short sessions, but limited for intensive development.

---

## Installing dependencies (inside the dev container)

```bash
# Install all dependencies including dev tools
uv sync --extra dev

# Install with a specific optional connector
uv sync --extra dev --extra vmware
```

---

## Running tests

```bash
# Run the full test suite with branch coverage report
uv run pytest

# Run only unit tests
uv run pytest tests/unit/

# Run a specific test file
uv run pytest tests/unit/test_resolver.py -v
```

---

## Code quality checks

```bash
# Lint (style and common errors)
uv run ruff check src/ tests/

# Format (auto-fix formatting)
uv run ruff format src/ tests/

# Type check
uv run mypy src/univorch/
```

These same checks run automatically in CI (GitHub Actions) on every push to `main`.

---

## Project structure

```
univorch/
├── src/univorch/          # application source code (src-layout)
│   ├── connectors/        # HypervisorConnector ABC + implementations
│   ├── jobs/              # Job engine, Command pattern
│   ├── persistence/       # Repository interfaces + TinyDB implementation
│   └── interfaces/
│       ├── cli/           # cmd2 command-line interface
│       └── web/           # NiceGUI web GUI (Sprint 2+)
├── tests/
│   ├── unit/              # isolated unit tests
│   ├── integration/       # service-level tests with TinyDB + MockConnector
│   └── conftest.py        # shared fixtures
├── demo/                  # example YAML files and demo guide for the professor
├── docs/                  # formal phase deliverables (English)
├── claude/                # AI-assisted development context (Spanish)
├── Dockerfile             # production container image
├── docker-compose.yml     # volume, port, and service configuration
├── univorch.sh            # thin wrapper script for operators
├── pyproject.toml         # unified project config (deps, Ruff, mypy, pytest)
└── .devcontainer/         # reproducible development environment for VSCode
    └── devcontainer.json
```

---

## CI/CD pipeline

GitHub Actions runs `.github/workflows/ci.yml` on every push and pull request:

1. **Ruff lint** — style and common error checks
2. **Ruff format** — verifies files are correctly formatted
3. **mypy** — validates type annotations and ABC contracts
4. **pytest** — runs the full test suite with branch coverage

A failed check blocks the commit from being considered passing on GitHub.
No manual intervention is required — the pipeline runs automatically.
