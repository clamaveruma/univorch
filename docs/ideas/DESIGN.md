# Orquestador de Máquinas Virtuales — Documento de Diseño
> Estado: trabajo en curso. Diseño conceptual de alto nivel, no de implementación.

---

## 1. Problema

En la escuela de informática se gestionan conjuntos de máquinas virtuales (VM) para prácticas de alumnos. Actualmente el administrador realiza manualmente el despliegue, recreación y gestión de cientos de VMs, con scripts ad hoc ligados a VMWare.

**Problemas principales:**
- Carga excesiva del administrador (despliegue, recreaciones, altas de alumnos tardías)
- Alumnos sin autonomía: no pueden arrancar, parar, ni restaurar sus propias VMs
- Scripts acoplados a un hipervisor concreto; cualquier cambio de plataforma los invalida
- Sin interfaz para usuarios no técnicos

**Necesidades funcionales a preservar en el diseño:**
- El alumno puede arrancar, parar, pausar, hacer snapshot y recrear sus VMs desde plantilla
- El profesor define las VMs de la asignatura; el sistema las replica por alumno
- Interfaz web intuitiva para perfiles no técnicos
- Abstracción del tipo de hipervisor (VMWare, Proxmox, otros)
- Soporte de múltiples hipervisores simultáneos, incluso de tipos distintos
- El orquestador no debe afectar al funcionamiento normal de los hipervisores existentes

---

## 2. Filosofía de diseño

### 2.1 Dos capas, no una

El sistema se divide en dos capas independientes:

**Capa 1 — Orquestador general (núcleo)**
Gestiona nodos en un árbol. No conoce conceptos de asignatura, alumno o cuaderno. Solo conoce carpetas, nodos de distintos tipos, definiciones heredadas en cascada y un bucle de reconciliación. Es reutilizable para cualquier contexto: universidad, empresa, laboratorio de investigación.

**Capa 2 — Aplicación de docencia**
Se construye sobre el orquestador. Interpreta ciertas ramas del árbol como asignaturas, ciertas carpetas como mesas de alumno, ciertos nodos como cuadernos editables. Presenta al usuario la metáfora de "mesa" y "biblioteca". En el futuro podrán existir otras aplicaciones sobre el mismo núcleo para otros contextos.

Esta separación permite que el administrador vea el árbol crudo si lo necesita, mientras el alumno solo ve su biblioteca de mesas — ambas vistas son proyecciones consistentes de la misma estructura subyacente.

### 2.2 Arquitectura declarativa (estilo GitOps)

El sistema es **declarativo**: el manager no da órdenes imperativas, sino que describe el estado deseado en un manifiesto. Un bucle de reconciliación compara el estado deseado con el estado real y aplica los cambios necesarios de forma autónoma.

Contraste:
- **Imperativo:** "crea esta VM, arráncala, añade memoria". Cada acción es un comando.
- **Declarativo:** "estas VMs deben existir con estas características". El sistema se encarga.

**La verdad está en el manifiesto**, no en los hipervisores. Los hipervisores están "obligados" a parecerse al manifiesto.

---

## 3. Modelo mental del usuario

### Roles

| Rol | Equivalente | Acceso |
|---|---|---|
| Superusuario | Administrador IT | Árbol completo, gestión de hipervisores y plantillas base |
| Manager | Profesor | Sus ramas del árbol; crea asignaturas y mesas |
| Usuario final | Alumno | Solo sus mesas asignadas |

### La biblioteca del alumno

El alumno abre la aplicación y ve **su biblioteca**: una colección de **mesas**, una por cada asignatura en la que está matriculado. No navega un árbol global; solo ve lo suyo.

### La mesa

Cada mesa es el espacio de trabajo personal del alumno para una asignatura. Contiene:
- **Las VMs** asignadas por el profesor (desplegadas o en estado provisionado)
- **Un cuaderno** con texto e instrucciones del profesor, y las anotaciones propias del alumno

La mesa es, internamente, una carpeta del árbol. El alumno ve "mi mesa de Redes"; el administrador ve `/asignaturas/redes/alumno-pepito/`. Son la misma cosa vista desde dos perspectivas.

### El cuaderno

El cuaderno es un **nodo de tipo cuaderno** dentro de la carpeta-mesa. Hereda del cuaderno de la asignatura (donde el profesor escribe el contenido general) y puede tener anotaciones personales del alumno. No es un elemento externo al árbol: es un nodo más, con su propio tipo y sus propias reglas de herencia.

Contiene texto narrativo del profesor y **bloques de VM** intercalados: no son simples enlaces sino widgets vivos que muestran el estado de la VM y permiten operarla (encender, apagar, snapshot, rollback, recrear) desde el propio cuaderno.

---

## 4. El árbol de nodos

### Tipos de nodo

El árbol contiene nodos de distintos tipos. Todos heredan propiedades en cascada desde la carpeta padre.

| Tipo | Descripción |
|---|---|
| Carpeta | Nodo contenedor. Tiene una definición común heredable |
| VM | Representa una máquina virtual (desplegada o provisionada) |
| Cuaderno | Documento editable con texto y bloques VM |
| Plantilla | Definición reutilizable de una VM base |
| (Otros por definir) | Extensible para futuras aplicaciones |

> Nota: el término "descriptor" de propuestas anteriores no se adopta aquí para evitar confusión. Los elementos del árbol son "nodos" de distintos tipos.

### Herencia en cascada

