# recterm — record an interactive shell session via script(1) so the chat
# agent (Claude Code) can see what's happening in the integrated terminal.
#
# Defines the function `recterm` and, at the bottom, an unconditional rule
# that prepends `[REC]` to the prompt whenever we are inside a script(1)
# session (detected via the SCRIPT environment variable that util-linux's
# script(1) exports for the spawned shell).
#
# Usage:
#   recterm              status + help
#   recterm on [path]    start a session (default log: /tmp/univorch-session.log)
#   recterm off          stop the current session (exits the recorded shell)
#   recterm status       quick state report
#
# Why a shell function instead of an executable script: `off` needs to call
# `exit` on the *current* shell (the one being recorded). An external `.sh`
# runs in a subshell, so its `exit` would only kill the subshell, not the
# recording. A sourced function runs in the same shell — its `exit` kills
# the shell, which kills script(1) above it. Clean stop.

_RECTERM_DEFAULT_LOG="/tmp/univorch-session.log"

recterm() {
    case "${1:-}" in
        on)
            if [ -n "${SCRIPT:-}" ]; then
                echo "recterm: ya estás grabando en $SCRIPT (SHLVL=$SHLVL)." >&2
                echo "         sal con 'recterm off' o 'exit' antes de empezar otra." >&2
                return 1
            fi
            local log="${2:-$_RECTERM_DEFAULT_LOG}"
            touch "$log"
            echo "recterm: grabando en $log (sal con 'recterm off' o Ctrl-D)."
            exec script -fa "$log"
            ;;
        off)
            if [ -z "${SCRIPT:-}" ]; then
                echo "recterm: no estás en una sesión grabada." >&2
                return 1
            fi
            echo "recterm: parando grabación de $SCRIPT."
            exit
            ;;
        status)
            if [ -n "${SCRIPT:-}" ]; then
                echo "recterm: grabando en $SCRIPT (SHLVL=$SHLVL)"
            else
                echo "recterm: no grabando"
            fi
            ;;
        ""|help|-h|--help)
            if [ -n "${SCRIPT:-}" ]; then
                echo "Estado: grabando en $SCRIPT (SHLVL=$SHLVL)"
            else
                echo "Estado: no grabando"
            fi
            cat <<EOF

Uso:
  recterm on [ruta]   inicia grabación (default: $_RECTERM_DEFAULT_LOG)
  recterm off         para la grabación actual
  recterm status      muestra el estado
  recterm             muestra esta ayuda
EOF
            ;;
        *)
            echo "recterm: comando desconocido '$1'. Prueba 'recterm' para ver la ayuda." >&2
            return 1
            ;;
    esac
}

# Mark the prompt when we are inside a script(1) recording session.
# util-linux's script(1) exports SCRIPT to the spawned shell with the log path.
# Using `if` instead of `&&` because the latter returns false when SCRIPT is
# unset — fine interactively, but it breaks `set -e` scripts that source us.
if [ -n "${SCRIPT:-}" ]; then
    PS1="[REC] $PS1"
fi
