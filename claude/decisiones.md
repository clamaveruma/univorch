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

## DEC-005b — Tipos de descriptor

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** Existen dos tipos de descriptor:
  - **Descriptor normal:** tiene definición + referencia a VM. Soporta todas las operaciones
  - **Descriptor de referencia:** solo tiene referencia a VM existente (sin definición). Operaciones limitadas: arrancar, parar, consultar estado. Sin deploy/undeploy ni herencia de plantillas
- **Referencia inversa:** campo de metadatos libre en la VM del hipervisor puede guardar la carpeta del orquestador — permite reconstruir el árbol y detectar VMs movidas directamente en el hipervisor
- **v1:** descriptores de referencia y descubrimiento de VMs existentes quedan fuera de v1
- **Futuro:** descubrimiento manual + autodescubrimiento en periodos de baja actividad
- **Ampliación 2026-05-23 (referencia inversa — ideas de futuro):** el campo de metadatos libre se expone en el interface común del conector como `set_metadata`/`get_metadata` (dict); cada conector lo traduce a su campo nativo (VMware `annotation`/notes, Proxmox `description`), guardando un JSON delimitado que coexiste con texto previo. Utilidades: recuperación ante pérdida/corrupción de TinyDB reconstruyendo el mapeo descriptor→VM; detección de VMs movidas/renombradas; detección de huérfanos/fantasmas; marcas para descriptores de referencia (con cuidado por no invasión); recuperación de crash a mitad de deploy (DEC-030); arbitraje multi-instancia/MSP con `instance_id`. Cautelas: la marca es pista, no verdad; no estampar VMs de terceros; no guardar secretos; respetar el límite de tamaño del campo. El MockConnector llevará un campo `metadata` en memoria desde Sprint 1 para TDD futuro. Ver `diario.md#2026-05-23`

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

## DEC-012 — Importación explícita de definiciones heredables

- **Fecha:** 2026-05-16 (revisado 2026-05-17) → ver `diario.md#2026-05-17`
- **Decisión:** El mecanismo es de **importación** (no exportación). Cuando se crea una carpeta hija, su creador declara qué definiciones importa de la carpeta padre. Lo que no se importa no es visible por debajo
- **Comodín `*`:** está soportado — importa todo lo disponible en la carpeta padre. Útil para casos como "cada carpeta de alumno importa todo lo de la asignatura"
- **Propiedad implícita:** el concepto de "propietario" de una carpeta no se implementa explícitamente. Emerge de la asignación de roles: los managers de una carpeta son sus propietarios efectivos; el admin es manager de todo; el alumno es end_user de su carpeta final
- **Formato:** YAML (o JSON). Detalle de implementación a definir en fase de arquitectura
- **Motivo:** Control explícito de visibilidad con flexibilidad máxima para el caso común
- **Refinamiento 2026-06-06 — closure de recursos (implementación efectiva).** El modelo conceptual del Sprint 2 (sesión de diseño 2026-05-27) ya recogía la regla: "una plantilla resuelve sus referencias internas desde donde fue definida, no desde donde fue importada". Al implementar el `_resolve_hypervisor` quedó sin aplicar; se corrige ahora. `resolve_descriptor` devuelve `(Descriptor, str | None)` donde el segundo es el path de la carpeta donde está definida la plantilla (None si no se usó plantilla). `_resolve_hypervisor` mira si el campo `hypervisor` viene del local del descriptor (`original.hypervisor is not None`) o del merge con la plantilla; en el segundo caso arranca el walker desde el `template_origin`. Consecuencia práctica: el demo `networks/` solo importa `[linux-vm]`, sin tener que importar también `mock01` que la plantilla usa internamente. Caso límite (descriptor con plantilla + override LOCAL del hipervisor) cubierto correctamente con la heurística simple "miramos si el campo era None pre-merge". Casos extremos que requieren modo anotado del Resolver siguen aplazados. Ver `diario.md#2026-06-06`
- **Refinamiento 2026-06-06 — walker genérico.** `_find_resource(name, start, repo, attribute)` extraído en el resolver. `_find_template` y `_find_hypervisor` quedan como adaptadores de una línea. Datastores e IP pools futuros plug-and-play. Misma regla de walking + import filter para todos los recursos heredables
- **Refinamiento 2026-06-06 — sintaxis YAML uniforme.** Plural en `define X:`, singular en `use X:`. Renombrado `define machine templates:` → `define templates:` para coherencia con `define hypervisors:` + `use hypervisor:`. El nombre interno Python (`vm_templates`) se queda — misma separación alias-YAML / nombre-Python que `connector_type`/`type`. Documentado en `docs/glossary.md` sección "Common syntax for inheritable resources" como contrato para datastores e IP pools futuros (con salvedades anotadas: IP pools quizá implícitos por carpeta, datastores quizá con contexto-hipervisor)

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
- **Motivo:** Necesario para HA futura. En activo/pasivo, el pasivo replica el estado en tiempo real

## DEC-016 — Operaciones del conector de hipervisor

