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

- [ ] Acceso a VMs existentes (VMs no creadas por el orquestador)
- [ ] Listado y gestión de usuarios
- [ ] Checklist de fases de desarrollo
- [ ] Desarrollo en diferentes plataformas
- [ ] Directrices de código
- [ ] Snapshots de alumnos (almacenamiento, límites, comportamiento en undeploy)
- [ ] Futuras aplicaciones: otros modelos de vista de usuario, desacople aplicaciones/motor, módulo de migración de máquinas, módulos de supervisión, integración de Chat IA en web y REPL CLI
- [ ] Subir PDFs de referencia al repo
- [ ] Buscar documento con referencia a MongoDB
