# UnivOrch — demostración para el tutor

> **AVISO IMPORTANTE.** Este documento describe una **demostración
> provisional** del estado del trabajo del TFG. **No es el TFG final**.
> El objetivo es que veas el modelo conceptual del orquestador
> funcionando con un conector simulado (mock), no presentar el producto
> terminado. Faltan piezas importantes que sí estarán en el TFG (en
> particular: conectores reales, autenticación, interfaz web, y la
> aplicación específica para despliegue de asignaturas).

Tiempo estimado: 10 minutos.

---

## 1. Qué vas a ver

El sistema sin GUI, en modo cliente/servidor:

- Un "daemon" que corre dentro de un contenedor
  Docker, expone una API REST en `localhost:8080` y persiste el estado
  en un volumen.
- Un **cliente CLI** que habla con ese demonio por HTTP. Acepta dos
  modos: una orden suelta desde tu shell, o un REPL interactivo.
- Un **ejemplo precargado en la imagen** con un laboratorio docente:
  una asignatura con tres alumnos y una plantilla compartida.

El conector hipervisor es un mock: no se crea nada real en disco, solo
se observa el modelo (herencia, ciclo de vida, dos ejes de estado).

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
curl http://localhost:8080/api/v1/health
```

Debe devolver `{"status":"ok"}`.

Para verlo de forma más visual, abre el navegador en cualquiera de
estas páginas:

- `http://localhost:8080/` — **Web GUI** (Sprint 4, lectura): cabecera con
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

## 7. Apagar

```
univorch /> quit
```

```bash
sudo ./univorch.sh stop
```

Los datos persisten en el volumen `univorch_univorch_data`. Para
empezar de cero, `sudo docker volume rm univorch_univorch_data` antes
del siguiente `start`.

---

## 8. Si algo falla

| Síntoma | Causa habitual y arreglo |
|---|---|
| `permission denied to /var/run/docker.sock` | Tu usuario no está en el grupo `docker`. Añade `sudo` (rápido) o `sudo usermod -aG docker $USER` + relogin (permanente). |
| `address already in use` al arrancar | Otro servicio ocupa el 8080. `UNIVORCH_PORT=9090 sudo ./univorch.sh start` o ajusta `.env`. |
| `cannot reach the UnivOrch daemon` | El contenedor no está corriendo. `sudo ./univorch.sh start`. |
| Logs del demonio | `sudo ./univorch.sh logs` |

---

## 9. Referencia rápida

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

## 10. Alcance del TFG

Lo que has probado hoy es el PoC del motor de orquestación, sin GUI
y con un conector simulado. El TFG, que sigue siendo una prueba de
concepto, añade encima tres piezas:

1. **Conectores reales** — VMware (vSphere) y Proxmox sobre el mismo
   contrato abstracto que ya cumple el mock. He empezado pruebas
   contra los hipervisores VMware del aulario por VPN.

2. **Interfaz web básica** — basada en NiceGUI sobre la misma API REST
   que ya tienes en `/docs`. Navegador del árbol, edición de nodos por
   diálogo, vista alternativa "desde el hipervisor".

3. **Aplicación docente** — capa sobre el motor genérico con
   vocabulario propio (asignatura, mesa, alumno) que despliega una
   asignatura entera a partir de una lista de alumnos y una plantilla
   común. **Esta es la pieza que cierra el TFG**: el motor existe para
   esto.

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

El historial completo, las decisiones de diseño y el código fuente
están en [github.com/clamaveruma/univorch](https://github.com/clamaveruma/univorch).
