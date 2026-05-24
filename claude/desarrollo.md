# Contexto de desarrollo — UnivOrch

Este fichero captura el contexto operativo del proyecto: qué hay que hacer ahora, cómo estructurar
el código, convenciones de desarrollo y alcance de los sprints. Complementa `diario.md` (cronológico)
y `decisiones.md` (decisiones técnicas). Actualizar cuando haya cambios de rumbo significativos.

---

## Estado actual de las fases

| Fase | Estado | Entregable |
|---|---|---|
| 1 — Definición del problema | ✅ Completada | `docs/vision.md` |
| 2 — Análisis de requisitos | ✅ Completada | `docs/requirements.md` |
| 3 — Diseño de arquitectura | ✅ Completada | `docs/architecture.md` |
| 4 — Selección de tecnologías | ✅ Completada | `docs/technologies.md` |
| 5 — Configuración del entorno | 🔄 En curso | ficheros de infra + `docs/environment.md` |
| 6 — Desarrollo iterativo (TDD) | ⏳ Pendiente | software funcionando |
| 7 — Evaluación y memoria | ⏳ Pendiente | memoria del TFG |

---

## Fase 5 — Pendiente de crear

Estos ficheros están diseñados pero aún no existen en el repo. Crearlos todos antes de arrancar
código de la Fase 6.

| Fichero | Propósito |
|---|---|
| `pyproject.toml` | Config unificada del proyecto (deps, herramientas) |
| `Dockerfile` | Imagen de producción |
| `docker-compose.yml` | Volumen TinyDB explícito, arranca el servicio |
| `univorch.sh` | Script fino que envuelve compose (start/stop/restart/status) |
| `.devcontainer/devcontainer.json` | Entorno de desarrollo reproducible |
| `.github/workflows/ci.yml` | Pipeline CI: Ruff + mypy + pytest en cada push |
| `docs/environment.md` | Entregable escrito de Fase 5 |

**Decisiones de Fase 5 confirmadas:**
- Estructura del código: `src/univorch/` (src-layout) ← **pendiente confirmación usuario**
- Puerto web NiceGUI: `8080` configurable por env var `UNIVORCH_PORT` ← **pendiente confirmación usuario**
- Python 3.12 en el contenedor
- `uv` como gestor de dependencias (binario Rust, multi-stage Docker)
- Imagen base devcontainer: `mcr.microsoft.com/devcontainers/python:3.12`
- Imagen producción publicada en `ghcr.io/clamaveruma/univorch`

**Opciones de entorno de desarrollo (todas compatibles con el mismo devcontainer.json):**
- VSCode + Dev Container local (Docker en el PC)
- VSCode + SSH al servidor Linux propio + Dev Container en el servidor (opción preferida para Fase 6
  — sin límites de horas, acceso directo a hipervisores VMware/Proxmox en la misma red)
- GitHub Codespaces (120 core-horas/mes en plan gratuito ≈ 2 h/día — válido para sesiones cortas
  de documentación, no para desarrollo intensivo de Fase 6)
- VSCode local sin contenedor (requiere instalar dependencias a mano)

---

## Estructura del código

```
src/
└── univorch/
    ├── __init__.py
    ├── config.py                  # configuración global, carga de env vars
    ├── models.py                  # dataclasses: Folder, Descriptor, Job, Session
    ├── resolver.py                # función pura: (ancestors, imports) → definición efectiva
    │                              # dos modos: normal y anotado (DEC-026, DEC-027)
    ├── service.py                 # OrchestratorService — facade único (DEC-031)
    ├── connectors/
    │   ├── __init__.py
    │   ├── base.py                # ABC HypervisorConnector (DEC-029)
    │   ├── mock.py                # MockConnector — in-process, estado en memoria
    │   ├── vmware.py              # VMwareConnector — pyvmomi (extra opcional)
    │   └── proxmox.py             # ProxmoxConnector — proxmoxer (extra opcional)
    ├── jobs/
    │   ├── __init__.py
    │   ├── engine.py              # motor de Jobs: ciclo de vida, locking (DEC-028)
    │   └── commands.py            # Command pattern: DeployCommand, StartCommand, etc.
    ├── persistence/
    │   ├── __init__.py
    │   ├── base.py                # interfaces ABC de los Repositories (DEC-030)
    │   └── tinydb/
    │       ├── __init__.py
    │       └── repositories.py    # implementaciones TinyDB
    └── interfaces/
        ├── __init__.py
        ├── cli/
        │   ├── __init__.py
        │   └── app.py             # cmd2 — modo dual bash + REPL (DEC-018, DEC-031)
        └── web/
            ├── __init__.py
            └── app.py             # NiceGUI — Sprint 2+ (DEC-018)
```

