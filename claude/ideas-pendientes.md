# Ideas pendientes de discusión

Banco de ideas del usuario para retomar cuando lleguemos a cada parte. No
implementar nada sin abrir conversación primero. Organizado por área; cuando
una idea se materialice, se mueve a `decisiones.md` con su DEC y, si toca,
queda traza en `diario.md`.

---

## 1. Web GUI (Sprint 4+)

### 1.1 Editor online del árbol — añadir nodos hoja con diálogos

Permitir crear/editar carpetas y descriptores directamente desde la web sin
escribir YAML. Idea: un diálogo por cada tipo de nodo (carpeta, descriptor,
hipervisor, plantilla…) con los campos del modelo. Al validar, se inserta
en el árbol vía el facade (`OrchestratorService.load` con un mini-documento,
o un comando nuevo dedicado).

Diseño a discutir cuando toque:
- ¿Cada diálogo monta un `DefinitionDocument` mínimo y llama a `load`, o
  hay un endpoint REST nuevo `POST /folders`, `POST /descriptors`?
- ¿Cómo se aprovecha el JSON Schema para autogenerar los campos del
  formulario? Hay librerías React/Vue que lo hacen.
- ¿Edición de un nodo existente o solo creación? La edición se podría
  hacer reusando `load` (re-cargar la definición con los cambios).

### 1.2 Visor del árbol con tres modos: local / expandida / resuelta

Switch en la barra superior. Cada nodo de carpeta o descriptor es
desplegable para ver sus definiciones. Modos:

- **Local**: lo escrito en ese nodo, nada heredado.
- **Expandida**: con `import:` aplicados pero sin seguir referencias.
- **Resuelta**: por defecto, todo resuelto (plantillas mezcladas,
  hipervisor encontrado por closure, etc.).

Esto es la versión web de `inspect <path>` con sus flags. Se aprovecha
el método del servicio que ya existe.

### 1.3 Diálogo de previsualización antes de cargar

Al subir un YAML, en vez de cargarlo directo, mostrar un diálogo con la
previsualización de qué se va a crear/modificar (parecido a `plan` de
Terraform). El usuario revisa y confirma. Encaja con DEC-027 (plan/diff).

### 1.4 Vista alternativa: hipervisores y máquinas

Otro modo de visualización que NO sigue el árbol de carpetas, sino que
escanea todo el árbol buscando `define hypervisors:` y construye una vista
"desde el hipervisor": cada hipervisor con sus VMs desplegadas, sus
plantillas (`base_vm`), datastores (cuando existan). Útil para el rol de
admin de infraestructura. La operacionalidad inversa a la vista de
carpetas, que es la educativa/organizativa.

---

## 2. Capa 2 — Aplicación de docencia

### 2.1 Arquitectura de despliegue de la capa 2

Varias aproximaciones a discutir:

- **(a) Módulo integrado en el mismo programa.** La capa 2 vive en
  `src/univorch/teaching/` y se carga junto al core. Pros: simple,
  comparte BD y servicio. Contras: el core lleva código que muchos
  desplegadores no necesitan.
- **(b) Otro programa en el mismo contenedor.** Proceso aparte, comparte
  el sistema de ficheros y la BD. Más limpio en separación; complica
  arranque y comunicación entre los dos.
- **(c) Extensión / add-in.** Paquete Python separado
  (`univorch-teaching`) que el usuario instala opcionalmente, registrado
  vía entry points. Coherente con cómo dejaremos los conectores. Pros:
  modularidad real. Contras: complejidad de empaquetado.
- **(d) Cliente externo del REST.** La capa 2 es **otro programa**
  cualquiera (Python, Node, lo que sea) que consume el REST del core.
  Cero acoplamiento. Pros: prueba la API pública, valida que el core es
  reusable. Contras: dos servicios a desplegar.

Tema relacionado: **¿API propia o integrada?** Si la capa 2 vive dentro
del contenedor, puede compartir el `/api/v1/` y añadir
`/api/v1/teaching/...`, o exponer un puerto distinto.

### 2.2 Marcadores en el árbol

Idea del usuario: una carpeta de asignatura lleva un marcador para que la
capa 2 sepa "esto es una asignatura"; cada carpeta de alumno lleva otro
marcador "esto es una mesa". A discutir cuando lleguemos:

- ¿Es un campo nuevo `kind: subject | desk | ...` en el `Folder`? ¿O un
  tag dentro de `description`? ¿O metadatos en un campo dedicado?
