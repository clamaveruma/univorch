# Diario del proyecto

---

## 2026-05-16

### Inicio del proyecto

- Se crea el repositorio `clamaveruma/orch_pru` en GitHub
- Se define la estructura de memoria persistente basada en ficheros Markdown
- Se establece el uso de `CLAUDE.md` como punto de entrada con imports y reglas

### Decisiones de configuración del proyecto

- **Formato de memoria:** Markdown (`.md`) para todos los ficheros de contexto
- **Estructura de directorios:** `claude/` para memoria interna, `docs/` para documentación técnica, `CLAUDE.md` en raíz
- **Diario:** se actualiza cuando hay algo relevante; Claude avisa escuetamente cuando lo hace
- **Commits automáticos:** sin pedir confirmación; Claude informa en el chat
- **Estilo de trabajo:** colaborativo — proponer, aclarar, confirmar, ejecutar. Un tema cada vez
- **Sin complacencia:** Claude debe ser crítico y objetivo, ofrecer alternativas
- **Idiomas:** chat en español; código, `docs/` y memoria del TFG en inglés; ficheros internos (`claude/`) en español
- **Modelos:** Sonnet por defecto; Opus para decisiones críticas de arquitectura; Claude avisa cuando conviene cambiar

### Plan de proyecto acordado

Se definen 7 fases con nombres profesionales (ver `docs/plan.md`):
1. Definición del problema
2. Análisis de requisitos
3. Diseño de arquitectura
4. Selección de tecnologías
5. Configuración del entorno
6. Desarrollo iterativo (TDD)
7. Evaluación y memoria

### Contexto del proyecto

- **Alumno:** Claudio María Martínez Velasco — Ingeniería de Computadores, Universidad de Málaga
- **Tutor:** Guillermo Pérez Trabado, Dpto. Arquitectura de Computadores
- **Título:** Un orquestador de máquinas virtuales para entornos docentes y de investigación. Prueba de concepto
- **Base de partida:** librerías Python del tutor — `esxobjects` (interfaz VMware) y `yamlinfr` (despliegue desde YAML)
- **Horas totales del TFG:** 296h distribuidas en 9 fases según anteproyecto
- Desarrollo asistido por IA (Claude Code)

### Documentos de referencia cargados en `docs/ideas/`

- `DESIGN.md` — diseño conceptual detallado
- `Ideas_orquestador.odt` — ideas técnicas
- `Necesidad.odt` — contexto del problema real
- `ideas-raw.md` — ideas sobre mensajería, MCP, Android
- `Anteproyecto_Claudio_Mar-2026-Revisado.docx` — documento oficial del TFG

### Sesión de análisis y decisiones de diseño (tarde)

Se analizaron todos los documentos de referencia y se tomaron 18 decisiones de diseño (ver `claude/decisiones.md` DEC-001 a DEC-018). Resumen de las más relevantes:

- Arquitectura en dos capas: orquestador genérico + aplicación de docencia
- Diseño declarativo estilo Terraform/Ansible; reconciliación automática para futuro
- Objeto clave: **descriptor** (analogía con descriptor de fichero en SO)
- Árbol de descriptores con herencia en cascada de propiedades obligatoria en v1
- Exportación explícita: cada carpeta declara qué publica hacia abajo
- RBAC con 3 roles: superusuario, manager, end_user
- Metáfora para alumno: **mesa** (carpeta) y **ordenador** (descriptor)
- Persistencia: patrón Repository con TinyDB → MongoDB futuro
- Jobs persistidos en BD desde el principio para preparar HA activo/pasivo
- Operaciones del conector: deploy/undeploy (borrado total), start/stop/pause/resume/get_status
- Datastores como recurso con alias, heredable en cascada
- Interfaces v1: CLI (cmd2, dual bash+REPL) + Web GUI (NiceGUI); TUI (Textual) para futuro

### Pendientes para próximas sesiones

- [x] Acceso a VMs existentes → DEC-020
- [x] Listado y gestión de usuarios → DEC-021
- [ ] Checklist de fases de desarrollo
- [ ] Desarrollo en diferentes plataformas
- [ ] Directrices de código
- [ ] Snapshots de alumnos (almacenamiento, límites, comportamiento en undeploy)
- [ ] Gestión de IPs, posible integración con IPAM
- [ ] Gestión de excepciones comunes y estados desconectados
- [ ] Fuentes de verdad y estados incoherentes
- [ ] Informes posibles
- [ ] Futuras aplicaciones: otros modelos de vista de usuario, desacople aplicaciones/motor, módulo de migración de máquinas, módulos de supervisión, integración de Chat IA en web y REPL CLI
- [ ] Subir PDFs de referencia al repo
- [ ] Buscar documento con referencia a MongoDB

