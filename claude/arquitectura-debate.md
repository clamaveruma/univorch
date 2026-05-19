# Arquitectura — documento de debate (Fase 3, borrador)

> Documento **interno de discusión**, no es el entregable.
> El entregable final será `docs/arquitectura.md` (en inglés), redactado **después** de acordar aquí.
> Estructura: por cada área, el dilema → opciones con pros/contras → recomendación → preguntas abiertas.
> Al final, un checklist de decisiones para agilizar la conversación.

Estado: en debate con el usuario (tema a tema, formato pedagógico). Las decisiones cerradas se recogen abajo.

---

## Decisiones ya acordadas en diálogo (2026-05-19)

> Estas ya están cerradas con el usuario. El resto del documento es el análisis original.

- **A1 — Estructura repo:** un solo paquete + entry points para los dos puntos de extensión (conectores y aplicaciones). Simple donde se puede, barrera real solo donde importa.
- **A2 — Frontera del core:** facade `OrchestratorService` limpio desde el inicio, pero **sin** formalizar como API pública de plugins en v1 (opción 2). Crecimiento futuro mencionado en la memoria.
- **B1 — Árbol:** materialized path (ruta tipo fichero; los ancestros salen gratis de la clave).
- **B2 — Resolución de herencia:** lazy (al vuelo), modelada como **función pura**; un **único `Resolver`** para definiciones y permisos (son el mismo problema).
- **Modelo de herencia (DEC-026):** combinación por tipo de dato:
  - Escalar → reemplaza · Lista → acumula · Mapa → fusión recursiva
  - **Excepción declarable** para campos donde el defecto rompe (caso v1: `ip_pool` → reemplazar bloque entero, porque rango/máscara/gateway son una unidad y DEC-025 permite override)
  - **Permisos** = dos listas en la definición: `managers` y `end_users`, que **acumulan** al bajar. Un usuario puede estar en ambas (inofensivo: manager engloba end_user). Superusuario, caso aparte (raíz)
  - Limitación v1: no se puede eliminar hacia abajo lo heredado (listas solo crecen); revocación en el nivel de origen
  - Futuro anotado: directiva `@REMOVE` para listas/mapas (debe respetar la autoridad de permisos) y propiedades inmutables. Fuera de v1

---

## Bloque A — Estructura del código y separación de capas

### A1 — Organización del repositorio

**Dilema:** cómo materializar la separación capa 1 (core genérico) / capa 2 (app docente) para que sea real y no solo conceptual.

| Opción | Pros | Contras |
|---|---|---|
| (a) Un paquete, módulos internos (`univorch.core`, `univorch.apps.teaching`, `univorch.connectors`, `univorch.api`, `univorch.web`, `univorch.cli`) | Simple, un solo instalable, fácil para PoC | La frontera capa1/capa2 es solo disciplina, nada la fuerza |
| (b) Varios paquetes instalables (`univorch-core`, `univorch-teaching`, `univorch-vmware`...) | Frontera estricta y real | Tooling pesado para una PoC, sobrediseño |
| (c) Un paquete + **entry points** para conectores y apps | Simple como (a) pero la frontera es real: app y conectores se descubren, no se importan a mano; terceros extienden sin tocar el core | Algo de ceremonia con entry points |

**Recomendación:** **(a)+(c)**. Un repositorio/paquete con módulos internos bien separados, pero conectores y aplicaciones registrados vía entry points. Así la frontera de los dos puntos de extensión clave (hipervisores y apps) es real, y el resto es simple. Coherente con el NFR "nuevo hipervisor = implementar interfaz, sin tocar el core".

### A2 — Frontera del core: API pública

**Dilema:** la app docente (y futuras apps) no deben hurgar en los internos del core. ¿Qué expone el core?

**Recomendación:** un **facade explícito** — `OrchestratorService` — con operaciones de alto nivel (`create_folder`, `set_definition`, `create_descriptor`, `deploy`, `undeploy`, `run_batch`, `apply`, `get_tree`, `get_status`...) que devuelven Jobs y DTOs. Todo lo demás es interno. Ese facade es el contrato que mantiene la capa 2 desacoplada. (Se conecta con G1.)

**Pregunta abierta:** ¿quieres que el core tenga un *plugin API* documentado desde v1 (pensando en CTF, exámenes...) o lo dejamos emerger y lo documentamos cuando aparezca la segunda app?

---

## Bloque B — El árbol de descriptores (el núcleo)

### B1 — Representación y persistencia del árbol

**Dilema:** es la estructura central. Debe soportar: resolución de herencia raíz→nodo, operaciones de subárbol (desplegar una asignatura entera), mover/renombrar carpetas.

