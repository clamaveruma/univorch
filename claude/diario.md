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

### Aclaración del modelo de herencia — DEC-012 revisado

Se cierra la discusión sobre el mecanismo de herencia/importación con tres decisiones finales:

1. **Importaciones, no exportaciones:** la carpeta hija declara qué importa del padre (no el padre qué exporta). Quien crea la carpeta hija — que en ese momento es el propietario efectivo del padre — decide qué trae consigo hacia abajo
2. **Comodín `*`:** soportado en v1. Importa todo lo disponible en la carpeta padre. Caso de uso típico: carpeta de alumno importa `*` de la carpeta de asignatura
3. **Propiedad implícita:** el concepto de "propietario" de una carpeta no se implementa. Emerge del RBAC: managers de una carpeta = propietarios efectivos; admin = manager de todo; alumno = end_user de su carpeta final. No hace falta ningún campo ni mecanismo adicional

DEC-012 actualizado en `claude/decisiones.md`. `docs/requisitos.md` secciones 4.1, 4.2 y UC-MGR-1 actualizados para reflejar el modelo de importación.

### Separación de capas en el interfaz del conector — DEC-016 revisado

Discusión sobre el interfaz común de hipervisores. Conclusiones:

1. **`deploy`/`undeploy` no son del conector:** son conceptos del orquestador. El conector solo expone primitivas del hipervisor. El orquestador implementa `deploy` → `connector.clone()` y `undeploy` → `connector.delete()`
2. **Operación `clone(mode)`:** parámetro `mode="linked"|"full"`, `linked` por defecto. `full` queda en el contrato del interfaz desde ya, pero **no soportado en v1** (lanza excepción "no soportado"). Así el contrato es estable y full clone se añade en el futuro sin cambiarlo
3. **Linked clone y condiciones del hipervisor:** cada hipervisor tiene sus condiciones (VMware: snapshot en VM base; Proxmox: clonar desde plantilla + storage compatible). Se asume que la VM base las cumple; cómo prepararla irá en la ayuda del programa. Si no se cumplen, `clone` lanza excepción con la info necesaria para diagnosticar
4. **`delete`** sustituye al antiguo nombre interno `undeploy` a nivel conector: elimina VM y disco; el descriptor vuelve a `provisioned`

DEC-016 actualizado en `claude/decisiones.md`. `docs/requisitos.md` sección 4.4 reescrita para separar primitivas del conector de la orquestación.

### Revisión final de requisitos — cierre de Fase 2

Se aplican todos los ajustes pendientes al documento de requisitos:

- **DEC-025 — IP pools por carpeta:** pools como parámetro heredable en cascada; validación de solapamiento al definir (no al desplegar); reserva/liberación de IP en deploy/undeploy. El orquestador asigna y registra; cómo la VM recibe la IP en la red es problema externo. Futuro: IPPoolRepository → IPAM externo
- **Detección de `drifted` en v1:** solo bajo demanda al llamar a `get_status`/`get_info`. Sin verificación al arranque en v1
- **`unreachable`:** reactivo — se marca cuando una operación falla por error de comunicación, no de forma proactiva
- **Undeploy del alumno:** permitido, con doble confirmación de aviso antes de proceder
- **Modelo de visibilidad simplificado:** el mecanismo de importación ES el control de visibilidad; las credenciales del hipervisor siempre ocultas. UC-ADM-6 reescrito en consecuencia
- **UC-AUTH-2 eliminado:** redundante; la visualización de recursos de cada rol ya está cubierta en sus UCs específicos
- **Jobs batch:** "one child Job per item or target" (no solo VMs)
- **Sección 4.7 nueva:** IP address management. Secciones 4.8–4.11 renumeradas
- **Constraints y Out of scope:** reescritos para reflejar pools propios en v1 e integración IPAM externa fuera de v1

### Fase 2 cerrada — inicio de Fase 3 (arquitectura)

- Documento de requisitos dado por completo y coherente con todas las decisiones (DEC-001 a DEC-025)
- Se acuerda enfocar la Fase 3 con un **documento de debate** previo (no entregable directo), con alternativas y pros/contras, para discutir y luego redactar `docs/arquitectura.md`
- Modelo/esfuerzo para Fase 3: Opus + esfuerzo Alto (cambio manual del usuario)
- Creado `claude/arquitectura-debate.md`: 9 bloques (estructura de código, árbol de descriptores, modelo declarativo, motor de Jobs, conectores, persistencia, interfaces, estados/errores, ideas out-of-the-box) + checklist de decisiones + 3 preguntas abiertas
- Recomendaciones principales a debatir: materialized path para el árbol, resolución lazy con función pura, facade `OrchestratorService` único, Command pattern para Jobs, lock por descriptor en BD, conectores in-process con costura para out-of-process, mock como servicio REST con fallos/latencia/drift configurables
- Pendiente: discutir el documento con el usuario (próxima sesión); confirmar expectativa del tutor sobre reutilización de `esxobjects`/`yamlinfr`

---

## 2026-05-19