Cada carpeta tiene una **definición común**. La definición efectiva de un nodo es la combinación recursiva de las definiciones de sus carpetas padre, sobrescrita por la definición local. Esto permite:

- Definir el hipervisor una sola vez a nivel de asignatura y que todas las VMs lo hereden
- Definir la plantilla base a nivel de asignatura y que el profesor no necesite repetirla
- Propagar permisos y roles por niveles del árbol

### Estados de una VM

```
Provisionado → Desplegado (creado, parado) → Arrancando → En ejecución
                     ↑                                          ↓
                 Recrear                                   Parado / Pausado
```

El estado **provisionado** es clave: la VM está definida en el árbol pero no existe en el hipervisor. Permite tener toda la infraestructura de una asignatura declarada antes de que los alumnos la necesiten.

---

## 5. Modelo declarativo: el manifiesto del profesor

### Estructura (borrador, sintaxis no definitiva)

```yaml
asignatura: redes-2026
profesor: prof.jimenez

plantillas:
  - nombre: linux-router
    base: debian-12
    hipervisor: vmware-aulario
    cpu: 2
    ram: 2GB
  - nombre: linux-cliente
    base: debian-12
    cpu: 1
    ram: 1GB

mesas-por-alumno:
  - linux-router
  - linux-cliente
  - linux-cliente

alumnos: !import alumnos-redes-2026.csv
```

El sistema deriva: si hay 30 alumnos, crea 30 carpetas-mesa, cada una con sus nodos VM en estado provisionado.

### Cómo se aplica un cambio

| Patrón | Descripción |
|---|---|
| Reemplazo completo | Se sube el manifiesto entero; el sistema calcula el diff y aplica |
| Edición en la web | El profesor edita campos en un formulario; el sistema serializa y reconcilia |
| (Futuro) Enlace a Git | El manifiesto vive en un repo; el sistema se sincroniza automáticamente |

Para v1 se recomienda **subida directa + edición web**. La opción Git se reserva como modo avanzado.

### Reglas de reconciliación

| Cambio en el manifiesto | Acción del reconciliador |
|---|---|
| Nueva VM añadida | Se crea en provisionado en todas las mesas. Inocuo. |
| VM eliminada | Se destruye si está provisionada; aviso y ventana de tiempo si está desplegada. |
| Cambio de parámetros de una VM desplegada | Se registra; se aplica en la próxima recreación. La VM se marca como "obsoleta respecto al manifiesto". |
| Cambio de texto del cuaderno | Propagación inmediata. No toca infraestructura. |
| Nuevo alumno añadido | Se crea su mesa en provisionado. Inocuo. |
| Alumno eliminado | Se destruye su mesa (v1: sin archivo). |

**Heurística general:** lo que es texto y definición se propaga inmediatamente; lo que tocaría máquinas vivas espera a la próxima recreación voluntaria del alumno.

### Separación de verdades

| Capa | Quién la controla | Cuándo cambia |
|---|---|---|
| Estado declarado | Profesor vía manifiesto | Cuando el profesor edita y aplica |
| Estado de despliegue de la VM | Alumno (arrancar, parar, recrear) | Interacción imperativa del alumno |
| Contenido interno de la VM | Alumno (dentro del SO) | Opaco al orquestador; preservado por snapshots |
| Anotaciones personales | Alumno | En cualquier momento |

El reconciliador solo actúa sobre la primera capa. Nunca toca el contenido interno de las VMs ni las anotaciones del alumno.

---

## 6. Hipervisores

El orquestador se comunica con los hipervisores mediante **conectores** (drivers). Cada conector adapta las operaciones genéricas (clonar, arrancar, parar, snapshot, borrar) a la API específica de cada tipo de hipervisor.

**Principio de no invasión:** los hipervisores siguen funcionando con normalidad. El orquestador es una capa adicional; si cae o no se usa, los hipervisores no se ven afectados.

Los conectores previstos inicialmente: VMWare (ESX), Proxmox. La arquitectura permite añadir otros en el futuro.

---

## 7. Decisiones pendientes

Las siguientes decisiones están abiertas y requieren más discusión:

1. **Formato de entrada del manifiesto para el profesor:** ¿editor web con formularios, o fichero YAML que el profesor edita externamente? Determina si hay un editor visual desde v1.

2. **Granularidad del manifiesto:** ¿un único fichero por asignatura, o múltiples manifiestos pequeños (uno por plantilla, uno por cuaderno, etc.) que el sistema compone?

3. **¿Qué pasa con los snapshots del alumno cuando se elimina una VM del manifiesto?** Decisión de política: borrar todo (v1 simple) o archivar.

4. **Anotaciones en v1:** ¿se implementan desde el principio o se deja el cuaderno como texto heredado del profesor, sin anotaciones propias del alumno en v1?

5. **Gestión de IPs:** se ha considerado integrar un IPAM o continuar con el truco de codificar IP en MAC. Pendiente de decisión para fases posteriores.

6. **Alta disponibilidad:** se quiere en el futuro pero no en v1. El modelo de almacenamiento del árbol debe tenerse en cuenta para no bloquear esta opción.

---

## 8. Fuera de alcance (por ahora)

- Diseño de implementación (qué librerías Python usar)
- Gestión de IPs / IPAM
- Alta disponibilidad / clustering
- Autenticación avanzada (OAuth2, LDAP)
- Cuotas de recursos
- Aplicaciones sobre el orquestador distintas a la de docencia