```
tests/
├── unit/
│   ├── test_resolver.py           # Hypothesis + pytest (función pura, caso ideal)
│   ├── test_models.py
│   ├── test_commands.py
│   └── test_mock_connector.py
├── integration/
│   └── test_service.py            # OrchestratorService con TinyDB y mock
└── conftest.py                    # fixtures compartidos

demo/
├── README.md                      # guía paso a paso para el profesor
├── setup.yml                      # árbol de carpetas y descriptores de ejemplo
└── templates.py                   # (o YAML) descripción de las VMs base del mock
```

---

## Sprint 1 — alcance y demo del profesor

### Objetivo
Entregable funcional mínimo: el profesor recibe un script, levanta UnivOrch, interactúa con una
demo usando la CLI, y puede ver los conceptos clave en acción sin necesidad de hipervisor real.

### Qué entra en Sprint 1

- [ ] Modelo de datos: `Folder`, `Descriptor`, `Job` (sin herencia completa todavía — YAMLs
      autocontenidos en Sprint 1; Resolver completo en Sprint 2)
- [ ] Repositorios TinyDB: `FolderRepository`, `DescriptorRepository`, `JobRepository`
- [ ] `MockConnector` con `empty()`, `with_demo_templates()`, `with_templates()` y métodos de
      inspección (`deployed_vms()`, `inject_drift()`, `make_unreachable()`)
- [ ] Motor de Jobs básico: ciclo de vida `pending → running → completed/failed`, lock por
      descriptor en BD
- [ ] Commands: `DeployCommand`, `UndeployCommand`, `StartCommand`, `StopCommand`,
      `GetStatusCommand`
- [ ] `OrchestratorService`: `apply()`, `deploy()`, `start()`, `stop()`, `get_status()`,
      `list_tree()`
- [ ] Parser YAML con `ruamel.yaml` (preserva comentarios — DEC-027)
- [ ] CLI cmd2 con comandos: `apply`, `deploy`, `undeploy`, `start`, `stop`, `status`, `list`
- [ ] Autenticación básica: token de sesión en BD (SessionRepository)
- [ ] Demo: carpeta `demo/` con YAMLs y README para el profesor
- [ ] Docker: `Dockerfile` + `docker-compose.yml` + `univorch.sh start`
- [ ] Tests: cobertura del Resolver, MockConnector y operaciones básicas del service

### Qué queda fuera de Sprint 1

- Herencia en cascada completa (Resolver con imports y comodín `*`) → Sprint 2
- Web GUI (NiceGUI) → Sprint 2
- RBAC completo → Sprint 2
- Conectores reales (VMware, Proxmox) → Sprint 3+
- Capa docente (asignaturas/alumnos) → Sprint final
- Pools de IPs → Sprint posterior
- Gestión de usuarios vía web → Sprint posterior

### Demo para el profesor — flujo previsto

El profesor ejecuta `./univorch.sh start` y abre el REPL con `./univorch.sh cli`:

```
univorch> apply demo/setup.yml
# Crea /lab, /lab/networks y 3 descriptores en estado 'provisioned'

univorch> list /
# Muestra el árbol completo con estados

univorch> cd /lab/networks
univorch /lab/networks>

univorch /lab/networks> deploy student01
# Mock clona desde 'linux-base'; descriptor pasa a 'deployed'

univorch /lab/networks> status student01
# State: deployed | Runtime: stopped

univorch /lab/networks> start student01
# Runtime: running

univorch /lab/networks> status student01
# State: deployed | Runtime: running

univorch /lab/networks> stop student01
univorch /lab/networks> undeploy student01
# Descriptor vuelve a 'provisioned'

univorch /lab/networks> list
# Árbol de la carpeta actual con estados

univorch /lab/networks> exit
```

Los YAMLs de la `demo/` son el material didáctico: muestran la estructura declarativa y los
comentarios preservados. Ver también `demo/README.md` para la guía completa del profesor.

---

## Sintaxis YAML de Sprint 1

Acordada el 2026-05-22. Referencia: `demo/setup.yml`.