- **Fecha:** 2026-05-16 (revisado 2026-05-17) → ver `diario.md#2026-05-17`
- **Separación de capas:** `deploy`/`undeploy` son conceptos del **orquestador**, no del conector. El conector solo expone primitivas del hipervisor. El orquestador implementa `deploy` → `connector.clone()` y `undeploy` → `connector.delete()`
- **Decisión:** Todo conector implementa un interfaz común con estas operaciones mínimas:
  - `clone(mode="linked"|"full")` — crear una VM a partir de la VM base. `mode="linked"` por defecto. `mode="full"` queda en el contrato pero **no soportado en v1** (lanza excepción "no soportado")
  - `delete` — eliminar la VM y su disco virtual completamente
  - `start` / `stop` / `force_stop`
  - `pause` / `resume`
  - `get_status` / `get_info`
  - Snapshots: desarrollo futuro. Pendiente discutir gestión de snapshots de alumnos
- **Linked clone en v1:** cada hipervisor tiene sus condiciones para linked clone (VMware: snapshot en la VM base; Proxmox: clonar desde plantilla y storage compatible). Se asume que la VM base las cumple; cómo prepararla figurará en la ayuda del programa. Si no se cumplen, `clone` lanza una excepción con la información necesaria para diagnosticar
- **Principio:** Las VMs desplegadas son siempre clones de una VM base creada por el admin
- **Principio de no invasión:** los hipervisores siguen funcionando con normalidad; UnivOrch es una capa adicional que no interfiere
- **Undeploy:** borrado total — VM y disco virtual eliminados del hipervisor; el descriptor queda en estado `provisioned`

## DEC-017 — Datastores como recurso con alias

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **Decisión:** Los datastores se tratan como un recurso más, definido dentro de la configuración del hipervisor con un alias interno. Se heredan en cascada igual que hipervisores y plantillas
- **Dos indirecciones de naturaleza distinta:**
  - Primera: alias → datastore real — la resuelve el orquestador
  - Segunda: datastore → almacenamiento físico — la resuelve el hipervisor, opaca para el orquestador

## DEC-018 — Interfaces de cliente

- **Fecha:** 2026-05-16 → ver `diario.md#2026-05-16`
- **v1 obligatorio:**
  - **CLI** (cmd2): modo doble — comandos bash individuales + shell REPL interactivo. Autenticación con token de sesión. Soporte de scripts
  - **Web GUI** (NiceGUI): interfaz para todos los roles, especialmente el alumno
- **Desarrollo futuro:**
  - **TUI** (Textual): modo monitor de solo lectura

## DEC-019 — Nombre del proyecto

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** El proyecto se llama **UnivOrch** — Universal Virtual Orchestrator
- **Motivo:** Nombre libre en PyPI, GitHub y DockerHub. Contiene "orch", evoca universalidad, pronunciable
- **Alternativas descartadas:** Maestro (orquestador de Netflix), Orchid (ocupado), Orchis/Orchon (demasiado cortos)

## DEC-020 — Acceso a VMs existentes

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** UnivOrch puede trabajar en paralelo con los hipervisores sin interferir. Las VMs existentes (no creadas por UnivOrch) se gestionan mediante **descriptores de referencia** (sin definición, solo enlace a VM real)
- **v1:** fuera de alcance. Se implementará en versiones posteriores
- **Futuro:** descubrimiento manual primero, luego autodescubrimiento en periodos de baja actividad

## DEC-021 — Gestión de usuarios

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** Los usuarios se almacenan en un fichero YAML gestionado por el admin vía web GUI. Interfaz `UserRepository` abstrae el almacenamiento para facilitar la migración futura a LDAP/AD u otros directorios externos
- **v1:**
  - Fichero YAML con lista de usuarios (username, password en texto plano, role, display_name, email)
  - Contraseñas en texto plano aceptadas para la prueba de concepto. **Nota:** migrar a hashing (bcrypt) antes de cualquier despliegue real
  - Solo el superusuario puede crear/editar/borrar usuarios vía web GUI
- **Asignación de usuarios a roles:** se define en la carpeta, no en el registro de usuario. Cada carpeta declara qué usuarios tienen acceso y con qué rol local. La asignación se hereda en cascada hacia abajo en el árbol
  - Raíz: asigna superusuarios
  - Carpeta asignatura: asigna managers (profesores) y puede asignar end_users
  - Carpeta alumno (mesa): asigna end_users (alumnos)
- **Comportamiento de rol por rama:** un mismo usuario puede tener roles distintos en ramas diferentes del árbol. El rol se aplica desde la carpeta donde se asigna hacia abajo. Se puede sobreescribir en cualquier subcarpeta (mismo mecanismo de herencia en cascada con sobreescritura local). La aplicación docente no necesita este comportamiento en v1, pero el motor genérico lo soporta de forma natural
- **Futuro:** integración con LDAP/AD (solo cambia la implementación del UserRepository); profesores con capacidad de añadir sus propios alumnos; SSO

