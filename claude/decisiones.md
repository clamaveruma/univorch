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
- **Motivo:** TinyDB y MongoDB comparten filosofía documental — la migración solo afecta a la implementación del Repository

## DEC-008 — Uso de patrones de diseño

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Se usarán patrones de diseño (referencia: refactoring.guru) cuando simplifiquen el proyecto, no por obligación
- **Motivo:** El proyecto es académico, open source y lo retomarán otros desarrolladores. Prima que funcione y se entienda

## DEC-009 — Metáfora de usuario final

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** El alumno (usuario final) ve una abstracción simplificada: solo ve **mesas** y **ordenadores**. No ve carpetas ni jerarquía
- **Vocabulario por capas:**
  - Carpeta de alumno → el alumno la ve como **mesa**
  - Descriptor de VM → el alumno lo ve como **ordenador**
- **Motivo:** Eliminar complejidad innecesaria para el usuario final

## DEC-010 — Herencia en cascada en v1

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** La herencia en cascada de propiedades es **necesaria desde v1**, no es opcional
- **Funcionamiento:** Raíz define hipervisores y plantillas base → carpeta asignatura referencia y puede derivar plantillas → descriptor individual solo elige plantilla y hereda el resto
- **Motivo:** Sin herencia, cada descriptor repetiría definiciones completas. Con cientos de VMs la gestión sería inviable

## DEC-011 — Modelo de permisos: RBAC con herencia jerárquica

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** 3 roles (superusuario, manager, end_user) con permisos estándar fijos en código. Única excepción configurable en v1: el admin restringe qué plantillas e hipervisores ve cada manager
- **Principio clave:** visibilidad vs usabilidad — un rol puede *usar* un recurso sin *ver* su definición completa
- **Desarrollo futuro:** personalización granular de permisos por carpeta

## DEC-012 — Exportación explícita de definiciones heredables

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Cada carpeta declara explícitamente qué elementos publica hacia abajo mediante una lista `exports` en su definición común. Lo que no está en `exports` no se hereda
- **Formato:** YAML (o JSON). Detalle de implementación en memoria a definir en fase de arquitectura
- **Motivo:** Control explícito de visibilidad

## DEC-013 — Gestión de IPs

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Integración con IPAM queda fuera de v1. Se mantiene como desarrollo futuro
- **Motivo:** Complejidad no justificada para la prueba de concepto

## DEC-014 — Modelo de operaciones: patrón Job

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Toda operación genera un **Job** con ID único y estado (`pending → running → completed / failed`). Los Jobs batch tienen sub-Jobs hijo, uno por VM
- **API:** `POST /jobs` para lanzar, `GET /jobs/{id}` para consultar estado
- **v1:** operaciones síncronas directas, pero el modelo Job se diseña desde el principio
- **Desarrollo futuro:** cola asíncrona, HA activo/pasivo con replicación en tiempo real

## DEC-015 — Jobs persistidos en base de datos

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Los Jobs se persisten en la base de datos desde el principio, no viven solo en memoria
- **Motivo:** Necesario para HA futura. En activo/pasivo, el pasivo replica el estado en tiempo real — si el activo cae, el pasivo tiene todos los Jobs

## DEC-016 — Operaciones del conector de hipervisor

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Todo conector implementa un interfaz común con estas operaciones mínimas:
  - `deploy` — clonar VM base y desplegar (linked clone preferido para ahorro de disco)
  - `undeploy` — eliminar VM y disco virtual completamente; el descriptor queda en estado `provisioned`
  - `start` / `stop` / `force_stop`
  - `pause` / `resume`
  - `get_status` / `get_info`
  - Snapshots: `snapshot_create`, `snapshot_restore`, `snapshot_delete`, `snapshot_list` — **desarrollo futuro**
- **Principio:** Las VMs desplegadas son siempre clones de una VM base creada por el admin. El manager nunca instala SO ni configura hardware
- **Undeploy:** borrado total — VM y disco virtual eliminados del hipervisor
