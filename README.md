# RPA Playwright Bot Framework

## 1. Propósito y Descripción
Plantilla corporativa y marco de trabajo estandarizado para la creación de Bots de Automatización de Procesos Robóticos (RPA) y Web Scraping. Automatiza la extracción de datos, descarga de reportes y tramitación web operando directamente con los navegadores nativos del sistema operativo (Google Chrome y Microsoft Edge), con almacenamiento de credenciales seguras en Windows DPAPI, telemetría informativa no bloqueante en SQLite y notificaciones duales mediante Microsoft Graph API o Microsoft Outlook de escritorio.

---

## 2. Stack Tecnológico y Arquitectura
- **Lenguaje:** Python 3.10+
- **Automatización Web (Core):** Playwright (modo síncrono nativo sobre Google Chrome y Microsoft Edge del sistema).
- **Arquitectura:** Arquitectura Limpia y Modular basada en Page Object Model (POM), orquestador desacoplado y servicios de infraestructura independientes.
- **Gestión de Credenciales:** Windows Credential Manager vía DPAPI (`keyring`), asegurando aislamiento por prefijo de bot.
- **Formato de Consola:** `rich` (tablas, paneles de estado e interactividad sobria, sin emoticones).
- **Almacenamiento / Telemetría:** SQLite en modo WAL (`bot_memory.db`) para control de idempotencia y trazabilidad de ejecuciones con fecha y hora local del sistema (`datetime.now()`). Operación de persistencia estrictamente no bloqueante.
- **Notificaciones:** Microsoft Graph API (desatendido en la nube) y Microsoft Outlook local (vía COM en segundo plano).
- **Empaquetado:** PyInstaller en modo `--onedir` con icono corporativo.

---

## 3. Prerrequisitos del Sistema
- **Sistema Operativo:** Windows 10, Windows 11 o Windows Server 2016+.
- **Python:** Versión 3.10 o superior instalada.
- **Navegadores Compatibles:** Google Chrome o Microsoft Edge instalado nativamente en el sistema.
- **Conectividad:** Acceso a la red corporativa o VPN si el portal objetivo o las APIs lo requieren.

---

## 4. Configuración del Entorno de Desarrollo
Instrucciones estrictas para inicializar y activar el entorno virtual y dependencias (prohibido instalar paquetes en el entorno global):

```powershell
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno virtual en Windows PowerShell
.\.venv\Scripts\Activate.ps1

# 3. Actualizar pip e instalar dependencias fijadas
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Configuración de Variables de Entorno y Credenciales

### Variables en `config/settings.py`
Las variables generales de operación (rutas, timeouts y dominios autorizados) se gestionan en `config/settings.py`:
- `DEFAULT_TIMEOUT_MS`: Tiempo de espera estándar para elementos de UI (por defecto `30000`).
- `NAVIGATION_TIMEOUT_MS`: Tiempo de espera para carga completa de páginas (`45000`).
- `ALLOWED_DOMAINS`: Lista de dominios permitidos para navegación segura.

### Gestión de Credenciales Seguras en Windows DPAPI
Las credenciales sensibles **nunca se almacenan en código ni en archivos de texto**. Se cifran directamente en el perfil del usuario activo de Windows:

```powershell
# Desplegar el menú interactivo de credenciales
python main.py auth
```

Opciones disponibles en el menú interactivo:
1. **App Web**: Usuario y contraseña para el portal objetivo.
2. **App Interna / ERP**: Credenciales para sistemas locales.
3. **Base de Datos**: Host, base de datos, usuario y contraseña.
4. **Microsoft Graph API**: Tenant ID, Client ID, Client Secret, remitente y destinatarios separados por `;`.
5. **Outlook Local**: Lista de destinatarios separados por `;`.

Para verificar la presencia de credenciales sin revelar secretos:
```powershell
python main.py auth verify
```

> [!IMPORTANT]
> **Aislamiento por Bot:** Cada nuevo bot derivado debe definir sus propios identificadores de servicio en `config/settings.py` (ej. `BOT_SUNAT_PORTAL`) para evitar colisiones con otros procesos en el mismo equipo.

---

## 6. Ejecución del Bot

### Ejecución en Modo Desarrollo (Navegador Visible)
Ideal para depuración y supervisión visual:
```powershell
python main.py run --items "PO-1001,PO-1002"
```

### Ejecución en Modo Desatendido (Headless)
Mandatorio para servidores o tareas programadas en Windows Task Scheduler:
```powershell
python main.py run --items "PO-1001,PO-1002" --headless
```

### Ejecución con Notificaciones por Microsoft Graph API
Requiere correos separados por `;` (cierre inmediato con error si faltan):
```powershell
python main.py run --items "PO-1001" --headless --notify-graph --emails "operador@empresa.com;supervisor@empresa.com"
```

### Ejecución con Notificaciones por Microsoft Outlook Local
Envía en segundo plano sin requerir que Outlook esté visible en pantalla:
```powershell
python main.py run --items "PO-1001" --headless --notify-outlook --emails "operador@empresa.com;supervisor@empresa.com"
```

### Forzar Reprocesamiento de Items
Ignora el estado completado previo en la base de datos de memoria:
```powershell
python main.py run --items "PO-1001" --force
```

### Consulta de Estado y Limpieza de Memoria
```powershell
# Ver tabla de auditoría con Rich
python main.py status

