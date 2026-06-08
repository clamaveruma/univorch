#!/usr/bin/env bash
# Thin wrapper around docker compose for managing the UnivOrch service.
# Usage: ./univorch.sh {start|stop|restart|status|logs|cli}
#
# Compose v1 vs v2: prefers the v2 plugin ('docker compose') when present,
# falls back to the legacy v1 binary ('docker-compose'). v1 is still the
# default on Debian/Ubuntu/Mint installs that come from the distro repo
# instead of the official Docker one.

set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

# Load .env if present so messages printed by this wrapper expand
# UNIVORCH_PORT to the value the installer wrote. (docker compose
# reads .env on its own; this 'source' is only for the echo lines.)
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$SCRIPT_DIR/.env"
    set +a
fi

# Resolve the compose command into an array so we can expand it cleanly
# (otherwise quoting 'docker compose' as one string breaks the argv split).
if docker compose version >/dev/null 2>&1; then
    COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE=(docker-compose)
else
    echo "Error: ni 'docker compose' (v2) ni 'docker-compose' (v1) están disponibles." >&2
    echo "Instala el plugin: https://docs.docker.com/compose/install/" >&2
    exit 1
fi

usage() {
    cat <<EOF
Usage: $(basename "$0") COMMAND

Commands:
  start    Start UnivOrch in the background
  stop     Stop UnivOrch
  restart  Restart UnivOrch
  status   Show container status
  logs     Follow service logs (Ctrl+C to exit)
  cli      Open an interactive CLI session inside the container
EOF
    exit 1
}

case "${1:-}" in
    start)
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" up -d
        echo "UnivOrch started."
        echo "Web GUI:    http://localhost:${UNIVORCH_PORT:-8080}/"
        echo "REST API:   http://localhost:${UNIVORCH_PORT:-8080}/api/v1/"
        echo "Health:     http://localhost:${UNIVORCH_PORT:-8080}/api/v1/health"
        echo "Interactive CLI: ./univorch.sh cli"
        ;;
    stop)
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" down
        ;;
    restart)
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" restart
        ;;
    status)
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" ps
        ;;
    logs)
        "${COMPOSE[@]}" -f "$COMPOSE_FILE" logs -f
        ;;
    cli)
        # Open the CLI inside the running container. Two modes:
        #   - './univorch.sh cli'              -> interactive REPL (tty + stdin)
        #   - './univorch.sh cli <comando...>' -> single command (bash mode)
        # The CLI talks HTTP to the daemon at http://localhost:8080, which
        # is the daemon running as PID 1 of this same container.
        shift  # drop the literal 'cli' from "$@"
        if [ $# -eq 0 ]; then
            docker exec -it univorch univorch
        else
            # Bash mode: only -i (stdin), no -t (no TTY) so scripts that
            # redirect the output do not get pseudo-terminal escapes.
            docker exec -i univorch univorch "$@"
        fi
        ;;
    *)
        usage
        ;;
esac
