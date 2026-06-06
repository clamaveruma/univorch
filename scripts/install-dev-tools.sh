#!/bin/bash
# install-dev-tools.sh — idempotent installer for the dev environment.
#
# What it does:
#   1. Copies scripts/lib/recterm.bash to ~/.local/bin/recterm.bash.
#   2. Adds two lines to ~/.bashrc (only if not already there):
#      - auto-activation of the project's .venv
#      - source of the recterm function
#   3. Sources the new config in the current shell so changes take effect now.
#
# Designed to run from `postCreateCommand` in .devcontainer/devcontainer.json
# (one-shot at container creation) and also by hand at any time.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOME_BIN="$HOME/.local/bin"
RECTERM_SRC="$REPO_DIR/scripts/lib/recterm.bash"
RECTERM_DEST="$HOME_BIN/recterm.bash"
BASHRC="$HOME/.bashrc"
VENV_ACTIVATE="$REPO_DIR/.venv/bin/activate"

echo "install-dev-tools: instalando en $HOME"

# 1. copy the recterm function file
mkdir -p "$HOME_BIN"
cp "$RECTERM_SRC" "$RECTERM_DEST"
echo "  ✓ recterm copiado a $RECTERM_DEST"

# helper: add a line to ~/.bashrc only if it's not already there (idempotent)
add_to_bashrc() {
    local line="$1"
    local description="$2"
    if grep -qxF "$line" "$BASHRC"; then
        echo "  · $description ya estaba en .bashrc"
    else
        printf '\n# %s\n%s\n' "$description" "$line" >> "$BASHRC"
        echo "  ✓ $description añadido a .bashrc"
    fi
}

# 2a. auto-activate the project venv
add_to_bashrc \
    "[ -f $VENV_ACTIVATE ] && [ -z \"\${VIRTUAL_ENV:-}\" ] && source $VENV_ACTIVATE" \
    "Auto-activar el venv del proyecto orch_pru"

# 2b. source the recterm function
add_to_bashrc \
    "[ -f $RECTERM_DEST ] && source $RECTERM_DEST" \
    "Cargar la herramienta recterm"

# 3. apply right now in the current shell (best-effort — non-interactive shells
#    don't need the prompt change, but the function and venv become available)
if [ -f "$VENV_ACTIVATE" ] && [ -z "${VIRTUAL_ENV:-}" ]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
fi
# shellcheck disable=SC1090
source "$RECTERM_DEST"

echo "install-dev-tools: listo."
echo "  - 'recterm' ya está disponible en este shell."
echo "  - El venv se auto-activará en terminales nuevas."
