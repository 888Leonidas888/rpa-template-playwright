# MEMORY.md - Memoria Operativa y Flujo del Bot RPA

Este documento registra la arquitectura, el flujo de ejecución, los estados y las decisiones de diseño del STN RPA Bot Framework. Se mantiene actualizado de forma continua para servir como fuente de verdad del ciclo de vida del bot.

---

## 1. Arquitectura y Componentes del Sistema

El bot está estructurado en 7 capas estrictas para evitar el acoplamiento y garantizar la mantenibilidad:

```
[CLI / UI Máscara] (commands.py con Rich / ui/)
        │
        ▼
[Orquestador de Negocio] (services/bot_service.py)
   ├── Consulta Idempotencia ──► [Base SQLite (WAL)] (core/database.py -> bot_memory.db)
   ├── Recupera Credenciales ──► [Windows DPAPI] (config/security.py)
   ├── Comanda Navegador     ──► [Browser Manager] (infrastructure/browser_manager.py)
   │                                 │
   │                                 ├── 1° Intenta: Google Chrome
   │                                 ├── 2° Fallback: Microsoft Edge
   │                                 └── 3° Falla con BrowserNotFoundError si ninguno existe
   ├── Ejecuta Acciones Web  ──► [Page Objects] (pages/base_page.py -> sample_portal_page.py)
   ├── Registra Resultado    ──► [Base SQLite] (Guarda estado SUCCESS/FAILED/SKIPPED)
   └── Despacha Alertas      ──► [Notificadores] (Graph API / Outlook COM local)
```

---

## 2. Flujo de Ejecución del Bot

```mermaid
flowchart TD
    A[Inicio: python main.py run] --> B{¿Credenciales en DPAPI?}
    B -- No --> C[Panel Error Rich y Cierre: Fail-Fast]
    B -- Sí --> D[Leer Items a Procesar]
    D --> E{¿Ya completado en SQLite?}
    E -- Sí & sin --force --> F[Marcar como SKIPPED y omitir]
    E -- No --> G[Iniciar BrowserManager]
    G --> H{¿Google Chrome disponible?}
    H -- Sí --> I[Abrir Chrome]
    H -- No --> J{¿Microsoft Edge disponible?}
    J -- Sí --> K[Abrir Edge]
    J -- No --> L[Disparar BrowserNotFoundError y Notificar Alerta]
    I --> M[Interactuar con Portal POM]
    K --> M
    M --> N[Registrar Resultado en SQLite WAL]
    N --> O{¿Flags de Notificacion?}
    O -- notify-graph --> P[Despachar email via Graph API]
    O -- notify-outlook --> Q[Despachar email via Outlook COM local]
    O -- Ninguno --> R[Tabla Resumen con Rich y Fin]
    P --> R
    Q --> R
```

---

## 3. Matriz de Configuración de Credenciales (DPAPI)

Accesible mediante el menú interactivo: `python main.py auth`

| Servicio | Tipo de Datos Almacenados | Uso Principal |
| :--- | :--- | :--- |
| **App Web** | `Usuario` y `Contraseña` cifrados en Windows | Portal externo objetivo para descargas y scraping |
| **App SIGE** | `Usuario` y `Contraseña` cifrados en Windows | Acceso al sistema interno SIGE |
| **Base de Datos** | `Host`, `Database`, `User`, `Password` | Conexión directa a bases de datos relacionales |
| **Microsoft Graph** | `Tenant ID`, `Client ID`, `Secret`, `Sender`, `Recipients` | Notificaciones desatendidas por correo corporativo |
| **Outlook Local** | Lista de `Destinatarios` (separados por `;`) | Notificaciones a través de la sesión Outlook del equipo |

> [!IMPORTANT]
> **Contexto de Sesión Windows**: DPAPI cifra con el perfil del usuario Windows activo. Si el bot se ejecuta de forma desatendida mediante Windows Task Scheduler, `python main.py auth` debe ejecutarse bajo esa misma cuenta de servicio.

---

## 4. Opciones de Ejecución en Línea de Comandos (CLI con Rich)

* `python main.py run`: Ejecuta el bot con la ventana del navegador **visible** por defecto.
* `python main.py run --headless`: Ejecuta el bot en segundo plano (obligatorio para servidores o tareas programadas).
* `python main.py run --notify-graph --emails "user1@stn.com;user2@stn.com"`: Envía alerta por Graph API (falla si faltan correos).
* `python main.py run --notify-outlook --emails "user1@stn.com;user2@stn.com"`: Envía alerta por Outlook sin requerir que la ventana esté abierta.
* `python main.py status`: Muestra la tabla de ejecuciones acumuladas en `bot_memory.db` con formato `rich.table`.
* `python main.py clear-memory`: Limpia el historial SQLite para pruebas en limpio.

---

## 5. Historial de Decisiones Técnicas

* **Decisión 01 (Navegadores)**: Se descartó el empaquetado de Chromium portable (300+ MB) en favor de Google Chrome con fallback automático a Microsoft Edge nativo del sistema.
* **Decisión 02 (Modo Headless)**: La ventana visible es el comportamiento predeterminado para supervisión visual; `--headless` es mandatorio en producción y tareas programadas.
* **Decisión 03 (Notificaciones Duales)**: Se separaron los canales en `--notify-graph` (cloud Azure AD) y `--notify-outlook` (cliente local de escritorio vía COM en segundo plano).
* **Decisión 04 (Interfaz de Usuario y Rich)**: La máscara web se implementa con HTML5, CSS y JavaScript Vanilla puro, paleta oscura y Font Awesome (cero emojis). La consola utiliza `rich` para tablas, paneles y estados coloreados.
* **Decisión 05 (Concurrencia SQLite)**: Se configuró SQLite con WAL mode (`PRAGMA journal_mode=WAL`) y `busy_timeout=30000` para evitar bloqueos por concurrencia.
