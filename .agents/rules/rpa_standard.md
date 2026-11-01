# Estándar Arquitectónico y de Seguridad para Bots RPA (Playwright + Python)

Este documento define la arquitectura obligatoria e inmutable que cualquier agente de IA o desarrollador debe respetar al crear, modificar o extender bots en este repositorio.

---

## 1. Regla de Oro: Arquitectura por Capas Inmutable
Queda estrictamente prohibido improvisar estructuras de carpetas alternativas (como meter todo en scripts sueltos, crear monolitos en `src/`, o dispersar selectores web). Todo bot RPA debe ceñirse a las 7 capas estándar:

1. **`cli/`**: Interfaz de consola (`commands.py`), puntos de entrada y subcomandos (`run`, `auth`, `status`, `install-browser`).
2. **`config/`**: Configuración centralizada (`settings.py`), logging rotativo (`logger_config.py`) y seguridad DPAPI (`security.py`).
3. **`core/`**: Modelos de datos (`models.py`) y base SQLite local para idempotencia y memoria de ejecuciones (`database.py`).
4. **`infrastructure/`**: Ciclo de vida del navegador Chromium (`browser_manager.py`) y conectores de red externos (`notifiers/`).
5. **`pages/`**: Page Object Model (POM). Cada pantalla o portal web debe aislarse en su propia clase heredando de `BasePage`. **Ningún selector CSS o XPath puede vivir fuera de `pages/`**.
6. **`services/`**: Orquestación del caso de uso (`bot_service.py`). Coordina insumos, consulta idempotencia en SQLite, comanda acciones web a `pages/`, guarda resultados y dispara alertas.
7. **`tests/`**: Pruebas unitarias e integración simulada con `pytest`.

---

## 2. Seguridad y Credenciales (DPAPI Obligatorio)
* **Cero contraseñas en código o `.env` planos**: Toda clave o token de portales debe gestionarse mediante Windows Credential Manager (DPAPI) usando `keyring` a través de `config/security.py`.
* **Sanitización de URLs**: Toda navegación web debe validar protocolo HTTPS y pertenencia a dominios autorizados mediante `validate_url()`.
* **Protección de Datos Sensibles**: Nunca exponer en logs, pantallas ni reportes de chat contraseñas o tokens. Usar placeholders (`<SECRET>`, `<API_KEY>`).

---

## 3. Idempotencia y Tolerancia a Fallos
* **Memoria en SQLite (`bot_memory.db`)**: Antes de interactuar con el navegador para un registro o ID, el orquestador **debe** consultar `db.is_already_completed(item_id)`. Si ya fue completado exitosamente, debe omitirse (*SKIPPED*) salvo que se use el flag `--force`.
* **Registro Inmediato**: Cada resultado (éxito o fallo) se persiste en base de datos inmediatamente tras su intento, garantizando que si el bot se interrumpe, pueda reanudarse exactamente donde quedó.

---

## 4. Estrategia de Navegación y Empaquetado
* **Navegadores Nativos**: El bot debe conectarse por defecto a Google Chrome (`channel="chrome"`). Si no está disponible, debe conmutar automáticamente a Microsoft Edge (`channel="msedge"`). Si ninguno existe, debe fallar de forma controlada (`BrowserNotFoundError`) y notificar el error.
* **Modo Headless**: Por defecto, la ejecución gráfica es visible para supervisión del operador. Si se especifica el flag `--headless`, se ejecuta en segundo plano.
* **Script de Build**: El empaquetado debe realizarse exclusivamente mediante el script `build.ps1` configurado con `--onedir` y los `--hidden-import` requeridos.

---

## 5. Calidad de Código y Pruebas
* **Convención de Nombres**: Clases, métodos y variables en inglés técnico (`SamplePortalPage`, `process_items`).
* **Type Hints**: Obligatorios en todos los argumentos y retornos de función.
* **Verificación de Linters**: Ejecutar `ruff check .` y `pytest` antes de considerar terminada cualquier modificación.