| Opción | Pros | Contras |
|---|---|---|
| Adjacency list (cada nodo guarda `parent_id`) | Escrituras triviales | Recorrer ancestros = varias consultas o recursión |
| **Materialized path** (cada nodo guarda su ruta `/root/asigX/alum1`) | La cadena de ancestros sale **gratis** de la propia clave → ideal para herencia; subárbol = consulta por prefijo | Mover una carpeta = reescribir rutas del subárbol |
| Closure table | Consultas de jerarquía muy potentes | Sobrediseño para PoC y para BD documental |
| Filesystem como árbol | Inspeccionable, versionable en git | Choca con Repository/Mongo; concurrencia (ver Bloque I) |

**Recomendación:** **Materialized path**. La resolución de herencia es exactamente "recorrer raíz→nodo"; con la ruta tienes los ancestros sin consultas extra. El despliegue de una asignatura es una consulta por prefijo. Mover carpetas es raro, y la reescritura del subárbol es asumible a esta escala y es en sí misma un Job. Encaja igual en TinyDB y MongoDB.

### B2 — Resolución de herencia + imports

**Dilema:** ¿se calcula la definición efectiva al vuelo o se materializa?

| Opción | Pros | Contras |
|---|---|---|
| **Lazy** (recorrer ancestros y aplicar imports+overrides al leer) | Siempre correcto, sin caché que invalidar, coste ~O(profundidad) y el árbol es plano (raíz/asig/alumno ≈ 3-4 niveles) | Recalcula en cada lectura (irrelevante a esta escala) |
| Materializado (guardar definición resuelta por nodo) | Lecturas rápidas | Invalidación en cascada compleja, riesgo de definición obsoleta = bugs sutiles |

**Recomendación:** **Lazy**, con memoización opcional por petición. A cientos de nodos y árbol plano es trivialmente barato y mucho menos propenso a bugs. Componente claro `DefinitionResolver`.

**Idea:** modelar la resolución como **función pura** `(ancestros, imports) → definición efectiva`. Función pura = test trivial (oro para TDD) y reutilizable por el futuro bucle de reconciliación. La resolución de roles RBAC usa el mismo recorrido → simetría: un único `Resolver` para definiciones y para permisos.

---

## Bloque C — Modelo declarativo

### C1 — Cómo el usuario aporta el estado deseado (pendiente desde Fase 2)

**Dilema:** UC-MGR-5 permite crear descriptores en lote por YAML; ¿cómo entra ese YAML?

**Recomendación:** una única operación de core `apply(document)`. La CLI lee el fichero y manda el contenido por REST (`univorch apply -f asignatura.yaml`); la web lo sube por formulario. Mismo punto de entrada. El esquema del documento es parte de la arquitectura. La creación masiva de descriptores es solo un documento con muchos descriptores → unifica UC-MGR-5 con el modelo declarativo.

### C2 — Motor de diff: deseado vs actual

| Opción | Pros | Contras |
|---|---|---|
| Imperativo puro (cada llamada muta y genera Job) | Lo más simple, encaja con "cambios bajo demanda" (DEC-006) | Sin visión de "estado deseado" global |
| Declarativo plan/apply estilo Terraform (diff → plan → confirmar → aplicar) | UX declarativa, dry-run | Motor de reconciliación completo = mucho para PoC |

**Recomendación:** **híbrido**. El core es imperativo (cada operación = un Job). Encima, una capa fina declarativa: `apply(document)` calcula el diff contra el árbol actual y emite las operaciones imperativas como un Job batch, con modo `plan` (dry-run) que muestra qué cambiaría sin tocar nada. Da la UX declarativa sin motor de reconciliación, y **esa función de diff es la semilla del futuro bucle de reconciliación**. Alineado con la filosofía de `yamlinfr` del tutor.

---

## Bloque D — Motor de Jobs

### D1 — Ejecución (síncrona en v1, preparada para asíncrona)

**Recomendación:** ejecución detrás de una interfaz `JobExecutor`. v1 = `SynchronousExecutor` (crea Job `pending`, ejecuta inline `running`, cierra `completed/failed`, devuelve). Futuro = `QueuedExecutor` (Celery/RQ/asyncio) con los mismos registros Job y la misma máquina de estados. **No** meter cola ahora (YAGNI), solo aislar la ejecución tras la interfaz.

### D2 — Modelo de Job

**Recomendación:** **patrón Command**. Cada operación = objeto Command (`Deploy`, `Undeploy`, `CreateFolder`...) con `execute()`. El Job es el registro persistido que envuelve un Command + ciclo de vida + resultado. Batch = Command compuesto → Job padre + Jobs hijo. Máquina de estados del Job mínima: `pending → running → completed/failed` (`cancelled` queda para futuro). Limpio, testable, encaja con "toda operación es un Job".