## DEC-022 — Máquina de estados del descriptor

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** El descriptor tiene 4 estados propios del orquestador (no del hipervisor):
  - `provisioned` — descriptor definido, sin VM en el hipervisor
  - `deployed` — VM existe y está correctamente desplegada
    - flag `drifted` — condición dentro de `deployed`: la VM existe pero su config difiere del descriptor; el re-deploy la corrige
  - `broken` — operación fallida que dejó estado inconsistente; el usuario consulta el historial de Jobs para ver el motivo; salida mediante `force-undeploy`
  - `unreachable` — no hay comunicación con el hipervisor
- **Nota:** los estados runtime de la VM (running, stopped, paused) son del hipervisor y se consultan con `get_status`; el orquestador no los almacena como estado propio

## DEC-023 — Logs y retención de operaciones

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** Dos canales de logging diferenciados:
  - **Logs del sistema:** módulo estándar `logging` de Python → syslog/journald. Trazas del programa, errores, arranque/parada. Rotación gestionada por el SO
  - **Logs de operaciones:** historial de Jobs persistido en BD. Necesario para HA y para mostrar al usuario el motivo de estados `broken` o fallidos
- **Retención de Jobs:** configurable por el admin (valor por defecto: 90 días). Propiedad global, no heredable en cascada
- **Futuro:** ajustar política de retención (por tiempo, por cantidad, o combinada) según necesidades reales

## DEC-024 — Backup de la base de datos

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** Backup automático periódico con política de retención GFS (Grandfather-Father-Son): últimas N copias diarias, M semanales, K mensuales
- **v1:** TinyDB es un fichero JSON — backup por copia simple. Restauración manual por el admin
- **MongoDB (futuro):** `mongodump`/`mongorestore`, misma política GFS. Compatible sin cambios de concepto
- **Futuro:** interfaz en web GUI para ver backups disponibles y restaurar con un clic

## DEC-025 — Gestión de IPs: pools por carpeta

- **Fecha:** 2026-05-17 → ver `diario.md#2026-05-17`
- **Decisión:** v1 gestiona IPs mediante pools propios por carpeta. El IP-pool es un parámetro más de carpeta, sigue el mismo modelo de herencia en cascada que el resto de propiedades. Una subcarpeta puede sobreescribir el pool heredado
- **Validación al definir:** cuando se crea o edita un pool, el sistema comprueba que su rango no solape con ningún otro pool existente. Si solapa, rechaza la operación. La comprobación es en escritura, no en despliegue
- **En deploy:** el orquestador elige la primera IP libre del pool aplicable, la asigna al descriptor y la registra en BD
- **En undeploy:** la IP se libera y vuelve al pool
- **Refinamiento 2026-05-23 (multi-IP):** el modelo debe permitir **varias IPs por descriptor** (VMs multi-NIC). v1 asigna una sola IP del pool; la estructura de datos se diseña en plural para no rehacerla al añadir multi-NIC. Ver `diario.md#2026-05-23`
- **Fuera de alcance del orquestador:** cómo la VM recibe efectivamente esa IP en la red (DHCP, cloud-init u otro mecanismo) no es responsabilidad de UnivOrch
- **Futuro:** integración con IPAM externo (phpIPAM, NetBox) — solo cambia la implementación del IPPoolRepository

## DEC-026 — Modelo de herencia: combinación por tipo de dato

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **Decisión:** la regla de combinación en la herencia en cascada la determina el **tipo del dato**:
  - **Escalar** (`var: valor`) → reemplaza (el hijo pisa al padre)
  - **Lista** (`var: [a, b]`) → acumula (se añaden elementos)
  - **Mapa** (`var: {campo: val}`) → fusión recursiva (mismas reglas en los sub-campos)
- **Excepción declarable:** campos concretos donde el defecto no encaja se marcan para usar otra regla. Caso conocido v1: `ip_pool` → **reemplazar el bloque completo** (no fusión recursiva), porque rango/máscara/gateway solo tienen sentido como unidad coherente y DEC-025 permite que una subcarpeta sobreescriba el pool heredado
- **Permisos como parámetro de la definición:** dos listas separadas, `managers` y `end_users`, que **acumulan** al bajar. Un usuario puede estar en ambas (manager engloba end_user; redundante pero inofensivo en el modelo de 3 roles). El superusuario es caso aparte (asignado en raíz, DEC-021)
- **Limitación v1:** no se puede eliminar hacia abajo lo heredado (las listas solo crecen). La revocación se hace en el nivel donde se asignó
- **Resolución:** lazy (al vuelo), modelada como función pura `(ancestros, imports) → definición efectiva`; el mismo `Resolver` resuelve definiciones y permisos (son el mismo problema)
- **Futuro anotado:** (a) directiva tipo `@REMOVE` para eliminar elementos heredados de listas/mapas — debería respetar la regla de autoridad de permisos; (b) propiedades inmutables que no se puedan redefinir hacia abajo. Ambas fuera de v1
- **Trazabilidad:** refina DEC-010 (herencia obligatoria), DEC-012 (imports + comodín `*`), DEC-021 (roles en carpeta, cascada con sobreescritura)

