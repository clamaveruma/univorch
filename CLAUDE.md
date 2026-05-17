# Orquestador Universal de Máquinas Virtuales

@claude/proyecto.md
@claude/diario.md
@claude/decisiones.md

---

## Estilo de trabajo y colaboración

- No seas complaciente. Si algo no te convence, dilo con argumentos. Prioriza la objetividad sobre la cortesía.
- Trabaja en modo colaborativo: tras cada petición, haz preguntas de aclaración si hay ambigüedad. Propón antes de ejecutar. Asegúrate de que ambos entendemos y estamos de acuerdo antes de hacer cualquier cambio de diseño, arquitectura o código.
- Ofrece alternativas y mejoras cuando las veas, especialmente en decisiones de diseño.
- No ejecutes nada que el usuario no haya confirmado explícitamente. Propón, aclara, confirma, ejecuta.

## Idiomas

- **Chat y conversación:** español
- **Código Python:** inglés exclusivamente (clases, variables, funciones, comentarios, textos)
- **Documentación técnica (`docs/`):** inglés
- **Memoria del TFG:** inglés
- **Ficheros internos (`claude/`, `CLAUDE.md`):** español

## Guía de modelos y esfuerzo

El cambio de modelo lo hace el usuario manualmente. Claude avisa cuando conviene cambiar.

| Fase / Tarea | Modelo recomendado | Esfuerzo |
|---|---|---|
| Conversación y documentación general | Sonnet | Medio |
| Análisis de requisitos | Sonnet / Opus | Alto |
| **Diseño de arquitectura** | **Opus** | **Alto** |
| Selección de tecnologías | Sonnet | Medio |
| Configuración del entorno | Haiku / Sonnet | Bajo |
| Desarrollo iterativo (código rutinario) | Sonnet | Medio |
| Bugs complejos o decisiones críticas en código | Opus | Alto |
| Redacción de la memoria del TFG | Sonnet | Medio |
| Tareas mecánicas (formatear, renombrar, commits) | Haiku | Bajo |

## Reglas de memoria y diario

- El diario (`claude/diario.md`) es la fuente principal de verdad cronológica del proyecto
- Actualiza el diario frecuentemente: tras cada decisión, tema cerrado o bloque de conversación relevante — no esperes al commit
- Cada vez que actualices el diario, indica en el chat un mensaje muy corto: "📓 diario actualizado"
- Si una decisión es técnicamente significativa, añádela también a `claude/decisiones.md` con referencia al diario
- Si un tema crece demasiado, crea un fichero nuevo en `claude/` con nombre descriptivo y refiérelo desde el diario
- Nunca borres entradas antiguas del diario; si algo cambia, anótalo como nueva entrada

## Reglas de commits

- Hacer commit automáticamente al terminar cada bloque de trabajo relacionado, sin pedir confirmación
- Actualizar `claude/diario.md` en el mismo commit si hay contexto nuevo relevante
- Mensaje de commit descriptivo en español
- Informar en el chat de lo que se ha commiteado
- Siempre hacer push a la rama activa tras el commit