- Si es un campo, lo lee la capa 2 pero el core lo ignora. Coherente con
  DEC-004 (dos capas).
- Vocabulario: en el modelo interno hablamos de `folder`; en la capa 2
  hablamos de `subject` (asignatura), `desk` (mesa), `student` (alumno).
  Misma carpeta vista con dos lentes.

### 2.3 "Alumno genérico" como descriptor base — opinión inicial

El usuario presenta dos opciones para clonar el setup de cada alumno:
- (a) Plantilla declarada en la carpeta de asignatura.
- (b) Carpeta `alumno-generico/` con descriptores base; la capa 2 copia
  esa carpeta entera para cada alumno real.

**Mi opinión inicial** (a discutir más a fondo cuando toque):

**Las dos son válidas y son COMPLEMENTARIAS según el caso.**

- (a) plantilla cubre el caso "una VM por alumno". Lo tenemos hoy, sin
  añadir nada. Una asignatura con `define templates: alumno-mesa: {...}`
  y cada carpeta de alumno con `student01: { use template: alumno-mesa }`.
- (b) alumno genérico cubre el caso "N VMs por alumno". Una asignatura
  donde cada mesa tiene cliente + servidor + router: la carpeta
  `alumno-generico/` define los tres descriptores; la capa 2 clona la
  carpeta entera para `alumno01/`, `alumno02/`, etc.

Para el TFG bastaría con (a). La (b) requiere una operación nueva
"clonar subárbol con renombrado de paths", que tiene su miga pero es
valiosa intelectualmente — material para la memoria.

Voto: implementar (a) en la capa 2 v1, dejar (b) escrita en la memoria
del TFG como extensión natural.

---

## 3. Vocabulario YAML — pregunta abierta

El usuario nota: cada palabra reservada (`description`, `import`,
`define X:`, `use X:`, futuras) reduce el espacio de nombres legales para
carpetas y descriptores. Hoy:

- A nivel de raíz: `kind`, `version`.
- A nivel de folder: `description`, `import`, `define hypervisors`,
  `define templates`.

**¿Es problema? ¿Cambiar sintaxis?**

**Mi opinión inicial:**

En la práctica, **no es problema serio** por dos razones:
1. Las reservadas con espacios (`define hypervisors`) no chocan con los
   nombres legales de carpetas o descriptores (`_SEGMENT` exige
   `[A-Za-z0-9_-]+`, sin espacios). La única reservada que sí podría
   chocar es `description` (sin espacios).
2. El sufijo `/` ya desambigua carpetas de descriptores; las reservadas
   son siempre **propiedades del nodo**, no hijos.

**Si en el futuro la lista crece y hay conflictos reales**, las opciones:
- Cambiar a sintaxis con prefijo (`_define_hypervisors:`,
  `_description:`). Feo pero seguro.
- Anidar las propiedades del nodo en una sección:
  ```yaml
  lab/:
    _meta: { description: ..., import: [...] }
    _define: { hypervisors: {...}, templates: {...} }
    networks/: ...
    vm01: ...
  ```
  Más verboso pero deja claro dónde están las propiedades y dónde los
  hijos. Misma idea que `metadata:` + `spec:` de Kubernetes.

Voto: **dejar como está**. La lista de reservadas no va a crecer mucho
(quizá 6-8 totales). Si aparece un conflicto real con un nombre que el
usuario quiera, hay escape (renombrar). Tema para reabrir cuando
lleguemos a meter datastores e IP pools — ahí evaluamos si el modelo se
satura.

---

## 4. Memoria del TFG

### 4.1 Roles y permisos

En el TFG **solo se implementa el superusuario**. Pero el código y la
documentación dejan preparado el modelo de roles (DEC-011, DEC-021,
DEC-026) y los puntos de extensión:

- `SessionRepository` ya planificado en DEC-030 (no construido aún).
- RBAC centralizado en el facade (DEC-031).
- Resolver de permisos que reusa la cascada de definiciones (DEC-026:
  "permisos y definiciones son el mismo problema").
- Asignación de roles en la carpeta (DEC-021).
- Tres roles: superusuario, manager, end_user.

Sección dedicada en la memoria: "Modelo de seguridad — diseñado para
roles, implementado con superusuario en v1". Argumenta la decisión
(scope del PoC) y explica cómo se completaría sin tocar la arquitectura.

### 4.2 (Lugar para otras notas TFG cuando aparezcan)