## DEC-027 — Modelo declarativo: apply / plan / validación

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **Decisión:** core imperativo + capa declarativa fina. Operación única `apply(document)`; `plan` es el mismo flujo sin la ejecución (dry-run)
- **Flujo:** parseo → diff → validación → plan → ejecución. La **validación** (fail fast) comprueba RBAC, recursos (IPs libres, hipervisor alcanzable), consistencia (impacto sobre VMs desplegadas) y locks. Si falla, no se modifica nada
- **Atomicidad v1:** best-effort con informe (no rollback total). Lo aplicado queda aplicado; lo fallido queda visible en estado `broken`/`provisioned`. Modelo equivalente a Ansible/Terraform
- **Exclusión mutua:** lock por descriptor en BD (detalle de mecanismo → DEC del Bloque D)
- **Dos categorías de operación:** sobre máquinas (deploy/start/stop; lentas; conector→hipervisor) vs sobre definiciones (carpeta/descriptor; escritura en BD). Misma arquitectura, contenido de validación distinto
- **`apply(document)`:** documento con carpeta, varios descriptores, o ambos. Mecanismo único de carga masiva (resuelve pendiente de Fase 2)
- **Tres vías de edición:** CLI `set`, editor web YAML en vivo, upload/download de YAML. Todas usan el mismo motor `apply`
- **Export/round-trip:** solo la **definición local escrita** es exportable y reimportable con fidelidad. La **definición efectiva resuelta** es solo lectura (su valor depende del punto del árbol; no reimportable). UI con dos acciones diferenciadas
- **Export portable:** selección de qué exportar (máquinas/ramas) y modo **absoluto** (ruta fija, copia exacta) o **relativo/portable** (plantilla; al importar se exige punto destino)
- **Comentarios (Opción C):** estructura parseada = verdad operativa; blob YAML persistido con `ruamel.yaml` en modo round-trip conserva comentarios y formato. `set` modifica solo el campo afectado preservando el resto
- **Resolver con dos modos:** normal (valores) y **anotado** (valor + origen por propiedad). El anotado alimenta el editor web (heredadas coloreadas + origen). A diseñar en el `Resolver` desde el inicio
- **Editor web:** panel YAML editable + árbol resuelto en tiempo real; heredadas en otro color con origen; botón "Comprobar" = `plan`; aviso al sobreescribir una heredada
- **Trazabilidad:** apoya DEC-006 (declarativo), DEC-014/DEC-015 (Jobs), DEC-026 (Resolver). Resuelve el pendiente de Fase 2 sobre carga masiva de YAML

## DEC-028 — Motor de Jobs: Command pattern, síncrono v1, locking

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **Patrón Command:** cada operación (deploy, undeploy, start, stop, crear carpeta, editar descriptor) se encapsula como un objeto con dos métodos: `validate()` e `execute()`. El `plan`/dry-run llama a `validate()` de cada Command sin ejecutar ninguno. El motor trata todos los Commands igual, independientemente de su tipo
- **Ejecución v1 — síncrono con modelo asíncrono:** el Job se persiste en BD al crearse (estado `pending`), se actualiza a `running` al empezar y a `completed`/`failed` al terminar. El usuario espera el resultado síncronamente. La interfaz ya habla en Jobs desde v1 — el día que se añada una cola asíncrona, no cambia nada de cara afuera (costura limpia)
- **Lock por descriptor en BD:** campo en el registro del descriptor con el ID del Job que lo ocupa. Se adquiere antes de ejecutar, se libera al terminar (bien o mal). Reside en BD (no en memoria) para sobrevivir a reinicios y para HA activo/pasivo futura
- **Batch — política todo-o-se-rechaza:** el Job padre adquiere los locks de todos los descriptores afectados antes de empezar (durante la fase de validación del Bloque C). Si alguno está ocupado, el apply entero se rechaza limpiamente antes de tocar nada. Si todos están libres, los bloquea, ejecuta los child Jobs en orden, y libera todos al terminar
- **Jobs interrumpidos al arrancar:** si el servicio cae con Jobs en `running`, al reiniciar se detectan en BD y se marcan `interrupted`; se notifica al admin. No se relanzan automáticamente en v1. Recuperación automática es desarrollo futuro (HA)
- **Trazabilidad:** detalla DEC-014 (patrón Job), DEC-015 (Jobs persistidos), DEC-027 (validate en el flujo apply)

