# Diario del proyecto

---

## 2026-05-16

### Inicio del proyecto

- Se crea el repositorio `clamaveruma/orch_pru` en GitHub
- Se define la estructura de memoria persistente basada en ficheros Markdown
- Se establece el uso de `CLAUDE.md` como punto de entrada con imports a ficheros especializados

### Decisiones

- **Formato de memoria:** Markdown (`.md`) para todos los ficheros de contexto, por legibilidad y compatibilidad con Claude Code
- **Estructura de directorios:** ficheros de contexto en `claude/`, `CLAUDE.md` en raíz solo con imports y reglas
- **Diario como fuente principal:** el diario cronológico (`claude/diario.md`) es la referencia principal del proyecto; `proyecto.md` y `decisiones.md` son índices de consulta rápida
- **Commits automáticos:** Claude hace commit al terminar cada bloque de trabajo, informa en el chat, sin interrumpir el flujo
- **Estructura dinámica:** Claude puede crear nuevos ficheros en `claude/` si un tema lo requiere

### Estado al cierre de sesión

- Estructura inicial creada y subida a GitHub
- Stack tecnológico y arquitectura pendientes de definir
