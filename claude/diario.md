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

### Rename del repositorio

- Repositorio renombrado de `clamaveruma/orch_pru` a `clamaveruma/univorch` en GitHub.
- Las menciones históricas al nombre antiguo en el diario se conservan (política de no
  reescribir entradas pasadas).
- Ficheros actualizados: `docs/environment.md`, `docker-compose.yml`, `claude/proyecto.md`.
- Remote del Codespace actualizado: `git remote set-url origin https://github.com/clamaveruma/univorch`.

### Cierre de sesión 2026-05-22

- Toda la documentación al día: `technologies.md`, DEC-033, `desarrollo.md`, `demo/`.
- Próxima sesión: arrancar TDD con `src/univorch/connectors/base.py` (ABC
  `HypervisorConnector`). Primer test antes de la primera línea de implementación.

---

## 2026-05-23

### Repaso de diseño previo al ABC del conector (Opus, esfuerzo alto)

Sesión de reflexión antes de escribir la primera línea de código del conector. Se aclaran
y deciden varios puntos del modelo. Pendiente formalizar en `decisiones.md` (DEC-034, DEC-035)
tras confirmación del usuario.

**Arreglo de entorno — intérprete de Python en VSCode**
- El aviso "Could not resolve interpreter path '.venv/bin/python'" al reconectar al Codespace
  es un falso positivo de timing: el `.venv` existe y persiste; la ruta relativa se evalúa
  antes de montar el workspace. Arreglo: usar `${workspaceFolder}/.venv/bin/python` en
  `.devcontainer/devcontainer.json`. Pendiente de aplicar.

**Pydantic — adopción acotada (futura DEC-034)**
- Se adopta Pydantic v2 "de forma sencilla, donde simplifique". Dónde SÍ: entidades
  (`Folder`, `Descriptor`, `Job`, `Session`) como `BaseModel` por la serialización a TinyDB
  (`model_dump()`/`model_validate()` eliminan el código de conversión a mano); validación del
  documento `apply` (`ApplyDocument(BaseModel)`); tipo de retorno `VMInfo` de `get_info()`.
  Dónde NO: el Resolver (opera sobre `definition` libre; Hypothesis necesita dicts arbitrarios);
  `RuntimeState` (es un `Enum`, no Pydantic); `config.py` (2 env vars, `os.environ` basta); el
  campo `definition` del descriptor (queda `dict` flexible, lo fusiona la herencia DEC-026).
  "Sencillo" = `BaseModel` pelado, sin validators salvo donde cacen un bug real, sin alias ni
  serializers custom. El patrón Repository (DEC-030) aísla la serialización → decisión reversible.

**Tipos que cruzan la frontera del conector**
- `RuntimeState(Enum)`: RUNNING, STOPPED, PAUSED, UNKNOWN — estado de energía del hipervisor.
- `VMInfo(BaseModel)`: id, name, runtime_state, cpu, memory_mb, disk_gb (opcionales por ahora).
- `get_status()` devuelve solo `RuntimeState` (consulta barata y frecuente); `get_info()`
  devuelve el `VMInfo` completo (foto para comparar y detectar `drifted`). `get_status` es,
  conceptualmente, "una porción barata de `get_info`".

**Dos ejes de estado (aclaración de DEC-022/032)**
- `status` muestra el producto de dos máquinas de estado: estado del descriptor
  (`provisioned`/`deployed`+`drifted`/`broken`/`unreachable`) y, solo cuando está `deployed`,
  el estado runtime (`running`/`stopped`/`paused`/`unknown`). "deployed + running",
  "unreachable" (= disconnected), etc. son combinaciones de esos dos ejes, no un único estado.

**Identidad de la VM**
- En el orquestador: clave única = path completo (materialized path).
- En el hipervisor: siempre un **id estable** (VMware: MoRef `vm-1234` + instanceUuid; Proxmox:
  VMID entero + node). El **nombre NO sirve como clave** (mutable, no único).
- El conector devuelve un **id opaco (`str`)** desde `clone()`; el core lo guarda en el descriptor
  junto al conector y lo trata como caja negra. El `vm_id` es estado de runtime del descriptor:
  `None` en `provisioned`, se rellena en `deploy`, se limpia en `undeploy`.
- instanceUuid (VMware) importa más para el descubrimiento futuro de VMs preexistentes (DEC-020).

**Metadatos en la VM del hipervisor — referencia inversa (ideas de futuro, no v1)**
- Cada hipervisor tiene un campo de texto libre: VMware `annotation`/notes; Proxmox `description`.
  En el interface común se expone como `set_metadata`/`get_metadata` (dict); cada conector traduce.
- Se guarda un JSON delimitado (bloque marcado tipo `# BEGIN/END managed by UnivOrch`) que
  coexiste con texto previo del humano.
- Utilidades futuras: (1) recuperación ante pérdida/corrupción de TinyDB reconstruyendo el mapeo
  descriptor→VM desde los hipervisores; (2) detección de VMs movidas/renombradas a mano;
  (3) detección de huérfanos/fantasmas (categoría 4 de las 8); (4) marcas para descriptores de
  referencia (con cuidado por no invasión, DEC-020); (5) recuperación de crash a mitad de deploy
  (limitación de consistencia DEC-030); (6) arbitraje multi-instancia/MSP con `instance_id`.
- Cautelas: la marca es pista, no verdad (un humano puede editarla); no estampar VMs de terceros;
  no guardar secretos (es visible en el hipervisor); respetar límites de tamaño del campo (~KB).
- Sprint 1: el MockConnector llevará un campo `metadata` en su estado en memoria desde ya (coste
  cero) para poder hacer TDD de la reconciliación en el futuro sin hipervisor real.
- Refina DEC-005b (referencia inversa) y DEC-020 (descubrimiento).

**Operativa por rol — huecos detectados**
- Hueco A (acceso del alumno): NO es un hueco. La web muestra la(s) IP(s) de cada VM; cómo se
  conecta es ajeno al core. Matices: el modelo debe permitir varias IPs (multi-NIC); URL de
  consola noVNC = mejora opcional futura.
- Hueco B (gestión de Jobs): hace falta, y distinta por rol (admin todo / manager su rama /
  alumno los suyos). Sprints siguientes.
- Hueco C (`whoami` + usabilidad): `whoami` entra. cmd2 da `help`/`help <cmd>` autogenerados,
  tab-completion de comandos y, clave, **completers de paths del árbol** (navegar como un FS).
  Prompt podría incluir el rol (`univorch:admin /lab/networks>`) — opcional.
- Recordatorio: crear mesas/asignaturas/alumnos es **capa 2** (aplicación docente), no el core.

**Idempotencia (futura DEC-035)**
- Todas las operaciones del orquestador son idempotentes por la filosofía declarativa (DEC-006):
  son aserciones de estado ("asegura X"), no deltas imperativos. Se documentará por operación.
- **La idempotencia vive en el orquestador, NO en el conector.** Las primitivas del conector
  (`clone`, `delete`) NO son idempotentes; el Command (DEC-028) comprueba el estado y solo llama
  al conector si hace falta. Conector primitivo + orquestador convergente.
- Límite honesto: idempotencia solo en el camino feliz. `deploy` sobre `broken` o `start` sobre
  `unreachable` son errores, no no-ops.
- No-op (orden de algo ya hecho) = **éxito + mensaje informativo, nunca warning** (modelo Ansible
  `changed`/`unchanged`). El Job lo registra como no-op. Coherente con el `plan`/diff (DEC-027):
  `apply` informaría `3 unchanged, 1 created`; `start` ya encendido → `already running (no change)`.

### Primer código — contrato del conector (TDD)

Arranca la Fase 6 en código. Se desarrolla el contrato del conector en tres piezas, cada una
escrita, revisada por el usuario y commiteada por separado (ritmo lento acordado):

- **Pieza 1 — tipos de frontera** (`connectors/types.py`): `RuntimeState(StrEnum)`
  RUNNING/STOPPED/PAUSED/UNKNOWN y `VMInfo(BaseModel)` (id opaco, name, runtime_state, cpu/mem/disk
  opcionales). Test: estados del enum, comportamiento StrEnum, construcción mínima, round-trip
  `model_dump`/`model_validate`, campo requerido. Commit `c60f857`.
- **Pieza 2 — ABC** (`connectors/base.py`): `HypervisorConnector(ABC)` con los 9 métodos de DEC-016.
  Contrato de errores común (`ValueError`/`ConnectionError`) en el docstring de la clase, no
  repetido por método. Idempotencia anotada en los métodos de ciclo de vida. Añadido
  `CloneMode(StrEnum)` {LINKED, FULL} a `types.py`. Commits `57e636f`.
- **Pieza 3 — test del ABC** (`tests/unit/test_connector_base.py`): subclase completa instanciable,
  ABC no instanciable directamente, subclase incompleta → `TypeError`. Demuestra el "fail fast" del
  ABC. Commit `57e636f`.

Decisiones de implementación de esta tanda:
- Plugin `pydantic.mypy` activado en `pyproject.toml` para que mypy valide la construcción de modelos
  (coherente con `strict = true` + DEC-034).
- Nombre del fichero del contrato: `base.py` (convención Python estándar; se descartó `common_*` por
  no idiomático).
