# UnivOrch — demostración para el tutor

> **AVISO IMPORTANTE.** Este documento describe una **demostración
> provisional** del estado del trabajo del TFG. **No es el TFG final**.
> El objetivo es que veas el modelo conceptual del orquestador
> funcionando con un conector simulado (mock), no presentar el producto
> terminado. Faltan piezas importantes que sí estarán en el TFG (en
> particular: conectores reales contra hipervisores VMware/Proxmox,
> autenticación y permisos efectivos, y una interfaz web completa con
> operaciones de escritura).

Tiempo estimado: 15 minutos.

---

## 1. Qué vas a ver

El sistema sin GUI, en modo cliente/servidor:

- Un "daemon" que corre dentro de un contenedor
  Docker, expone una API REST en `localhost:8080` y persiste el estado
  en un volumen.
- Un **cliente CLI** que habla con ese demonio por HTTP. Acepta dos
  modos: una orden suelta desde tu shell, o un REPL interactivo.
- **Ejemplos precargados en la imagen**: un laboratorio sencillo
  (`setup.yml`) y, para la aplicación de docencia, una asignatura con
  su escritorio de máquinas y una lista de alumnos
  (`teaching/`).

El conector hipervisor es un mock: no se crea nada real en disco, solo
se observa el modelo (herencia, ciclo de vida, dos ejes de estado).

Verás también la **aplicación de docencia** (la "capa 2") en acción:
cómo un profesor despliega una asignatura entera —una carpeta de
máquinas por alumno— con un par de comandos (sección 7).

---

## 2. Instalar

> **Aviso sobre `sudo`.** El instalador y el script `univorch.sh`
> hablan con Docker. Si tu usuario no pertenece al grupo `docker`,
> necesitas `sudo` delante de cada orden (es lo que asumen los
> ejemplos de este tutorial). Alternativa permanente:
> `sudo usermod -aG docker $USER` y cerrar/abrir sesión; a partir
> de ahí ya no hace falta `sudo` para nada de Docker.

Una sola orden:

```bash
curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/install.sh | sudo bash
```

Si quieres ver qué hace el instalador antes, sustituye `sudo bash` por
`less` al final.

El instalador deja un directorio `univorch/` con `univorch.sh` y
`docker-compose.yml`. No arranca nada por sí mismo. Si el puerto 8080
está ocupado en tu máquina, te pregunta interactivamente por otro y lo
fija en `.env`.

---

## 3. Arrancar y comprobar

```bash
cd univorch
sudo ./univorch.sh start
```

> **Importante: el puerto.** El instalador usa el **8080** por defecto,
> pero si ese puerto estaba ocupado en tu máquina te habrá pedido otro
> (típicamente **9090**). El mensaje de arranque te muestra las URLs
> exactas con **tu** puerto — úsalas. En los ejemplos de abajo aparece
> `8080`; si tú usas otro, sustitúyelo. (Si pruebas el `8080` y ves una
> respuesta HTML rara de "Temporary Redirect", es otro servicio tuyo
> ocupando ese puerto, no UnivOrch.)

Comprueba que responde (ajusta el puerto al tuyo):

```bash
curl http://localhost:8080/api/v1/health
```

Debe devolver `{"status":"ok"}`.

Para verlo de forma más visual, abre el navegador en cualquiera de
estas páginas (de nuevo, con tu puerto):

- `http://localhost:8080/` — **Web GUI** (lectura): cabecera con
  contadores y árbol de descriptores navegable. Click en un descriptor
  abre el detalle con su definición efectiva.
- `http://localhost:8080/docs` — **Swagger UI** (autogenerada por
  FastAPI): API entera explorable, con botones para probar cada endpoint
  sin escribir `curl`.
- `http://localhost:8080/redoc` — **ReDoc**: misma información en
  formato más narrativo, útil para leer la especificación de un vistazo.

---

## 4. Dos formas de hablar con el sistema

**Orden suelta** (modo bash, se ejecuta y vuelve a tu shell):

