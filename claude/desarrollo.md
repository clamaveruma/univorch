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
- [ ] `MockConnector` con `empty()`, `with_defaults()`, `with_templates()` y métodos de
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

El profesor ejecuta `./univorch.sh start`, abre un terminal y:

```bash
# 1. Ver la ayuda
univorch --help

# 2. Aplicar la definición de ejemplo (crea árbol de carpetas + descriptores)
univorch apply demo/setup.yml

# 3. Ver el árbol creado
univorch list /

# 4. Desplegar una VM (mock clona desde template)
univorch deploy /laboratorio/practica01/alumno01

# 5. Ver el estado — descriptor pasa a 'deployed'
univorch status /laboratorio/practica01/alumno01

# 6. Arrancar la VM
univorch start /laboratorio/practica01/alumno01

# 7. Ver estado runtime (deployed + running)
univorch status /laboratorio/practica01/alumno01

# 8. Parar
univorch stop /laboratorio/practica01/alumno01

# 9. Ver el árbol completo con estados
univorch list /laboratorio/
```

Los YAMLs de la `demo/` son el material didáctico: muestran la estructura declarativa, la herencia
(aunque simplificada en Sprint 1) y los comentarios preservados.

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
- Sin comentarios que expliquen *qué* hace el código — solo *por qué* cuando no es obvio
- Sin docstrings largos; una línea si hace falta

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

### Patrones clave a respetar
- El `OrchestratorService` es la única puerta de entrada — CLI y web no tocan repositorios ni
  conectores directamente (DEC-031)
- Los estados del descriptor solo cambian como resultado de un Job (DEC-032)
- Los Jobs se persisten en BD antes de ejecutarse (DEC-028)
- El MockConnector implementa el mismo ABC que los reales — nunca añadir lógica especial al
  service para el mock (DEC-029)

---

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