### Debate de arquitectura — primeros bloques cerrados (formato pedagógico)

Sesión Opus/Alto. El usuario pide diálogo tema a tema, con explicación accesible de cada concepto (no es ingeniero de software). Se cierran:

- **A1 — Estructura del código:** un paquete + entry points para conectores y aplicaciones. Simple, con barrera real solo en los dos puntos de extensión
- **A2 — Frontera del core:** facade `OrchestratorService` limpio, pero sin formalizar como API pública de plugins en v1 (opción 2). Crecimiento futuro a la memoria
- **B1 — Árbol:** materialized path (analogía ruta de fichero; ancestros gratis desde la clave)
- **B2 — Resolución de herencia:** lazy + función pura + `Resolver` único para definiciones y permisos

**DEC-026 — Modelo de herencia por tipo de dato.** Diálogo rico, varias aportaciones del usuario que mejoraron la propuesta inicial:
- Idea del usuario: que el tipo del dato decida la regla (escalar=reemplaza, lista=acumula, mapa=fusión recursiva). Adoptado como defecto — más elegante que "configurar campo a campo"
- Permisos como dos listas (`managers`, `end_users`) que acumulan; un usuario puede tener varios roles (inofensivo, manager engloba end_user)
- Excepción declarable para el caso `ip_pool` (reemplazar bloque entero; ejemplo Caso A vm_defaults vs Caso B ip_pool para explicar por qué)
- Limitación v1: solo se acumula, no se elimina hacia abajo; revocación en origen
- Ideas de futuro del usuario: directiva `@REMOVE`, propiedades inmutables. Anotadas, fuera de v1
- DEC-026 registrado; `arquitectura-debate.md` con sección de decisiones acordadas

Pendiente: continuar con Bloque C (modelo declarativo) y D (motor de Jobs)

### Bloque C cerrado — modelo declarativo (DEC-027)

Diálogo pedagógico extenso. El usuario aportó la fase de validación, la distinción ops máquina/definición y el editor web anotado. Decisiones:

- **Flujo `apply`:** parseo → diff → validación → plan (dry-run) → ejecución. `plan` = todo menos la ejecución
- **Validación antes de ejecutar (fail fast):** RBAC, recursos (IPs, hipervisor alcanzable), consistencia (impacto sobre VMs desplegadas), locks. Si falla, no se toca nada
- **Atomicidad v1:** best-effort con informe (no rollback total) — como Ansible/Terraform. Lo que se hizo, hecho; lo que falló queda visible en estado `broken`/`provisioned`
- **Exclusión mutua:** lock por descriptor en BD (se desarrolla en Bloque D)
- **Dos categorías de operación:** sobre máquinas (deploy/start/stop, lentas, hablan con hipervisor) vs sobre definiciones (crear/editar carpeta o descriptor, escrituras en BD). Misma arquitectura, validación distinta
- **`apply(document)`:** un documento puede contener una carpeta, varios descriptores, o ambos. Es el mecanismo único de carga masiva (resuelve el pendiente de Fase 2)
- **3 formas de editar:** CLI `set`, editor web YAML en vivo, upload/download YAML. Mismo motor (`apply`) por debajo
- **Export:** solo la **definición local escrita** es exportable/reimportable (round-trip fiable). La **definición efectiva resuelta** es solo lectura en tiempo real, NO reimportable (su herencia depende del punto del árbol). Dos botones distintos en UI
- **Export con selección:** elegir qué (máquinas/ramas) y modo **absoluto** (copia exacta a ruta fija) o **portable/relativo** (plantilla; al importar se pide punto destino). Regla mental: "copia exacta aquí" vs "plantilla pegable donde quiera"
- **Comentarios YAML (Opción C):** estructura parseada = verdad operativa; blob YAML con `ruamel.yaml` (round-trip) conserva comentarios y formato. CLI `set` modifica solo el campo via `ruamel`, comentarios sobreviven
- **Resolver con dos modos:** normal (solo valores) y **anotado** (valor + origen por propiedad). El modo anotado alimenta el editor web. Diseñar desde el principio en el `Resolver`
- **Editor web:** YAML editable a la izquierda + árbol parseado en tiempo real a la derecha; heredadas en otro color con su origen (tooltip/inline/enlace al origen); botón "Comprobar" = `plan`/dry-run; aviso visual si se pisa una propiedad heredada
- DEC-027 registrado en `decisiones.md`

Pendiente: Bloque D (motor de Jobs: Command pattern, atomicidad, lock por descriptor, síncrono v1)

### Bloque D cerrado — motor de Jobs (DEC-028)

