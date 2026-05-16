# Diario del proyecto

---

## 2026-05-16

### Inicio del proyecto

- Se crea el repositorio `clamaveruma/orch_pru` en GitHub
- Se define la estructura de memoria persistente basada en ficheros Markdown
- Se establece el uso de `CLAUDE.md` como punto de entrada con imports y reglas

### Decisiones tomadas

- **Formato de memoria:** Markdown (`.md`) para todos los ficheros de contexto
- **Estructura de directorios:** `claude/` para memoria interna, `docs/` para documentación técnica, `CLAUDE.md` en raíz
- **Diario:** se actualiza cuando hay algo relevante, no solo en commits; Claude avisa escuetamente cuando lo hace
- **Commits automáticos:** sin pedir confirmación; Claude informa en el chat
- **Estilo de trabajo:** colaborativo — proponer, aclarar, confirmar, ejecutar. Sin sorpresas en decisiones de diseño
- **Sin complacencia:** Claude debe ser crítico y objetivo, ofrecer alternativas
- **Idiomas:** chat en español; código, docs técnicos (`docs/`) y memoria del TFG en inglés; ficheros internos (`claude/`) en español
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

El alcance de la Fase 6 se decide sprint a sprint según tiempo disponible.

### Contexto del proyecto

- **Alumno:** Claudio María Martínez Velasco — Ingeniería de Computadores, Universidad de Málaga
- **Tutor:** Guillermo Pérez Trabado, Dpto. Arquitectura de Computadores
- **Título:** Un orquestador de máquinas virtuales para entornos docentes y de investigación. Prueba de concepto
- **Base de partida:** librerías Python del tutor — `esxobjects` (interfaz VMware) y `yamlinfr` (despliegue desde YAML)
- **Horas totales del TFG:** 296h distribuidas en 9 fases según anteproyecto
- Desarrollo asistido por IA (Claude Code)
- El autor tiene base técnica sólida pero menos experiencia en desarrollo software → herramientas modernas pero sin sobresofisticar

### Documentos de referencia cargados en `docs/ideas/`

- `DESIGN.md` — diseño conceptual detallado: árbol de nodos, arquitectura declarativa estilo GitOps, metáfora de mesa/biblioteca para el alumno, manifiesto YAML del profesor, bucle de reconciliación
- `Ideas_orquestador.odt` — ideas técnicas: VM Descriptor, máquina de estados, definiciones heredadas en cascada, parámetros de creación vs ejecución, roles, stack propuesto
- `Necesidad.odt` — contexto del problema real: escuela de informática, VMware, scripts manuales, IPs en MAC, carga del administrador
- `ideas-raw.md` — ideas sobre mensajería pub/sub, MCP, Android (contexto personal, relevancia indirecta al TFG)
- `Anteproyecto_Claudio_Mar-2026-Revisado.docx` — documento oficial del TFG con objetivos, fases, temporización y stack confirmado

### Pendiente para próxima sesión

- Analizar todos los documentos e identificar qué ideas aplican a cada fase
- Subir PDFs de referencia al repo (versiones legibles de los ODT/DOCX)
- Iniciar Fase 1: definición formal del problema