# Limpiar historial de memoria SQLite
python main.py clear-memory
```

---

## 7. Estructura del proyecto

```txt
rpa-playwright-template/
│
├── .agents/                      # Directrices y skills locales para agentes de IA
│   ├── rules/rpa_standard.md     # Las 12 Reglas obligatorias de desarrollo y arquitectura
│   └── skills/rpa-scaffold/      # Guía procedimental y generador de README
├── AGENTS.md                     # Directrices principales de entrada para asistentes
├── MEMORY.md                     # Memoria operativa, esquema SQLite y registro de decisiones
│
├── assets/                       # Recursos estáticos corporativos
│   └── icons/
│       └── python.ico            # Icono corporativo para la compilación del ejecutable
│
├── cli/                          # Capa de presentación por consola (CLI)
│   ├── __init__.py
│   └── commands.py               # Comandos: run, auth, status, clear-memory con Rich
│
├── config/                       # Configuración y seguridad
│   ├── __init__.py
│   ├── settings.py               # Rutas, timeouts y nombres de servicio DPAPI
│   ├── security.py               # Menú interactivo y cifrado en Windows DPAPI
│   └── logger_config.py          # Logging rotativo a consola y archivo
│
├── core/                         # Capa de dominio y persistencia
│   ├── __init__.py
│   ├── models.py                 # DTOs: TaskItem, ExecutionResult, ExecutionStatus
│   └── database.py               # Base SQLite no bloqueante para auditoría (bot_memory.db)
│
├── infrastructure/               # Drivers y adaptadores de comunicación externa
│   ├── __init__.py
│   ├── browser_manager.py        # Orquestación de Chrome primario y Edge fallback nativos
│   └── notifiers/                # Adaptadores de notificación (Graph API y Outlook local)
│       ├── base_notifier.py
│       ├── graph_notifier.py
│       └── outlook_notifier.py
│
├── pages/                        # Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py              # Clase base con clics seguros, capturas y descargas
│   └── sample_portal_page.py     # Página de ejemplo extensible para portales web
│
├── services/                     # Lógica de negocio y orquestación
│   ├── __init__.py
│   └── bot_service.py            # Orquestador del flujo operativo
│
├── tests/                        # Pruebas automatizadas (pytest)
│   ├── test_browser_manager.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_orchestrator.py
│   └── test_security.py
│
├── ui/                           # Máscara web opcional (HTML5, CSS y JS Vanilla)
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── downloads/                    # Descargas locales generadas por el bot
├── logs/                         # Trazabilidad rotativa y capturas de error
├── build.ps1                     # Script de compilación limpia con PyInstaller
├── new-bot.ps1                   # Script para generar nuevos bots a partir de esta plantilla
├── main.py                       # Punto de entrada de la aplicación
├── requirements.txt              # Dependencias fijadas del proyecto
└── README.md                     # Documentación técnica estandarizada
```

---

## 8. Distribución y configuración

### Compilación Limpia a Ejecutable Independiente (.exe)
Todo bot debe compilarse de forma directa y limpia **sin mantener archivos `*.spec`** que causan desincronizaciones de dependencias. Se utiliza el icono corporativo ubicado en `assets/icons/python.ico`:

```powershell
# Ejecutar compilación automatizada
.\build.ps1
```

O comando directo equivalente mediante PyInstaller:
```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --onedir --console `
    --name "rpa-bot" `
    --icon "assets/icons/python.ico" `
    --add-data "config;config" `
    --add-data "core;core" `
    --add-data "infrastructure;infrastructure" `
    --add-data "pages;pages" `
    --add-data "services;services" `
    --add-data "cli;cli" `
    --add-data "assets;assets" `
    --hidden-import "keyring.backends.Windows" `
    --hidden-import "playwright" `
    --hidden-import "playwright.sync_api" `
    --hidden-import "sqlite3" `
    --hidden-import "requests" `
    --hidden-import "rich" `
    main.py
```

### Configuración en el Servidor / Equipo Destino
1. Copiar la carpeta distribuible `dist\rpa-bot\` al servidor o estación de trabajo destino.
2. Iniciar sesión con la cuenta de Windows que ejecutará el bot.
3. Configurar las credenciales seguras mediante el ejecutable:
   ```powershell
   cd dist\rpa-bot
   .\rpa-bot.exe auth
   ```
4. Programar la ejecución en segundo plano (Headless) en Windows Task Scheduler:
   ```powershell
   .\rpa-bot.exe run --headless --notify-outlook --emails "supervisor@empresa.com"
   ```