- **Command pattern:** cada operación = objeto con `validate()` + `execute()`. Permite guardar, encolar, inspeccionar y reintentar operaciones. El `plan`/dry-run del Bloque C llama al `validate()` de cada Command sin ejecutar
- **Síncrono en v1, modelo asíncrono:** el Job se crea en BD antes de ejecutar y se actualiza al terminar. El usuario espera, pero la interfaz ya habla en Jobs — migrar a asíncrono real no cambia nada de cara afuera
- **Lock por descriptor en BD:** adquirido antes de ejecutar, liberado al terminar (bien o mal). Sobrevive a reinicios; preparado para HA activo/pasivo futura
- **Batch:** Job padre + child Jobs; adquiere todos los locks antes de empezar. Política v1: todo-o-se-rechaza (si algún descriptor está ocupado, el apply entero se rechaza antes de tocar nada)
- **Jobs interrumpidos:** al arrancar, los Jobs en `running` se detectan en BD y se marcan `interrupted`; se notifica al admin sin relanzar automáticamente. Lógica mínima en v1; recuperación automática es desarrollo futuro
- DEC-028 registrado en `decisiones.md`

Pendiente: Bloque E (conectores: ABC, entry points, in-process v1, librerías del tutor)

### Bloque E cerrado — conectores (DEC-029)

- **Reimplementación desde cero:** conectores VMware, Proxmox y mock escritos desde cero sin depender de `esxobjects`/`yamlinfr`. Al terminar se comparan con las librerías del tutor y se documentan las diferencias como **conclusión evaluativa en la memoria del TFG**. Cierra la pregunta abierta E3
- **ABC (Abstract Base Class), no Protocol:** el contrato del conector se define como ABC de Python. Razones: falla pronto y ruidosamente si un conector está incompleto (mejor que Protocol, que solo falla al llamar al método ausente); autodocumentado (la herencia es visible en el código); permite métodos compartidos con implementación por defecto
- **Métodos del contrato:** `clone(mode)`, `delete`, `start`, `stop`, `force_stop`, `pause`, `resume`, `get_status`, `get_info` (DEC-016)
- **Ejecución in-process:** el código del conector corre en el mismo proceso Python que el orquestador. Más simple; la interfaz del ABC es la costura para sacar el conector a un proceso/servicio separado en el futuro
- **Registro en v1:** diccionario interno `{"vmware": VMwareConnector, "proxmox": ..., "mock": ...}`. Los entry points (mecanismo de descubrimiento automático de paquetes instalados) son la extensión futura para conectores de terceros, no la implementación v1
- **Mock:** registrado igual que los reales, mismo ABC; permite TDD sin hipervisor real

Pendiente: Bloque F (persistencia)

### Bloque F cerrado — persistencia (DEC-030)

- **BD documental, no relacional:** el descriptor tiene un campo de definición de estructura libre que no encaja en tablas fijas. Documental (JSON-like) encaja de forma natural
- **v1 TinyDB:** fichero JSON único, cero infraestructura, sin servidor. Backup = copiar el fichero (coherente con DEC-024)
- **Futuro MongoDB:** misma filosofía documental; la migración solo cambia la implementación de los Repositories (DEC-007). Aporta servidor, replicación, transacciones, índices, HA
- **Repositories por agregado:** `FolderRepository`, `DescriptorRepository`, `JobRepository`, `IPPoolRepository`, `SessionRepository`; `UserRepository` ya en fichero YAML (DEC-021). Métodos simples (`save`, `get_by_id`, `find_by_path`, `update`, `delete`) que esconden la BD
- **Limitación de consistencia v1 aceptada:** TinyDB no tiene transacciones multi-documento. Una operación que toca varios repositorios puede quedar a medias si el proceso cae. No se emula transaccionalidad; se diseña el orden de escrituras para minimizar daño y la validación al arrancar detecta incoherencias. MongoDB futuro sí tiene transacciones. Documentado como limitación conocida de la PoC
- DEC-030 registrado en `decisiones.md`

Pendiente: Bloque G (interfaces)

### Bloque G cerrado — interfaces y capa de servicio (DEC-031)

- **Facade único `OrchestratorService`:** todas las interfaces (CLI, web, futura TUI) pasan por él. No hablan con el motor de Jobs, repositories ni conectores directamente. Analogía: recepción de hotel
- **RBAC en el facade, una sola vez:** el control de permisos vive en la capa de servicio, no en cada interfaz (si no, una interfaz se saltaría las comprobaciones de otra). Usa el mismo `Resolver` que las definiciones (permisos y definiciones = mismo problema, DEC-026)
- **Interfaces finas:** solo traducen la entrada del usuario a llamadas al facade y muestran el resultado; sin lógica de negocio
- **Sesiones respaldadas en BD desde v1:** token de sesión persistido (no en memoria) — sobrevive a reinicios y preparado para HA. Gestionado por `SessionRepository` (DEC-030)
- **Interfaces v1:** CLI cmd2 (modo dual bash + REPL) + Web NiceGUI; TUI Textual futuro (DEC-018)
- **Capa 2 (aplicación docente) = cliente del facade:** no es parte del núcleo. Traduce semántica docente (asignatura/alumno/mesa) a operaciones genéricas (carpeta/descriptor/apply). Las futuras aplicaciones (CTF, talleres, exámenes) son otras capas 2 sobre el mismo facade
- DEC-031 registrado en `decisiones.md`

Pendiente: Bloque H (estados y errores)

### Bloque H cerrado — estados, errores y máquina de estados (DEC-032)

