# STN RPA Playwright Bot Template (Arquitectura Estándar)

Plantilla corporativa y marco de trabajo estandarizado para la creación de Bots de Automatización de Procesos (RPA) y Web Scraping utilizando **Python**, **Playwright**, **Google Chrome / Microsoft Edge**, **Windows Credential Manager (DPAPI)**, persistencia **SQLite** y empaquetado autónomo con **PyInstaller**.

Repositorio oficial: [888Leonidas888/rpa-template-playwright](https://github.com/888Leonidas888/rpa-template-playwright.git)

---

## 1. Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas limpia, desacoplada y orientada a la mantenibilidad:

```
rpa-playwright-template/
├── .agents/                      # Reglas y Skills locales para asistentes de IA (Antigravity / Claude / Copilot)
│   ├── rules/rpa_standard.md     # Reglas obligatorias de arquitectura, seguridad y cero improvisación
│   └── skills/rpa-scaffold/      # Guía procedimental para crear páginas POM, orquestación y compilación
├── cli/                          # Interfaz de línea de comandos (Argparse)
│   ├── __init__.py
│   └── commands.py               # Subcomandos: run, auth, status, clear-memory, install-browser
├── config/                       # Configuración y utilidades del sistema
│   ├── __init__.py
│   ├── settings.py               # Rutas de ejecución, timeouts y dominios autorizados
│   ├── security.py               # Gestión de credenciales seguras vía Windows DPAPI (keyring)
│   └── logger_config.py          # Logging rotativo (consola y archivo logs/bot.log)
├── core/                         # Capa de dominio y persistencia
│   ├── __init__.py
│   ├── models.py                 # DTOs: TaskItem, ExecutionResult, ExecutionStatus
│   └── database.py               # Base SQLite local para auditoría e idempotencia (bot_memory.db)
├── infrastructure/               # Adaptadores externos y drivers del sistema operativo
│   ├── __init__.py
│   ├── browser_manager.py        # Gestor de Playwright: Chrome (primario) -> Edge (fallback) -> Error
│   └── notifiers/                # Despacho de notificaciones (Microsoft Graph API y Webhooks)
├── pages/                        # Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py              # Clase base con clics seguros, capturas en fallos y descargas
│   └── sample_portal_page.py     # Ejemplo de implementación para páginas web objetivo
├── services/                     # Capa de casos de uso y orquestación
│   ├── __init__.py
│   └── bot_service.py            # Orquestador del flujo: lectura, validación, ejecución y reporte
├── tests/                        # Suite de pruebas automatizadas (pytest)
│   ├── test_browser_manager.py   # Pruebas de estrategia de navegadores Chrome/Edge
│   ├── test_database.py          # Pruebas de base de datos e idempotencia
│   ├── test_security.py          # Pruebas de validación HTTPS y DPAPI
│   └── test_orchestrator.py      # Pruebas del orquestador de negocio simulado
├── downloads/                    # Carpeta local para almacenamiento de archivos descargados
├── logs/                         # Carpeta local para logs rotativos y capturas de pantalla de error
├── build.ps1                     # Script de empaquetado automatizado con PyInstaller (--onedir)
├── new-bot.ps1                   # Script para generar un nuevo proyecto a partir de esta plantilla
├── main.py                       # Punto de entrada de la aplicación
└── requirements.txt              # Dependencias de producción y desarrollo
```

---

## 2. Estrategia de Navegadores (Cero Descargas Pesadas)

A diferencia de configuraciones que congelan más de 300 MB de Chromium portable, esta plantilla aprovecha los navegadores ya instalados en el sistema operativo del usuario:

1. **Google Chrome (Canal Primario)**: Se intenta instanciar `channel="chrome"`.
2. **Microsoft Edge (Fallback Automático)**: Si Chrome no está presente, conmuta automáticamente a `channel="msedge"` (preinstalado en Windows 10/11).
3. **Fallo Controlado**: Si ninguno de los dos navegadores está disponible, se dispara la excepción `BrowserNotFoundError`, se registra en el log y se despacha una notificación de alerta inmediata al operador.

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

### 2. Configurar Credenciales Seguras (DPAPI)
Las credenciales nunca se guardan en texto plano; se cifran con la clave del usuario de Windows:
```powershell
python main.py auth setup
```
Para verificar que las credenciales están presentes:
```powershell
python main.py auth verify
```

### 3. Ejecutar el Bot

Por defecto, la ejecución muestra la ventana gráfica del navegador para facilitar la supervisión del operador:
```powershell
# Ejecución visible por defecto
python main.py run --items "PO-1001,PO-1002"

# Ejecución en segundo plano (Headless)
python main.py run --items "PO-1001,PO-1002" --headless

# Ejecución con notificación de resultados por Graph/Webhook
python main.py run --items "PO-1001" --headless --notify

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
4. Incluir la carpeta `.agents/` para que el asistente de IA siga el mismo estándar automáticamente.

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

Este paquete no requiere paquetes pesados de navegador porque se conecta directamente al Chrome o Edge del equipo cliente.
