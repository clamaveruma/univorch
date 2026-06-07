# ---------------------------------------------------------------------------
# Stage 1 — builder
# Installs dependencies into a virtual environment using uv.
# Keeping this separate from the runtime image reduces the final image size.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Copy uv binary from its official image.
# Pin to a specific version (not :latest) for reproducible builds.
# Check https://github.com/astral-sh/uv/releases for the latest version.
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

WORKDIR /app

# Copy only the project definition first so Docker can cache the dependency
# layer — it is rebuilt only when pyproject.toml changes, not on every
# source code change.
COPY pyproject.toml ./
COPY src/ ./src/

# Install production dependencies only (no dev tools in the image).
# --no-dev skips the [dev] optional group.
RUN uv sync --no-dev

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# Minimal image with only what UnivOrch needs to run.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage.
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src   /app/src

# Add the venv to PATH so 'univorch' and 'python' resolve to the right binaries.
ENV PATH="/app/.venv/bin:$PATH"

# Configuration via environment variables — override in docker-compose.yml.
ENV UNIVORCH_PORT=8080
ENV UNIVORCH_DB_PATH=/data/univorch.json

# /data is where TinyDB stores its JSON file.
# This directory MUST be mounted as a volume — without it, all data is
# lost when the container is recreated. See docker-compose.yml.
VOLUME ["/data"]

EXPOSE ${UNIVORCH_PORT}

# Start the UnivOrch REST daemon (uvicorn + FastAPI).
# Sprint 3.2 (B-2): named entry point `univorchd` registered in
# pyproject.toml. Equivalent to `python -m univorch.interfaces.rest` but
# shorter and self-documenting in `docker ps` and the logs.
CMD ["univorchd"]