## DEC-029 — Conectores de hipervisor

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **Implementación desde cero:** conectores VMware, Proxmox y mock se reimplementan limpiamente sin reutilizar `esxobjects` ni `yamlinfr` como dependencias. Al completarlos se compara el diseño con las librerías del tutor; las diferencias se documentan como evaluación comparativa en la memoria del TFG
- **Contrato:** ABC `HypervisorConnector` con los métodos de DEC-016. ABC elegido sobre Protocol por: comprobación en tiempo de instanciación (fail fast), autodocumentación por herencia explícita, posibilidad de métodos con implementación por defecto compartida
- **Registro en v1:** diccionario interno mapeando nombre de tipo a clase de conector. Abstracción preparada para que en el futuro se pueda alimentar también por entry points (plugins de terceros instalables via pip) sin cambiar el núcleo
- **Ejecución:** in-process en v1. El ABC es la costura para externalizar el conector a un servicio separado en el futuro sin cambiar el orquestador
- **Mock:** conector `mock` implementado con el mismo ABC; configurable para simular fallos, latencia y deriva de configuración. Permite TDD sin hipervisor real
- **Trazabilidad:** concreta DEC-016 (operaciones del conector), DEC-004 (arquitectura en dos capas), A1 (entry points como punto de extensión)

## DEC-030 — Persistencia: BD documental, TinyDB→MongoDB, Repositories por agregado

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **BD documental (no relacional):** el descriptor tiene un campo de definición de estructura libre/variable que no encaja en tablas de columnas fijas. Un modelo documental (JSON-like) lo representa de forma natural
- **v1 TinyDB:** base de datos documental en un único fichero JSON. Sin servidor, sin red, sin configuración. Backup = copia del fichero (coherente con DEC-024)
- **Futuro MongoDB:** misma filosofía documental; producción, replicación, transacciones multi-documento, índices, HA activo/pasivo. La migración solo afecta a la implementación de los Repositories (DEC-007)
- **Repositories por agregado:** `FolderRepository`, `DescriptorRepository`, `JobRepository`, `IPPoolRepository`, `SessionRepository`. `UserRepository` ya definido en fichero YAML (DEC-021). Cada uno expone métodos simples (`save`, `get_by_id`, `find_by_path`, `update`, `delete`) y oculta completamente el motor de BD
- **Consistencia v1 — limitación aceptada:** TinyDB no soporta transacciones multi-documento. Una operación que escribe en varios repositorios (ej. deploy: descriptor + job + ip_pool) puede quedar incoherente si el proceso cae a medias. No se emula transaccionalidad en v1; se diseña el orden de escrituras para minimizar el daño y la validación al arranque detecta incoherencias. MongoDB (futuro) aporta transacciones reales. Limitación conocida y documentada de la PoC; consistente con el best-effort de DEC-027
- **Trazabilidad:** concreta DEC-007 (patrón Repository), DEC-024 (backup), DEC-015 (Jobs persistidos); coherente con DEC-027 (atomicidad best-effort) y DEC-028 (lock en BD)