```bash
sudo ./univorch.sh cli tree /
sudo ./univorch.sh cli load /opt/univorch/examples/setup.yml
sudo ./univorch.sh cli inspect /lab/networks/student03
```

**Sesión interactiva** (REPL, con historial y autocompletado de Tab):

```bash
sudo ./univorch.sh cli
```

Te abre el prompt:

```
univorch />
```

Y dentro escribes las mismas órdenes sin el `./univorch.sh cli` por
delante. Se sale con `quit` o Ctrl-D.

Los ejemplos siguientes usan el REPL por brevedad, pero todo lo mismo
funciona desde la línea de comandos directa.

---

## 5. Cargar el ejemplo y recorrer el árbol

El ejemplo viene dentro de la imagen, en `/opt/univorch/examples/`.

```
univorch /> load /opt/univorch/examples/setup.yml
/lab                       folder /lab created
/lab/networks              folder /lab/networks created
/lab/networks/student01    descriptor /lab/networks/student01 created
/lab/networks/student02    descriptor /lab/networks/student02 created
/lab/networks/student03    descriptor /lab/networks/student03 created
```

```
univorch /> tree /
  lab/
    networks/
    □ student01
    □ student02
    □ student03
```

Símbolos: `□` provisionado · `■` desplegado · `✗` roto · `▲` inalcanzable.

La pieza interesante del modelo es la **herencia en cascada**.
Inspecciona la definición efectiva del tercer alumno:

```
univorch /> inspect /lab/networks/student03
/lab/networks/student03   (descriptor)
  description:       Standard student Linux workstation
  use hypervisor:    mock01
  base_vm:           linux-base
  use template:      linux-vm
  cpu:               4
  memory_mb:         2048
  disk_gb:           20
  state:             provisioned
```

El descriptor de `student03` **solo** dice `use template: linux-vm` y
`cpu: 4` (sobreescritura local de un campo). Todo lo demás —
`description`, `base_vm`, `memory_mb`, `disk_gb`, y el hipervisor
`mock01` — viene heredado de la plantilla declarada arriba, en `/lab`.
La referencia al hipervisor se resuelve en el **entorno léxico de la
plantilla** (en inglés "closure"), no en el del alumno: por eso
`/lab/networks` no necesita importar `mock01` explícitamente, solo la
plantilla que ya lo usa.

Para comparar, mira la definición **local** del mismo descriptor (lo
que realmente está escrito en el árbol):

```
univorch /> inspect --local /lab/networks/student03
```

Verás solo las dos líneas (`use template:` y `cpu: 4`).

---

## 6. Ciclo de vida de una VM

Dos ejes de estado en juego:

- **`state`** del descriptor (lado del orquestador): provisionado →
  desplegado → de vuelta a provisionado.
- **`runtime`** de la VM (lado del hipervisor): parado/encendido/
  pausado.

Cambia primero a la carpeta de los alumnos para no escribir el path
absoluto en cada orden — el cliente acepta paths relativos al cwd igual
que una shell de Linux:

```
univorch /> cd /lab/networks
univorch /lab/networks/> deploy student01
deployed as mock-vm-1

univorch /lab/networks/> status student01
/lab/networks/student01  state=deployed  runtime=stopped  vm_id=mock-vm-1

univorch /lab/networks/> start student01
started

univorch /lab/networks/> status student01
/lab/networks/student01  state=deployed  runtime=running  vm_id=mock-vm-1

univorch /lab/networks/> stop student01
stopped

univorch /lab/networks/> undeploy student01
undeployed

univorch /lab/networks/> status student01
/lab/networks/student01  state=provisioned  runtime=-  vm_id=-
```

Observa que `start`/`stop` no tocan el `state` del descriptor: solo el
runtime de la VM. Por contra, `deploy`/`undeploy` sí cambian el `state`
(crean o destruyen la VM en el hipervisor).

---

## 7. La aplicación de docencia

