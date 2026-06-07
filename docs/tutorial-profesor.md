# UnivOrch — Tutorial de instalación y demo

> Prueba de concepto de un orquestador universal de máquinas virtuales,
> desarrollado como Trabajo Fin de Grado de Ingeniería de Computadores
> (Universidad de Málaga, 2025–2026). Autor: Claudio M. Martínez Velasco.
> Tutor: Guillermo Pérez Trabado.

Este documento guía paso a paso la instalación y la prueba del sistema con
el conector mock (sin hipervisor real). Tiempo estimado: **10 minutos**.

---

## 1. ¿Qué vas a probar?

UnivOrch es una capa de abstracción que gestiona máquinas virtuales de forma
agnóstica al hipervisor. En esta versión de demostración, el hipervisor es
un **mock** que simula VMs en memoria — no se crea nada real en disco.
Sirve para inspeccionar el modelo conceptual del sistema (árbol de
recursos, herencia, ciclo de vida) sin necesidad de un VMware o un Proxmox
detrás.

Al terminar el tutorial habrás:

- Arrancado el servicio en un contenedor Docker.
- Cargado un árbol de ejemplo con un laboratorio docente.
- Desplegado, arrancado, parado y retirado una VM.
- Visto cómo la herencia en cascada y las plantillas estructuran el modelo.

---

## 2. Requisitos

- **Linux, macOS o Windows con WSL2.**
- **Docker** instalado y funcionando. Verificación rápida:
  ```bash
  docker --version
  docker compose version
  ```
- **Permiso para usar Docker**: o estás en el grupo `docker`, o vas a
  llevar `sudo` por delante en cada orden del demonio (en inglés "daemon").
- **Conexión a internet** la primera vez (para descargar la imagen).

---

## 3. Instalación

Copia y pega en tu terminal:

```bash
curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/install.sh | bash
```

Esto descarga e ejecuta el instalador, que:

1. Comprueba que tienes Docker.
2. Detecta si el puerto 8080 está libre; si no, te pregunta por otro.
3. Crea un directorio `univorch/` en tu carpeta actual con dos ficheros:
   - `univorch.sh` — script que envuelve `docker compose` con órdenes cortas.
   - `docker-compose.yml` — receta del contenedor.
4. **No** arranca el servicio: eso lo decides tú en el siguiente paso.

Al terminar te muestra los próximos comandos.

### Si te falta confianza con `curl | bash`

Es válido. Puedes ver el script antes de ejecutarlo:

```bash
curl -sSL https://raw.githubusercontent.com/clamaveruma/univorch/main/install.sh | less
```

Cuando confirmes que el contenido te parece razonable, vuelve a lanzarlo
con `| bash` al final.

---

## 4. Arrancar el servicio

```bash
cd univorch
./univorch.sh start
```

La primera vez Docker descarga la imagen (~100 MB, 30–60 segundos
dependiendo de tu conexión). En arranques posteriores levanta el
contenedor en uno o dos segundos.

Al terminar verás:

```
UnivOrch started.
REST API:   http://localhost:8080/api/v1/
Health:     http://localhost:8080/api/v1/health
Interactive CLI: ./univorch.sh cli
```

(Si el instalador eligió otro puerto, aparecerá ese.)

Comprueba que el servicio responde:

```bash
curl http://localhost:8080/api/v1/health
```

Debe devolver `{"status":"ok"}`.

---

## 5. Entrar al cliente y cargar el ejemplo

```bash
./univorch.sh cli
```

Esto te abre el REPL (intérprete interactivo) **dentro del contenedor**.
Verás el prompt:

```
univorch />
```

El ejemplo precargado vive en `/opt/univorch/examples/setup.yml`. Cárgalo:

```
univorch /> load /opt/univorch/examples/setup.yml
```

Verás líneas como:

```
/lab                       folder /lab created
/lab/networks              folder /lab/networks created
/lab/networks/student01    descriptor /lab/networks/student01 created
/lab/networks/student02    descriptor /lab/networks/student02 created
/lab/networks/student03    descriptor /lab/networks/student03 created
```

Has creado un árbol con un laboratorio (`/lab`), dentro una carpeta de
asignatura (`/lab/networks`) y dentro tres alumnos.

---

## 6. Recorrer el árbol

Lista lo que hay en la raíz:

```
univorch /> tree /
```

Resultado esperado:

```
  lab/
    networks/
    □ student01
    □ student02
    □ student03
```

Los símbolos son indicadores de estado:

| Símbolo | Estado |
|---|---|
| `□` | provisionada (definida, no desplegada) |
| `■` | desplegada (existe la VM) |
| `✗` | rota (operación a medias) |
| `▲` | inalcanzable (sin conexión al hipervisor) |

Como el conector es mock y todavía no has desplegado nada, las tres están
provisionadas.

Inspecciona la definición efectiva de un alumno:

```
univorch /> inspect /lab/networks/student03
```

Verás:

```
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

Esto demuestra el corazón del modelo: el alumno solo define `use template:
linux-vm` y un override local de `cpu: 4`. Todo lo demás (description,
base_vm, memory_mb, disk_gb) viene **heredado** de la plantilla que está
declarada arriba, en `/lab`. La hipervisor (`mock01`) llega por el mismo
mecanismo, siguiendo el "cierre" o entorno léxico (en inglés "closure") de
la plantilla.

---

## 7. El ciclo de vida de una VM

Vas a desplegar `student01`, arrancarla, pararla y retirarla, observando los
cambios de estado.

### Desplegar

```
univorch /> deploy /lab/networks/student01
```

Respuesta:

```
deployed as mock-vm-1
```

El mock ha creado una VM con identificador `mock-vm-1`. Comprueba el estado:

```
univorch /> status /lab/networks/student01
```

```
/lab/networks/student01  state=deployed  runtime=stopped  vm_id=mock-vm-1
```

**Dos ejes de estado** en juego (es una distinción clave del modelo):

- **`state`**: el lado del orquestador. Refleja el ciclo de vida del
  descriptor (provisioned, deployed, broken…).
- **`runtime`**: el lado del hipervisor. Refleja el estado eléctrico de la
  VM (running, stopped, paused…).

Acabas de desplegar, así que el descriptor está en `deployed` y la VM
recién clonada está parada (`stopped`).

### Arrancar y parar

```
univorch /> start /lab/networks/student01
started