### D3 — Concurrencia y bloqueo

**Dilema:** ¿qué impide dos operaciones sobre el mismo descriptor? (nota previa en diario: "concurrencia bloqueada por Job activo").

| Opción | Pros | Contras |
|---|---|---|
| Lock global | Trivial | Serializa todo, mata el batch |
| **Lock por descriptor/subárbol en BD** (un descriptor con Job activo rechaza nuevos Jobs mutadores) | Granular, el batch bloquea solo sus objetivos, las lecturas nunca bloquean | Hay que gestionar el lock y su liberación |

**Recomendación:** lock advisory **a nivel descriptor**, registrado en BD (un descriptor con Job activo rechaza otro Job mutador). El lock en BD (no en memoria) es justo lo que hace viable el futuro multi-worker/HA. Documentar el supuesto single-writer de v1.

---

## Bloque E — Conectores de hipervisor

### E1 — Arquitectura del plugin

**Recomendación:** ABC `HypervisorConnector` con las operaciones acordadas (DEC-016). Descubrimiento por entry points indexado por `type` de hipervisor. Registro `type → clase conector`. La config (dirección/credenciales) se inyecta desde la definición de hipervisor ya resuelta por la cascada.

### E2 — In-process vs out-of-process (idea relevante)

| Opción | Pros | Contras |
|---|---|---|
| In-process (importar librería y llamar) | Simple, rápido | Una llamada colgada/que peta puede bloquear o tumbar el worker; timeouts duros difíciles en hilos Python |
| Out-of-process (conector como subproceso/microservicio) | Aislamiento: timeout = matar proceso, contención de fallos, incluso otro lenguaje | IPC, complejidad de despliegue |

**Recomendación v1:** conectores **in-process** tras la ABC, con timeouts estrictos y conversión de fallo de comunicación → `unreachable`. **Pero** diseñar la frontera del conector para que un adaptador out-of-process sea posible después — y de hecho **el mock ya va a ser un servicio aparte**, lo que demuestra que la costura existe. El out-of-process es la evolución natural para fiabilidad/HA dado el problema de `unreachable`/timeouts.

### E3 — Librerías del tutor (`esxobjects`, `yamlinfr`)

**Dilema:** son la base de partida del TFG. ¿Se reutilizan o se reimplementan limpio?

- `esxobjects` → envolver dentro de `VMwareConnector` (adaptador). **No** filtrar tipos de `esxobjects` al core; el conector traduce a la interfaz común.
- `yamlinfr` → su enfoque YAML→infra es el ancestro conceptual de C2. Opciones: (i) depender de ella, (ii) adoptar su esquema YAML pero reimplementar limpio dentro de la arquitectura.

**Recomendación:** estudiar `yamlinfr`, adoptar ideas de su esquema, reimplementar limpio (mantiene el core sin deudas externas). **Pregunta abierta para ti:** ¿el tutor espera reutilización directa de su código, o le vale "inspirado en, reescrito limpio"? Esto afecta a la memoria del TFG.

---

## Bloque F — Persistencia

### F1 — Repositorios y transaccionalidad

**Recomendación:** un repositorio por raíz de agregado: `TreeRepository` (carpetas+descriptores como árbol), `JobRepository`, `UserRepository`, e IPs **dentro del TreeRepository** (los pools son propiedad de carpeta) — *a discutir si merece su propio repo*. TinyDB no tiene ACID real: para PoC, aceptar single-process y, si una operación multi-documento falla a medias, marcar el Job `failed` y el descriptor `broken` (coherente con la máquina de estados: el fallo es **visible**, no silencioso). MongoDB futuro da transacciones reales.

### F2 — Migración a MongoDB

Interfaz de repositorio agnóstica del almacén; modelo de documento (dict/JSON) elegido para que TinyDB y MongoDB sean casi idénticos. No filtrar idioms de consulta de TinyDB fuera del repositorio. (DEC-007.)

---

## Bloque G — Interfaces y comunicación interna

### G1 — Capa de servicio compartida

**Recomendación (confirma tu propuesta):** un único `OrchestratorService` in-process (el facade del core). La web (NiceGUI) lo llama **directo** (mismo proceso, llamadas a función). La API REST (FastAPI) es un adaptador fino sobre el mismo servicio. La CLI es cliente REST. Una implementación, dos pieles de transporte. La **autorización RBAC se aplica en la capa de servicio**, no por transporte → un único punto de control.

### G2 — Autenticación y sesiones

**Dilema:** ¿dónde viven las sesiones/tokens? Impacta en HA.