## DEC-031 — Interfaces y capa de servicio: facade único, RBAC centralizado

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19`
- **Facade único `OrchestratorService`:** punto de entrada limpio y único. Todas las interfaces (CLI, web GUI, futura TUI) y la capa 2 (aplicación docente) lo usan. Ninguna habla directamente con el motor de Jobs, los Repositories ni los conectores
- **RBAC centralizado en el facade:** el control de permisos se aplica en la capa de servicio, una sola vez, no en cada interfaz. Garantiza reglas consistentes independientemente de la puerta de entrada. Usa el mismo `Resolver` de definiciones (permisos y definiciones son el mismo problema de herencia — DEC-026)
- **Interfaces finas:** cada interfaz solo traduce la entrada del usuario a llamadas al facade y renderiza el resultado. Cero lógica de negocio en la UI. Añadir una interfaz nueva no toca el núcleo
- **Sesiones en BD desde v1:** autenticación con token de sesión persistido en BD (no en memoria). Sobrevive a reinicios; preparado para HA activo/pasivo. Gestionado por `SessionRepository` (DEC-030)
- **Interfaces v1:** CLI con cmd2 (modo dual: comandos sueltos tipo bash para scripts + shell REPL interactivo) + Web GUI con NiceGUI (todos los roles, incluye el editor YAML del Bloque C/DEC-027). TUI con Textual queda para el futuro (consistente con DEC-018)
- **Capa 2 como cliente del facade:** la aplicación docente no es parte del núcleo; es un cliente que traduce semántica docente (asignatura, alumno, mesa) a operaciones genéricas. Mantiene el núcleo reutilizable: CTF, talleres, exámenes serían otras capas 2 sobre el mismo facade (coherente con DEC-004)
- **Trazabilidad:** concreta A2 (facade sin API pública formal en v1), DEC-018 (interfaces de cliente), DEC-004 (dos capas), DEC-021/DEC-026 (RBAC con Resolver), DEC-030 (SessionRepository)

## DEC-032 — Estados, errores y máquina de estados (diseño)

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19` (Bloque H)
- **4 estados del descriptor:** `provisioned`, `deployed` (con flag `drifted` como condición interna), `broken`, `unreachable`. Confirma DEC-022 a nivel de diseño de arquitectura
- **Estados runtime separados:** encendida/apagada/en pausa son del hipervisor, se consultan con `get_status`. El orquestador no los almacena como estado propio
- **Regla de oro:** los estados del descriptor solo cambian como resultado de un Job. No hay cambios de estado fantasma — todo es predecible y auditable a través del historial de Jobs
- **Detección reactiva en v1:** `drifted` se detecta bajo demanda (al llamar `get_status`/`get_info`); `unreachable` es reactivo a un fallo de comunicación. Sin bucle proactivo de verificación en v1
- **8 categorías de problemas cubiertas por mecanismos ya diseñados:** conectividad → `unreachable`; deriva → `drifted`; recursos del hipervisor → Job falla → `broken`; recursos huérfanos → detección bajo demanda; operaciones sobre el árbol → validación previa (fail-fast); ciclo de vida → `broken` + lock; capa de datos → limitación de consistencia aceptada (DEC-030); usuarios y permisos → RBAC centralizado en el facade
- **Mock como herramienta de prueba:** configurable para simular fallos, latencia y deriva — permite TDD de toda la lógica de errores sin hipervisor real
- **Trazabilidad:** confirma DEC-022 (estados del descriptor), coherente con DEC-027 (validación fail-fast), DEC-028 (lock + `broken`), DEC-030 (limitación de consistencia), DEC-031 (RBAC en facade)
- **Refinamiento 2026-05-25 — definición precisa de `broken` y dónde se determina:**
  - **Definición:** un descriptor está `broken` cuando una **operación de ciclo de vida
    (deploy/undeploy) falla a medias** y deja **incierta/inconsistente** la correspondencia
    descriptor↔VM (el orquestador no puede fiarse de si la VM existe o coincide). Requiere
    intervención (`force-undeploy`)
  - **Se pone `broken`:** (1) en `deploy`/`undeploy`, si el conector falla tras pasar la
    validación (un `clone`/`delete` a medias deja la VM en estado incierto) — el Command lo marca,
    guarda y relanza; fuente principal en v1. (2) Futuro: por **reconciliación** (descriptor vs
    realidad del hipervisor). (3) Ventana "conector OK pero falla el `save`" (DEC-030): no se puede
    registrar en el momento (la BD es lo que falla) → se detecta por reconciliación. Futuro
  - **NO se pone `broken`:** rechazos de validación (no se intentó nada); fallos de
    `start`/`stop`/`pause`/`resume` (no cambian la correspondencia; transitorios → a lo sumo
    `unreachable`); `unreachable` es estado aparte (conectividad, recuperable)
  - **Salida:** `force-undeploy` (limpia VM residual → `provisioned`). No construido aún
  - **Implicación en `validate`:** para que un fallo en `execute` sea un fallo real a medias (no un
    error de config), `validate` debe cazar precondiciones predecibles (plantilla existe, hipervisor
    alcanzable — DEC-027 lo permite consultando al conector). A afinar
  - **Alcance:** definido ahora; **se implementa junto con la simulación de fallos del mock (M4)** y
    las rutas de error, porque probar `broken` requiere fallos simulados. La demo mínima es camino
    feliz y no toca `broken`. Ver `diario.md#2026-05-25`
- **Validación antes del Job (aclaración con el usuario, 2026-05-25):** la validación que **rechaza**
  vive en el `OrchestratorService` (valida la operación o el batch entero y rechaza **sin crear
  ningún Job**, DEC-027/028). El **motor de Jobs** solo ejecuta Commands ya validados: crea el Job y
  lo marca `COMPLETED`/`FAILED` según falle la **ejecución** (runtime). `execute()` revalida por
  dentro solo como red de seguridad para llamadas sueltas. Semántica: fallo de validación → **no hay
  Job**; fallo de ejecución → **Job `FAILED`**

## DEC-033 — Stack tecnológico v1

