#!/usr/bin/env bash
# sync-overleaf.sh
#
# Sincroniza el contenido de docs/memoria/ con el repositorio Git del
# proyecto Overleaf. Pensado para el flujo cliente Free de Overleaf,
# donde la sincronización con GitHub no está disponible pero el clon
# Git nativo del proyecto sí.
#
# Por defecto opera en modo "push" (sube docs/memoria/ a Overleaf).
# Para tirar de los cambios hechos por el usuario en Overleaf hacia el
# repositorio, pasa "pull" como primer argumento.
#
# El token se lee de ~/.overleaf-token (debe existir con permisos 600
# y sin acabar en newline visible). Nunca se imprime ni se loguea.
#
# Uso:
#   scripts/sync-overleaf.sh           # push: repo -> Overleaf
#   scripts/sync-overleaf.sh push      # idem, explícito
#   scripts/sync-overleaf.sh pull      # Overleaf -> repo (manual luego)

set -euo pipefail

PROJECT_ID="6a255d34fb4d51b796ceed0a"
TOKEN_FILE="$HOME/.overleaf-token"
MIRROR_DIR="$HOME/.overleaf-mirror"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/docs/memoria"
MODE="${1:-push}"

# --- Sanity checks ----------------------------------------------------

if [ ! -r "$TOKEN_FILE" ]; then
    echo "Error: $TOKEN_FILE no existe o no es legible." >&2
    echo "Crea uno generando un Project Token en Overleaf y guárdalo con:" >&2
    echo "  read -rs T && echo \"\$T\" > ~/.overleaf-token && chmod 600 ~/.overleaf-token" >&2
    exit 1
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: $SOURCE_DIR no existe." >&2
    exit 1
fi

# Token sin newlines accidentales, almacenado solo en memoria del shell.
OVERLEAF_TOKEN=$(tr -d '\n\r' < "$TOKEN_FILE")
if [ -z "$OVERLEAF_TOKEN" ]; then
    echo "Error: el token está vacío." >&2
    exit 1
fi

# La URL incluye el token como parte de la URL HTTP Basic. Es lo que el
# clon Git de Overleaf espera. Mantén la variable como local; no la
# imprimas. Las URLs en errores de git van a stderr con el token oculto
# por GIT_ASKPASS... aún así evitamos ecos innecesarios.
OVERLEAF_URL="https://git:${OVERLEAF_TOKEN}@git.overleaf.com/${PROJECT_ID}"

# --- Ensure local mirror is up to date --------------------------------

if [ ! -d "$MIRROR_DIR/.git" ]; then
    echo "Clonando proyecto Overleaf en $MIRROR_DIR (primera vez)..."
    git clone --quiet "$OVERLEAF_URL" "$MIRROR_DIR"
else
    echo "Actualizando $MIRROR_DIR desde Overleaf..."
    git -C "$MIRROR_DIR" remote set-url origin "$OVERLEAF_URL"
    git -C "$MIRROR_DIR" fetch --quiet origin
    git -C "$MIRROR_DIR" reset --hard --quiet origin/master 2>/dev/null \
        || git -C "$MIRROR_DIR" reset --hard --quiet origin/main
fi

# --- Mode: push -------------------------------------------------------

if [ "$MODE" = "push" ]; then
    echo "Copiando docs/memoria/* a $MIRROR_DIR ..."
    # Borra todo menos .git; vuelve a copiar el contenido entero.
    # rsync -a --delete sería más eficiente pero el devcontainer base
    # podría no traerlo; usamos find+cp.
    find "$MIRROR_DIR" -mindepth 1 -maxdepth 1 -not -name ".git" -exec rm -rf {} +
    cp -r "$SOURCE_DIR"/. "$MIRROR_DIR"/

    cd "$MIRROR_DIR"
    if [ -z "$(git status --porcelain)" ]; then
        echo "Sin cambios respecto al estado actual de Overleaf."
        exit 0
    fi

    git add -A
    git -c user.name="UnivOrch sync" -c user.email="sync@univorch.local" \
        commit --quiet -m "Sync from clamaveruma/univorch ($(git -C "$REPO_ROOT" rev-parse --short HEAD))"
    git push --quiet origin HEAD
    echo "Sincronización completada. Vuelve a compilar en Overleaf para ver los cambios."
    exit 0
fi

# --- Mode: pull -------------------------------------------------------

if [ "$MODE" = "pull" ]; then
    echo "El mirror $MIRROR_DIR ya está alineado con Overleaf."
    echo "Para integrar los cambios al repositorio principal:"
    echo "  diff -ru $SOURCE_DIR/ $MIRROR_DIR/ | less"
    echo "  cp -r $MIRROR_DIR/. $SOURCE_DIR/    # con cuidado: sobrescribe"
    exit 0
fi

echo "Modo desconocido: '$MODE'. Usa 'push' o 'pull'." >&2
exit 1
