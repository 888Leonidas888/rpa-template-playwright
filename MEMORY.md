# MEMORY.md - Memoria Operativa y Flujo del Bot RPA

Este documento registra la arquitectura, el flujo de ejecución, los estados y las decisiones de diseño del RPA Bot Framework. Se mantiene actualizado de forma continua para servir como fuente de verdad del ciclo de vida del bot.

---

## 1. Arquitectura y Componentes del Sistema

El bot está estructurado en capas estrictas y desacopladas para garantizar la mantenibilidad y pruebas unitarias aisladas:

```
[CLI / UI Máscara] (commands.py con Rich / ui/)
        │
        ▼
[Orquestador de Negocio] (services/bot_service.py)
   ├── Consulta Idempotencia ──► [Base SQLite Telemetría] (core/database.py -> bot_memory.db)
   ├── Recupera Credenciales ──► [Windows DPAPI Aislado] (config/security.py)
   ├── Comanda Navegador     ──► [Browser Manager] (infrastructure/browser_manager.py)
   │                                 │
   │                                 ├── 1° Intenta: Google Chrome nativo
   │                                 ├── 2° Fallback: Microsoft Edge nativo
   │                                 └── 3° Falla con BrowserNotFoundError si ninguno existe
   ├── Ejecuta Acciones Web  ──► [Page Objects] (pages/base_page.py -> sample_portal_page.py)
   ├── Registra Telemetría   ──► [Base SQLite No Bloqueante] (Hora local: started_at, finished_at, created_at, updated_at)
   └── Despacha Alertas      ──► [Notificadores] (Graph API / Outlook COM local)
```

---

## 2. Flujo de Ejecución del Bot

```mermaid
flowchart TD
    A["Inicio: python main.py run"] --> B{"¿Credenciales en DPAPI?"}
    B -- No --> C["Panel Error Rich y Cierre: Fail-Fast"]
    B -- Sí --> D["Leer Items a Procesar"]
    D --> E{"¿Item ya completado en SQLite?"}
    E -- Sí y sin --force --> F["Marcar como SKIPPED y omitir"]
    E -- No --> G["Iniciar BrowserManager"]
    G --> H{"¿Google Chrome disponible?"}
    H -- Sí --> I["Abrir Chrome"]
    H -- No --> J{"¿Microsoft Edge disponible?"}
    J -- Sí --> K["Abrir Edge"]
    J -- No --> L["Disparar BrowserNotFoundError y Notificar Alerta"]
    I --> M["Interactuar con Portal POM"]
    K --> M
    M --> N["Registrar Telemetría en SQLite (Hora Local, No Bloqueante)"]
    N --> P{"¿Flags de Notificacion?"}
    P -- notify-graph --> Q["Despachar email via Graph API"]
    P -- notify-outlook --> R["Despachar email via Outlook COM local"]
    P -- Ninguno --> S["Tabla Resumen con Rich y Fin"]
    Q --> S
    R --> S
```

---

## 3. Matriz de Configuración de Credenciales (DPAPI) y Aislamiento

Accesible mediante el menú interactivo: `python main.py auth`

| Servicio Configurable | Nombre de Servicio DPAPI (settings.py) | Tipo de Datos Almacenados | Uso Principal |
| :--- | :--- | :--- | :--- |
| **App Web** | `CRED_SERVICE_PORTAL` | `Usuario` y `Contraseña` cifrados | Portal externo objetivo para descargas y scraping |
| **App Interna / ERP** | `CRED_SERVICE_INTERNAL_APP` | `Usuario` y `Contraseña` cifrados | Acceso a sistemas internos o ERP |
| **Base de Datos** | `CRED_SERVICE_DB` | `Host`, `Database`, `User`, `Password` | Conexión directa a bases de datos relacionales |
| **Microsoft Graph** | `CRED_SERVICE_GRAPH` | `Tenant ID`, `Client ID`, `Secret`, `Sender`, `Recipients` | Notificaciones desatendidas por correo corporativo |
| **Outlook Local** | `CRED_SERVICE_OUTLOOK` | Lista de `Destinatarios` (separados por `;`) | Notificaciones a través de la sesión Outlook del equipo |

> [!IMPORTANT]
> **Aislamiento de Servicios**: Windows Credential Manager indexa credenciales por cuenta de usuario de Windows y nombre de servicio (`ServiceName`). Cada bot debe definir su propio prefijo en `config/settings.py` (ej. `BOT_SUNAT_...`) para no colisionar con otros bots.
> **Contexto de Sesión Windows**: DPAPI cifra con el perfil del usuario Windows activo. Si el bot se ejecuta de forma desatendida mediante Windows Task Scheduler, `python main.py auth` debe ejecutarse bajo esa misma cuenta de servicio.

