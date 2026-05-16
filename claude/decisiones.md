# Índice de decisiones técnicas

Este fichero recoge las decisiones técnicas importantes del proyecto con referencia a la entrada del diario donde se tomaron.

---

## DEC-001 — Formato de memoria persistente

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Usar Markdown (`.md`) para todos los ficheros de contexto
- **Motivo:** Legibilidad humana, flexibilidad de estructura, compatibilidad nativa con Claude Code

## DEC-002 — Estructura de directorios de contexto

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Directorio `claude/` para ficheros de memoria; `CLAUDE.md` en raíz solo con imports y reglas
- **Motivo:** Mantener la raíz limpia; centralizar contexto en un lugar predecible

## DEC-003 — Diario como fuente principal

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** `claude/diario.md` es la referencia cronológica principal; otros ficheros son índices
- **Motivo:** Captura el *porqué* de cada decisión en su contexto temporal; facilita reconstruir la evolución del proyecto
