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
| 5 — Configuración del entorno | ✅ Completada | infra + `docs/environment.md` |
| 6 — Desarrollo iterativo (TDD) | 🔄 En curso | software funcionando — Sprint 1 cerrado |
| 7 — Evaluación y memoria | ⏳ Pendiente | memoria del TFG |

---

## Entornos de desarrollo soportados

El mismo `.devcontainer/devcontainer.json` funciona en:

- **VSCode + Dev Container local** (Docker en el PC).
- **VSCode + Remote-SSH al servidor Linux propio + Dev Container en el servidor.** Opción
  preferida cuando lleguemos a conectores reales (acceso directo a hipervisores
  VMware/Proxmox en la misma red).
- **GitHub Codespaces** (120 core-horas/mes en plan gratuito; bien para sesiones cortas).
- VSCode local sin contenedor (requiere instalar dependencias a mano).

Imagen base del devcontainer: `mcr.microsoft.com/devcontainers/python:3.12`. La imagen
de producción se publicará en `ghcr.io/clamaveruma/univorch`.

---

## Estructura del código

Estructura **objetivo** (* = aún no construido). Lo que existe hoy refleja Sprint 1
cerrado; los marcados `*` entran en sprints siguientes.

```
src/
└── univorch/
    ├── __init__.py
    ├── __main__.py                # entry point del contenedor (sleep loop)
    ├── models.py                  # Pydantic: Folder, Descriptor, Job, ApplyDocument, …
    ├── service.py                 # OrchestratorService — facade único (DEC-031)
    ├── parser.py                  # ruamel.yaml + Pydantic
    ├── resolver.py *              # función pura ancestors→definición efectiva (Sprint 2, DEC-026)
    ├── connectors/
    │   ├── base.py                # ABC HypervisorConnector (DEC-029)
    │   ├── types.py               # RuntimeState, VMInfo, CloneMode
    │   ├── mock.py                # MockConnector — in-process, estado en memoria
    │   ├── vmware.py *            # VMwareConnector — pyvmomi (Sprint 3+)
    │   └── proxmox.py *           # ProxmoxConnector — proxmoxer (Sprint 3+)
    ├── jobs/
    │   ├── engine.py              # motor de Jobs: ciclo de vida (DEC-028)
    │   └── commands.py            # Command pattern: 6 commands de máquina + definición
    ├── persistence/
    │   └── tinydb/
    │       └── repositories.py    # FolderRepository, DescriptorRepository, JobRepository
    └── interfaces/
        ├── cli/
        │   └── app.py             # cmd2 — modo dual bash + REPL (DEC-018, DEC-031)
        └── web/                   # NiceGUI — Sprint 2 (DEC-018)
            └── app.py *
```

```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_commands.py
│   ├── test_connector_base.py
│   ├── test_mock_connector.py
│   ├── test_cli.py
│   └── test_resolver.py *         # Hypothesis + property-based (Sprint 2)
├── integration/
│   └── test_service.py
└── conftest.py                    # fixtures compartidos

demo/
├── README.md                      # guía paso a paso para el profesor
└── setup.yml                      # árbol de carpetas y descriptores de ejemplo
```

---

## Sprint 1 — alcance y demo del profesor

### Objetivo
Entregable funcional mínimo: el profesor recibe un script, levanta UnivOrch, interactúa con una
demo usando la CLI, y puede ver los conceptos clave en acción sin necesidad de hipervisor real.

### Qué entra en Sprint 1

- [x] Modelos Pydantic: `Folder`, `Descriptor`, `Job`, `OperationType`, `JobStatus`,
      `ApplyDocument` (YAMLs autocontenidos; herencia/Resolver → Sprint 2).
- [x] Repositorios TinyDB: `FolderRepository`, `DescriptorRepository`, `JobRepository`.
- [x] `MockConnector` con `empty()` / `with_demo_templates()` / `with_templates()` y
      `deployed_vms()` para tests. Simulación de fallos (M4) aplazada con `broken`.
- [x] Motor de Jobs básico: `JobEngine.run(command)` ciclo `pending → running →
      completed/failed`. Lock por descriptor pospuesto (sin concurrencia en v1).
