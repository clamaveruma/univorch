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
        echo "REST API:   http://localhost:${UNIVORCH_PORT:-8080}/api/v1/"
        echo "Health:     http://localhost:${UNIVORCH_PORT:-8080}/api/v1/health"
        echo "Interactive CLI: ./univorch.sh cli"
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