Hasta aquí has manejado el **motor genérico**: carpetas y descriptores
de VM, sin saber nada de asignaturas ni alumnos. Encima de ese motor
hay una **aplicación de docencia** (la "capa 2"): un grupo de
subcomandos `teach` que hablan el vocabulario del profesor —
asignatura, escritorio (*desktop*), alumno— y traducen ese vocabulario
a operaciones del motor. El motor no sabe nada de docencia; la
aplicación es un cliente más que construye y carga definiciones.

La idea es esta: el profesor describe **una** vez cómo es el conjunto
de máquinas de un alumno (el *desktop* de la asignatura), da una lista
de alumnos, y la aplicación genera toda la infraestructura: una carpeta
por alumno con sus máquinas dentro.

El contenedor trae dos ficheros de ejemplo en
`/opt/univorch/examples/teaching/`:

- `subject-redes.yml` — una asignatura "Redes" cuyo desktop son **seis**
  máquinas: workstation, server, router, firewall, switch y client.
- `students-redes.yml` — una lista de **diez** alumnos (el último es un
  email, para mostrar que un nombre de usuario puede ser un email).

### 7.1 Cargar la asignatura

```
univorch /> teach load-subject /opt/univorch/examples/teaching/subject-redes.yml /
/redes-2026  folder /redes-2026 created
```

`teach load-subject` primero **valida** que el fichero sea una
asignatura bien formada (que esté marcada como tal, que tenga un desktop
no vacío, que cada máquina del desktop sea una plantilla resoluble, que
no traiga carpetas sueltas). Si algo falla, no carga nada y te dice por
qué. Si pasa, la carga como una rama normal del árbol.

Mira la asignatura cargada:

```
univorch /> inspect /redes-2026
/redes-2026/   (folder)
  description:               Computer Networks — Fall 2026
  metadata:
    kind:                    subject
    desktop:                 ['workstation', 'server', 'router', 'firewall', 'switch', 'client']
  define templates:
    workstation: ...
    server:      ...
    ... (las seis plantillas)
```

El bloque `metadata` (`kind: subject` y el `desktop`) es lo que el motor
guarda pero **no interpreta** — solo lo lee la aplicación docente. Las
seis plantillas del desktop están definidas abajo, cada una con sus
recursos (CPU, memoria...).

### 7.2 Cargar la lista de alumnos

Un solo comando genera toda la infraestructura. Con 10 alumnos y un
desktop de 6 máquinas, son 10 carpetas + 60 descriptores:

```
univorch /> teach load-students /opt/univorch/examples/teaching/students-redes.yml /redes-2026
/redes-2026/alumno01  folder /redes-2026/alumno01 created
/redes-2026/alumno01/workstation  descriptor ... created
/redes-2026/alumno01/server  descriptor ... created
... (seis por alumno)
/redes-2026/alumno02  ...
...
/redes-2026/juan.perez@uma.es/...  ...
```

> El orden de los argumentos es como en `load`: primero el fichero,
> después la carpeta destino (la asignatura). Si entras en la asignatura
> con `cd /redes-2026`, puedes omitir el destino y escribir solo
> `teach load-students <fichero>`.

Recorre el resultado:

```
univorch /> tree /redes-2026
  alumno01/
    □ client
    □ firewall
    □ router
    □ server
    □ switch
    □ workstation
  alumno02/
    □ client
    ...
  juan.perez@uma.es/
    □ client
    ...
```

Diez alumnos, seis máquinas cada uno, todas en estado `provisioned`
(□): definidas pero todavía sin VM creada en el hipervisor. Fíjate en
el último alumno, `juan.perez@uma.es`: un email como nombre de usuario
se trata igual que cualquier otro.

### 7.3 La herencia en acción

Cada máquina de cada alumno es **minúscula** en el árbol: la aplicación
solo le puso una referencia a su plantilla. Compruébalo con el modo
`--local` (lo que está escrito en el nodo):

```
univorch /> inspect --local /redes-2026/alumno01/router
/redes-2026/alumno01/router   (descriptor)
  use template:      router
  state:             provisioned
```