```yaml
kind: apply        # único tipo soportado en Sprint 1
version: "1"

folders:
  - path: /lab                   # obligatorio; ruta absoluta en el árbol
    description: "..."           # opcional

descriptors:
  - path: /lab/networks/student01  # obligatorio
    description: "..."             # opcional
    hypervisor: mock               # obligatorio: mock | vmware | proxmox
    base_vm: linux-base            # obligatorio: nombre de la VM base en el hipervisor
    cpu: 2                         # opcional (mock lo ignora; útil para validación futura)
    memory_mb: 2048                # opcional
    disk_gb: 20                    # opcional
```

**Limitación de Sprint 1:** los descriptores son autocontenidos — llevan toda su configuración
inline. En Sprint 2, `hypervisor`, `base_vm` y otros campos vendrán heredados de la carpeta
padre (herencia en cascada del Resolver). Los campos `cpu`/`memory_mb`/`disk_gb` están en el
schema para que el YAML sea realista y los tests de validación tengan algo que comprobar.

---

## Comandos CLI de Sprint 1

| Comando | Argumentos | Descripción |
|---|---|---|
| `apply <file>` | path al fichero YAML | Crea/actualiza árbol desde documento |
| `list [path]` | ruta (default: CWD) | Lista carpetas y descriptores con estado |
| `deploy <path>` | ruta absoluta o relativa | Despliega un descriptor (clone en el conector) |
| `undeploy <path>` | ruta absoluta o relativa | Elimina la VM; descriptor vuelve a `provisioned` |
| `start <path>` | ruta absoluta o relativa | Arranca la VM |
| `stop <path>` | ruta absoluta o relativa | Para la VM |
| `status <path>` | ruta absoluta o relativa | Estado del descriptor + estado runtime del hipervisor |
| `cd <path>` | ruta (solo REPL) | Cambia la carpeta de trabajo (CWD) |
| `pwd` | — (solo REPL) | Muestra la carpeta de trabajo actual |

**Resolución de rutas:** cualquier path que no empiece por `/` se resuelve relativo al CWD.
Ejemplo: estando en `/lab/networks`, `deploy student01` es equivalente a
`deploy /lab/networks/student01`.

---

## Convenciones de código

### Idioma
- **Código Python:** inglés exclusivamente — clases, funciones, variables, comentarios, strings de
  UI, mensajes de error, docstrings
- **Ficheros `claude/`:** español
- **Ficheros `docs/`:** inglés

### Estilo
- Python 3.12, type hints en todas las funciones y métodos públicos
- `@override` en todos los métodos de conectores y repositorios que implementen un ABC
- Ruff para linting y formateo (configurado en `pyproject.toml`)
- mypy en modo estricto para el núcleo (`src/univorch/core/`, conectores, repositorios)
- Funciones y métodos cortos: deben caber en una pantalla (~30 líneas máximo). Si crece más,
  extraer función privada con nombre descriptivo — el nombre actúa como comentario
- Comentarios inline solo para el *por qué*, nunca para el *qué*. El código bien nombrado
  ya explica el qué

### Docstrings — formato Google style

Todos los módulos, clases y métodos públicos llevan docstring. Formato Google style:

```python
def clone(self, source_id: str, mode: str = "linked") -> str:
    """Create a VM by cloning a base template.

    Args:
        source_id: ID of the base template to clone from.
        mode: Clone mode. Only 'linked' is supported in v1;
              'full' raises NotImplementedError.

    Returns:
        The ID of the newly created VM.

    Raises:
        ValueError: If source_id does not exist in the template pool.
        ConnectionError: If the hypervisor is configured as unreachable.
        NotImplementedError: If mode is not 'linked'.
    """
```

**Por qué no usamos @param (estilo Doxygen/Javadoc):**
Los type hints ya documentan los tipos directamente en la firma y mypy los valida. Repetirlos
en el docstring sería redundante y quedarían desincronizados si alguien cambia la firma. La
sección `Raises:` sí aporta información que los type hints no pueden expresar.

**Clases:** docstring explicando qué representa Y por qué existe separada (razón arquitectónica).
**Métodos privados (`_método`):** docstring si la lógica no es evidente; opcional si el nombre
ya lo dice todo.

### TDD
- Tests antes o junto al código, nunca después
- Tests unitarios para toda función pura (especialmente el Resolver — usar Hypothesis)
- Tests de integración para el service con TinyDB real (no mockeado) y MockConnector
- La cobertura de ramas es el indicador — no el número de líneas
- Cada Command tiene su propio test de `validate()` y de `execute()`

