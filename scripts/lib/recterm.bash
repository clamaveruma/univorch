# recterm — record an interactive shell session via script(1) so the chat
# agent (Claude Code) can see what's happening in the integrated terminal.
#
# Defines the function `recterm` and, at the bottom, prepends `[REC]` to the
# prompt whenever we are inside a recterm-managed session. Detection uses our
# own exported `RECTERM_LOG` variable: util-linux 2.41+ does NOT export any
# marker of its own (older docs mentioned a `SCRIPT` var that newer versions
# dropped), so we set our own marker before exec'ing script(1) — exported
# variables survive `exec` and are inherited by the child shell script spawns.
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
            if [ -n "${RECTERM_LOG:-}" ]; then
                echo "recterm: ya estás grabando en $RECTERM_LOG (SHLVL=$SHLVL)." >&2
                echo "         sal con 'recterm off' o 'exit' antes de empezar otra." >&2
                return 1
            fi
            local log="${2:-$_RECTERM_DEFAULT_LOG}"
            touch "$log"
            echo "recterm: grabando en $log (sal con 'recterm off' o Ctrl-D)."
            export RECTERM_LOG="$log"
            # Sin `exec` a propósito: si reemplazáramos el bash padre con
            # script(1), al terminar la grabación no quedaría ningún shell
            # vivo y la terminal de VSCode se cerraría. Llamando normal,
            # cuando script termina volvemos al bash original — la terminal
            # sigue viva. El coste es una capa extra en el árbol de procesos.
            script -fa "$log"
            unset RECTERM_LOG  # limpiar tras la sesión por si el usuario
                               # reusa el shell (caso raro pero defensivo)
            ;;
        off)
            if [ -z "${RECTERM_LOG:-}" ]; then
                echo "recterm: no estás en una sesión grabada." >&2
                return 1
            fi
            echo "recterm: parando grabación de $RECTERM_LOG."
            exit
            ;;
        status)
            if [ -n "${RECTERM_LOG:-}" ]; then
                echo "recterm: grabando en $RECTERM_LOG (SHLVL=$SHLVL)"
            else
                echo "recterm: no grabando"
            fi
            ;;
        ""|help|-h|--help)
            if [ -n "${RECTERM_LOG:-}" ]; then
                echo "Estado: grabando en $RECTERM_LOG (SHLVL=$SHLVL)"
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

# Mark the prompt when we are inside a recterm-managed session.
# Using `if` instead of `&&` because the latter returns false when the var is
# unset — fine interactively, but it breaks `set -e` scripts that source us.
if [ -n "${RECTERM_LOG:-}" ]; then
    PS1="[REC] $PS1"
fi