---

## 4. Esquema de Memoria y Telemetría Local (`bot_memory.db`)

Tabla: `task_records`
* `id`: INTEGER PRIMARY KEY AUTOINCREMENT
* `item_id`: TEXT UNIQUE
* `status`: TEXT (`SUCCESS`, `FAILED`, `SKIPPED`)
* `started_at`: TEXT (Fecha y hora local de inicio `%Y-%m-%d %H:%M:%S`)
* `finished_at`: TEXT (Fecha y hora local de finalización `%Y-%m-%d %H:%M:%S`)
* `created_at`: TEXT (Fecha y hora local de inserción inicial)
* `updated_at`: TEXT (Fecha y hora local de última actualización)
* `duration_seconds`: REAL
* `error_message`: TEXT
* `details`: TEXT

> [!NOTE]
> El guardado en base de datos es de carácter meramente informativo y de respaldo. Las escrituras están protegidas contra excepciones para garantizar que un fallo en SQLite nunca interrumpa el flujo del bot (*non-blocking*).

---

## 5. Opciones de Ejecución en Línea de Comandos (CLI con Rich)

* `python main.py run`: Ejecuta el bot con la ventana del navegador **visible** por defecto.
* `python main.py run --headless`: Ejecuta el bot en segundo plano (obligatorio para servidores o tareas programadas).
* `python main.py run --force`: Fuerza el reprocesamiento de items incluso si ya figuraban como completados.
* `python main.py run --notify-graph --emails "user1@empresa.com;user2@empresa.com"`: Envía alerta por Graph API (falla si faltan correos).
* `python main.py run --notify-outlook --emails "user1@empresa.com;user2@empresa.com"`: Envía alerta por Outlook sin requerir que la ventana esté abierta.
* `python main.py status`: Muestra la tabla de ejecuciones acumuladas en `bot_memory.db` con formato `rich.table`.
* `python main.py clear-memory`: Limpia el historial SQLite para pruebas en limpio.

---

## 6. Historial de Decisiones Técnicas

* **Decisión 01 (Navegadores Nativos)**: Se descartó el empaquetado y descarga de Chromium portable en favor de Google Chrome con fallback automático a Microsoft Edge nativo del sistema.
* **Decisión 02 (Modo Headless)**: La ventana visible es el comportamiento predeterminado para supervisión visual; `--headless` es mandatorio en producción y tareas programadas.
* **Decisión 03 (Notificaciones Duales)**: Se separaron los canales en `--notify-graph` (cloud Azure AD) y `--notify-outlook` (cliente local de escritorio vía COM en segundo plano).
* **Decisión 04 (Interfaz de Usuario y Rich)**: La máscara web se implementa con HTML5, CSS y JavaScript Vanilla puro, paleta oscura y Font Awesome (cero emojis). La consola utiliza `rich` para tablas, paneles y estados coloreados.
* **Decisión 05 (Concurrencia SQLite)**: Se configuró SQLite con WAL mode (`PRAGMA journal_mode=WAL`) y `busy_timeout=30000` para evitar bloqueos por concurrencia.
* **Decisión 06 (Persistencia y Memoria Local)**: La persistencia para reanudar tareas interrumpidas es una decisión de diseño definida en el plan inicial del bot, eliminando el flag runtime `--no-db`. Las marcas de tiempo se graban en hora local del sistema (`datetime.now()`) y las escrituras son estrictamente no bloqueantes.
* **Decisión 07 (Reutilización y DRY)**: Antes de implementar componentes o funciones, es mandatorio verificar la existencia previa en el repositorio para evitar duplicar código.
* **Decisión 08 (Aislamiento de Nombres DPAPI)**: Cada bot derivado del template debe configurar prefijos propios en `config/settings.py` para prevenir colisiones de credenciales en Windows Credential Manager.
* **Decisión 09 (Compilación Limpia con PyInstaller)**: Todo bot debe compilarse de forma directa y limpia sin mantener archivos `*.spec`, integrando el icono corporativo `assets/icons/python.ico`.
* **Decisión 10 (Entorno Virtual `.venv` Obligatorio)**: Prohibido instalar paquetes en el entorno global. Toda ejecución y empaquetado se hace desde `.venv`, manteniendo `requirements.txt` actualizado.