### Commits
- Automáticos al terminar cada bloque de trabajo
- Mensaje descriptivo en español
- Actualizar `claude/diario.md` en el mismo commit si hay contexto nuevo
- Siempre push tras el commit

### Excepciones vs comprobaciones al estilo C

Python favorece el estilo **EAFP** (*Easier to Ask Forgiveness than Permission*): intentar la
operación y capturar el error, en lugar de comprobar antes si es posible. El código del camino
feliz queda limpio; el manejo de errores va en bloques `except` separados.

**Regla para este proyecto:**

| Situación | Mecanismo |
|---|---|
| Input inválido, bug, entorno roto | Excepción (`ValueError`, `RuntimeError`…) |
| Violación de permisos | Excepción (`PermissionError`) |
| Hipervisor inalcanzable, operación imposible | Excepción (`ConnectionError`) |
| Validación donde queremos *todos* los errores | `list[str]` de retorno |

La excepción a las excepciones: **`validate()` devuelve `list[str]`** en lugar de lanzar.
Motivo: queremos recoger *todos* los problemas del apply antes de rechazarlo. Si lanzásemos
al primer error, el usuario no sabría cuántos otros problemas hay. Misma razón por la que un
compilador muestra todos los errores a la vez.

### Patrones clave a respetar
- El `OrchestratorService` es la única puerta de entrada — CLI y web no tocan repositorios ni
  conectores directamente (DEC-031)
- Los estados del descriptor solo cambian como resultado de un Job (DEC-032)
- Los Jobs se persisten en BD antes de ejecutarse (DEC-028)
- El MockConnector implementa el mismo ABC que los reales — nunca añadir lógica especial al
  service para el mock (DEC-029)

---

## Forma de trabajo — acuerdo con el usuario

Este acuerdo se estableció al inicio de la Fase 6 y debe respetarse en todas las sesiones:

- **El usuario decide** qué se hace en cada momento
- **Claude pregunta** antes de actuar — nunca asume ni ejecuta sin confirmación explícita
- **El usuario ejecuta** siempre que sea posible: comandos, configuración, edición de ficheros,
  creación de ficheros, commits, push
- **El código Python** lo escribe el usuario, por partes, entendiendo cada pieza antes de escribirla.
  Claude explica el diseño y el porqué, propone la estructura, revisa lo escrito
- **Claude explica, propone y revisa** — no ejecuta sin permiso
- **Tareas mecánicas** (commits, diario, renombrar ficheros): el usuario decide si las hace él o
  las delega a Claude. Preguntarle en cada caso si no está claro
- El objetivo es que el usuario entienda y pueda defender todo el código en la memoria del TFG
- **Código Python:** lo escribe Claude, pero despacio — primero explica qué va a hacer y por qué,
  espera a que el usuario lo entienda, lo escribe, el usuario lo revisa, y no se avanza hasta que
  no queden dudas. Ritmo: pocos métodos cada vez
- **Herramientas de desarrollo:** Claude dice qué hacer, el usuario ejecuta los comandos en su
  terminal y edita los ficheros. Claude puede leer cualquier fichero del repo y ver la salida de
  los comandos si el usuario la pega en el chat
- **Visibilidad:** Claude lee ficheros guardados y salidas de terminal pegadas — no ve en tiempo
  real lo que se escribe. Flujo: editar → guardar → "ya está" o pegar el error → Claude revisa
- **Commits y push:** tarea mecánica — Claude los hace salvo que el usuario quiera hacerlos él

## Contexto de transición: de Claude Code Web a Claude Code en VSCode

La conversación de diseño (Fases 1-5) ocurrió en Claude Code Web. El historial de chat no se
transfiere entre sesiones, pero TODO lo importante está capturado en los ficheros `claude/`:

- `claude/diario.md` — cronología completa de decisiones y razonamientos
- `claude/decisiones.md` — DEC-001 a DEC-033 con trazabilidad
- `claude/desarrollo.md` — este fichero: contexto operativo de desarrollo
- `claude/arquitectura-debate.md` — documento de trabajo de Fase 3 (histórico, no actualizar)
- `docs/` — entregables formales de cada fase

Una nueva sesión de Claude Code que lea el `CLAUDE.md` (con sus imports) tiene todo el contexto
necesario para continuar sin perder nada relevante.

**Para instalar Claude Code en VSCode:** extensión `anthropic.claude-code` del marketplace.
En el devcontainer, se declara en `customizations.vscode.extensions` del `devcontainer.json`
y se instala automáticamente al abrir el contenedor.