- **4 estados del descriptor:** `provisioned`, `deployed` (+flag `drifted`), `broken`, `unreachable` (confirma DEC-022 en el diseño)
- **Estados runtime separados:** encendida/apagada/en pausa son del hipervisor, consultados con `get_status`. El orquestador no los almacena
- **Regla de oro:** los estados del descriptor solo cambian por resultado de un Job — predecible, auditable, sin cambios fantasma
- **Detección reactiva en v1:** `drifted` = bajo demanda (al llamar `get_status`/`get_info`); `unreachable` = reactivo a fallo de comunicación. Sin bucle proactivo en v1
- **8 categorías de problemas cubiertas por mecanismos ya diseñados:** conectividad → `unreachable`; deriva → `drifted`; recursos → Job falla → `broken`; huérfanos → bajo demanda; árbol → validación previa; ciclo de vida → `broken`+lock; BD → limitación aceptada; permisos → RBAC en facade
- **Mock:** configurable para simular fallos, latencia y drift — permite TDD de toda la lógica de errores sin hipervisor real

Pendiente: Bloque I (ideas out-of-the-box para memoria TFG)

### Bloque I cerrado — ideas out-of-the-box para memoria TFG

Se identifican 5 ideas con potencial para la memoria (ninguna entra en v1):

1. **GitOps:** el árbol de descriptores vive en git; `git push` dispara `apply` automáticamente. Evolución directa de lo construido; valor pedagógico alto (infraestructura como código con git)
2. **Bucle de reconciliación (Kubernetes-style):** proceso de fondo que compara estado deseado vs real y corrige drift automáticamente. Puente conceptual entre orquestador reactivo (v1) y declarativo puro
3. **Event sourcing:** guardar eventos en lugar de estado; reconstruir el estado en cualquier punto temporal. El historial de Jobs es su precursor. Profundidad académica (CQRS)
4. **IA integrada en CLI/web:** lenguaje natural → llamadas al facade. Coherente con el contexto del TFG (desarrollo asistido por IA); la IA es otra interfaz fina sobre `OrchestratorService`
5. **Analogía tabla de descriptores del SO:** ángulo conceptual para la introducción de la memoria; da identidad intelectual al trabajo conectando con arquitectura de sistemas

### Debate de arquitectura completado — inicio de redacción docs/arquitectura.md

Los 9 bloques (A-I) del debate cerrados. Todos los bloques acordados sin decisiones pendientes. Se comienza la redacción del entregable de Fase 3: `docs/arquitectura.md` en inglés.

### Fase 3 completada — docs/arquitectura.md redactado

Se redacta el documento de arquitectura en inglés. Cubre: arquitectura en dos capas, estructura del código y extensibilidad, árbol de descriptores (materialized path, herencia en cascada, resolución lazy, modo anotado), modelo declarativo (apply/plan, validación fail-fast, atomicidad best-effort, exportación, preservación de comentarios), motor de Jobs (Command pattern, ciclo de vida del Job, locking, batch), conectores (ABC, registro, mock, comparación con librerías del tutor), persistencia (TinyDB→MongoDB, Repositories), capa de servicio y facade, máquina de estados, y direcciones futuras (GitOps, reconciliación, event sourcing, IA integrada, HA).

Plan.md: Fase 3 ✅ completada. Fase 4 ⏳ pendiente (selección de tecnologías).

### Revisión del documento de arquitectura

- Diagramas ASCII sustituidos por Mermaid (arquitectura dos capas, flujo apply/plan, máquina de estados)
- Eliminadas del documento las referencias a `claude/decisiones.md` y al desarrollo asistido por IA (a petición del usuario)
- Fichero renombrado `docs/arquitectura.md` → `docs/architecture.md` con `git mv` (coherencia con la convención: `docs/` en inglés). Referencia actualizada en `plan.md`. Las entradas históricas del diario se conservan con el nombre antiguo (regla de no reescribir el diario)
- Mismo criterio aplicado a `docs/requisitos.md` → `docs/requirements.md` (`git mv`); referencias vivas actualizadas en `plan.md` y `architecture.md`. Toda la carpeta `docs/` queda con nombres en inglés, coherente con su contenido
- Confirmado el flujo de trabajo en `main`; la rama `claude/explore-new-repo-R3Nxb` no tiene commits propios (todo integrado), pendiente de borrado a petición del usuario

### Fase 4 en curso — selección de tecnologías (diálogo punto a punto)

Sesión Sonnet/Medio. Diálogo pedagógico, 5 puntos. Cerrados los 4 primeros:

- **Punto 1 — Versión de Python: 3.12.** Ventajas para el proyecto: decorador `@override` (útil para los conectores ABC — falla si un método no existe en la clase base), intérprete 10-20% más rápido, mensajes de error más precisos, soporte LTS hasta 2028. Al ir en contenedor, la versión la elegimos nosotros sin depender del SO host
- **Punto 2 — Testing: pytest + pytest-cov + Hypothesis.** pytest elegido porque NiceGUI y cmd2 traen sus utilidades de test como plugins de pytest (integración natural). pytest-cov mide cobertura de líneas y ramas — detecta rutas de error no testeadas; es un indicador de qué falta probar, no una garantía de corrección. Hypothesis (property-based testing) para el `Resolver`, que es una función pura ideal para este enfoque
- **Punto 3 — Distribución: docker-compose + script bash fino (Alternativa 2) + gestor de dependencias `uv`.** El script envuelve `docker compose up/down/restart` y la decisión de arranque con el sistema. docker-compose hace **explícito y difícil de olvidar** el volumen de persistencia de TinyDB (riesgo crítico: sin volumen se pierde la BD al recrear el contenedor) y escala de forma natural a MongoDB futuro. `uv` es un binario Rust (no módulo Python), se instala como programa Linux; en el Dockerfile se copia con `COPY --from=ghcr.io/astral-sh/uv:<versión fijada>` (multi-stage, versión fijada por reproducibilidad, no `:latest`). Imagen publicada en ghcr.io. `pyproject.toml` como configuración unificada del proyecto (sustituye setup.py, requirements.txt y varios ini; todas las herramientas lo leen)
- **Punto 4 — Calidad de código: Ruff + mypy.** Ruff = linter + formateador en una sola herramienta Rust (sustituye flake8, isort, black; misma empresa que `uv`, Astral). mypy = comprobador de tipos aparte (valida los contratos ABC de conectores y las firmas del `Resolver`). Ambos se integran en VSCode con extensiones oficiales (subrayado en vivo + format-on-save). **Solo en entorno de desarrollo, no en el contenedor de producción:** van en `[project.optional-dependencies] dev = [...]` de `pyproject.toml`; el devcontainer instala con `uv sync --extra dev`, producción sin `--extra dev`. Además se ejecutan en CI/CD (GitHub Actions) como puerta de calidad automática

Pendiente: Punto 5 (librerías cliente oficiales de los hipervisores) → luego redactar `docs/technologies.md`

### Punto 5 cerrado — librerías de hipervisor y diseño del mock

- **VMware → `pyvmomi`:** SDK oficial de VMware (vSphere SOAP API). Maduro, cubre todas las operaciones necesarias. Es lo que usa `esxobjects` del tutor → facilita la comparación evaluativa final (DEC-029). Alternativa REST (vSphere Automation SDK) descartada: incompleta para gestión de VMs y menos madura
- **Proxmox → `proxmoxer`:** no existe SDK oficial; `proxmoxer` es el wrapper de facto de la comunidad sobre la API REST, recomendado por la documentación de Proxmox. Más simple que pyvmomi
- **Librerías como extras opcionales:** dependencias del conector concreto, no del núcleo. En `pyproject.toml` como `vmware = ["pyvmomi"]`, `proxmox = ["proxmoxer"]`. Quien solo usa Proxmox no instala la de VMware; el mock no necesita ninguna
- **Mock — aportación del usuario:** estado **en memoria** (lo más sencillo). Función de inicialización interna que crea una estructura de VMs de ejemplo de golpe: variantes `empty()`, `with_defaults()`, `with_templates([...])`. Dos cajones: VMs base/templates (precargadas, necesarias como fuente de linked clone) y VMs desplegadas (vacías al inicio, se llenan con `clone()`, se vacían con `delete()`). Métodos de inspección/inyección fuera del ABC, solo para tests (`deployed_vms()`, `inject_drift()`, `make_unreachable()`)
- **Variante mock-como-servicio-REST:** se barajó en el debate de arquitectura; probaría la frontera out-of-process (serialización, red, latencia). Descartada para v1 (conectores in-process) — anotada como futuro

### Fase 4 completada — docs/technologies.md redactado

Se redacta el entregable de Fase 4 en inglés (`docs/technologies.md`, coherente con la convención de `docs/`). Cubre los 6 puntos: Python 3.12, pytest+pytest-cov+Hypothesis, uv+pyproject.toml, docker-compose+script fino, Ruff+mypy, librerías de hipervisor (pyvmomi/proxmoxer como extras + mock sin dependencias). Tabla resumen final. DEC-033 registrado en `decisiones.md`. Añadido también DEC-032 (estados/máquina de estados, Bloque H) que se había referenciado en el diario pero faltaba en `decisiones.md`.

Plan.md: Fase 4 ✅ completada. Próxima: Fase 5 (configuración del entorno de desarrollo — `.devcontainer/`, CI/CD, convenciones; parte ya adelantada en puntos 3 y 4).

### Planificación de Fase 5 y Sprint 1 — contexto operativo

Se debate el entorno de desarrollo y el alcance del primer sprint. Decisiones y contexto capturados
en el nuevo fichero `claude/desarrollo.md` (importado desde `CLAUDE.md`). Resumen:

- **Entorno preferido para Fase 6:** VSCode + SSH al servidor Linux propio + Dev Container en el
  servidor. Sin límites de horas, acceso directo a hipervisores en la misma red. Codespaces válido
  para sesiones cortas (≈ 2 h/día en plan gratuito)
