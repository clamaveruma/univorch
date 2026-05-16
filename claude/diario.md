# Diario del proyecto

---

## 2026-05-16

### Inicio del proyecto

- Se crea el repositorio `clamaveruma/orch_pru` en GitHub
- Se define la estructura de memoria persistente basada en ficheros Markdown
- Se establece el uso de `CLAUDE.md` como punto de entrada con imports a ficheros especializados

### Decisiones tomadas

- **Formato de memoria:** Markdown (`.md`) para todos los ficheros de contexto
- **Estructura de directorios:** ficheros de contexto en `claude/`, documentación en `docs/`, `CLAUDE.md` en raíz
- **Diario como fuente principal:** `claude/diario.md` es la referencia cronológica; se actualiza cuando hay algo relevante que registrar, no solo en commits
- **Commits automáticos:** Claude hace commit al terminar cada bloque de trabajo, sin pedir confirmación; informa en el chat
- **Estilo de trabajo:** colaborativo — proponer, aclarar, confirmar, ejecutar. Sin sorpresas en decisiones de diseño
- **Sin complacencia:** Claude debe ser crítico y objetivo, ofrecer alternativas

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

- TFG de Ingeniería de Computadores
- Prueba de concepto de orquestador universal de VMs para entornos docentes y de investigación
- Desarrollo asistido por IA
- El autor tiene base técnica sólida pero menos experiencia en desarrollo software → se usarán herramientas modernas pero sin sobresofisticar

### Estado al cierre de bloque

- Estructura de repositorio creada
- Plan de proyecto documentado en `docs/plan.md`
- Stack tecnológico y arquitectura pendientes de definir
- Pendiente: subir ficheros de referencia con ideas del proyecto