Solo una línea de definición. Ahora sin `--local` (la definición
**efectiva**, resuelta por herencia):

```
univorch /> inspect /redes-2026/alumno01/router
/redes-2026/alumno01/router   (descriptor)
  use hypervisor:    mock01
  base_vm:           linux-base
  cpu:               1
  memory_mb:         1024
  state:             provisioned
  (resolved from template: router)
```

Todos los campos (hipervisor, base_vm, CPU, memoria) los ha **heredado**
de la plantilla `router`, que está definida una sola vez en la
asignatura. La nota `(resolved from template: router)` indica de dónde
vienen. El profesor define las máquinas una vez; los 60 descriptores las
heredan sin repetir nada.

### 7.4 Desplegar una máquina del alumno

El despliegue es una operación del motor, igual que antes. Despliega,
por ejemplo, el router del alumno con email:

```
univorch /> deploy /redes-2026/juan.perez@uma.es/router
deployed as mock-vm-1
```

El motor resuelve la plantilla `router` por herencia, encuentra el
hipervisor `mock01` (también heredado de la asignatura) y crea la VM.

### 7.5 Exportar la lista de alumnos

`teach save-students` hace lo inverso de `load-students` a nivel de
lista: lee las carpetas de alumno y devuelve el fichero de lista,
reutilizable el curso siguiente:

```
univorch /> teach save-students /redes-2026
kind: student-list
version: "1"
students:
  - alumno01
  - alumno02
  ...
  - juan.perez@uma.es
```

### Qué falta en la aplicación docente

Esta es una primera versión. Quedan, documentados como trabajo futuro:
despliegue de la asignatura entera en un comando (hoy se despliega
máquina a máquina o rama a rama); baja de alumnos (quitar a quien ya no
está en la lista, con aviso); envío de correos a los alumnos; interfaz
web docente; y el control de permisos efectivo (que el profesor solo vea
sus asignaturas).

---

## 8. Apagar

```
univorch /> quit
```

```bash
sudo ./univorch.sh stop
```

Los datos persisten en el volumen `univorch_univorch_data`. Para
empezar de cero, `sudo docker volume rm univorch_univorch_data` antes
del siguiente `start`.

Para **borrar todo** (contenedor, volumen con la base de datos, imagen
y directorio local), el instalador deja un `uninstall.sh` listo en el
mismo directorio:

```bash
sudo ./uninstall.sh
```

Te pide confirmación una sola vez. Si quieres conservar la base de
datos o la imagen entre desinstalaciones, añade `--keep-data` o
`--keep-image` (o ambos). Equivalente si ya borraste el directorio a
mano:

```bash
curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/uninstall.sh | sudo bash -s -- --yes
```

---

## 9. Si algo falla

| Síntoma | Causa habitual y arreglo |
|---|---|
| `permission denied to /var/run/docker.sock` | Tu usuario no está en el grupo `docker`. Añade `sudo` (rápido) o `sudo usermod -aG docker $USER` + relogin (permanente). |
| `address already in use` al arrancar | Otro servicio ocupa el 8080. `UNIVORCH_PORT=9090 sudo ./univorch.sh start` o ajusta `.env`. |
| `cannot reach the UnivOrch daemon` | El contenedor no está corriendo. `sudo ./univorch.sh start`. |
| Logs del demonio | `sudo ./univorch.sh logs` |

---

## 10. Referencia rápida

**Desde el host:**

Todas las órdenes asumen `sudo` delante si tu usuario no está en el
grupo `docker`.

| Orden | Hace |
|---|---|
| `sudo ./univorch.sh start` / `stop` / `restart` | Ciclo de vida del contenedor |
| `sudo ./univorch.sh status` | Estado del contenedor |
| `sudo ./univorch.sh logs` | Sigue los registros |
| `sudo ./univorch.sh cli [orden]` | Cliente: REPL si no hay orden, modo bash si la hay |

