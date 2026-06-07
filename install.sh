#!/usr/bin/env bash
# UnivOrch installer — Sprint 3.4 (B-2 model).
#
# Drops two files in ./univorch/: the docker-compose recipe and the
# wrapper script. Does NOT start the service — that is the user's
# explicit next step. Walks through the obvious pre-flight checks so
# typical failures (missing Docker, wrong group, busy port) surface up
# front with actionable messages instead of opaque ones later.
#
# Run with:
#   curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/install.sh | bash

set -euo pipefail

# --- Configuration --------------------------------------------------------

REPO_RAW="https://raw.githubusercontent.com/clamaveruma/univorch/main"
INSTALL_DIR="${UNIVORCH_INSTALL_DIR:-$PWD/univorch}"
DEFAULT_PORT="${UNIVORCH_PORT:-8080}"

# --- Colours (only if stdout is a tty) ------------------------------------

if [ -t 1 ]; then
    BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    RED=$'\033[31m'; BLUE=$'\033[34m'; RESET=$'\033[0m'
else
    BOLD=''; GREEN=''; YELLOW=''; RED=''; BLUE=''; RESET=''
fi

info()    { echo "${BLUE}[univorch]${RESET} $*"; }
ok()      { echo "${GREEN}[univorch]${RESET} $*"; }
warn()    { echo "${YELLOW}[univorch]${RESET} $*" >&2; }
fail()    { echo "${RED}[univorch]${RESET} $*" >&2; exit 1; }

# --- Pre-flight checks ----------------------------------------------------

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        fail "Docker no está instalado. Instálalo desde https://docs.docker.com/get-docker/ y vuelve a ejecutar este instalador."
    fi
    # 'docker compose' (plugin v2) preferred over 'docker-compose' (legacy v1).
    if ! docker compose version >/dev/null 2>&1; then
        fail "Docker está, pero 'docker compose' (v2) no responde. Asegúrate de tener el plugin instalado (paquete docker-compose-plugin o equivalente)."
    fi
    ok "Docker y docker compose disponibles."
}

check_docker_access() {
    # Try the cheapest possible command: 'docker info' touches the socket.
    if docker info >/dev/null 2>&1; then
        ok "Acceso al daemon de Docker confirmado."
        return
    fi
    cat <<EOF >&2
${RED}[univorch]${RESET} No se puede hablar con el daemon de Docker.
   Causas típicas:
     - El daemon no está corriendo: 'sudo systemctl start docker'
     - Tu usuario no está en el grupo 'docker' y no estás usando 'sudo'.
       Solución rápida (esta vez): ejecuta el instalador con 'sudo bash'.
       Solución permanente: 'sudo usermod -aG docker \$USER' y vuelve a
       iniciar sesión.

EOF
    exit 1
}

check_port() {
    local port=$1
    # ss is universally installed on modern Linux; lsof is a fallback.
    if command -v ss >/dev/null 2>&1; then
        ss -tln 2>/dev/null | awk '{print $4}' | grep -qE ":${port}\$"
    elif command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"${port}" -sTCP:LISTEN -t >/dev/null 2>&1
    else
        # No tool: assume it is free (the user will see the error later).
        return 1
    fi
}

pick_port() {
    local port=$DEFAULT_PORT
    if ! check_port "$port"; then
        ok "Puerto ${port} libre."
        echo "$port"
        return
    fi

    warn "Puerto ${port} ocupado en este host."
    if command -v ss >/dev/null 2>&1; then
        local who
        who=$(ss -tlnp 2>/dev/null | awk -v p=":${port}\$" '$4 ~ p {print $0}' | head -n1)
        [ -n "$who" ] && warn "Detalle: ${who}"
    fi

    # Are we attached to a real terminal? If piped from curl|bash, /dev/tty
    # is still attached to the user's shell — read from it explicitly.
    local new_port=""
    if [ -e /dev/tty ]; then
        echo -n "${BOLD}Indica un puerto libre alternativo [9090]:${RESET} " >/dev/tty
        IFS= read -r new_port </dev/tty || new_port=""
    fi
    new_port=${new_port:-9090}

    if check_port "$new_port"; then
        fail "Puerto ${new_port} también ocupado. Aborto. Libera uno y vuelve a ejecutar."
    fi
    ok "Usaremos el puerto ${new_port} del host."
    echo "$new_port"
}

# --- Download phase -------------------------------------------------------

download() {
    local url=$1 dest=$2
    if ! curl -fsSL "$url" -o "$dest"; then
        fail "Fallo al descargar ${url}. Revisa tu conexión o la URL del repositorio."
    fi
}

# --- Main flow ------------------------------------------------------------

main() {
    echo "${BOLD}UnivOrch — instalador${RESET}"
    echo

    check_docker
    check_docker_access

    local port
    port=$(pick_port)

    mkdir -p "$INSTALL_DIR"
    info "Descargando ficheros en ${INSTALL_DIR}/"

    download "${REPO_RAW}/univorch.sh"        "${INSTALL_DIR}/univorch.sh"
    download "${REPO_RAW}/docker-compose.yml" "${INSTALL_DIR}/docker-compose.yml"
    chmod +x "${INSTALL_DIR}/univorch.sh"
    ok "univorch.sh y docker-compose.yml listos."

    # Persist the chosen port so 'univorch.sh start' uses it on first run.
    # Writing into .env keeps the choice across reboots without surprising
    # the user (docker compose reads .env automatically from its dir).
    if [ "$port" != "8080" ]; then
        echo "UNIVORCH_PORT=${port}" > "${INSTALL_DIR}/.env"
        info "Puerto del host fijado a ${port} en .env"
    fi

    echo
    echo "${BOLD}Listo.${RESET} Próximos pasos:"
    echo
    echo "  cd ${INSTALL_DIR}"
    echo "  ./univorch.sh start          ${BLUE}# arranca el contenedor${RESET}"
    echo "  ./univorch.sh cli            ${BLUE}# entra al REPL${RESET}"
    echo
    echo "Si tu usuario no está en el grupo 'docker', usa 'sudo ./univorch.sh start'."
    echo "El tutorial completo: https://github.com/clamaveruma/univorch/blob/main/docs/tutorial-profesor.md"
}

main "$@"
