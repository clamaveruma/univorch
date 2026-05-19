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
