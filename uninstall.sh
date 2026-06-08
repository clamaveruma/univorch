#!/usr/bin/env bash
# UnivOrch uninstaller — symmetric to install.sh.
#
# Stops the running container and, depending on the flags, also removes
# the local files, the persistent volume (which holds the database) and
# the Docker image.
#
# Run with:
#   curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/uninstall.sh | sudo bash -s -- --yes
#
# Or, on a local clone:
#   sudo ./uninstall.sh                 # interactive
#   sudo ./uninstall.sh --yes           # default scope, no prompts
#   sudo ./uninstall.sh --yes --keep-data --keep-image
#
# Default scope when --yes is given without other flags:
#   - stop and remove the container
#   - remove the named volume that stores the database  (DESTRUCTIVE)
#   - remove the local univorch/ directory
#   - remove the Docker image
# Use --keep-data and/or --keep-image to keep those pieces.

set -euo pipefail

# --- Configuration --------------------------------------------------------

INSTALL_DIR="${UNIVORCH_INSTALL_DIR:-$PWD/univorch}"
IMAGE="ghcr.io/clamaveruma/univorch"

# --- Colours (only if stdout is a tty) ------------------------------------

if [ -t 1 ]; then
    BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'
    RED=$'\033[31m'; BLUE=$'\033[34m'; RESET=$'\033[0m'
else
    BOLD=''; GREEN=''; YELLOW=''; RED=''; BLUE=''; RESET=''
fi

info()    { echo "${BLUE}[univorch]${RESET} $*"  >&2; }
ok()      { echo "${GREEN}[univorch]${RESET} $*" >&2; }
warn()    { echo "${YELLOW}[univorch]${RESET} $*" >&2; }
fail()    { echo "${RED}[univorch]${RESET} $*" >&2; exit 1; }

# --- Flag parsing ---------------------------------------------------------

ASSUME_YES=0
KEEP_DATA=0
KEEP_IMAGE=0

while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes)    ASSUME_YES=1 ;;
        --keep-data) KEEP_DATA=1 ;;
        --keep-image) KEEP_IMAGE=1 ;;
        -h|--help)
            cat <<EOF
UnivOrch uninstaller.

Usage: $0 [options]

  -y, --yes        skip the confirmation prompt (required when stdin is not a tty,
                   typical of 'curl | sudo bash')
      --keep-data  do NOT remove the named Docker volume (preserves the database)
      --keep-image do NOT remove the Docker image (saves a download next time)
  -h, --help       this message
EOF
            exit 0
            ;;
        *) fail "Unknown option: $1 (try --help)" ;;
    esac
    shift
done

# --- Docker availability --------------------------------------------------

if ! command -v docker >/dev/null 2>&1; then
    warn "Docker no está instalado. Solo limpiaré el directorio local (si existe)."
    DOCKER_AVAILABLE=0
else
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=1
        if docker compose version >/dev/null 2>&1; then
            COMPOSE_CMD="docker compose"
        elif command -v docker-compose >/dev/null 2>&1; then
            COMPOSE_CMD="docker-compose"
        else
            COMPOSE_CMD=""
        fi
    else
        warn "Docker no responde (¿permisos? ¿daemon parado?). Saltaré los pasos que lo usan."
        DOCKER_AVAILABLE=0
    fi
fi

# --- Scope summary --------------------------------------------------------

echo
info "Plan de desinstalación:"
echo "  - Parar y eliminar el contenedor univorch."
[ "$KEEP_DATA"  -eq 1 ] || echo "  - Borrar el volumen con la base de datos ${RED}(DESTRUCTIVO)${RESET}."
[ "$KEEP_IMAGE" -eq 1 ] || echo "  - Borrar la imagen ${IMAGE}."
echo "  - Borrar el directorio ${INSTALL_DIR}/ (si existe)."
echo

# --- Confirmation ---------------------------------------------------------

if [ "$ASSUME_YES" -ne 1 ]; then
    if [ ! -t 0 ]; then
        fail "stdin no es interactivo (estás ejecutando con 'curl | bash'). Añade --yes para confirmar."
    fi
    read -r -p "¿Continuar? [s/N] " answer
    case "$answer" in
        [sSyY]|[sS][iI]|[yY][eE][sS]) ;;
        *) info "Abortado."; exit 0 ;;
    esac
fi

# --- 1. Stop and remove the container -------------------------------------

if [ "$DOCKER_AVAILABLE" -eq 1 ]; then
    if [ -f "${INSTALL_DIR}/docker-compose.yml" ] && [ -n "${COMPOSE_CMD}" ]; then
        info "Parando el servicio con ${COMPOSE_CMD} down..."
        # 'down' removes the container and the default network in one shot;
        # the named volume only goes with -v, which we add only if requested.
        if [ "$KEEP_DATA" -eq 1 ]; then
            (cd "${INSTALL_DIR}" && ${COMPOSE_CMD} down) || warn "Falló 'compose down', sigo."
        else
            (cd "${INSTALL_DIR}" && ${COMPOSE_CMD} down -v) || warn "Falló 'compose down -v', sigo."
        fi
    else
        # Fallback: container started by hand without compose.
        if docker ps -a --format '{{.Names}}' | grep -q '^univorch$'; then
            info "Eliminando el contenedor univorch (sin compose)..."
            docker rm -f univorch >/dev/null || warn "Falló 'docker rm', sigo."
        fi
    fi
    ok "Contenedor eliminado."
fi

# --- 2. Volume (only if compose did not catch it, e.g. KEEP_DATA + manual) -

if [ "$DOCKER_AVAILABLE" -eq 1 ] && [ "$KEEP_DATA" -ne 1 ]; then
    # Compose volumes are prefixed with the project name (the install dir
    # basename). Try a couple of likely candidates.
    for vol in univorch_univorch_data univorch_data; do
        if docker volume inspect "$vol" >/dev/null 2>&1; then
            docker volume rm "$vol" >/dev/null && ok "Volumen $vol eliminado." \
                || warn "No pude eliminar el volumen $vol."
        fi
    done
fi

# --- 3. Image -------------------------------------------------------------

if [ "$DOCKER_AVAILABLE" -eq 1 ] && [ "$KEEP_IMAGE" -ne 1 ]; then
    # Match every locally cached tag of the image.
    image_ids=$(docker images --format '{{.Repository}}:{{.Tag}}' \
                    | grep "^${IMAGE}:" || true)
    if [ -n "$image_ids" ]; then
        info "Borrando imágenes locales de ${IMAGE}..."
        echo "$image_ids" | xargs -r docker rmi -f >/dev/null \
            && ok "Imagen eliminada." \
            || warn "No pude eliminar alguna imagen."
    fi
fi

# --- 4. Local directory ---------------------------------------------------

if [ -d "${INSTALL_DIR}" ]; then
    info "Borrando ${INSTALL_DIR}/..."
    # Use a subshell anchored at /tmp so that 'rm -rf' works even when the
    # script was invoked from inside ${INSTALL_DIR} itself (typical: 'sudo
    # ./uninstall.sh' from the directory we are about to delete). Bash's
    # cwd is allowed to be a deleted directory but new commands may fail;
    # anchoring to /tmp avoids the trap altogether.
    ( cd /tmp && rm -rf "${INSTALL_DIR}" )
    ok "Directorio eliminado."
fi

echo
ok "UnivOrch desinstalado."