univorch /> status /lab/networks/student01
/lab/networks/student01  state=deployed  runtime=running  vm_id=mock-vm-1

univorch /> stop /lab/networks/student01
stopped
```

El `state` no cambia (sigue desplegada) pero el `runtime` sí. Esto refleja
que arrancar o parar no destruyen la VM, solo cambian su estado eléctrico.

### Retirar

```
univorch /> undeploy /lab/networks/student01
undeployed

univorch /> status /lab/networks/student01
/lab/networks/student01  state=provisioned  runtime=-  vm_id=-
```

La VM ha desaparecido del hipervisor. El descriptor vuelve a
`provisioned`: la definición sigue en el árbol pero no hay nada
desplegado. Es exactamente como estaba antes del `deploy`.

---

## 8. Salir y parar el servicio

Sal del REPL:

```
univorch /> quit
```

Para el contenedor cuando termines:

```bash
./univorch.sh stop
```

Los datos persisten en un volumen Docker llamado `univorch_univorch_data`.
Si vuelves a arrancar, el árbol que cargaste seguirá ahí.

Para empezar de cero (borrando todo lo que hayas cargado):

```bash
./univorch.sh stop
docker volume rm univorch_univorch_data
./univorch.sh start
```

---

## 9. Cosas que pueden salir mal

### "permission denied" al usar Docker

```
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

Tu usuario no está en el grupo `docker`. Dos opciones:

- **Rápido**: prefija las órdenes con `sudo` (`sudo ./univorch.sh start`).
- **Permanente**: `sudo usermod -aG docker $USER`, cierra sesión y vuelve a
  entrar. Aviso: estar en el grupo `docker` equivale a tener root.

### "address already in use" al arrancar

Algo está escuchando ya en el puerto 8080. Compruébalo con:

```bash
ss -tlnp | grep ':8080'
```

Si es un servicio tuyo legítimo, arranca UnivOrch en otro puerto:

```bash
UNIVORCH_PORT=9090 ./univorch.sh start
```

(El instalador detecta esto y lo gestiona; si volvió a romper, es que el
servicio en conflicto arrancó después.)

### El árbol aparece vacío tras arrancar

Estás en una sesión limpia o has borrado el volumen. Vuelve a cargar el
ejemplo:

```
univorch /> load /opt/univorch/examples/setup.yml
```

### Ver los logs del demonio

```bash
./univorch.sh logs
```

Muestra los registros del proceso uvicorn dentro del contenedor (las
peticiones HTTP que entran, los errores, etc.). Útil para diagnosticar.

---

## 10. Referencia rápida de órdenes

### Desde el host

| Orden | Hace |
|---|---|
| `./univorch.sh start` | Arranca el contenedor |
| `./univorch.sh stop` | Lo apaga limpiamente |
| `./univorch.sh restart` | Stop + start |
| `./univorch.sh status` | Estado del contenedor |
| `./univorch.sh logs` | Sigue los registros |
| `./univorch.sh cli` | Abre el REPL del cliente |

### Desde el REPL

| Orden | Hace |
|---|---|
| `help` | Lista de órdenes disponibles |
| `help <orden>` | Ayuda detallada de una orden |
| `tree /` | Vista del árbol completo |
| `ls /lab` | Listado de un nivel (como `ls`) |
| `cd /lab/networks` | Cambia la carpeta de trabajo |
| `pwd` | Imprime la carpeta actual |
| `load <fichero>` | Carga un YAML en el árbol |
| `inspect <ruta>` | Muestra la definición efectiva |
| `deploy <ruta>` | Despliega una VM |
| `start <ruta>` | Enciende una VM desplegada |
| `stop <ruta>` | Apaga una VM desplegada |
| `undeploy <ruta>` | Retira una VM (mantiene la definición) |
| `status <ruta>` | Estado del descriptor + runtime |
| `connect <url>` | Cambia el destino del cliente en caliente |
| `quit` | Sale del REPL |

### Desde HTTP (para integraciones)

La API REST está en `http://localhost:8080/api/v1/`. Ejemplos:

```bash
curl http://localhost:8080/api/v1/tree?path=/
curl -X POST http://localhost:8080/api/v1/deploy?path=/lab/networks/student01
```

La documentación interactiva (Swagger UI) está en
`http://localhost:8080/docs` cuando el servicio está corriendo. Te permite
explorar y probar todos los puntos de acceso del API desde el navegador.

---

## 11. Próximos pasos

Lo que has probado es la **prueba de concepto** del orquestador. El modelo
está completo (árbol, herencia, ciclo de vida, motor de Jobs, API REST,
cliente CLI), pero el conector es un mock.

Lo que vendrá en próximas versiones:

- **Conectores reales**: VMware (vSphere) y Proxmox.
- **Interfaz web**: NiceGUI sobre la misma API REST.
- **Autenticación y RBAC**: usuarios, roles, permisos por carpeta.
- **Aplicación docente**: capa específica para gestionar asignaturas y
  alumnos, con vocabulario adaptado a entornos universitarios.

El código fuente, las decisiones de diseño, y el historial completo están
en el repositorio: [github.com/clamaveruma/univorch](https://github.com/clamaveruma/univorch).