---

## 2026-05-17

### Continuación de decisiones de diseño

Se retoma el diálogo de decisiones. Se cierran dos temas del backlog:

**DEC-005b — Tipos de descriptor (retomado)**
- Descriptor normal: definición + referencia a VM
- Descriptor de referencia: solo enlace a VM existente, sin definición, operaciones limitadas
- v1: descriptores de referencia fuera de alcance

**DEC-019 — Nombre del proyecto**
- Nombre elegido: **UnivOrch** (Universal Virtual Orchestrator)
- Libre en PyPI, GitHub y DockerHub

**DEC-020 — Acceso a VMs existentes**
- Principio de no invasión confirmado
- Descriptores de referencia para VMs preexistentes
- v1: fuera de alcance; futuro: descubrimiento manual primero, luego autodescubrimiento

**Nota para Fase 5 — Entorno de desarrollo multi-plataforma**
- Desarrollo desde varios PCs: VSCode + Dev Containers como base. Mismo `.devcontainer/` funciona en local, Codespaces y VSCode Remote SSH
- Claude Code (web, CLI, VSCode) comparte contexto a través de los ficheros `claude/` en git — no hay memoria de sesión entre instancias, pero el repo es la fuente de verdad
- Sincronización: GitHub. No trabajar con dos sesiones de Claude Code en paralelo sobre el mismo repo sin hacer push/pull entre ellas
- Retomar en Fase 5 para definir el `.devcontainer/` concreto

**Nota para memoria TFG — Snapshots de alumnos**
- Fuera de v1, pero se esboza en la memoria
- El alumno gestiona snapshots exclusivamente a través de UnivOrch, nunca del hipervisor
- Comportamiento en undeploy: política configurable por carpeta (herencia en cascada), por defecto "avisar y confirmar" antes de destruir snapshots
- Límites de snapshots (cantidad, espacio) también configurables en cascada desde la raíz
- Ampliar en la fase de redacción de la memoria

**Nota para Fase 5 — Directrices de código**
- Python, versión reciente (definir cuál en Fase 5)
- Nivel básico e intermedio; si surge necesidad de algo avanzado, discutirlo antes de implementar
- Logging con el módulo estándar de Python (`logging`), escribiendo al log del sistema (syslog/journald) — es un servicio
- Claude propondrá convenciones completas cuando lleguemos a esa fase

**DEC-021 — Gestión de usuarios**
- Fichero YAML, texto plano (PoC), editable por admin vía web
- UserRepository como interfaz de abstracción para futura integración LDAP/AD
- Asignación usuario↔rol en la carpeta (no en el registro de usuario), herencia en cascada
- Raíz asigna superusuarios; carpeta asignatura asigna managers; carpeta alumno asigna end_users
- Un mismo usuario puede tener roles distintos en ramas diferentes del árbol; sobreescritura local en cualquier subcarpeta

### Gestión de excepciones y estados — análisis inicial

Se identifican 8 categorías de problemas a tratar (la mayoría para diseño y memoria, algunas con decisión necesaria en v1):

1. **Conectividad con hipervisor:** estado `unreachable` en descriptor; credenciales caducadas
2. **Deriva de configuración:** VM modificada directamente en el hipervisor → descriptor marcado como `drifted`; re-deploy restaura la definición del descriptor como verdad
3. **Recursos del hipervisor:** datastore lleno, plantilla base eliminada, linked clone roto
4. **Recursos huérfanos:** VM sin descriptor (VM fantasma) y descriptor sin VM (descriptor huérfano)
5. **Operaciones sobre el árbol:** renombrar/mover/copiar carpetas — cada una con implicaciones distintas en referencias e herencia
6. **Ciclo de vida de operaciones:** deploy parcial → estado `broken`; Jobs `interrupted` al arrancar tras apagado; concurrencia bloqueada por Job activo; timeout
7. **Capa de datos:** BD corrompida o inaccesible; reconciliación BD↔hipervisor en arranque en frío
8. **Usuarios y permisos:** referencias colgadas al borrar usuario; conflictos de rol entre padre e hijo en árbol

Pendiente: decidir estados del descriptor (máquina de estados) y comportamiento de Jobs interrumpidos al arrancar — resuelto en DEC-022 y nota de futuro

### Fase 1 completada — docs/vision.md redactado

