# Raw Ideas

# Contexto de Arquitectura: Agente de IA Distribuido y Sistemas de Mensajería

## 1. Perfil del Entorno y Objetivos técnicos
* **Rol del Sistema:** Documento de contexto para fase de tormenta de ideas y diseño de arquitectura.
* **Infraestructura Base:** Servidor Dell PowerEdge R730 corriendo Proxmox VE. Nodos virtuales (VMs/Contenedores Docker) listos para desplegar servicios de backend.
* **Filosofía de Diseño:** Desacoplamiento de componentes, alta seguridad (vía Tailscale para acceso remoto sin exposición de puertos públicos), baja latencia y control absoluto de los datos locales.
* **Meta Final:** Crear un sistema híbrido donde una interfaz móvil (Android) pueda interactuar de manera asíncrona y fluida con servicios locales del servidor y el almacenamiento, delegando la "inteligencia" a modelos de IA en la nube o locales.

---

## 2. Bloque de Arquitectura: Sistemas de Mensajería y Pub/Sub
Para evitar el acoplamiento directo entre la interfaz de usuario (móvil) y la lógica pesada del servidor, se plantea un diseño dirigido por eventos (Event-Driven).

### Tecnologías en Consideración:
* **RabbitMQ + plugin MQTT:** Para entornos que requieran una persistencia robusta de mensajes en cola. Ideal si se pierde la cobertura en el móvil, garantizando que la orden se ejecute al reconectar.
* **Mosquitto (MQTT):** Alternativa ligera (Docker) óptima para dispositivos móviles por su bajo consumo de batería y protocolo de mensajería rápido ("Publish/Subscribe").
* **Redis Pub/Sub:** Evaluado para telemetría en tiempo real o actualizaciones de estado de tareas de larga duración (ej. progreso de indexación o procesamiento de documentos).

### Flujo de Datos Propuesto:
1. **Android (Publisher):** Envía un payload JSON (`{"accion": "X", "payload": "Y"}`) a un topic específico (ej: `casa/agente/peticion`).
2. **Broker (Proxmox):** Enruta el mensaje.
3. **Agente (Subscriber):** Un script en Python escucha el topic, despierta a la IA (Claude API) con el contexto necesario, ejecuta la tarea local y devuelve el resultado a `casa/android/respuesta`.

---

## 3. Integración con Model Context Protocol (MCP)
MCP se define como el estándar abierto universal (respaldado por la Linux Foundation) para conectar clientes de IA con fuentes de datos y herramientas de ejecución locales.



### Matriz de Compatibilidad y Casos de Uso del Ecosistema Claude:
* **Claude Code (CLI):** Herramienta nativa para desarrolladores en terminal. Soporta MCP de forma directa (local y remoto). Ideal para interactuar con los repositorios y logs del servidor de forma directa.
* **Claude Desktop:** Soporta MCP mediante archivo de configuración local `config.json`.
* **Claude API / Agentes Propios:** Actúan como clientes MCP de forma programática. Permiten conectar a la IA con cualquier base de datos (Postgres), sistemas de archivos locales (notas de Obsidian) o APIs REST personalizadas.
* **Claude Web / App Oficial:** **No soportan MCP local por diseño de seguridad.** Se limitan a conectores cloud oficiales (Gmail, Google Drive) con permisos de solo lectura.

---

## 4. Estrategia de Interfaz en Android y Clientes de IA
Dado el aislamiento ("sandboxing") de Android y las restricciones de las aplicaciones comerciales, se definen tres vías de integración para interactuar con los ficheros y servicios del teléfono:

### Vía A: OpenWebUI como Progressive Web App (PWA) (Recomendado)
* **Frontend:** Desplegado en Docker (Proxmox), accedido vía Tailscale en Chrome Android y guardado en la pantalla de inicio.
* **Voz:** Integración nativa de Whisper (Speech-to-Text) para comandos de voz tipo "walkie-talkie" y Text-to-Speech de alta calidad para respuestas.
* **Backend:** Al ser una plataforma autoalojada, actúa como Cliente MCP y pasarela directa al almacenamiento local y correo corporativo.

### Vía B: Orquestación con Tasker o Termux
* **Tasker:** Para interceptar eventos del sistema Android (notificaciones, llamadas, estados de hardware) y transformarlos en peticiones HTTP hacia la API del agente o publicaciones en el Broker MQTT.
* **Termux:** Entorno Linux real en Android para ejecutar scripts Python locales que sirvan de puente intermedio utilizando `Termux:API`.

### Vía C: El Ecosistema Gemini (Híbrido)
* **Ventajas:** Acceso profundo al sistema operativo del teléfono mediante extensiones nativas (Utilidades, control de hardware, alarmas, envíos por WhatsApp). Gemini Live ofrece conversación fluida sin latencia.
* **Desventajas:** Dificultad para integrarse con infraestructura local (NAS, Outlook corporativo) sin exponer servidores MCP con URLs públicas HTTPS estrictas.

---

## 5. Próximos pasos en la Tormenta de Ideas (Brainstorming)
Al inicializar la sesión en Claude Code con este contexto, se priorizará el debate sobre:
1. Estructurar el archivo `docker-compose.yml` base en Proxmox que incluya el Agente (OpenWebUI/Dify) y el Broker de Mensajería (Mosquitto/RabbitMQ).
2. Diseño lógico del script de Python que actuará como "Servidor MCP Personalizado" para traducir intenciones de la IA en mensajes Pub/Sub.
3. Definición de payloads e hilos de ejecución asíncronos para que la IA no bloquee el cliente de voz mientras procesa archivos del NAS.
