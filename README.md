# STN RPA Playwright Bot Template (Arquitectura Estándar)

Plantilla corporativa y marco de trabajo estandarizado para la creación de Bots de Automatización de Procesos (RPA) y Web Scraping utilizando **Python**, **Playwright**, **Windows Credential Manager (DPAPI)**, persistencia **SQLite** y empaquetado autónomo con **PyInstaller**.

---

## 1. Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas limpia, desacoplada y orientada a la mantenibilidad:

```
rpa-playwright-template/
├── .agents/                      # Reglas y Skills locales para asistentes de IA (Antigravity / Claude)
│   ├── rules/rpa_standard.md     # Reglas obligatorias de arquitectura y seguridad
│   └── skills/rpa-scaffold/      # Guía procedimental para crear páginas, servicios y compilación
├── cli/                          # Interfaz de línea de comandos (Argparse)
│   ├── __init__.py
│   └── commands.py               # Subcomandos: run, auth, status, install-browser, clear-memory
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
│   ├── browser_manager.py        # Gestor de Playwright con soporte para Chromium portable congelado
│   └── notifiers/                # Despacho de notificaciones (Microsoft Graph API y Webhooks)
├── pages/                        # Page Object Model (POM)
│   ├── __init__.py
│   ├── base_page.py              # Clase base con clics seguros, capturas en fallos y descargas
│   └── sample_portal_page.py     # Ejemplo de implementación para páginas web objetivo
├── services/                     # Capa de casos de uso y orquestación
│   ├── __init__.py
│   └── bot_service.py            # Orquestador del flujo: lectura, validación, ejecución y reporte
├── tests/                        # Suite de pruebas automatizadas (pytest)
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

## 2. Puesta en Marcha Rápida (Desarrollo)

### Requisitos Previos
* Windows 10/11 o Windows Server.
* Python 3.10 o superior instalado.

### 1. Inicializar Entorno Virtual
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Descargar Navegador Chromium Portable
Para que el bot pueda operar tanto en desarrollo como empaquetado:
```powershell
python main.py install-browser
```

### 3. Configurar Credenciales Seguras (DPAPI)
Las credenciales nunca se guardan en texto plano; se cifran con la clave del usuario de Windows:
```powershell
python main.py auth setup
```
Para verificar que las credenciales están presentes:
```powershell
python main.py auth verify
```

### 4. Ejecutar el Bot
* Modo Headless (segundo plano por defecto):
  ```powershell
  python main.py run --items "PO-1001,PO-1002"
  ```
* Modo con interfaz gráfica visible (para depuración):
  ```powershell
  python main.py run --items "PO-1001" --no-headless
  ```
* Forzar reprocesamiento (ignorando registros previos en SQLite):
  ```powershell
  python main.py run --items "PO-1001" --force
  ```

---

## 3. Generación de un Nuevo Bot desde la Plantilla

Para crear un nuevo proyecto sin copiar archivos manualmente ni arrastrar historiales viejos:

```powershell
.\new-bot.ps1 -Name "bot-sunat-detracciones" -Destination "C:\Users\jescriba\Desktop\development\bot-sunat-detracciones"
```

El script se encargará de:
1. Copiar toda la arquitectura limpia (excluyendo entornos virtuales y caches).
2. Personalizar los nombres en los scripts y comandos CLI.
3. Inicializar un repositorio Git limpio con la rama `caracteristica/scaffold-inicial`.
4. Incluir la carpeta `.agents/` para que el asistente de IA siga el mismo estándar automáticamente.

---

## 4. Pruebas y Control de Calidad

Antes de realizar cambios o empaquetar, compruebe que todas las pruebas pasen y el código cumpla los estándares de formato:

```powershell
# Ejecución de pruebas unitarias
pytest

# Análisis estático y linter
ruff check .
```

---

## 5. Compilación a Ejecutable Independiente (.exe)

Para generar la distribución binaria de producción:

```powershell
.\build.ps1
```

El binario resultante se ubicará en `dist/rpa-bot/`:
* `dist/rpa-bot/rpa-bot.exe`: Binario principal.
* `dist/rpa-bot/browsers/`: Navegador Chromium portable embebido.
* `dist/rpa-bot/downloads/`: Directorio de salida.
* `dist/rpa-bot/logs/`: Directorio para trazabilidad.

Este directorio puede comprimirse en `.zip` y distribuirse a cualquier equipo con Windows sin necesidad de tener Python ni Playwright instalados.