**Órdenes del cliente** (con `help <orden>` ves la ayuda detallada de cada
una):

```
load <fichero>       carga un YAML en el árbol
tree [ruta]          subárbol completo
ls   [ruta]          un solo nivel
cd   [ruta]          cambia la carpeta de trabajo (REPL)
inspect <ruta>       definición efectiva (con --local: solo local)
deploy <ruta>        despliega una VM
start <ruta>         enciende
stop <ruta>          apaga
undeploy <ruta>      retira la VM (mantiene la definición)
status <ruta>        estado del descriptor + runtime
connect <url>        cambia el destino del cliente en caliente (REPL)
```

**API REST**: `http://localhost:8080/api/v1/`. La documentación
interactiva (Swagger UI) está en `http://localhost:8080/docs` cuando el
servicio corre. Permite probar todos los puntos de acceso desde el
navegador.

---

## 11. Alcance del TFG

Lo que has probado hoy es el PoC con un conector simulado. Ya incluye
el motor de orquestación (secciones 5-6), una interfaz web de lectura
(sección 3) y una primera versión de la aplicación de docencia
(sección 7). El TFG, que sigue siendo una prueba de concepto, lo
completa con:

1. **Conectores reales** — VMware (vSphere) y Proxmox sobre el mismo
   contrato abstracto que ya cumple el mock. Pendiente de acceso a los
   hipervisores del aulario.

2. **Interfaz web con operaciones de escritura** — sobre la base de
   lectura que ya tienes. Crear y editar nodos por diálogo, desplegar
   desde la web, y la vista de "mesa" para el alumno.

3. **Más de la aplicación docente** — la base ya está (cargar
   asignatura y alumnos, sección 7). Faltan el despliegue de la
   asignatura entera en un comando, la baja de alumnos y los avisos por
   correo.

### Después del TFG

El proyecto queda planteado como una prueba de concepto. Muchas piezas
quedan diseñadas pero no implementadas, para iteraciones posteriores
del trabajo:

- Control de usuarios, autenticación y permisos (RBAC).
- Web más completa y cuidada (acciones, edición avanzada, dashboards).
- Integración con sistemas de gestión de direcciones IP (IPAM).
- Gestión de snapshots de VMs.
- Modelado de datastores como recurso heredable.
- Conectores adicionales (Hyper-V, KVM, plataformas cloud).
- Alta disponibilidad del servicio (activo-pasivo, MongoDB en sustitución
  de TinyDB).
- Despliegue desde repositorios git (GitOps).

---

## 12. Vista previa del rediseño de la interfaz web (bocetos)

Para que veas a dónde queremos llegar con la web, hay dos **bocetos
visuales** del rediseño completo. Son páginas HTML autocontenidas
(Vue + Quasar por CDN) **desconectadas del orquestador**: muestran
datos de ejemplo embebidos y no llaman al daemon. Sirven para hacerse
una idea de la dirección visual y de la interacción esperada; la
versión final, conectada a la API real, se parecerá a esto.

- **Vista del administrador / profesor** (árbol de descriptores con
  filtro, panel de detalle por nodo, badges para plantillas e
  hipervisores, acciones contextuales por estado):
  [admin-standalone.html](https://raw.githack.com/clamaveruma/univorch/main/demo/ui_kits/admin-standalone.html)

- **Vista del alumno** (la metáfora "mesa con ordenadores" — las VMs
  aparecen como iconos de PC sobre una mesa, con iconos SVG por
  estado y acciones por VM):
  [user-standalone.html](https://raw.githack.com/clamaveruma/univorch/main/demo/ui_kits/user-standalone.html)

> Como son páginas estáticas, los botones no producen efecto: están
> ahí solo para mostrar la disposición y la iconografía. Lo que sí
> funciona es el "click" en un nodo del árbol para que cambie el
> panel de detalle a la derecha.

El historial completo, las decisiones de diseño y el código fuente
están en [github.com/clamaveruma/univorch](https://github.com/clamaveruma/univorch).
