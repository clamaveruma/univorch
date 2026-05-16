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
- **Motivo:** Captura el *porqué* de cada decisión en su contexto temporal

## DEC-004 — Arquitectura en dos capas

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Separar el orquestador genérico (capa 1) de la aplicación de docencia (capa 2)
- **Motivo:** El núcleo es reutilizable para cualquier contexto; la capa 2 interpreta el árbol con semántica de asignaturas/alumnos

## DEC-005 — Terminología: "descriptor"

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** El objeto que representa una VM en el orquestador se llama **descriptor**
- **Motivo:** Analogía clara con descriptor de fichero en un SO — representa la VM sin ser la VM. Comprensible para cualquier ingeniero de computadores

## DEC-006 — Arquitectura declarativa

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** El sistema es declarativo: el usuario describe el estado deseado en ficheros (YAML/JSON); el orquestador se encarga de materializarlo
- **Motivo:** Filosofía tipo Terraform/Ansible — el usuario no da órdenes imperativas, declara lo que quiere
- **Nota:** El bucle de reconciliación automático se deja como desarrollo futuro. La v1 aplica los cambios bajo demanda

## DEC-007 — Capa de persistencia: patrón Repository

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** La persistencia se abstrae mediante el patrón Repository. Implementación inicial con TinyDB. Migración futura a MongoDB para HA
- **Motivo:** TinyDB y MongoDB comparten filosofía documental — la migración solo afecta a la implementación del Repository. El Repository también gestionará copias de seguridad automáticas

## DEC-008 — Uso de patrones de diseño

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Se usarán patrones de diseño (referencia: refactoring.guru) cuando simplifiquen el proyecto, no por obligación
- **Motivo:** El proyecto es académico, open source y lo retomarán otros desarrolladores. Prima que funcione y se entienda

## DEC-009 — Metáfora de usuario final

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** El alumno (usuario final) ve una abstracción simplificada del árbol: solo ve **mesas** y **ordenadores**. No ve carpetas ni jerarquía
- **Vocabulario por capas:**
  - Carpeta de alumno → el alumno la ve como **mesa**
  - Descriptor de VM → el alumno lo ve como **ordenador**
- **Motivo:** Eliminar complejidad innecesaria para el usuario final. El alumno solo necesita saber que tiene mesas y que cada mesa tiene ordenadores