- Fix del aviso del intérprete en VSCode: `${workspaceFolder}/.venv/bin/python` en `devcontainer.json`.
- Feedback del usuario sobre comentarios: útiles para entender el código, sin sobreexplicar (no
  justificar features del lenguaje en comentarios). Aplicado al recortar docstrings.

Estado: 9 tests en verde, `types.py` y `base.py` al 100% de cobertura. Toda la puerta de calidad
(ruff + mypy + pytest) pasa en local.

Próximo: **`MockConnector`** — primera implementación real del ABC, estado en memoria (plantillas
precargadas + VMs desplegadas), TDD del comportamiento (clone, start/stop, get_status/get_info,
simulación de fallos/latencia/drift). Variantes `empty()`/`with_defaults()`/`with_templates()` y
métodos de inspección fuera del ABC (`deployed_vms`, `inject_drift`, `make_unreachable`).

---

## 2026-05-24

### MockConnector completo (M1-M3, TDD)

Primera implementación real del ABC, en tres sub-piezas commiteadas por separado:
- **M1** (`46b9d62`): estado en memoria (templates + deployed + contador), constructores
  `empty()`/`with_demo_templates()`/`with_templates()`, `clone()` (rechaza FULL, valida plantilla,
  id determinista `mock-vm-N`, nace STOPPED) y `get_status()` vía helper `_get()` (EAFP).
- **M2** (`61a44ab`): ciclo de vida `start`/`stop`/`force_stop`/`pause`/`resume`. Tabla de
  transiciones acordada: start/stop/force_stop totales (convergen al destino); pause/resume sobre
  una VM STOPPED → `ValueError`. `force_stop` = `stop` en el mock (no hay SO real). Idempotencia "de
  verdad" (reporte unchanged) vive en el orquestador (DEC-035), no aquí: el conector solo fija estado.
- **M3** (`46b9d62`… `M3` commit): `delete` (no idempotente, DEC-035), `get_info` (VMInfo con specs
  en None), `deployed_vms()` (inspección fuera del ABC). Mock al 100% de cobertura.
- **M4** (simulación de fallos: `make_unreachable`/latencia/`inject_drift`) pospuesto hasta que haya
  lógica de errores del orquestador que probar.