- **Fecha:** 2026-05-19 → ver `diario.md#2026-05-19` (Fase 4)
- **Lenguaje — Python 3.12:** decorador `@override` (verificación temprana de los contratos ABC de conectores), intérprete 10-20% más rápido que 3.11, mensajes de error más precisos, soporte hasta 2028. La versión la fija el contenedor, independiente del SO host
- **Testing — pytest + pytest-cov + Hypothesis:** pytest porque NiceGUI y cmd2 publican sus utilidades de test como plugins de pytest (integración natural). pytest-cov mide cobertura de líneas y ramas (indicador de rutas no probadas, no garantía de corrección). Hypothesis (property-based) para el `Resolver` (función pura, caso ideal)
- **Gestor de dependencias — `uv`:** binario Rust (no módulo Python), instalado como programa. En el Dockerfile se copia con `COPY --from=ghcr.io/astral-sh/uv:<versión fijada>` (multi-stage, versión fijada por reproducibilidad). `pyproject.toml` como configuración unificada del proyecto (sustituye setup.py, requirements.txt y varios ini)
- **Distribución — docker-compose + script bash fino (Alternativa 2):** el script envuelve `docker compose up/down/restart` y el arranque con el sistema. docker-compose hace explícito el volumen de persistencia de TinyDB (riesgo crítico si se olvida) y escala de forma natural a MongoDB futuro. Imagen publicada en ghcr.io
- **Calidad de código — Ruff + mypy:** Ruff = linter + formateador en una herramienta Rust (sustituye flake8, isort, black; Astral, misma empresa que `uv`). mypy = comprobador de tipos (valida contratos ABC de conectores y firmas del `Resolver`). Solo en entorno de desarrollo (`[project.optional-dependencies] dev`), no en el contenedor de producción. Integrados en VSCode (extensiones oficiales) y en CI/CD (GitHub Actions) como puerta de calidad
- **Librerías de hipervisor — extras opcionales:** `pyvmomi` (SDK oficial de VMware, vSphere API SOAP; lo que usa `esxobjects` del tutor, facilita la comparación final) y `proxmoxer` (wrapper de facto de la comunidad sobre la API REST de Proxmox; no existe SDK oficial). Modelados como extras opcionales en `pyproject.toml` (`vmware = [...]`, `proxmox = [...]`) — dependencias del conector concreto, no del núcleo
- **Mock — sin dependencias:** clase Python in-process sobre el mismo ABC `HypervisorConnector`, estado en memoria. Función de inicialización con variantes (`empty()`, `with_defaults()`, `with_templates([...])`); las VMs base precargadas son necesarias como fuente de linked clone. Métodos de inspección/inyección fuera del ABC, solo para tests (`deployed_vms()`, `inject_drift()`, `make_unreachable()`). Variante mock-como-servicio-REST anotada como futuro (probaría la frontera out-of-process)
- **Transporte REST — FastAPI + uvicorn + httpx:** FastAPI expone la API que la CLI consumirá
  en Sprint 2+. El argumento principal para el REST **no** es la comodidad de la CLI remota
  (el admin ya tiene SSH), sino la **API pública como efecto secundario**: integraciones
  externas (scripts, CI/CD, GitOps futuro). La CLI remota sin SSH es un beneficio secundario.
  Documentado así en la memoria del TFG. uvicorn sirve FastAPI; httpx es el cliente HTTP de
  la CLI. Núcleo primero: FastAPI/httpx no se usan en Sprint 1.
- **CLI output — Rich:** librería de output formateado para el terminal (colores por estado,
  tablas, progreso). Dependencia de **producción** (forma parte de la UI del CLI, no de las
  herramientas de desarrollo). Misma empresa (Textualize) que Textual (TUI futura).
- **Trazabilidad:** concreta DEC-029 (conectores ABC, mock para TDD), DEC-030 (TinyDB), coherente con DEC-026 (Resolver como función pura → Hypothesis). Entregable: `docs/technologies.md`. Actualizado 2026-05-22 con FastAPI, uvicorn, httpx y Rich.

## DEC-034 — Adopción acotada de Pydantic v2

- **Fecha:** 2026-05-23 → ver `diario.md#2026-05-23`
- **Decisión:** se adopta **Pydantic v2** de forma deliberadamente sencilla, solo donde simplifica el diseño. Dependencia de producción (FastAPI ya lo arrastra en Sprint 2; entra antes para las entidades y la validación de `apply`)
- **Dónde SÍ se usa:**
  - **Entidades del dominio** (`Folder`, `Descriptor`, `Job`, `Session`) como `BaseModel`. Motivo principal: la frontera de serialización con TinyDB — `model_dump()`/`model_validate()` eliminan el código manual de conversión objeto↔dict JSON. La validación en construcción (p.ej. `path` debe empezar por `/`) es un extra alineado con el "fail fast" del proyecto
  - **Validación del documento `apply`**: `ApplyDocument(BaseModel)` valida el esquema (kind, version, folders[].path, descriptors[].connector, descriptors[].template…) y da errores claros
  - **Tipo de retorno `VMInfo`** de `get_info()` en el conector
- **Dónde NO se usa:**
  - **El Resolver:** opera sobre el campo `definition` de estructura libre (DEC-030) y Hypothesis necesita generar dicts arbitrarios; la validación estorbaría. Trabaja sobre dicts puros
  - **`RuntimeState`:** es un `Enum` de stdlib, no un modelo Pydantic
  - **`config.py`:** dos env vars → `os.environ` basta; `pydantic-settings` sería excesivo
  - **El campo `definition` del `Descriptor`:** se queda como `dict` flexible (la herencia DEC-026 fusiona estructuras anidadas arbitrarias; evolucionará en Sprint 2)
- **"Sencillo" significa:** `BaseModel` pelado, sin validators salvo donde cacen un bug real, sin alias ni serializers custom ni genéricos
- **Reversibilidad:** el patrón Repository (DEC-030) aísla la serialización; la representación de las entidades se puede cambiar después con coste bajo
- **Tipos que cruzan la frontera del conector:** `RuntimeState(Enum)` = RUNNING/STOPPED/PAUSED/UNKNOWN; `VMInfo(BaseModel)` = id, name, runtime_state, cpu, memory_mb, disk_gb (opcionales). `get_status()` → `RuntimeState` (consulta barata); `get_info()` → `VMInfo` (foto completa para detectar `drifted`). El `id` es **opaco para el core**, significativo solo para el conector (VMware MoRef/instanceUuid; Proxmox VMID+node); el nombre no sirve como clave
- **Trazabilidad:** coherente con DEC-029 (ABC del conector), DEC-030 (TinyDB/Repository), DEC-026 (Resolver sobre dicts), DEC-033 (FastAPI usa Pydantic), DEC-022/032 (estados, `VMInfo` alimenta `drifted`)

