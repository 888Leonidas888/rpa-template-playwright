# STN RPA Playwright Bot Template (Arquitectura Estándar)

Plantilla corporativa y marco de trabajo estandarizado para la creación de Bots de Automatización de Procesos (RPA) y Web Scraping utilizando **Python**, **Playwright**, **Google Chrome / Microsoft Edge**, **Windows Credential Manager (DPAPI)**, persistencia **SQLite**, notificaciones (**Microsoft Graph / Outlook**) y empaquetado autónomo con **PyInstaller**.

Repositorio oficial: [888Leonidas888/rpa-template-playwright](https://github.com/888Leonidas888/rpa-template-playwright.git)

---

## 1. Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas limpia, desacoplada y orientada a la mantenibilidad:

```
rpa-playwright-template/
├── .agents/                      # Reglas y Skills locales para asistentes de IA (Antigravity / Claude / Copilot)
│   ├── rules/rpa_standard.md     # Las 10 Reglas obligatorias de arquitectura, seguridad y cero improvisacion
│   └── skills/rpa-scaffold/      # Guia procedimental para crear paginas POM, orquestacion y compilacion
├── AGENTS.md                     # Directrices principales de entrada para asistentes de codigo
├── MEMORY.md                     # Memoria operativa continua del bot (flujo, decisiones y estados)
├── cli/                          # Interfaz de linea de comandos (Argparse)
│   ├── __init__.py
│   └── commands.py               # Subcomandos: run, auth, status, clear-memory
├── config/                       # Configuracion y utilidades del sistema
│   ├── __init__.py
│   ├── settings.py               # Rutas de ejecucion, timeouts y dominios autorizados
│   ├── security.py               # Menu interactivo y gestion DPAPI (Web, SIGE, BBDD, Graph, Outlook)
│   └── logger_config.py          # Logging rotativo (consola y archivo logs/bot.log)
├── core/                         # Capa de dominio y persistencia
│   ├── __init__.py
│   ├── models.py                 # DTOs: TaskItem, ExecutionResult, ExecutionStatus
│   └── database.py               # Base SQLite local para auditoria e idempotencia (bot_memory.db)
├── infrastructure/               # Adaptadores externos y drivers del sistema operativo
│   ├── __init__.py
│   ├── browser_manager.py        # Gestor de Playwright: Chrome (primario) -> Edge (fallback) -> Error
│   └── notifiers/                # Despacho de notificaciones (Graph API y Outlook local en segundo plano)
│       ├── base_notifier.py
│       ├── graph_notifier.py
│       └── outlook_notifier.py
├── pages/                        # Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py              # Clase base con clics seguros, capturas en fallos y descargas
│   └── sample_portal_page.py     # Ejemplo de implementacion para paginas web objetivo
├── services/                     # Capa de casos de uso y orquestacion
│   ├── __init__.py
│   └── bot_service.py            # Orquestador del flujo: lectura, validacion, ejecucion y reporte
├── tests/                        # Suite de pruebas automatizadas (pytest)
│   ├── test_browser_manager.py   # Pruebas de estrategia de navegadores Chrome/Edge
│   ├── test_database.py          # Pruebas de base de datos e idempotencia
│   ├── test_security.py          # Pruebas de validacion HTTPS y DPAPI (Web, SIGE, BBDD, Graph, Outlook)
│   └── test_orchestrator.py      # Pruebas del orquestador de negocio simulado
├── ui/                           # Mascara web para usuario (HTML5, CSS3 y JS Vanilla oscuro con Font Awesome)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── downloads/                    # Carpeta local para almacenamiento de archivos descargados
├── logs/                         # Carpeta local para logs rotativos y capturas de pantalla de error
├── build.ps1                     # Script de empaquetado automatizado con PyInstaller (--onedir)
├── new-bot.ps1                   # Script para generar un nuevo proyecto a partir de esta plantilla
├── main.py                       # Punto de entrada de la aplicacion
└── requirements.txt              # Dependencias de produccion y desarrollo
```

---

## 2. Estrategia de Navegadores (Cero Descargas Pesadas)

1. **Google Chrome (Canal Primario)**: Se intenta instanciar `channel="chrome"`.
2. **Microsoft Edge (Fallback Automático)**: Si Chrome no está presente, conmuta automáticamente a `channel="msedge"` (preinstalado en Windows 10/11).
3. **Fallo Controlado**: Si ninguno de los dos navegadores está disponible, se dispara la excepción `BrowserNotFoundError`, se registra en el log y se despacha una notificación de alerta inmediata al operador (*fail-fast*).

---

## 3. Puesta en Marcha Rápida (Desarrollo)

### Requisitos Previos
* Windows 10/11 o Windows Server con Google Chrome o Microsoft Edge.
* Python 3.10 o superior instalado.

### 1. Inicializar Entorno Virtual
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar Credenciales Seguras (Menú Interactivo DPAPI)
Ejecute el menú interactivo para configurar cualquiera de los servicios requeridos:
```powershell
python main.py auth
```
Opciones disponibles en el menú:
1. Credenciales App Web (Portal objetivo)
2. Credenciales App SIGE (Sistema interno)
3. Conexión de Base de Datos
4. Microsoft Graph API (con correos separados por `;`)
5. Destinatarios Microsoft Outlook Local

Para verificar el estado de las credenciales configuradas:
```powershell
python main.py auth verify
```

### 3. Ejecutar el Bot

```powershell
# Ejecución visible por defecto (ideal para supervisión)
python main.py run --items "PO-1001,PO-1002"

# Ejecución en segundo plano (Headless)
python main.py run --items "PO-1001,PO-1002" --headless

# Ejecución con notificación por Microsoft Graph (valida correos con ';')
python main.py run --items "PO-1001" --headless --notify-graph --emails "operador@stn.com;supervisor@stn.com"

# Ejecución con notificación por Microsoft Outlook local (en segundo plano, sin requerir Outlook abierto)
python main.py run --items "PO-1001" --headless --notify-outlook --emails "operador@stn.com;supervisor@stn.com"

# Forzar reprocesamiento (ignorando registros previos en SQLite)
python main.py run --items "PO-1001" --force
```

---

## 4. Generación de un Nuevo Bot desde la Plantilla

Para crear un nuevo proyecto sin copiar archivos manualmente ni arrastrar historiales viejos:

```powershell
.\new-bot.ps1 -Name "bot-sunat-detracciones" -Destination "C:\Users\jescriba\Desktop\development\bot-sunat-detracciones"
```

El script se encargará de:
1. Copiar toda la arquitectura limpia (excluyendo entornos virtuales, logs y bases de datos).
2. Personalizar los nombres en los scripts y comandos CLI.
3. Inicializar un repositorio Git limpio con la rama `caracteristica/scaffold-inicial`.
4. Incluir `AGENTS.md`, `MEMORY.md` y `.agents/` para que el asistente de IA siga el mismo estándar automáticamente.

---

## 5. Pruebas y Control de Calidad

Antes de realizar cambios o empaquetar, compruebe que todas las pruebas pasen y el código cumpla los estándares de formato:

```powershell
# Ejecución de pruebas unitarias
pytest

# Análisis estático y linter
ruff check .
```

---

## 6. Compilación a Ejecutable Independiente (.exe)

Para generar la distribución binaria de producción:

```powershell
.\build.ps1
```

El binario resultante se ubicará en `dist/rpa-bot/`:
* `dist/rpa-bot/rpa-bot.exe`: Binario principal.
* `dist/rpa-bot/downloads/`: Directorio de salida.
* `dist/rpa-bot/logs/`: Directorio para trazabilidad.

---

## 7. Las 10 Reglas Obligatorias de Desarrollo

Cualquier cambio o extensión a este proyecto (o a cualquier bot creado a partir de esta plantilla) debe cumplir estrictamente las reglas definidas en [AGENTS.md](AGENTS.md) y [.agents/rules/rpa_standard.md](.agents/rules/rpa_standard.md):

1. **Cero Sobreingeniería (KISS / YAGNI)**: Si algo no queda claro, preguntar antes de asumir. Si una solución toma 3 líneas, no hacerla en 20. Cero fallbacks silenciosos no pedidos.
2. **Responsabilidad Única (SRP)**: Una función hace una tarea. No crear archivos inmensos. Alertar al usuario si se requiere refactorizar.
3. **Documentación en Español**: Documentación y docstrings en español. Comentarios estrictamente necesarios; el código debe ser autoleíble.
4. **Linters Obligatorios**: Ejecutar `ruff check .` y `pytest` antes de confirmar cambios.
5. **Máscara Web (UI)**: Si se requiere interfaz, usar **HTML5, CSS y JavaScript Vanilla**.
6. **Cero Emoticones (Iconografía Profesional)**: Prohibido emojis en UI o consola; usar exclusivamente **Font Awesome** o Bootstrap Icons.
7. **Estilo Dark Theme**: Colores oscuros minimalistas inspirados en la interfaz de Gemini (`#131314` fondo, `#1e1f20` tarjetas, `#a8c7fa` acentos).
8. **Menú de Credenciales en `auth`**: Menú interactivo para configurar App Web, App SIGE, BBDD, Graph (con correos separados por `;`) y Outlook local en Windows DPAPI.
9. **Notificaciones Duales**:
   * `--notify-graph`: Envia por Graph API; requiere correos separados por `;` (cierre inmediato con error si faltan).
   * `--notify-outlook`: Envia por Outlook local en segundo plano (sin esperar que Outlook esté abierto).
10. **Higiene de Repositorio y `MEMORY.md`**:
    * Ignorar todo archivo no-core en `.gitignore` o moverlo a la carpeta `.trash/` (ignorada).
    * Mantener siempre actualizado `MEMORY.md` y `README.md` tras cada `feat`.
    * Nunca trabajar sobre `main`; usar ramas kebab-case desde `main` y gestionar cambios con `gh`.