- Renombrado el constructor `with_defaults` → **`with_demo_templates`** (más descriptivo; "demo
  templates", coherente con `with_templates`).

### Modelos del dominio — `Folder`, `Descriptor` (TDD)

`src/univorch/models.py` con Pydantic (DEC-034):
- `DescriptorState(StrEnum)`: PROVISIONED/DEPLOYED/BROKEN/UNREACHABLE.
- `Folder` (path, description) y `Descriptor` (path, hypervisor, base_vm, specs, state, vm_id).
- `TreePath = Annotated[str, AfterValidator(_validate_path)]`: tipo reutilizable con **validación
  sintáctica** del path (empieza por `/`, sin segmentos vacíos, segmentos `[A-Za-z0-9_-]+`).
  No se repite el validador en cada modelo.
- **Separación de validación (decidida con el usuario):** la sintáctica va en el modelo; la
  contextual (padre existe, crear vs actualizar, referencias) y el RBAC van en el service/`apply`
  (DEC-027/031), nunca en el modelo. El patrón de nombres de segmento es provisional, a refinar.

### Renombrado de campos del descriptor

`connector` → **`hypervisor`** (el descriptor habla en dominio: dónde vive la VM, no el adaptador) y
`template` → **`base_vm`** (más claro, coherente con "VM"). Actualizados `demo/setup.yml` y la spec
YAML de `desarrollo.md`. El conector sigue recibiendo el id de plantilla como `source_id` (capa
distinta).

### Documento de diagramas — `docs/diagrams.md`

Nuevo documento "as-built" con Mermaid: diagrama de componentes (construido en sólido / pendiente en
discontinuo) y diagrama de clases del código actual. Se actualizará ~una vez al día para reflejar el
progreso (para el profesor y la memoria final). Distinto de `architecture.md`, que es el diseño
previsto. Decidido `.md` + Mermaid (versionado, renderiza en GitHub, exportable a PDF para la
memoria) frente a PDF como fuente.

Ampliado el mismo día: añadido un diagrama de despliegue (topología hosts/tiers: clientes /
orquestador en contenedor / hipervisores con VMs) y luego reorganizado todo el documento según el
**modelo C4** (Context, Container, Deployment, Component, Code). Context y Container con la notación
C4 nativa de Mermaid (experimental); Deployment/Component/Code como flowchart/classDiagram. Nota de
terminología: "container" en C4 ≠ contenedor Docker. C4 se mencionará en la memoria como marco.

Iteración posterior: el C4 nativo de Mermaid cruzaba flechas (layout flojo); se pasan §1 Context y
§2 Container a flowchart con etiquetas C4 (`«Person»`, `«Container»`…). Se mantiene el modelo C4.

### Persistencia: repositorios TinyDB (Folder, Descriptor)

`persistence/tinydb/repositories.py`. Tras debatir genérico vs dos repos, se eligen **dos repos
independientes** (el usuario prefiere evitar genéricos/`TypeVar`): `FolderRepository` y
`DescriptorRepository`, indexados por path. Métodos: `save` (upsert), `get`, `exists`,
`subtree(prefix)` (subárbol por materialized path, frontera de segmento), `delete`. Inyección de la
instancia `TinyDB` (tests con `MemoryStorage`, sin disco). Serialización Pydantic
`model_dump(mode="json")`/`model_validate`. ABC de repositorios pospuesta (aditiva: el core llama a
los métodos por inyección; añadir el ABC luego no toca el core). `subtree` filtra en Python con un
predicado simple (se evita la imprecisión de tipos de `.test()` de TinyDB sobre campos).

### J1 — modelo Job + JobRepository

- `models.py`: `JobStatus` (PENDING/RUNNING/COMPLETED=éxito/FAILED=error), `Operation`
  (DEPLOY/UNDEPLOY/START/STOP/CREATE_FOLDER/CREATE_DESCRIPTOR, crecerá), `Job` (id uuid auto,
  operation, target, status, created_at UTC auto, finished_at, message).
- **Terminología aclarada:** "operación" = concepto genérico (máquina vs definición, DEC-027); el
  enum `Operation` es el catálogo de tipos; toda operación genera un Job (DEC-014). Se decide
  **unificar todo en Jobs** (también las de definición/árbol: crear carpeta/descriptor) — sin
  excepciones, todo auditable. Esto amplía el set de Commands de J2.
- `JobRepository` (tabla `jobs`, clave `id`, distinta de los repos de árbol): `save`, `get`,
  `find_by_target` (historial de un descriptor), `find_by_status` (filtra + ordena FIFO por
  `created_at`).
- **Decisión documentada (cola de pendientes):** el usuario propuso mantener una cola/índice de
  pendientes a mano para no barrer toda la tabla. Se descarta: sería un índice secundario manual =
  estado duplicado, y TinyDB no tiene transacciones multi-documento (DEC-030), así que la cola y la
  tabla podrían desincronizarse — nueva fuente de incoherencia justo en el punto débil de TinyDB.
  La solución correcta es un **índice de BD** sobre `status`/`created_at`, responsabilidad del motor;
  llega con MongoDB en producción y el Repository lo oculta. En la PoC se acepta el barrido (tabla
  pequeña, acotada por retención DEC-023; Sprint 1 síncrono ≈0-1 pendientes). Buen material
  evaluativo para la memoria. FIFO sale de `created_at` cuando exista el worker asíncrono (futuro).
- **Lock por descriptor (DEC-028) pospuesto** hasta tocar concurrencia/HA.

Próximo: **J2** (Commands con `validate()`/`execute()`: deploy/undeploy/start/stop + crear
carpeta/descriptor) y **J3** (motor que ejecuta un Command y gestiona el ciclo de vida del Job).

### J2 — patrón Command (deploy/undeploy/start/stop)

`jobs/commands.py`. `Command(ABC)` con `operation` (ClassVar) + `target`, `validate() -> list[str]`
(acumula errores; es también el chequeo de `plan`/dry-run) y `execute() -> str` (devuelve mensaje
para `Job.message`). Decisiones acordadas con el usuario:

- **`execute()` es seguro en solitario:** empieza llamando a `validate()` y lanza si hay errores; no
  "confía a ciegas". `validate` = recoger todo sin tocar nada (para batch fail-fast); `execute` =
  actuar y lanzar; el motor (J3) lo envolverá en try/except → Job FAILED / descriptor broken.
- **Conector ya resuelto inyectado, no el registro.** El descriptor sabe su hipervisor por *nombre*
  (`hypervisor`, serializable); el objeto conector vivo no cabe en el descriptor. La capa que crea
  el Command (el `OrchestratorService`, J3) resolverá nombre→conector vía el registro (DEC-029) y le
  pasa al Command **un** `HypervisorConnector`.
- **Por qué path + repo y no el descriptor ya resuelto:** el descriptor es dato mutable persistido
  que el Command lee/modifica/guarda; se lee **fresco** del repo (no obsoleto) y la comprobación
  "no existe" es parte de `validate`. (El conector sí se pasa resuelto: objeto de runtime estable.)
- **Nombre de la VM en `clone` = path completo** (el mock lo guarda tal cual; los conectores reales
  lo sanearán: `/`→`_`, longitud máxima, etc. — pendiente para conectores reales). La identidad real
  es `vm_id` (clave) + path en el campo metadata del hipervisor (reverse reference, DEC-005b, futuro).
- **Idempotencia (DEC-035):** deploy/undeploy comprueban el estado del descriptor (no-op si ya en
  destino). start/stop **no cambian el estado del descriptor** (solo runtime); consultan `get_status`
  para reportar el no-op (`already running/stopped (no change)`).
- Commands: `DeployCommand` (provisioned→clone→deployed+vm_id), `UndeployCommand`
  (deployed→delete→provisioned, vm_id=None), `StartCommand`/`StopCommand` (runtime via conector).
- Tests parametrizados para las ramas de error comunes; `commands.py` al 100%.

### Renombrado Operation → OperationType + modelo conceptual

- `Operation` (enum) → **`OperationType`**: es el **tipo/op-code**, no un peer de Command/Job
  (aclaración del usuario). Se mantiene el nombre **`Command`** (patrón GoF, DEC-028; evita colisión
  con `OperationType`).
- Modelo documentado en el docstring de `commands.py`: **`OperationType`** = el tipo (op-code) ·
  **`Command`** = la operación en forma **ejecutable** (lógica + dependencias, en memoria) · **`Job`**
  = la operación en forma **registrada** (estado + resultado, en disco). Comparten `(operation,
  target)`; **1:1** entre Command ejecutado y Job. No es "Job = Command serializado": cada uno añade
  su dimensión (Command el *cómo*, Job el *qué pasó*).

### Cierre de sesión 2026-05-24

Estado del núcleo hacia la **demo mínima de Sprint 1** (orden bottom-up, TDD):
- ✅ `MockConnector` (M1-M3) · ✅ modelos `Folder`/`Descriptor` · ✅ repos TinyDB
  (`Folder`/`Descriptor`/`Job`) · ✅ `Job`/`JobStatus`/`OperationType` · ✅ Commands de máquina
  (`Deploy`/`Undeploy`/`Start`/`Stop`).
- ⏭️ **Pendiente para retomar:**
  1. **J2 (cierre):** `CreateFolderCommand` + `CreateDescriptorCommand` (operaciones de definición;
     reciben el objeto a crear, no conector; aquí entra la validación contextual "el padre existe").
  2. **J3 — motor de Jobs:** ejecuta un Command, crea/persiste el Job (pending→running→
     completed/failed), captura excepciones → FAILED + descriptor broken. (Lock pospuesto, DEC-028.)
  3. **`OrchestratorService`** (facade, DEC-031): `apply`/`deploy`/`start`/`stop`/`status`/`list`;
     resuelve el conector vía el registro y construye los Commands.
  4. **Parser YAML** (`ApplyDocument`) → `apply` ejecuta un Command por item.
  5. **CLI** (cmd2) → la demo de `demo/README.md` corre.
- 84 tests en verde; toda la puerta de calidad (ruff + mypy + pytest) pasa. `docs/diagrams.md`
  reorganizado según C4 (pendiente actualizarlo cuando avance el código: faltan Jobs/Commands).

### J2 cerrado — Commands de definición (CreateFolder/CreateDescriptor)

Continuación tras el cierre: se completa J2 con los dos commands de definición (sin conector).

- **`CreateFolderCommand(folder, folders)`**: validate = la carpeta padre existe (raíz `/`
  implícita); execute = no-op si idéntica, si no `save` (created/updated).
- **`CreateDescriptorCommand(descriptor, descriptors, folders)`**: validate = la carpeta padre
  existe. **Regla de redefinición (aportada por el usuario):** un descriptor solo se sobreescribe
  si está `provisioned`; si está `deployed` y la **definición cambia** → error ("undeploy primero");
  si la definición es **idéntica** → no-op (mantiene idempotencia de `apply` incluso sobre deployed).
  Así **nunca se pisa el runtime** (`state`/`vm_id`) — elimina la necesidad de "preservar runtime"
  que se había propuesto. La definición se compara con `model_dump(exclude={"state","vm_id"})`.
- Estos commands **reciben el objeto a crear** (no un path): el objeto aún no existe en el repo, es
  la entrada (asimetría con los de máquina, que leen un descriptor existente por path).
- **Decisión de nombres:** parámetro `connector` → **`hypervisor_connector`** en los commands de
  máquina (explícito: es el conector, y de dominio). Atributo interno `self._connector` por brevedad.
- **Command Factory:** el usuario propuso una factoría que guarde las referencias comunes (repos,
  registro) para construir Commands sin globales. Conclusión: es el papel del `OrchestratorService`;
  decisión de J3, no afecta a las clases Command. Empezar con el service construyendo directamente;
  extraer una `CommandFactory` solo si esa lógica crece. **Globales descartadas** (tests, multi-
  instancia, dependencias ocultas).

Estado: **J2 completo** (6 commands: Deploy/Undeploy/Start/Stop/CreateFolder/CreateDescriptor),
`commands.py` al 100%, 97 tests en verde.

### Conceptos aclarados (sesión, para la memoria)

- **Ciclo de vida de una operación:** entrada → service construye el Command → motor crea/persiste
  el Job (PENDING) → ejecuta (RUNNING) → desenlace (COMPLETED/FAILED, descriptor `broken` si falla).
  En **v1 síncrono el Command vive en memoria** todo el rato (no se reconstruye); en el **futuro
  asíncrono** el worker **reconstruye el Command desde el Job** (`operation`+`target` = op-code +
  operandos). Una **caché/cola en memoria** de pendientes sería optimización futura (fuera del TFG;
  MongoDB con índice probablemente la hace innecesaria); la BD es la fuente de verdad (HA, crash).
- **Batch** (futuro): operación compuesta → Job padre + Jobs hijos; resultado éxito/fallo/parcial
  (best-effort, DEC-027/028).

### Próximo (retomar aquí)
1. **J3 — motor de Jobs:** ejecuta un Command, crea/persiste el Job (pending→running→completed/
   failed), captura excepciones → FAILED + descriptor `broken`. (Lock pospuesto, DEC-028.)
2. **`OrchestratorService`** (facade): construye los Commands (resuelve conector vía registro) y los
   pasa al motor; `apply`/`deploy`/`start`/`stop`/`status`/`list`.
3. **Parser YAML** (`ApplyDocument`) → `apply` = un Command por item.
4. **CLI** (cmd2) → corre la demo.

---

## 2026-05-25

### Renombrados de claridad

- Parámetros de los Commands: `descriptors`→`descriptors_repo`, `folders`→`folders_repo`
  (atributos internos se mantienen cortos, igual que `hypervisor_connector`→`self._connector`).
- `operation` → **`operation_type`** en `Command` y `Job` (es el tipo/op-code; desambigua la
  confusión instancia/tipo). El enum sigue siendo `OperationType`. Matiz: diverge de
  `status: JobStatus` (no decimos `status_type`), pero "operation" sí arrastra la ambigüedad.

### Validación: dónde rechaza (corrección, aportada por el usuario)

Se corrige el modelo previo. La **validación que rechaza vive en el `OrchestratorService`**, no en
el motor: valida la operación (o el batch entero, `plan`) y **rechaza sin crear ningún Job**
(DEC-027/028 — crear un Job ya es tocar la BD). El **motor** solo ejecuta Commands ya validados.
Semántica limpia: **fallo de validación → no hay Job**; **fallo de ejecución (runtime) → Job
`FAILED`**. `execute()` revalida por dentro solo como red de seguridad para llamadas sueltas.

### `broken` — definición precisa (DEC-032 refinado)

Definido con el usuario (registrado en `decisiones.md`, DEC-032): `broken` = una operación de ciclo
de vida (deploy/undeploy) falla **a medias** y deja **incierta** la correspondencia descriptor↔VM.
Se determina en deploy/undeploy cuando el conector falla (fuente v1) y, en el futuro, por
reconciliación. NO en rechazos de validación, ni en fallos de start/stop, ni en `unreachable`.
Salida: `force-undeploy` (futuro). **Se implementará junto con la simulación de fallos del mock
(M4)** —aplazada— porque probar `broken` requiere fallos simulados; la demo mínima es camino feliz.

### J3 — motor de Jobs (`jobs/engine.py`, TDD)

`JobEngine(jobs_repo)` con `run(command) -> Job`: crea el Job (`PENDING`) y lo **persiste antes de
ejecutar** (DEC-028), lo marca `RUNNING`, ejecuta el Command, y lo cierra `COMPLETED` (con el mensaje)
o `FAILED` (con el error, capturando `Exception`), con `finished_at`. No valida (lo hace el service),
no marca `broken` (va con M4), sin lock (pospuesto). Tests con Commands "falsos" para aislar el motor;
incluye un test que comprueba que el Job está persistido y `RUNNING` durante `execute`. 100% cobertura.

Estado: **100 tests** en verde. Núcleo: conector, modelos, repos, Job, los 6 Commands y el **motor**.
Falta: `OrchestratorService` (facade) + parser YAML + CLI para la demo.

### S1 — OrchestratorService: construcción + operaciones de máquina (TDD)

`src/univorch/service.py`. Facade único (DEC-031); CLI/web/capa-2 pasan por aquí, nadie habla con
repos/conectores/motor directamente.
- `OrchestratorService(folders_repo, descriptors_repo, jobs_repo, hypervisor_connectors)` — el
  registro renombrado a `hypervisor_connectors`; crea el `JobEngine` por dentro.
- `OperationError(Exception)` con `errors: list[str]`: el **rechazo de validación** (no crea Job);
  la interfaz lo captura y muestra los motivos.
- `deploy`/`undeploy`/`start`/`stop(path) -> Job`: resuelven descriptor + conector (rechazo si no
  existe / hipervisor desconocido), `validate()` (rechazo si errores, **sin Job**), `engine.run()`.
- Helpers `_machine_command(cls, path)` y `_run(command)`. Alias PEP 695 `type MachineCommand`.
- Service construye los Commands directamente (sin `CommandFactory`, como acordado).
- Tests de integración (`tests/integration/test_service.py`): deploy completa y marca deployed;
  ciclo completo deploy→start→stop→undeploy; rechazos (path desconocido **sin crear Job**,
  hipervisor desconocido, descriptor broken). `service.py` al 100%; 105 tests en verde.
- Pendiente del service: **S2** (`status`/`list`, lecturas sin Job) y **S3** (`apply`).

### Notas de diseño futuro — async, concurrencia y transporte (para la memoria)

Discusión extensa con el usuario; **todo fuera de v1** (síncrono). Material evaluativo:
- **Jobs ≠ asincronía.** Un Job es persistencia/auditoría de un **cambio de estado**; async es "no
  bloquear". Ejes ortogonales. En v1 todo es síncrono aunque las escrituras creen Job.
- **Dos ejes:** **cola durable** (la tabla de Jobs; persistencia; solo escrituras) vs
  **concurrencia** (pool/asyncio + timeouts; ejecución paralela). El worker usa la concurrencia para
  procesar la cola durable. **Las lecturas usan solo la concurrencia**, sin cola durable.
- **No dos agentes redundantes:** una maquinaria de concurrencia compartida; la cola durable es
  solo-escrituras; las lecturas se la saltan.
- **Transporte REST — 3 patrones:** (a) respuesta síncrona completa; (b) **streaming** (chunked /
  NDJSON / SSE: una conexión que entrega resultados a trozos, **sin polling**); (c) **aceptado +
  poll** (devuelve job id, `GET /jobs/{id}`).
  - Escrituras largas (deploy de 100) → **(c) job + poll** (durable, no cuelga la conexión).
  - Lecturas masivas (status de 100) → **(a)** síncrona+concurrencia+timeout (simple) o **(b)**
    streaming.
- **Timeout y bloqueo de cabeza de línea:** con (a), si una máquina está caída, **toda** la consulta
  espera el timeout (p.ej. 3s) antes de devolver nada — las rápidas quedan rehenes de la lenta. Con
  **streaming (b)** las rápidas llegan al instante y la caída aparece "unreachable" tras su timeout.
  → para status masivo/dashboard, **streaming** es mejor UX; (a) vale para una/pocas.
- **Auditoría de lecturas** (quién consultó qué) → **log del sistema** (syslog, DEC-023), no Jobs.
- `unreachable` **persistido** (estado) lo pone una **operación** que falla por comunicación (vía su
  Job); un read solo **reporta** un "ahora no llego" transitorio.

### Próximo
1. **S2 — `status`/`list`** en el service (lecturas, sin Job; resultados —incl. mixtos— en el valor
   de retorno).
2. **S3 — `apply`** (batch de creaciones; orden padre-primero; validación del lote).
3. **Parser YAML** (`ApplyDocument`) → `apply` = un Command por item.
4. **CLI** (cmd2) → corre la demo.

### S2 — lecturas del service: `status` y `list_tree`

`service.py`. Lecturas, **sin Job** (no cambian estado):
- `status(path) -> DescriptorStatus`: estado del descriptor (BD) + runtime (consulta el conector
  solo si `deployed`). Si no existe → `OperationError`. DTO Pydantic (REST-ready):
  `{path, state, runtime_state|None, vm_id}`.
- `list_tree(path="/") -> list[TreeEntry]`: une `subtree` de carpetas y descriptores, ordenado por
  path; **solo lee la BD** (sin conectores). DTO `TreeEntry{path, kind, state|None}` (state None en
  carpetas). Llamado `list_tree` para no pisar el builtin.
- **Arreglo:** `_in_subtree` ahora trata la raíz `/` como "contiene todo" (antes `prefix + "/"` daba
  `//` y `subtree("/")` no devolvía nada). Necesario para `list /`.
- Comentario en el docstring de `OrchestratorService` explicando `path` (identificador =
  materialized path completo) y `hypervisor_connector`/registro (DEC-029), a petición del usuario.
- 111 tests; `service.py` y `repositories.py` al 100%.

### Próximo (actualizado)
1. **S3 — `apply`** (batch de creaciones; orden padre-primero; validación del lote, best-effort).
2. **Parser YAML** (`ApplyDocument`) → `apply` = un Command por item.
3. **CLI** (cmd2) → corre la demo de `demo/README.md`.

### S3 — `apply` (batch de creaciones, best-effort)

`models.py`: **`ApplyDocument`** (Pydantic, **plano** en v1): `kind`, `version`, `folders[]`,
`descriptors[]`. Es la entrada de `apply`; el parser YAML lo producirá.

`service.py`: `apply(document) -> list[ApplyResult]`:
- **orden de dependencia:** carpetas de menos a más profundas (`path.count("/")`), luego
  descriptores → el padre se crea antes que el hijo;
- por item, `_apply_one` ejecuta vía `_run` y convierte el **rechazo en un resultado** (no relanza)
  → **best-effort**: lo válido se aplica, lo rechazado se anota; cada item es su propio Job;
- `ApplyResult{path, ok, message}` como informe.
- 115 tests; `models.py` y `service.py` al 100%.

**Decisiones de sintaxis / alcance acordadas con el usuario:**
- **YAML plano en v1** (cada item con su path completo). El **anidamiento** (descriptores dentro de
  la carpeta, paths relativos) se introduce **en Sprint 2 con la herencia en cascada** (DEC-026):
  ahí la carpeta define `hypervisor`/`base_vm`/… y los descriptores anidados los **heredan** →
  quedan minúsculos. Sin herencia (v1) anidar solo ahorraría el prefijo y añadiría complejidad al
  parser. Es la discusión de sintaxis YAML ya marcada para un sprint futuro.

**Futuros pendientes (no olvidar):**
- **"todo-o-se-rechaza"** del batch (DEC-028): validar el lote entero (consciente del documento) y
  rechazar antes de tocar nada. Requiere validación document-aware + lock. v1 es best-effort (DEC-027).
- **Job padre** del batch (agrupar los Jobs hijos bajo uno; resultado éxito/fallo/parcial).
- **Anidamiento YAML + herencia** (Sprint 2).

### Próximo (tras S3)
1. **Parser YAML** (`ruamel.yaml`) → construye `ApplyDocument` desde el fichero; `apply` lo consume.
2. **CLI** (cmd2): `apply`/`deploy`/`undeploy`/`start`/`stop`/`status`/`list` + `cd`/`pwd` →
   corre la demo de `demo/README.md`. Es la última pieza para la demo mínima.

### Validación del documento — `extra="forbid"` (acordado)

Los modelos parseados del YAML (`Folder`, `Descriptor`, `ApplyDocument`) usan
`ConfigDict(extra="forbid")`: un campo desconocido (errata como `descripton`) → `ValidationError`,
en vez de descartarse en silencio. Mejor diagnóstico para ficheros escritos a mano. Es seguro para
los repos (el `model_validate` de TinyDB recibe exactamente los campos de `model_dump`).

### Notas de diseño futuro — hipervisores y herencia (Sprint 2)

Discusión con el usuario (todo para Sprint 2, con la herencia en cascada):
- **`hypervisor` obligatorio es *relativo*:** en v1 (autocontenido) el descriptor lo requiere; en
  Sprint 2 podrá **heredarse** → el campo pasará a **opcional** en el modelo y la comprobación "debe
  tener hipervisor" se mueve a **después de resolver la herencia** (sobre la definición efectiva).
  Encaja con la separación validación sintáctica (modelo) vs contextual (resolver/service),
  DEC-026/027.
- **Tres usos distintos del "hipervisor" en los ficheros de definición:**
  1. **Definir** un hipervisor: nombre → tipo, dirección, credenciales (el *recurso*; DEC-010, la
     raíz define hipervisores). Hoy es el registro cableado al arrancar.
  2. **Aliasar / definir basado en otro:** nombre nuevo derivado de uno existente — misma idea que
     los alias de datastores (DEC-017), llevada a hipervisores. El más avanzado; quizá post-Sprint 2.
  3. **Usar:** el descriptor (o heredado) referencia un nombre de hipervisor ya definido. Es lo que
     hace `descriptor.hypervisor` hoy, pero sin el paso de "definición" (el nombre apuntará a (1)).
  - Separación: **definir (recurso) ≠ aliasar (derivado) ≠ usar (referencia)**. Enlaza DEC-010,
    DEC-017, DEC-026, DEC-011 (visibilidad de hipervisores por rol).

### C1 — CLI base con cmd2 (`interfaces/cli/app.py`)

Primera pieza de la última interfaz. `cmd2.Cmd` con métodos `do_*` (sirven para REPL y bash a la vez):
- **`build_service(db)`** = raíz de composición: TinyDB → repos + `{"mock": with_demo_templates()}` →
  `OrchestratorService`. En Sprint 1 la CLI lo monta **en su propio proceso** (el mock en memoria se
  reinicia entre procesos; la demo es una sesión REPL, así funciona; daemon real en Sprint 2).
- **Navegación:** `_cwd` (carpeta actual), `do_cd`/`do_pwd`, prompt `univorch <cwd}>`, y `_resolve`
  (path relativo → absoluto contra el CWD).
- **`do_list`** (lectura): `service.list_tree(resolve(arg))` formateado.
- **`main()`:** lee `UNIVORCH_DB` (o default), construye el shell; si hay args → un comando (bash),
  si no → `cmdloop()` (REPL). No se testea unitariamente (punto de entrada interactivo).
- Tests (`tests/unit/test_cli.py`): `_resolve` (absoluto/relativo/vacío), `cd`/`pwd` (incl.
  encadenado y a raíz), `list`. Captura de salida con `StringIO` en `shell.stdout`. 129 tests; app.py
  al 85% (solo `main()` sin cubrir).
- Decisión de palabras: en el chat se usan términos españoles ("salvedad", "ensamblaje"…) en vez de
  jerga inglesa cuando existe equivalente (a petición del usuario).

### C2 — CLI: `status` y comandos de máquina (Rich vía cmd2 3.x)

Segunda pieza. Operaciones que cambian estado + lectura de estado:
- **`do_deploy`/`do_undeploy`/`do_start`/`do_stop`** delegan en un helper `_machine(operation, arg)`:
  resuelve el path, llama a la operación del service, captura `OperationError` (rechazo de
  validación → `perror`, en rojo a stderr), y si va bien imprime `job.message` en verde/rojo según
  `COMPLETED`/`FAILED`. La interfaz no decide nada: solo traduce y colorea (DEC-031).
- **`do_status`**: pinta el estado del descriptor con color por estado (`_STATE_STYLE`:
  provisioned=dim, deployed=verde, broken=rojo, unreachable=amarillo) y el runtime si está desplegado.
- **Colores con cmd2 3.x:** `poutput(..., style=...)` y `markup=True` (cmd2 3.x integra Rich y
  detecta TTY: color en terminal, texto plano en tests/redirección). Se descartó montar una `Console`
  de Rich aparte. El prompt coloreado se aplaza (API de cmd2 3.x).
- Tests: deploy→status, start cambia runtime, ciclo completo (deploy/start/stop/undeploy),
  provisioned sin runtime, rechazos (path desconocido no muestra éxito).

### C3 — CLI: comando `apply` (cierra la demo mínima)

Última pieza de la CLI y del núcleo de Sprint 1:
- **`do_apply(file)`**: lee el fichero con `load_apply_file` (parser ruamel + Pydantic), captura
  `OSError`/`YAMLError`/`ValidationError` → `perror` sin tocar nada; si parsea, recorre
  `service.apply(document)` e imprime el informe `ApplyResult` por item (verde si `ok`, rojo si no).
  Best-effort coherente con el service (DEC-027): lo válido se aplica, lo rechazado se anota.
- **Salvedad de mypy:** `YAMLError` se importa de `ruamel.yaml.error` (no del paquete raíz; los stubs
  no lo exponen arriba) aunque en runtime ambos funcionen.
- Tests: aplica un YAML real (con `tmp_path`) y comprueba que el árbol se crea; fichero inexistente →
  error a stderr, no crea nada.
- **Estado:** 137 tests en verde; toda la puerta de calidad (ruff + mypy strict + pytest) pasa.
  `app.py` al 92% (solo `main()` sin cubrir, punto de entrada). **La demo de `demo/README.md` corre
  de punta a punta** con `apply`/`list`/`deploy`/`start`/`status`/`stop`/`undeploy` + `cd`/`pwd`.

### Sprint 1 — núcleo mínimo completo

Cerrado el camino bottom-up con TDD: conector mock → modelos → repos TinyDB → Job/Command/motor →
`OrchestratorService` (facade) → parser YAML → CLI. La demo del profesor (sin hipervisor real,
mock en memoria) es ejecutable. Pendientes diferidos a Sprint 2+: herencia en cascada (Resolver),
web GUI (NiceGUI), RBAC, conectores reales, capa docente, `broken` + simulación de fallos del mock
(M4), todo-o-se-rechaza del batch + Job padre, prompt coloreado, daemon + REST.

### Próximo
- Probar la demo end-to-end (REPL interactivo + modo bash) y guiar al usuario.

---

## 2026-05-26

### Prueba del REPL y mejoras de usabilidad de la CLI (Bloques A y B)

El usuario prueba el REPL interactivo (`uv run univorch`) y detecta varias cosas a pulir. Antes,
aclaraciones de entorno surgidas de la prueba:
- **`uv run` vs `univorch` a secas:** `univorch` vive en `.venv/bin`; basta con el venv activado
  (`source .venv/bin/activate`) o `uv run univorch` (robusto: sincroniza el venv y ejecuta sin
  activarlo). `uv` es herramienta de **desarrollo**; en producción se entra con `./univorch.sh cli`
  (docker exec), sin uv. La activación del venv es mecanismo estándar de Python, no de uv: un script
  con `./` corre en un subshell y no modifica el shell padre → la activación exige `source`.
- **`univorch` vs `univorch.sh`:** el primero es el comando de la app (entry point); el segundo es el
  wrapper bash de `docker compose` (producción). `uv run univorch.sh` no tiene sentido.

**Bloque A — navegación correcta (commit `550e286`)**
- `_resolve` reescrito con `posixpath`: soporta `..`, `.` y combinaciones (`cd ../otro`); `normpath`
  no deja subir por encima de la raíz (`..` en `/` se queda en `/`). Beneficia a todos los comandos.
- `service.folder_exists(path)`: lectura nueva (la raíz `/` es implícita, sin registro). La CLI no
  toca el repo (DEC-031).
- `do_cd` valida que el destino sea **carpeta existente** (error en rojo si no; tampoco entra en un
  descriptor — como `cd` a un fichero en Unix). **`cd` sin argumento = no-op** (no hay "home"; para
  ver dónde estás está `pwd`).

**Bloque B — listados estilo Linux (commit de esta sesión)**
- **`list`/`ls` muestran un solo nivel** (hijos directos), como `ls`. En el service,
  `list_tree(path, recursive=False)` por defecto; devuelve los **descendientes** de `path` (no
  `path` mismo). `recursive=True` da el subárbol completo. Cambió el default → tests del service
  actualizados.
- **`ls`** alias de `list`. **`tree [path]`** nuevo: subárbol completo indentado (default = pwd).
- **`list`/`tree` dan error** si la carpeta no existe (coherente con `cd`).
- **Glifos de estado del descriptor (estilo B, geométrico, ancho fijo):** `□` provisioned (dim),
  `■` deployed (verde), `✗` broken (rojo), `▲` unreachable (amarillo). Carpetas estilo `ls -F`:
  `nombre/` en azul, **sin glifo**; fila `../` al inicio salvo en la raíz. Nombres en *basename*.
- **Decisión de diseño (dos ejes, DEC-022/032):** `list` solo muestra el **eje del descriptor**
  (BD, barato). `running`/`stopped` es el **eje runtime** (hipervisor) y consultarlo por cada VM es
  la "lectura masiva cara" (bloqueo de cabeza de línea / streaming, aplazado). Se queda en `status`;
  futuro `list --live`. Por eso el triángulo queda libre para `unreachable` sin ambigüedad con play.
- **Completado de Tab en `apply`** sobre ficheros del sistema (`complete_apply` → `path_complete`
  de cmd2), como hace el comando `shell`/`!`.
- **`demo/README.md`** actualizado: sección 2 usa `tree /` (antes `list /`) y explica los glifos.
- 152 tests en verde; `app.py` 95% (solo `main()`), `service.py` 100%.

**Elementos de ejemplo del mock:** `with_demo_templates()` precarga dos plantillas (`linux-base`,
`windows-base`) como origen de `clone`; el árbol empieza vacío (se siembra con `apply demo/setup.yml`).

### Bloque C — ayuda estructurada con argparse (cmd2)

El usuario observa que `help shell` (interno de cmd2) tiene ayuda rica y coloreada (Usage /
Positional Arguments / Options) mientras la nuestra era un docstring de una línea. Se adopta el
**Nivel 2**: cada comando se declara con **`@cmd2.with_argparser(parser)`** (cmd2 3.x,
`Cmd2ArgumentParser`). Beneficios: ayuda autogenerada y coloreada como la interna, validación de
argumentos, y un punto donde enganchar el completado de argumentos en el futuro.

- Factoría `_path_arg_parser(description, required)` para los comandos de un solo `path`
  (obligatorio en deploy/undeploy/start/stop/status; opcional en cd/list/ls/tree). `do_pwd` sin
  argumentos; `apply` con `file` + `completer=cmd2.Cmd.path_complete` (sustituye al antiguo
  `complete_apply`, ahora declarativo en el parser).
- Las firmas `do_*` pasan de `arg: str` a `args: argparse.Namespace` (leen `args.path`/`args.file`).
  Los tests, que conducen por cadenas (`onecmd_plus_hooks`), no cambian salvo quitar el test de
  `complete_apply`.
- **Leyenda de glifos en `help list`/`help ls`** (constante `_LIST_DESC` compartida): resuelve la
  petición del usuario sin un comando `legend` aparte. La lógica de `list` se extrae a `_list` para
  que `list` y `ls` la compartan (no se puede delegar entre dos `do_*` decorados).
- 151 tests en verde (uno menos: se retiró el de completado); `app.py` 95% (solo `main()`),
  `service.py` 100%.

### Terminología externa: "VM" en la CLI, "descriptor" solo en el código

El usuario observa que `descriptor` es jerga interna; el personal que use la CLI piensa en VMs.
Regla acordada (encaja con DEC-009: vocabulario por capa):
- **Externo** (ayuda CLI, mensajes de error de cara al usuario, futura web): **`VM`** a secas.
- **Interno** (clases, atributos, comentarios de código, `claude/`, `docs/`, memoria del TFG):
  **`descriptor`** — modelo del dominio, analogía pedagógica del SO (DEC-005).
- **Excepción** futura: comandos de creación/destrucción de la *definición* (cuando existan;
  hoy van por `apply`) podrían usar "VM descriptor" o "definition" porque ahí el matiz importa.

**Aplicado:**
- Textos de ayuda de `deploy`/`undeploy`/`start`/`stop`/`status`/`apply` reescritos a "VM"
  (incluyen "the definition stays" en `undeploy` para preservar el matiz). El docstring
  pedagógico del módulo `commands.py` se queda con `descriptor`.
- Mensajes user-facing del service (`OperationError`) y de `validate()` de los Commands:
  `"descriptor not found"` → `"VM not found"`; `"broken descriptor"` → `"broken VM"`;
  `"non-provisioned descriptor"` → `"non-provisioned VM"`; `"start/stop a descriptor that is not
  deployed"` → `"... a VM that is not deployed"`.
- Tests actualizados (2 aserciones en `test_commands.py`).

### Color de `deployed` retirado: verde sugería "running" (runtime)

Observación del usuario: el verde en `deployed` se lee como "encendido/corriendo", y eso es
**runtime** — el eje que decidimos NO mostrar en `list` (sería la lectura masiva cara al hipervisor,
DEC-032; el runtime sigue en `status`). El verde, aunque coherente con "estado bueno", crea
expectativa errónea. Se cambia a **`default`** (color del terminal): el glifo `■` ya indica
"existe"; el color queda para los estados excepcionales (rojo `broken`, amarillo `unreachable`).
Tabla actualizada: `□` provisioned (dim) · `■` deployed (default) · `✗` broken (rojo) ·
`▲` unreachable (amarillo).

### Vista detallada de `list` (aplazada a futuro sprint)

Discusión: el usuario propone un flag (sugirió `-a`) para `ls`/`list` que muestre información
extendida por cada VM. Salvedad: en Linux `-a` es "mostrar ocultos"; el listado largo es **`-l`**.
Cuando se retome, usar `-l` por coherencia con Linux. **Se queda como está**; se documenta para
retomar más adelante.

Campos contemplados, por fuente:
- **Del descriptor** (gratis, ya en el modelo): description, hypervisor, base_vm, cpu/memory/disk,
  vm_id, state.
- **Derivable de Jobs** (pequeño esfuerzo, lookup en `JobRepository.find_by_target`):
  created_at, deployed_at, last_action (operación + estado + cuándo — clave para diagnosticar
  `broken`/`failed`).
- **Del hipervisor** (runtime, caro): IPs, uso CPU/mem/disco, uptime → irá con `list --live`
  futuro (streaming, no en `-l`).
- **Sprints futuros** (la información no existe aún): quién creó el descriptor, quién desplegó
  la VM, número de despliegues (RBAC + auditoría); IPs asignadas (DEC-025); snapshots; definición
  efectiva tras herencia + procedencia por campo (Sprint 2 Resolver).

Diseño propuesto: tabla Rich vía `cmd2.poutput` (alinea columnas; en tests sale plano).
Service: `descriptor_details(path)` o `list_tree_verbose(path)` que joinea con Jobs.

### Pendientes anotados (futuro)
- Completado de Tab para **paths del árbol** en `cd`/`deploy`/`status`/… (navegar el árbol con Tab).
  Pieza propia, más trabajo (consulta el service). El argparse ya deja el gancho (`completer=`).
  **Fuera del TFG** (decisión del usuario).
- **`ls -l` / listado largo** (ver bloque de arriba): aplazado a futuro sprint con campos del
  descriptor + derivados de Jobs + futuros (autor de creación/despliegue, contador, IPs…).
- `list --live` (runtime por VM, con streaming).
- Descartado: `univorch --demo` (no necesario) y comando `legend` (la leyenda va en `help list`).

### Revisión de documentación (cierre de sesión Sprint 1)

Repaso completo de `docs/` y `claude/` para que el estado documental refleje el código real
tras el cierre de Sprint 1:
- `claude/proyecto.md`: estado actualizado (Fase 6 — Sprint 1 cerrado) y stack tecnológico
  enumerado (estaba "por definir" desde el inicio).
- `claude/desarrollo.md`: tabla de fases (5 ✅, 6 🔄); se retira el bloque "Fase 5 — Pendiente
  de crear" (todo construido); estructura del código marcada con `*` lo aún no construido
  (Resolver, web, conectores reales); checklist de Sprint 1 con `[x]`; flujo de demo actualizado
  con prompt `univorch />`, `tree /` (en lugar del antiguo `list /` recursivo) y glifos; tabla
  de comandos CLI con `ls` y `tree` añadidos.
- `docs/diagrams.md`: actualizado al 2026-05-26. Componentes (sección 4) con CLI, Service,
  Jobs, Parser, Repos+DB en verde sólido; Web y conectores reales en discontinuo. Código
  (sección 5) dividido en **5.1 dominio + conectores** (añade `Job`, `JobStatus`,
  `OperationType`, `ApplyDocument`) y **5.2 motor, persistencia, service, CLI** (añade
  `Command` + 6 subclases, `JobEngine`, los tres repositorios, `OrchestratorService` con sus
  DTOs `DescriptorStatus`/`TreeEntry`/`ApplyResult`/`OperationError`, y `UnivOrchShell` con
  sus `do_*`).
- `docs/{architecture,requirements,technologies,environment,vision}.md`: revisados, sin
  cambios — los términos `apply` y `descriptor` son **lenguaje de diseño** (no UI), siguen
  siendo válidos. Cuando se renombre `apply → load` (plan aprobado, pendiente de implementar)
  se actualizarán esos documentos en bloque.
- `docs/plan.md`: ya estaba al día (sin cambios).

### Rediseño del YAML: relativo + envoltura + items mixtos con `/` final

Cambio de modelo del documento YAML, profundo pero contenido. Resumen de las decisiones que se
tomaron en el diálogo de hoy y se implementaron:

- **Paths del YAML, estrictamente relativos.** El fichero ya no lleva paths absolutos; describe
  una **estructura reutilizable** que se engancha en la carpeta destino al cargarla. Encaja con
  DEC-027 (export/import portable) y prepara la herencia en cascada del Sprint 2 (DEC-026).
- **Sintaxis "tipo `ls`":** envoltura fina `kind: definition` / `version: "1"` arriba; tras ella,
  los items cuelgan **directamente** del nivel raíz del documento, **mezclados**: una clave
  acabada en `/` es una carpeta; sin `/` es una VM. Mismo patrón a cualquier profundidad. Sin
  secciones `folders:` / `descriptors:`.
- **Regla "no se tocan las propiedades del destino":** la carpeta destino preexiste con sus
  propias propiedades; el YAML solo coloca **cosas dentro** de ella. Por eso el nivel raíz del
  documento **no** admite `description` ni reservadas de carpeta. RBAC-natural: tener permiso
  para colocar dentro ≠ tener permiso para modificar. Para Sprint 2: los recursos de sistema
  (hipervisores, plantillas globales) viven en una carpeta administrativa, no en `/` (que es
  implícita).
- **`apply` → `load(file, [destination])`:** acción explícita (cargar en una carpeta), por
  simetría futura con `save` (extraer carpeta → fichero, aplazado a sprint posterior). Destino
  opcional con default = pwd. Comprueba que la carpeta destino existe; si no, error.
- **Comentarios — Modelo A:** el YAML es el "ingrediente"; la BD es la verdad operativa. Al
  hacer `load` los comentarios se pierden. `description:` es el campo estructurado para texto
  que debe persistir y reaparecer en un `save` futuro. Modelo B/C (preservar comentarios via
  ruamel round-trip) descartado: en cuanto CLI/web tocan la BD, el fichero deja de ser la
  fuente y no compensa la complejidad.
- **JSON Schema escrito a mano** en `docs/schema/definition.schema.json` — Pydantic no
  auto-genera la forma user-facing (`patternProperties` para `^[A-Za-z0-9_-]+/$` carpeta vs
  `^[A-Za-z0-9_-]+$` descriptor) porque el `model_validator(mode="before")` traduce entre forma
  externa e interna sin que JSON Schema lo vea. Se mantiene a mano (~75 líneas) con un **test
  anti-drift** (`tests/integration/test_schema.py`) que valida con Pydantic Y con `jsonschema`
  el mismo corpus de YAMLs (válidos e inválidos). Si los dos no coinciden, CI rojo.
- **Cómo se usa el schema:** **NO** en runtime. Solo en (a) editor del usuario (extensión YAML
  de Red Hat lee la directiva `# yaml-language-server:` y da autocompletado) y (b) el test
  anti-drift. Pydantic sigue siendo el único validador en `load`.

**Cambios de código:**
- `models.py`: nuevos `DescriptorDef` / `FolderDef` (autorreferencial) / `DefinitionDocument`,
  con `model_validator(mode="before")` que parte items mixtos por sufijo `/`. Pass-through si
  el input ya viene normalizado (Python: `DefinitionDocument(folders={...})`). Validación de
  nombres con el patrón de segmento existente. Las entidades persistidas (`Folder`,
  `Descriptor`) **sin cambios** — siguen llevando path absoluto y son la forma de storage.
- `parser.py`: `load_apply_document` → `parse_definition`; `load_apply_file` →
  `parse_definition_file`. Renombre para no chocar con la acción `load`.
- `service.py`: `apply(document)` → `load(document, destination="/")`. Walker recursivo
  `_load_folder` que materializa folders padre-primero y luego sus descendientes. Valida la
  existencia del destino antes de tocar nada. `ApplyResult` → `LoadResult`. `_apply_one` →
  `_load_one`.
- `commands.py`: bug arreglado en `CreateDescriptorCommand.validate` — no rechaza descriptores
  en la raíz (parent vacío = raíz implícita, mismo patrón que `CreateFolderCommand`).
- `interfaces/cli/app.py`: `do_apply` → `do_load`; parser `file` (Tab-complete) + `destination`
  posicional opcional (default = pwd). Captura `OperationError` del service (destino no
  existe) además de los errores de parseo.
- `demo/setup.yml`: reescrito en el nuevo formato (relativo, mixto, con directiva
  `# yaml-language-server` apuntando a `../docs/schema/definition.schema.json`).
- `demo/README.md`: actualizado para `load` (sección 1) y la línea de bash mode.

**Infra:**
- `docs/schema/definition.schema.json` — schema 2020-12 con `patternProperties` + negative
  lookahead para excluir `kind`/`version` (top) y `description` (dentro de carpeta) del match
  del descriptor.
- `pyproject.toml`: `jsonschema>=4.20` añadido a `[project.optional-dependencies].dev`.
- `.devcontainer/devcontainer.json`: extensión `redhat.vscode-yaml` (lee la directiva
  `# yaml-language-server:` para autocompletar/validar en VSCode).
- `tests/integration/test_schema.py`: test anti-drift Pydantic ↔ JSON Schema.

**Estado:** 160 tests en verde; service y modelos 100% / 84%; ruff y mypy limpios.

### Pendientes anotados para más adelante (Sprint 2+)

- **`save`**: comando inverso `save <dest_file> [origin]` que extrae el subárbol al destino y
  lo serializa en formato relativo. Aplazado.
- **Renombrar `apply` en `docs/architecture.md` y `docs/requirements.md`**: ahora son
  inconsistentes con el código. Se actualiza cuando estabilice (Sprint 2).
- **Doc del producto** (`docs/user-guide.md` o similar): introducir la regla "root es implícita
  y no admite propiedades; los recursos del sistema viven en una carpeta administrativa". El
  diario lo guarda; falta llevarlo a la doc de usuario cuando se cree.
- **Palabras reservadas dentro de FolderDef (Sprint 2):** `import`, `define hypervisors`,
  `define machine templates`, `based on`. Forman parte del modelo de herencia/derivación
  (DEC-010/012/017/026). El esquema actual ya las rechazaría (`extra="forbid"`); habrá que
  añadirlas como reservadas en el `_split_items` cuando toque.

### Cierre de la pieza A — glosario + docs al día

Tras la conversación sobre vocabulario (template vs base VM, descriptor vs VM, folder vs
directory…) se cierra el housekeeping documental del rediseño del YAML:

- **`docs/glossary.md`** (nuevo). Glosario en inglés (norma de `docs/`), agrupado por familia:
  árbol, hipervisor, definiciones + resolver, estado (dos ejes), operaciones (Operation /
  OperationType / Command / Job), acciones (load · save futuro · apply deprecado),
  permisos (RBAC), y al final **la regla de las dos capas de vocabulario** ("VM" en lo
  externo / "descriptor" en lo interno). Aclara también la distinción importante entre
  **base VM** (la modelo en el hipervisor, `base_vm` en código) y **template** (alias del
  orquestador, Sprint 2, definido en `define machine templates:`); eran ambiguas y el usuario
  pidió fijarlas. Cada entrada referencia la decisión técnica respaldatoria (DEC-XXX).
- **`docs/architecture.md` actualizado.** Sección 5.1 ahora se llama "The load/plan flow" y
  describe `load(document, destination)` (precondición de destino existente; el documento no
  toca propiedades del destino). Se añade una **nota de naming** explicando que la decisión
  histórica DEC-027 conserva su nombre original ("Declarative apply/plan flow") porque el
  diario no se reescribe. Las referencias vivas a `apply` pasan a `load` (sección 5.3 de
  interfaces de edición; sección de GitOps futuro; el "load-on-demand" del bucle de
  reconciliación; el "apply descriptors" en la capa docente, pasado a "create descriptors"
  por exactitud). Enlace al glosario al inicio.
- **`docs/requirements.md`.** Solo una mención de "apply" como **verbo inglés natural**
  ("Changes apply on the next recreation"), no como comando — se deja. Enlace al glosario
  al inicio.
- Sin cambios en `decisiones.md` (entradas históricas), `diario.md` (esta entrada nueva
  excepto), `proyecto.md`/`desarrollo.md` (ya al día), ni código (la pieza es 100% doc).

160 tests siguen verde tras los cambios. Memoria `spanish-chat-style.md` afinada con la
convención de jerga ("usar palabra española + (English) entre comillas en la primera
mención"); memoria nueva `code-walkthrough-style.md` con la regla de explicar siempre los
cambios de código en prosa antes de que el usuario los lea.

### Próximo: Sprint 2 — Resolver y herencia en cascada

Scope refinado:
- **Resolver** puro `(árbol, path) → definición efectiva` (modo normal solamente — el modo
  anotado se aplaza).
- **Palabras reservadas YAML en FolderDef:** `import`, `define hypervisors`,
  `define machine templates`, `based on`.
- `hypervisor` y `base_vm` **opcionales** en `DescriptorDef` (la comprobación se traslada al
  service tras resolver).
- Comando CLI nuevo **`inspect <path>`** (definición efectiva en texto).
- Tests con Hypothesis (Resolver es función pura, caso ideal).

Sprint 3 reducido a **contenedor descargable + Daemon REST + CLI cliente HTTP** (la web GUI
y RBAC pasan a sprints posteriores). Sprint 4 = web GUI básica de **solo lectura**. Sprint
5+ = web con acciones, RBAC, `rm`, `save`, conectores reales, capa docente.

### Sprint 2 — diseño del vocabulario YAML (largo diálogo, decisiones cerradas)

Antes de tocar código, conversación larga sobre la sintaxis de la herencia. Conclusiones que se
codifican en el modelo:

- **`define X:` / `use X:` / `based on:`** como tríada explícita. `define` declara un recurso
  (vive aquí desde ahora). `use` referencia uno ya declarado. `based on` deriva un recurso de
  otro (Pieza 4). Mejor que `templates:` o `hypervisors:` simples — el verbo da significado
  semántico.
- **`define machine templates`** (no `templates`) y **`define hypervisors`** como nombres con
  espacios. El usuario prefiere la forma verbosa por legibilidad. Se mapean a campos Python
  vía `Field(alias=...)` de Pydantic.
- **`use hypervisor:` (no `hypervisor:`)** en descriptores y plantillas para consistencia con
  `use template:`. Cambio de vocabulario respecto a Sprint 1.
- **Imports explícitos**, no implícitos: cada carpeta declara qué importa de su padre con
  `import: ALL` o `import: [name, prefix*]`. Razón (aportada por el usuario): un admin que
  define 100 plantillas no debe exponerlas todas; el profesor solo ve lo que importa.
- **Cierre del cierre (closure-like) de las plantillas:** una plantilla resuelve sus
  referencias internas (p.ej. `use hypervisor: mock`) **desde donde fue definida**, no desde
  donde fue importada. Beneficio: el profesor puede importar `linux-vm` sin tener que
  importar también el hipervisor; la plantilla resuelve su entorno léxico.
- **Imports transitivos**: si importas una plantilla, NO necesitas importar también las cosas
  que esa plantilla usa internamente. Las referencias internas resuelven contra el sitio donde
  el recurso fue definido (closure).
- **Resolución al vuelo, no al cargar:** el Resolver opera al acceder al descriptor (deploy,
  status, inspect), no al cargar el YAML. La BD guarda **solo la definición local**; lo
  resuelto se computa cada vez. Beneficio: si cambia una plantilla, todos los descriptores
  que la usan heredan el cambio automáticamente en el próximo deploy. La BD es la única
  fuente de verdad; lo derivado es deterministicamente reconstruible.
- **Distinción "hipervisor (recurso)" vs "tipo de conector":** el nombre que el usuario
  declara (`mock`, `hyperv1`, `hyperv-aulario`) vs el tipo de conector que lo gestiona
  (`type: mock`, `type: vmware`). Coinciden por casualidad para "mock" en el demo, pero son
  cosas distintas conceptualmente.
- **Listas de colecciones — no aplica:** nuestro modelo no tiene listas de colecciones.
  Listas son de strings (imports, managers futuro). Colecciones son dicts con nombre. La
  fusión recursiva por clave queda bien definida (DEC-026); `ip_pool` será una excepción
  (mapa que se reemplaza entero).
- **Root sin recursos:** decisión final. Root es implícita, sin registro `Folder` en BD. No
  admite `description`, `import`, ni `define X:`. Los recursos viven dentro de carpetas
  concretas que el admin crea (típicamente `/lab/`, `/admin/` o similar). El demo de Pieza 1
  pone hipervisor y plantilla en `/lab/` y `/lab/networks/` los importa.
- **`load` solo coloca hijos, nunca modifica el destino**. Las propiedades de identidad
  (description, import) y los recursos declarados (define X:) viven en una carpeta cuando se
  crea por primera vez; loads posteriores en una carpeta ya existente añaden hijos pero no
  modifican esos campos. Documentos con `define X:` o `import:` al nivel raíz se **rechazan
  con error explícito**.
- **Cuándo se resuelven los `use X:`:** todas las resoluciones (cascada + referencias) las
  hace el Resolver en una sola pasada al acceder al descriptor. El Command recibe la VM
  con valores concretos, ningún `use X:` pendiente.
- **`inspect <path>` tendrá tres modos** (cuando llegue, varias piezas después de Pieza 1):
  `--local` (lo escrito en el nodo), `--expanded` (con imports/herencia aplicada pero sin
  seguir referencias) y `--resolved` (por defecto, todo resuelto). Funciona tanto sobre
  carpetas como sobre descriptores. Modo "anotado" (procedencia por campo) aplazado.
- **Referencias colgadas tras un cambio posterior:** pendiente futuro. Pieza 1 valida
  *internamente* el documento que se carga; "rechazar cambios que orfanen descriptores
  existentes" es una validación global aplazada.
- **Naming en código:** `VMTemplateDef` (no `TemplateDef` — ambiguo) y `HypervisorDef` para
  el YAML. La regla de las dos capas (def vs persistido) se mantiene: ambas clases sirven
  para los dos contextos en este caso porque la forma es idéntica.

### Pieza 1.A — Modelos + YAML para la herencia (sin Resolver todavía)

Implementación de la primera sub-pieza de Sprint 2. **El YAML aprende el vocabulario nuevo;
nada se resuelve aún.**

**El qué:**
- Dos clases nuevas: `HypervisorDef` (con `connector_type: str` alias `type`) y `VMTemplateDef`
  (con `hypervisor` alias `use hypervisor`, `base_vm` y specs opcionales).
- `FolderDef` recibe tres campos nuevos con aliases: `imports` alias `import`,
  `hypervisors` alias `define hypervisors`, `vm_templates` alias `define machine templates`.
- `DescriptorDef` recibe `template` alias `use template`; sus `hypervisor` (ahora alias
  `use hypervisor`) y `base_vm` pasan a opcionales.
- `Folder` y `Descriptor` persistidos espejean los mismos campos (sin aliases — TinyDB usa
  nombres Python).
- `DefinitionDocument` **rechaza recursos al nivel raíz** con mensaje claro (`define X:` o
  `import:` arriba → error indicando "metédlos dentro de una carpeta").
- `_split_items` aprende las reservadas nuevas en FolderDef.
- `_normalize_imports` validator: `import: ALL` (string) y `import: linux-vm` (single) se
  normalizan a lista (`["*"]` o `["linux-vm"]`).
- Aliases con `populate_by_name=True`: Pydantic acepta tanto el alias (forma YAML) como el
  nombre Python (forma de construcción en código y de carga desde TinyDB).
- **Validaciones transitorias** en `service._machine_command` y `DeployCommand.execute`: si
  un descriptor llega sin `hypervisor`/`base_vm` (porque dependía de una plantilla y el
  Resolver no está cableado todavía), se devuelve `OperationError` con mensaje explícito
  (`"VM has no effective hypervisor: ... (resolver not yet wired)"`). Estas líneas
  desaparecen al aterrizar Pieza 1.C.

**Coste y consecuencias:**
- 168 tests verdes; ruff y mypy limpios.
- JSON Schema (`docs/schema/definition.schema.json`) actualizado al vocabulario nuevo
  (`$defs/Hypervisor`, `$defs/VMTemplate`, `Folder` con las nuevas propiedades, `Descriptor`
  con `use hypervisor:`/`use template:` y sin `required`).
- Demo (`demo/setup.yml`) reescrito en el formato nuevo: hipervisor + plantilla en `/lab/`
  y los tres estudiantes en `/lab/networks/` con `use template: linux-vm`.
- Test antiguo `test_rejects_descriptor_missing_hypervisor` queda obsoleto y se sustituye por
  `test_rejects_hypervisor_definition_missing_type` (el `type` del hipervisor sigue siendo
  obligatorio). Igual con sus equivalentes en `test_models.py` y `test_schema.py`.
- Siete tests positivos nuevos en `test_parser.py` para el vocabulario: define hypervisors,
  define machine templates, import normalization (ALL y lista), descriptor solo-con-template,
  rechazo del top-level.

**Estado real:** un descriptor que dependa de una plantilla (`use template:` sin `use hypervisor:`
inline) se persiste correctamente pero **no se puede desplegar todavía**. Deploy devuelve
`OperationError` claro. Los descriptores fully-inline (con `use hypervisor:` y `base_vm:`)
siguen funcionando. Pieza 1.B trae el Resolver puro; Pieza 1.C lo cablea al service y
desbloquea deploy.

### Pieza 1.B — Resolver puro (cascade inheritance)

Módulo nuevo `src/univorch/resolver.py`, ~70 líneas, sin estado y sin clases. Cuatro funciones:

- **`resolve_descriptor(descriptor, folders_repo) -> Descriptor`** (pública). Si el descriptor
  no tiene `template`, devuelve el input sin cambios. Si tiene, busca la plantilla con
  `_find_template` y fusiona campos con `_merge_template`. Levanta `ValueError` con mensaje
  claro si la plantilla no es accesible.
- **`_find_template(name, start, folders_repo)`** — el walker. Sube ancestros desde `start`
  (la carpeta del descriptor). En cada nivel: ¿la carpeta define la plantilla? Sí → devuelve.
  No → ¿el `import:` de **esta** carpeta deja pasar el nombre desde el padre? Sí → sigue
  subiendo. No → corta y devuelve None. Llegar a la raíz devuelve None (root sin recursos,
  decisión cerrada en Pieza 1.A).
- **`_merge_template(descriptor, template)`** — la regla "escalar local gana, hueco se rellena"
  (DEC-026). Recorre los seis campos comunes (`description`, `hypervisor`, `base_vm`, `cpu`,
  `memory_mb`, `disk_gb`); si el descriptor lo tiene non-None, no toca; si es None, lo coge
  de la plantilla. Usa `model_copy(update=...)` de Pydantic — función pura, no muta el
  descriptor original. El campo `template` se preserva en el resuelto (huella de origen,
  útil para `inspect`/auditoría).
- **`_import_allows(imports, name)`** — wildcard matching con `fnmatch.fnmatchcase`. `["*"]`
  pasa todo (forma normalizada de `import: ALL`), `[]` no pasa nada, `["hyperv-*"]` matchea
  por prefijo, etc.

**Lo que NO está en Pieza 1.B:**
- Validar que el nombre del hipervisor (local o heredado por plantilla) apunta a un hipervisor
  declarado en algún sitio accesible. El service sigue mirando solo su registro de conectores.
- Plantillas que derivan de plantillas (`based on:`) → Pieza 4.
- Modo anotado del Resolver (procedencia por campo) → futuro, fuera de Sprint 2.

**Tests (33 nuevos):**
- Walker y merge directos: 14 tests cubriendo plantilla local, herencia con import explícito,
  bloqueo por import vacío, `import: ALL`, comodín de prefijo, cadena de dos niveles,
  plantilla no encontrada, carpeta inexistente, llegada a raíz sin encontrar.
- Property-based con Hypothesis: tres propiedades sobre `_merge_template`. (1) Si un campo
  está local non-None, gana siempre. (2) Si está None, lo rellena la plantilla. (3) El merge
  es idempotente (`merge(merge(d,t), t) == merge(d,t)`). Hypothesis genera casos automáticos
  con cualquier combinación de campos set/unset en descriptor y plantilla.

**Estado:** 193 tests verde (160 anteriores + 33 nuevos), `resolver.py` al 100% de cobertura,
ruff y mypy strict limpios. El Resolver está aislado — el service no lo llama aún. Deploy de
un descriptor con `use template:` sigue fallando con "no effective hypervisor". Eso lo
desbloquea Pieza 1.C.

### Próximo
- **Pieza 1.C — Integración**: el service llama al Resolver en `_machine_command` y `status`;
  `CreateDescriptorCommand.validate` comprueba que las plantillas referenciadas son
  accesibles desde la posición del descriptor (validación al cargar, fail-fast);
  las validaciones transitorias de Pieza 1.A (`"resolver not yet wired"`) desaparecen.