Se redacta el documento de visión del producto en inglés (nivel C1). Cubre: problema, contexto, solución propuesta, conceptos clave (descriptor, árbol, herencia en cascada, Jobs, estados), usuarios y roles, arquitectura general, alcance de v1, aplicaciones futuras y no-objetivos. Plan.md actualizado con Fase 1 como completada.

**DEC-022 — Máquina de estados del descriptor**
- 4 estados: `provisioned`, `deployed` (con flag `drifted`), `broken`, `unreachable`
- Estados runtime (running/stopped/paused) son del hipervisor, consultados con `get_status`
- `broken` muestra historial de Jobs al usuario; salida con `force-undeploy`

**Nota para memoria TFG — Futuras aplicaciones**
- **Aplicación docente (TFG v1):** despliegue de asignatura — mesa modelo + lista de alumnos → crea mesas individuales, asigna permisos e IPs por política, envía correos a alumnos, informe al profesor. Utilidades: actualizar lista de alumnos, cambiar VM modelo
- **Otras aplicaciones posibles sobre el mismo motor:**
  - CTF y competiciones de ciberseguridad: entornos aislados por equipo, tiempo limitado
  - Talleres en conferencias: VM por asistente, ciclo de vida muy corto
  - Exámenes prácticos: VM aislada, snapshot al inicio y al final para corrección
  - Entornos de desarrollo bajo demanda: self-service por desarrollador desde plantilla
  - Testing/QA: VMs idénticas con distintas versiones de SO o software
  - Demo environments: despliegue para cliente, destrucción posterior
  - Laboratorios de investigación: réplica de entornos de experimentos, snapshots en puntos clave
  - Formación corporativa: igual que docencia pero para IT empresarial
  - MSP: cada cliente es una rama, una instancia de UnivOrch gestiona múltiples clientes
  - Pruebas de disaster recovery: despliegue periódico automático de réplica de producción
- En todos los casos el motor genérico es el mismo; cambia solo la aplicación de capa 2
- Operacionales: estado de VMs por carpeta, VMs en estado anómalo, Jobs activos, uso de recursos por hipervisor y datastore
- Históricos/auditoría: historial de operaciones por VM/usuario, Jobs fallidos, tiempos medios de deploy, actividad por usuario
- Docentes: alumnos sin VM desplegada, alumnos con VM anómala, dashboard por profesor, comparativa entre grupos
- Capacidad: previsión de recursos si se despliegan todas las VMs de una asignatura, VMs sin actividad reciente
- **TFG v1:** implementar uno operacional (estado por carpeta) y uno docente (estado de asignatura) como ejemplos

**Nota futuro — Jobs interrumpidos al arrancar**
- Si el orquestador cae con Jobs en estado `running`, al arrancar los detecta en BD y notifica al admin
- No se relanzan automáticamente — el admin decide
- Fuera del TFG; se esboza en la memoria como desarrollo futuro de HA

**DEC-023 — Logs y retención**
- Logs del sistema → syslog/journald (módulo `logging`)
- Logs de operaciones → Jobs en BD (retención configurable, por defecto 90 días, propiedad global)

**DEC-024 — Backup de la base de datos**
- Política GFS (Grandfather-Father-Son), restauración manual en v1

### Fase 1 cerrada, vision.md iterado

- `docs/vision.md` redactado y refinado: eliminados detalles de arquitectura/herramientas (van a Fase 3/4), inglés nivel B2 más natural, equilibrio prosa/estructura
- Renombrado **UniVorch → UnivOrch** en todo el repo
- Backlog completado: snapshots, excepciones (8 categorías), informes, futuras aplicaciones — todo registrado como notas de futuro o decisiones
- Limpieza: eliminados `ideas-raw.md` duplicados (pertenecían a otro proyecto)
- Repo migrado a rama `main` como rama de trabajo única

### Fase 2 iniciada — docs/requisitos.md redactado

Se redacta el documento de requisitos en formato ligero (acordado: casos de uso narrativos, no IEEE-830 pesado). Estructura: propósito, actores, casos de uso (core / aplicación docente / sistema), requisitos funcionales por área, no funcionales, restricciones, fuera de alcance. Trazabilidad a decisiones DEC-xxx.

- Distinción explícita entre casos de uso del **core** y de la **aplicación docente** (capa 2) para el manager
- Alumno ve "mesas" (DEC-009), nunca el árbol
- Sistema como motor de operaciones (síncrono en v1, modelo preparado para asíncrono) + tareas automáticas
- Plan.md: Fase 1 ✅ completada, Fase 2 🔄 en curso
- Pendiente: revisión del usuario; afinar casos de uso en sprints futuros si se necesita