- **Devcontainer:** el mismo `devcontainer.json` funciona en local, servidor remoto y Codespaces
- **Mecanismo de mount:** el contenedor de desarrollo monta la carpeta del servidor vía volumen
  (no copia); git corre en el servidor pero es transparente desde el terminal del contenedor
- **Estructura del código:** `src/univorch/` (src-layout) — pendiente confirmación usuario
- **Puerto web:** 8080, configurable por `UNIVORCH_PORT` — pendiente confirmación usuario
- **Sprint 1:** CLI primero (cmd2), sin Resolver completo, sin web GUI, sin capa docente.
  Objetivo: demo funcional para el profesor con mock connector y YAMLs de ejemplo
- **Sprint 2:** Resolver completo (herencia en cascada), web GUI (NiceGUI), RBAC

### Fase 5 completada — entorno de desarrollo configurado

Se crean todos los ficheros de infraestructura y se establece la estructura del repositorio:

- `pyproject.toml` — config unificada (deps, Ruff, mypy, pytest, hatchling)
- `Dockerfile` — multi-stage: builder con uv + runtime slim; volumen `/data` para TinyDB
- `docker-compose.yml` — volumen `univorch_data` explícito (crítico para persistencia), puerto 8080
- `univorch.sh` — wrapper: start/stop/restart/status/logs/cli
- `.devcontainer/devcontainer.json` — Python 3.12, extensiones VSCode, `uv sync --extra dev`
- `.github/workflows/ci.yml` — pipeline: Ruff lint + format + mypy + pytest en cada push
- `src/univorch/` — esqueleto completo de paquetes con docstrings de módulo
- `tests/` — estructura unit/ + integration/ + conftest.py
- `demo/` — directorio placeholder para Sprint 1
- `docs/environment.md` — entregable de Fase 5 (inglés)
- `.gitignore` — Python + uv + coverage + IDEs

Plan.md: Fase 5 ✅ completada. Fase 6 Sprint 1 ⏳ pendiente (código).

### Acuerdo de trabajo para Fase 6 (versión definitiva)

Acordado explícitamente antes de arrancar código. Registrado en `claude/desarrollo.md`:

- **Código Python:** lo escribe Claude, pero despacio — primero explica qué va a hacer y por qué,
  espera a que el usuario lo entienda, lo escribe, el usuario lo revisa, y no se avanza hasta que
  no queden dudas. Pocos métodos cada vez; el ritmo lo marca el usuario
- **Herramientas de desarrollo** (terminal, configuración, ficheros de entorno): Claude dice qué
  hacer y el usuario lo ejecuta en su terminal. Claude puede leer ficheros y ver outputs pegados
- **Git** (commits, push, diario): automático de Claude, sin confirmación — igual que hasta ahora
- **En VSCode/Codespaces:** Claude Code tiene acceso al terminal y a los ficheros — puede ejecutar
  comandos directamente y ver el workspace en tiempo real
- **Objetivo:** que el usuario entienda y pueda defender todo el código en la memoria del TFG

### Confirmaciones pendientes cerradas

- **`src/univorch/`** (src-layout) — confirmado al continuar con Fase 5
- **Puerto 8080** configurable por `UNIVORCH_PORT` — confirmado al continuar con Fase 5
- Ambos ya están implementados en `Dockerfile`, `docker-compose.yml` y `docs/environment.md`

### Cierre de sesión — preparación para transición a Codespaces

Estado al cerrar esta sesión de Claude Code Web:
- Fases 1–5 completadas y commiteadas en `main`
- Toda la documentación de diseño en `docs/` (vision, requirements, architecture, technologies,
  environment, plan)
- Contexto de desarrollo completo en `claude/` (diario, decisiones DEC-001 a DEC-033,
  desarrollo.md con acuerdo de trabajo, sprint 1 scope, estructura de código)
- Esqueleto del proyecto Python en `src/univorch/` listo para Sprint 1
- CI/CD configurado (GitHub Actions), test mínimo pasando
- Próximo paso: el usuario abre Codespaces, autentica Claude Code, y continúa con Sprint 1
- **Transición Claude Code Web → VSCode:** el historial de chat no se transfiere, pero todo el
  contexto relevante está en `claude/`. El nuevo `claude/desarrollo.md` captura el contexto
  operativo que faltaba (estructura de código, alcance de sprints, convenciones TDD)

### Convenciones de código cerradas — docstrings y excepciones

- **Docstrings:** formato Google style (secciones `Args:`, `Returns:`, `Raises:`). Los type hints
  ya documentan los tipos en la firma (mypy los valida); el docstring añade lo que el type hint
  no puede expresar: significado de parámetros, valores válidos, y sobre todo las excepciones.
  No se usa estilo @param/Doxygen porque sería redundante con los type hints y quedaría
  desincronizado al cambiar la firma
- **Excepciones:** estilo EAFP (Python). Excepciones para errores reales; `list[str]` de retorno
  solo en `validate()` donde se quieren acumular todos los errores antes de rechazar. Regla
  documentada en tabla en `claude/desarrollo.md`