## DEC-035 — Idempotencia de las operaciones

- **Fecha:** 2026-05-23 → ver `diario.md#2026-05-23`
- **Decisión:** todas las operaciones del orquestador son **idempotentes**: aplicarlas varias veces lleva al mismo estado final. Es consecuencia directa de la filosofía declarativa (DEC-006) — son **aserciones de estado** ("asegura que está desplegado/encendido"), no deltas imperativos
- **La idempotencia vive en el orquestador, NO en el conector:** las primitivas del conector (`clone`, `delete`) **no** son idempotentes (`clone` dos veces crea dos VMs). El **Command** (DEC-028) comprueba el estado actual del descriptor y solo llama al conector si hace falta. Separación: conector primitivo + orquestador convergente
- **No-op = éxito informativo, nunca warning:** si se ordena algo ya hecho, la operación devuelve **éxito** (exit code 0, scriptable) con un mensaje informativo, siguiendo el modelo Ansible `changed`/`unchanged`. El Job lo registra como no-op. Un warning sería semánticamente incorrecto (el estado deseado se cumple). Coherente con el `plan`/diff (DEC-027): `apply` informa `3 unchanged, 1 created`; `start` ya encendido → `already running (no change)`
- **Límite (camino feliz):** la idempotencia aplica al camino feliz. `deploy` sobre `broken` o `start` sobre `unreachable` son **errores**, no no-ops
- **Documentación:** cada operación se marca como idempotente en su docstring y en `docs/`
- **Trazabilidad:** concreta DEC-006 (declarativo), DEC-028 (Command), coherente con DEC-027 (plan/diff), DEC-022/032 (estados que distinguen no-op de error)

## DEC-036 — Conectores: registro de tipos + pool de sesiones vivas

- **Fecha:** 2026-06-06 → ver `diario.md#2026-06-06`
- **Decisión:** dos estructuras separadas, una para tipos (cómo construir) y otra para sesiones (los objetos vivos), en vez del dict mixto que llevábamos hasta ahora
- **Registro de tipos (`CONNECTOR_TYPES`):** dict hardcoded en `src/univorch/connectors/__init__.py` que mapea nombre de tipo → clase de conector (`{"mock": MockConnector, "vmware": VMwareConnector, ...}`). Añadir un conector = un import + una entrada. El servicio recibe este dict por `__init__` con default = `CONNECTOR_TYPES`. Inyección de dependencias estándar
- **Pool de sesiones vivas:** atributo `self._connection_pool: dict[str, HypervisorConnector]` del servicio. Clave: el **path del folder** que declaró el hipervisor en el árbol (`/lab`, `/research`). Valor: la instancia viva. Dos hipervisores con el mismo nombre en ramas distintas (p.ej. dos `aulario`) → dos sesiones distintas. Las sesiones se instancian al vuelo en el primer uso y se reutilizan en operaciones siguientes
- **No es un Repository:** las sesiones llevan recursos del SO (sockets, tokens TLS, estado en memoria del mock); no son datos serializables, no deben persistirse en TinyDB. Persistir credenciales sería un problema de seguridad (coherente con DEC-021). El nombre "HypervisorConnectionPool" se queda en concepto; en código es un `dict` simple — promover a clase cuando haga falta lifecycle (`close_all`, `invalidate`)
- **Resolución de "use hypervisor: X" en uso:** el servicio camina el árbol con `_find_hypervisor` (gemelo de `_find_template` del Resolver) desde el folder del descriptor, encuentra el `HypervisorDef`, valida que su `type:` está en el registro, consulta el pool, instancia o devuelve la cacheada. Una sola capa de comprobación, en el sitio donde el dato se usa
- **Validación al cargar retirada por sencillez:** se descarta la idea de validar `type:` en `define hypervisors:` durante el `load`. Era defensa en profundidad redundante; `_resolve_hypervisor` ya caza el mismo error cuando alguien usa el hipervisor. Precio aceptado: en YAMLs grandes, una errata puede no detectarse hasta que un descriptor de esa rama intente desplegar
- **Instanciación al vuelo con `cls()` sin argumentos:** funciona para el mock porque su default ya precarga las plantillas demo. Para conectores reales (Pieza posterior) el constructor deberá recibir address/credentials del `HypervisorDef`; firma a decidir entonces
- **Descubrimiento automático (entry points) fuera de v1:** DEC-029 ya lo dejaba como extensión futura para conectores publicados por terceros; el dict hardcoded es la forma honesta y simple para la PoC
- **Trazabilidad:** concreta DEC-029 (conectores ABC, registro nombre→clase), coherente con DEC-031 (servicio como facade único), DEC-026 (mismo walker que el Resolver), DEC-021 (no persistir credenciales), refina DEC-005b (referencia inversa / metadatos en el hipervisor — futuro)
