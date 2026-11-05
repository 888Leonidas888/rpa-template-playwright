---
name: rpa-scaffold
description: >-
  Guía operativa y procedimental para extender, crear páginas POM, orquestar flujos, compilar con PyInstaller y generar/actualizar la documentación técnica estandarizada (README.md) bajo la arquitectura corporativa RPA (Playwright + Python + DPAPI).
---

# Skill: Desarrollo, Extensión y Documentación de Bots RPA Estandarizados

Esta Skill define los procedimientos estándar para agentes de IA y desarrolladores al construir, extender, compilar y documentar bots RPA basados en esta plantilla, garantizando arquitectura modular, cero sobreingeniería y consistencia total.

---

## 1. Verificación Previa y Principio DRY (Don't Repeat Yourself)
Antes de crear nuevas utilidades o funciones:
1. **Páginas e Interacciones**: Inspeccionar `pages/base_page.py` para reutilizar métodos seguros de interacción (`safe_click`, `safe_fill`, `wait_for_element`, etc.).
2. **Navegadores**: Inspeccionar `infrastructure/browser_manager.py` (resolución automática de Chrome y Edge nativos locales).
3. **Seguridad**: Inspeccionar `config/security.py` (DPAPI con `keyring` de Windows).
4. **Base de Datos y Memoria**: Inspeccionar `core/database.py` (telemetría local con SQLite no bloqueante).
5. **Notificaciones**: Inspeccionar `infrastructure/notifiers/` (Graph API y Outlook local).

---

## 2. Flujo de Trabajo para Agregar una Nueva Automatización

### Paso 1: Aislamiento de Credenciales DPAPI en `config/settings.py`
Todo bot debe configurar su propio prefijo en los nombres de servicio para no colisionar con otros bots en la misma máquina Windows:
```python
# Ejemplo para Bot Sunat
CRED_SERVICE_PORTAL: str = "BOT_SUNAT_PORTAL"
CRED_SERVICE_INTERNAL_APP: str = "BOT_SUNAT_INTERNAL_APP"
CRED_SERVICE_DB: str = "BOT_SUNAT_DATABASE"
CRED_SERVICE_GRAPH: str = "BOT_SUNAT_GRAPH"
CRED_SERVICE_OUTLOOK: str = "BOT_SUNAT_OUTLOOK"
```

### Paso 2: Definir los Selectores y Acciones Web en `pages/`
Cree un nuevo archivo `pages/<portal_name>_page.py` heredando de `BasePage`:
```python
from pages.base_page import BasePage
from playwright.sync_api import Page

class MiPortalPage(BasePage):
    BTN_CONSULTAR = "#btnBuscar"
    INPUT_RUC = "#txtRuc"
    TABLA_RESULTADOS = ".grid-datos"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def consultar_ruc(self, ruc: str) -> bool:
        self.safe_fill(self.INPUT_RUC, ruc)
        self.safe_click(self.BTN_CONSULTAR)
        return self.wait_for_element(self.TABLA_RESULTADOS)
```

### Paso 3: Adaptar el Modelo de Tarea en `core/models.py`
Si los datos de entrada o salida tienen campos específicos, extienda `TaskItem` o `ExecutionResult` asegurando registrar la hora local del sistema (`datetime.now()`).

### Paso 4: Orquestar en `services/`
Incorpore la lógica de negocio en `services/bot_service.py`:
1. Comprobar si el registro ya está completado en `self.db.is_already_completed(item.item_id)` (cuando la persistencia de idempotencia esté activa según el plan del bot).
2. Invocar los métodos del Page Object correspondiente.
3. Capturar archivos descargados con `self.capture_download(...)`.
4. El registro de memoria local (`self.db.save_record(result)`) opera de forma meramente informativa y no bloqueante.

### Paso 5: Exponer Parámetros en `cli/commands.py`
Añada los flags necesarios al parser de `run` (ej. `--items`, `--headless`, `--notify-graph`, `--notify-outlook`). La persistencia no lleva flag runtime (`--no-db` no existe).

---

## 3. Generador y Actualizador de `README.md` Estandarizado

Al crear un nuevo bot o concluir un `feat` estructural, el agente debe generar o actualizar el `README.md` cumpliendo estrictamente con la siguiente estructura de 8 secciones:

### Estructura Mandatoria:
1. **`# [NOMBRE-DEL-BOT]`**: Título principal.
2. **`## 1. Propósito y Descripción`**: Breve descripción técnica de qué proceso automatiza, con qué plataformas interactúa y el beneficio operativo.
3. **`## 2. Stack Tecnológico y Arquitectura`**: Detalle del stack (Python 3.10+, Playwright, DPAPI, Rich, SQLite local).
4. **`## 3. Prerrequisitos del Sistema`**: Requisitos de S.O. (Windows 10/11 o Server), navegadores nativos instalados (Chrome/Edge), conectividad de red/VPN.
5. **`## 4. Configuración del Entorno de Desarrollo`**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
6. **`## 5. Configuración de Variables de Entorno y Credenciales`**:
   Explicación de variables `.env` (si aplican) y uso del menú DPAPI:
   ```powershell
   python main.py auth
   ```
7. **`## 6. Ejecución del Bot`**:
   Comandos exactos en consola con ejemplos reales (`run --headless`, flags de notificación).
8. **`## 7. Estructura del Proyecto`**: Diagrama en árbol del repositorio.
9. **`## 8. Distribución y Configuración`**:
   Instrucciones para la compilación limpia con PyInstaller (con icono corporativo y sin `.spec`) y configuración del binario compilado.

### Reglas de Documentación para el Agente:
- **Cero Relleno**: Sin saludos, introducciones motivacionales ni secciones de "futuras mejoras" no solicitadas.
- **Validación**: Comandos exactos listos para copiar y pegar en PowerShell.
- **Idioma**: Español técnico riguroso.

---

## 4. Compilación Limpia con PyInstaller (Sin archivos `*.spec`)

Para compilar el bot a ejecutable independiente de Windows:
```powershell
.\build.ps1
```
O directamente por línea de comandos:
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
> [!NOTE]
> Nunca mantener ni versionar archivos `*.spec`. Si PyInstaller genera temporalmente `rpa-bot.spec`, debe eliminarse al concluir la compilación.

---

## 5. Verificación de Calidad y Pruebas
Antes de confirmar cambios o abrir Pull Requests:
```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```