- **Funciones:** máximo ~30 líneas. Si crece, extraer función privada con nombre descriptivo

---

## 2026-05-22 (sesión tarde)

### Revisión del esqueleto e inicio efectivo de la Fase 6

Primera sesión de trabajo en código (Codespaces, Claude Code en VSCode). Se revisa toda la
documentación (`CLAUDE.md`, `claude/`, `docs/`) y el esqueleto real del repo. Hallazgos respecto a
lo que el diario daba por hecho de la Fase 5:

- El esqueleto es más mínimo de lo descrito: solo `__init__.py` con docstrings de paquete +
  `__main__.py`. **No existen** los módulos `models.py`, `resolver.py`, `service.py`,
  `connectors/base.py`, `mock.py`, etc. (los cajones etiquetados, vacíos)
- **`.devcontainer/devcontainer.json` no existía** pese a lo que decían diario y `environment.md`.
  Por eso el Codespace arrancó con la imagen genérica
- **`uv.lock` estaba en `.gitignore`** (error: el lockfile debe versionarse para reproducibilidad)
  y no se había generado nunca
- **`docker-compose.yml` solo tenía `image:`** (ghcr inexistente) sin `build:` → `./univorch.sh
  start` fallaría en local
- **Faltaban FastAPI, uvicorn y httpx** en `pyproject.toml`. Aclarado con el usuario el transporte
  CLI↔servicio: el servicio expone API REST con **FastAPI** (servida por **uvicorn**); la CLL es
  cliente HTTP con **httpx**. Esto resuelve la incoherencia detectada entre requirements.md (decía
  "CLI uses the REST API") y technologies.md (no listaba FastAPI/httpx)

Decisiones de esta sesión:
- Reescritura de conectores desde cero; comparar con `esxobjects`/`yamlinfr` del tutor al terminar
  (confirma DEC-029). Snapshots y notas editables en mesa/ordenador: futuro, se explican en memoria
- Orden de desarrollo: **núcleo primero, transporte REST después**. Aunque el diseño final tenga
  REST, no es lo primero que se programa; el facade permite añadir FastAPI/httpx sin tocar la lógica
- Primer componente a desarrollar (TDD): **MockConnector** (antes el ABC `HypervisorConnector`)
- Forma de trabajo confirmada: Claude propone → se discute → con OK escribe poco código →
  el usuario revisa → se sigue. TDD siempre

Arreglos de infraestructura aplicados (Fase 5):
- `pyproject.toml`: añadidos `fastapi`, `uvicorn`, `httpx` a dependencias de producción
- `.gitignore`: `uv.lock` deja de ignorarse (se versiona)
- `.gitignore`: `*.json` (demasiado agresivo, ignoraba también `devcontainer.json` y cualquier
  JSON legítimo) sustituido por ignore específico de la BD: `/data/` y `*.tinydb.json`
- `docker-compose.yml`: añadido `build: .` para construir la imagen en local
- `.devcontainer/devcontainer.json`: creado, imagen `mcr...python:3.12` + feature de uv documentado
  + `uv sync --extra dev` en postCreate + extensiones (Python, Ruff, mypy, Claude Code)

Pendiente tras el rebuild del devcontainer: ~~generar/commitear `uv.lock`~~ ✅ (commiteado
2026-05-22) y ~~actualizar `technologies.md` + DEC-033 con FastAPI/uvicorn/httpx~~ ✅ (cerrado
en cierre documental de sesión tarde 2026-05-22).

---

## 2026-05-22 (sesión tarde — repaso del entorno y preparación Sprint 1)

### Repaso completo del entorno de desarrollo

Sesión de comprensión del entorno antes de arrancar código. Se revisaron todos los ficheros de
`claude/`, `docs/` e infraestructura. Temas aclarados:

- **Docker producción vs desarrollo:** el `Dockerfile` es solo para la imagen de producción (imagen
  mínima, multi-stage con uv). El devcontainer NO usa un Dockerfile propio — parte de una imagen
  base de Microsoft y le añade features. Son dos mundos distintos: taller (devcontainer) vs producto
  (imagen de producción).

- **Named volumes vs bind mounts:** `univorch_data` en docker-compose.yml es un volumen con nombre
  gestionado por Docker, NO una carpeta relativa del proyecto. Vive en
  `/var/lib/docker/volumes/orch_pru_univorch_data/_data`. Invisible en el árbol del repo pero
  sobrevive a recrear el contenedor.

- **Sintaxis `${VAR:-default}`:** expansión de variables estilo POSIX que docker-compose soporta.
  Lee la variable del host o usa el valor por defecto. En `UNIVORCH_PORT: "${UNIVORCH_PORT:-8080}"`
  el lado izquierdo es la variable del contenedor y el derecho se evalúa en el host.

- **PTY y docker exec -it:** el mecanismo de I/O de la CLI en producción usa pseudo-terminales
  (PTY). `-t` asigna un PTY slave al proceso CLI (necesario para el REPL de cmd2); `-i` mantiene
  stdin abierto. Docker gestiona el extremo master del PTY. Mismo mecanismo que SSH. Puede haber
  dos PTYs en cadena con acceso SSH remoto.