**Recomendación:** store de sesiones/tokens tras una pequeña interfaz; v1 = **respaldado en BD** (comportamiento consistente tras reinicio, listo para HA — barato con la BD que ya tenemos). Autenticación con los mecanismos estándar del framework. La autorización reutiliza el `Resolver` de roles (misma maquinaria que la herencia → simetría).

---

## Bloque H — Estados, errores y observabilidad

### H1 — Máquina de estados del descriptor

**Recomendación:** componente explícito `DescriptorState` (transiciones `provisioned↔deployed`, `→broken`, `→unreachable`, flag `drifted`). **Las transiciones solo las dispara el resultado de un Job** (única fuente de verdad: el estado es consecuencia de Jobs). Pura y testable. `force-undeploy` única salida de `broken`.

### H2 — Mock hypervisor (clave para TDD)

**Recomendación:** servicio aparte (mismo contenedor), REST, implementa las mismas operaciones lógicas. Diseñarlo como una herramienta de TDD potente: latencia configurable, fallos configurables (error de comunicación → ejercita `unreachable`; fallo a media operación → ejercita `broken`), estado persistente para que clone/start/stop sean realistas, y capacidad de **simular drift externo** (mutar una VM "a espaldas" de UnivOrch) para probar la detección de `drifted`. Hace testable todo el diseño de excepciones/estados sin hipervisores reales.

---

## Bloque I — Ideas "out of the box"

1. **GitOps / árbol en git:** el estado deseado del árbol como YAML en un repo git; UnivOrch lo aplica. Potente para docencia (infraestructura de asignatura versionada, revisión por PR de una asignatura), encaja con declarativo + auditoría. **Descartado para el almacén de v1** (choca con Repository/Mongo) pero **muy interesante como "fuente de configuración" futura** enchufada a `apply(document)`.

2. **Event sourcing sobre el log de Jobs:** el estado del sistema = plegado del log de Jobs. Los Jobs ya son el registro persistido de auditoría + sustrato de replicación HA. ES completo es demasiado para PoC, **pero diseñar las transiciones de estado como consecuencia de Jobs (H1) es "ES-lite"** y deja la puerta abierta. Merece nombrarlo explícitamente en la memoria.

3. **Conectores como procesos aislados (E2):** historia de fiabilidad — un VMware colgado no tumba el orquestador. El mock-como-servicio ya valida la costura.

4. **No cerrar la puerta a la reconciliación:** mantener la función de diff (C2) pura y autónoma para que un futuro bucle solo la invoque en un timer.

5. **Analogía SO "tabla de descriptores":** exponer semántica open/close/handle en la API por elegancia conceptual (coherente con el nombre "descriptor"). Probablemente cosmético; lo menciono por si encaja en el relato del TFG.

---

## Checklist de decisiones para mañana

| # | Decisión | Recomendación |
|---|---|---|
| A1 | Estructura repo | 1 paquete + entry points (conectores/apps) |
| A2 | Frontera del core | Facade `OrchestratorService`; ¿plugin API documentado ya? |
| B1 | Representación del árbol | Materialized path |
| B2 | Resolución herencia | Lazy, función pura, `Resolver` único (defs + roles) |
| C1 | Entrada de YAML | Operación única `apply(document)` (CLI y web) |
| C2 | Diff/declarativo | Híbrido: core imperativo + capa `apply`/`plan` |
| D1 | Ejecución Jobs | Interfaz `JobExecutor`; v1 síncrono |
| D2 | Modelo Job | Command pattern + registro Job |
| D3 | Concurrencia | Lock por descriptor en BD |
| E1 | Plugin conector | ABC + entry points por `type` |
| E2 | In/out-of-process | In-process v1, costura para out-of-process futuro |
| E3 | Librerías tutor | Adaptar `esxobjects`; reimplementar limpio inspirado en `yamlinfr` — **confirmar expectativa del tutor** |
| F1 | Repositorios | Uno por agregado; fallo a medias → `broken` visible |
| G1 | Capa servicio | Facade único; RBAC en la capa de servicio |
| G2 | Sesiones | Respaldadas en BD desde v1 |
| H1 | Estados | Transiciones solo por resultado de Job |
| H2 | Mock | Servicio REST con fallos/latencia/drift configurables |

**Preguntas abiertas que necesito de ti:**
1. ¿Plugin API del core documentado desde v1, o emerge con la 2ª app? (A2)
2. Expectativa del tutor sobre `esxobjects`/`yamlinfr`: ¿reutilización directa o reescritura limpia inspirada? (E3)
3. ¿Te interesa el ángulo GitOps/event-sourcing para la memoria del TFG aunque quede fuera de v1? (Bloque I)
