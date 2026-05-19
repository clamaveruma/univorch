#!/usr/bin/env bash
# Thin wrapper around docker compose for managing the UnivOrch service.
# Usage: ./univorch.sh {start|stop|restart|status|logs|cli}

set -euo pipefail

COMPOSE_FILE="$(dirname "$(realpath "$0")")/docker-compose.yml"

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
        docker compose -f "$COMPOSE_FILE" up -d
        echo "UnivOrch started."
        echo "Web UI (Sprint 2+): http://localhost:${UNIVORCH_PORT:-8080}"
        echo "CLI: ./univorch.sh cli"
        ;;
    stop)
        docker compose -f "$COMPOSE_FILE" down
        ;;
    restart)
        docker compose -f "$COMPOSE_FILE" restart
        ;;
    status)
        docker compose -f "$COMPOSE_FILE" ps
        ;;
    logs)
        docker compose -f "$COMPOSE_FILE" logs -f
        ;;
    cli)
        # Open an interactive CLI session inside the running container.
        # The container must already be started with './univorch.sh start'.
        docker exec -it univorch univorch
        ;;
    *)
        usage
        ;;
esac