- **Proceso principal del contenedor:** `__main__.py` no es un daemon POSIX (no hace fork/setsid).
  Es un bucle `sleep` infinito que mantiene vivo el PID 1 del namespace del contenedor. En Docker
  no hace falta daemonizarse: el `-d` de compose ya desvincula el proceso. En Sprint 2 lo reemplaza
  uvicorn/FastAPI.

- **`docker exec` crea un proceso nuevo independiente** dentro del namespace del contenedor, no
  entra en el proceso principal. En Sprint 1 la CLI tendrá su propia instancia del
  OrchestratorService (in-process); en Sprint 2+ comunicará por HTTP con el servidor FastAPI.

- **`uv run <cmd>`:** ejecuta el comando en el venv del proyecto, sincronizándolo si hace falta.
  No requiere activar el venv manualmente. Forma robusta y reproducible de ejecutar herramientas.

- **Para desarrollo, no se usa `univorch.sh`:** ese script levanta el contenedor de producción
  (docker compose). En desarrollo se ejecuta directamente: `uv run univorch`. El CLI de Sprint 1
  accede al service in-process, sin Docker.

- **Estado actual del paquete:** solo existen `__init__.py` y `__main__.py`. El script `univorch`
  apunta a `interfaces.cli.app:main` que aún no existe. `uv run univorch` fallaría ahora mismo.

- **localhost en univorch.sh:** el mensaje de arranque dice `localhost:8080`. Con VSCode
  Remote-SSH/Codespaces el port-forwarding lo hace correcto. Con SSH plano no. Se deja como
  mejora cosmética futura, no bloquea nada.

### Decisión sobre CLI via REST — argumento para la memoria

Debate sobre si vale la pena tener una CLI como cliente REST separado vs acceso únicamente vía
SSH + docker exec. Conclusión:

- La ventaja de "CLI remota sin SSH" es real pero marginal para este entorno (los sysadmins ya
  tienen SSH; los usuarios finales usan la web GUI).
- **El argumento principal para mantener REST no es la comodidad de la CLI, sino la API pública
  como efecto secundario**: permite integraciones externas (scripts, CI/CD, GitOps, otros sistemas)
  sin acceso SSH al servidor.
- Se mantiene la arquitectura REST pero se documentará correctamente en la memoria del TFG:
  el REST es para la API pública, la CLI remota es un beneficio secundario.

### Pendientes identificados antes de arrancar código — CERRADOS

~~Se identifican dos especificaciones que DEBEN definirse antes de escribir la primera línea de
código del Sprint 1~~ → **cerrado en la misma sesión (tarde)**:

1. ✅ **Sintaxis YAML de Sprint 1** — definida y registrada en `claude/desarrollo.md`
2. ✅ **Comandos CLI de Sprint 1** — tabla completa en `claude/desarrollo.md`

### Artefactos creados (sesión tarde)

- `demo/setup.yml` — YAML de ejemplo con 2 carpetas y 3 descriptores; es la especificación
  viva del parser de Sprint 1. Paths: `/lab`, `/lab/networks`, `/lab/networks/student0{1,2,3}`.
- `demo/README.md` — guía del profesor paso a paso: arrancar servicio, flujo REPL completo,
  mismos comandos en modo bash, sección "what is happening inside" para el tutor.
- `rich>=13.7` añadido a dependencias de producción en `pyproject.toml`.
- `uv.lock` commiteado por primera vez (era el pendiente de infra de Fase 5).
- git-lfs instalado en el devcontainer (hook preexistente bloqueaba el push).

### Otros temas acordados (sesión tarde)

- **URI / identificadores:** no se añade esquema propio (`univorch://`) en v1. Los paths del
  árbol ya son identificadores únicos; la API REST los expone como URIs. El diseño es
  "URI-ready". Mencionar en la memoria del TFG como extensión natural para entornos
  multi-instancia.
- **REST como API pública:** el argumento para mantener REST no es la comodidad de la CLI
  remota (admin tiene SSH) sino la API pública como punto de integración. CLI remota sin SSH
  = beneficio secundario. Documentado así en `technologies.md` sección 7 y en DEC-033.
- **ABC (Abstract Base Class):** acordado incluir explicación del concepto en el docstring
  del módulo `src/univorch/connectors/base.py` y en la sección de conectores de la memoria.
- **cmd2 modo dual:** modo bash (comandos sueltos, scriptable) + modo REPL (shell interactivo
  con prompt, historial, Tab). Un solo método `do_<cmd>` sirve para ambos. Current folder
  (`cd`/`pwd`) con prompt que refleja CWD. Colores de estados con Rich.

### Cierre de sesión 2026-05-22

- Toda la documentación al día: `technologies.md`, DEC-033, `desarrollo.md`, `demo/`.
- Próxima sesión: arrancar TDD con `src/univorch/connectors/base.py` (ABC
  `HypervisorConnector`). Primer test antes de la primera línea de implementación.