- [x] Commands (6): `DeployCommand`, `UndeployCommand`, `StartCommand`, `StopCommand`,
      `CreateFolderCommand`, `CreateDescriptorCommand`. Patrón Command con `validate()` +
      `execute()` (DEC-028).
- [x] `OrchestratorService`: `apply()`, `deploy()`, `undeploy()`, `start()`, `stop()`,
      `status()`, `list_tree(recursive)`, `folder_exists()`. Validación que rechaza en el
      service (sin Job); motor solo ejecuta validados (DEC-027/032).
- [x] Parser YAML con `ruamel.yaml` (`extra="forbid"` caza erratas; round-trip se aplaza
      a Sprint 2 con el editor web).
- [x] CLI cmd2 con argparse (`with_argparser`): `apply`, `deploy`, `undeploy`, `start`,
      `stop`, `status`, `list`/`ls`, `tree`, `cd`, `pwd`. Glifos de estado, ayuda
      autogenerada coloreada, terminología "VM" externa.
- [x] Demo: `demo/setup.yml` + `demo/README.md`.
- [x] Tests: 152 en verde, `service.py` 100%, `app.py` 95% (solo `main()`).
- [ ] Autenticación + sesiones en BD → **aplazado a Sprint 2** con RBAC (no aporta sin
      Resolver/permisos).
- [ ] Docker compose + `univorch.sh` → infra de Fase 5; el demo se ejecuta hoy con
      `uv run univorch` (proceso in-process). Daemon + REST entran en Sprint 2.

### Qué queda fuera de Sprint 1

- Herencia en cascada completa (Resolver con imports y comodín `*`) → Sprint 2
- Web GUI (NiceGUI) → Sprint 2
- RBAC completo → Sprint 2
- Daemon + REST (FastAPI / uvicorn / httpx) → Sprint 2
- Conectores reales (VMware, Proxmox) → Sprint 3+
- `broken` + simulación de fallos del mock (M4) → cuando se necesite (Sprint 2)
- Capa docente (asignaturas/alumnos) → Sprint final
- Pools de IPs → Sprint posterior
- Gestión de usuarios vía web → Sprint posterior

### Demo para el profesor — flujo (Sprint 1)

Hoy se ejecuta con `uv run univorch` (en producción será `./univorch.sh cli`). Los
estados se ven en color (`□` dim · `■` default · `✗` rojo · `▲` amarillo) y las
carpetas en azul con `/` al final estilo `ls -F`. Tab autocompleta el path del fichero
en `apply`.

```
univorch /> apply demo/setup.yml
univorch /> tree /
univorch /> cd /lab/networks
univorch /lab/networks> list
univorch /lab/networks> deploy student01
univorch /lab/networks> status student01
univorch /lab/networks> start student01
univorch /lab/networks> stop student01
univorch /lab/networks> undeploy student01
univorch /lab/networks> quit
```

Ver `demo/README.md` para la guía completa del profesor.

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
| `apply <file>` | path al fichero YAML (Tab completa) | Crea/actualiza árbol desde documento |
| `list [path]` / `ls [path]` | ruta (default: CWD) | Lista **un nivel** (hijos directos) con glifos de estado |
| `tree [path]` | ruta (default: CWD) | Subárbol completo indentado |
| `deploy <path>` | ruta absoluta o relativa | Despliega una VM (clone en el hipervisor) |
| `undeploy <path>` | ruta absoluta o relativa | Elimina la VM (definición se conserva) |
| `start <path>` | ruta absoluta o relativa | Arranca (power on) una VM desplegada |
| `stop <path>` | ruta absoluta o relativa | Para (power off) una VM desplegada |
| `status <path>` | ruta absoluta o relativa | Estado de la VM + estado runtime del hipervisor |
| `cd [path]` | ruta absoluta/relativa (`..` permitido); sin arg = no-op | Cambia la carpeta de trabajo |
| `pwd` | — | Muestra la carpeta de trabajo actual |
| `help [cmd]` | — | Ayuda autogenerada por argparse, coloreada en TTY |

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
