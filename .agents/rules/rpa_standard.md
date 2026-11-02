# Reglas Obligatorias y Estándar de Desarrollo para Bots RPA (STN Framework)

Este documento define las directrices y restricciones obligatorias que **todo agente de IA o desarrollador** debe acatar sin excepción al crear, modificar o extender bots en este repositorio o en proyectos derivados de esta plantilla.

---

## 1. Regla de Oro: Arquitectura por Capas Inmutable
Queda estrictamente prohibido improvisar estructuras de carpetas alternativas (como meter todo en scripts sueltos, crear monolitos en `src/`, o dispersar selectores web). Todo bot RPA debe ceñirse a las 7 capas estándar:

1. **`cli/`**: Interfaz de consola (`commands.py`), puntos de entrada y subcomandos (`run`, `auth`, `status`, `clear-memory`).
2. **`config/`**: Configuración centralizada (`settings.py`), logging rotativo (`logger_config.py`) y seguridad DPAPI (`security.py`).
3. **`core/`**: Modelos de datos (`models.py`) y base SQLite local para idempotencia y auditoría de ejecuciones (`database.py`).
4. **`infrastructure/`**: Ciclo de vida del navegador (`browser_manager.py`) y adaptadores de red externos (`notifiers/`).
5. **`pages/`**: Page Object Model (POM). Cada pantalla o portal web debe aislarse en su propia clase heredando de `BasePage`. **Ningún selector CSS o XPath puede vivir fuera de `pages/`**.
6. **`services/`**: Orquestación del caso de uso (`bot_service.py`). Coordina insumos, consulta idempotencia en SQLite, comanda acciones web a `pages/`, guarda resultados y dispara alertas.
7. **`tests/`**: Pruebas unitarias e integración simulada con `pytest`.

---

## 2. Estrategia Obligatoria de Navegación (Chrome -> Edge -> Fallo Controlado)
* **Cero descargas pesadas**: Queda prohibido obligar a descargar o congelar binarios portables de Chromium (300+ MB) en entornos donde ya existan navegadores de sistema.
* **Prioridad 1 (Google Chrome)**: El bot debe intentar instanciar por defecto Google Chrome (`channel="chrome"`).
* **Prioridad 2 (Microsoft Edge - Fallback)**: Si Chrome no está instalado, el bot debe conmutar automáticamente a Microsoft Edge (`channel="msedge"`).
* **Fallo Controlado con Notificación**: Si ninguno de los dos navegadores está disponible, el sistema debe disparar la excepción `BrowserNotFoundError`, registrar el error y despachar una notificación de alerta inmediata al operador (*fail-fast*).

---

## 3. Estándar de Argumentos CLI (`--headless`)
* **Presencia Obligatoria**: En la consola de comandos (`cli/commands.py`), la acción `run` debe incluir **siempre** el argumento `--headless`.
* **Comportamiento**:
  * **Por defecto (`False`)**: La ejecución inicia con la ventana gráfica del navegador **visible** para permitir la supervisión visual del operador.
  * **Con el flag presente (`True`)**: Si el usuario especifica `--headless`, el bot opera en segundo plano sin interfaz gráfica (modo servidor / scheduled task).

---

## 4. Control de Versiones, Ramas y GitHub CLI (`gh`)
* **Protección de `main`**: Queda estrictamente prohibido trabajar o realizar commits directamente sobre `main` o `master`.
* **Ramas de trabajo desde `main`**: Todo cambio debe desarrollarse en una rama específica creada a partir de la última versión de `main`, usando nombres descriptivos en español con kebab-case:
  * `caracteristica/nombre-descriptivo` (nuevas funcionalidades)
  * `mejora/nombre-descriptivo` (optimizaciones)
  * `correccion/nombre-descriptivo` (corrección de errores)
  * `refactor/nombre-descriptivo` (refactorizaciones)
* **Subida y Pull Requests con `gh`**: Todos los cambios deben subirse al repositorio remoto y fusionarse mediante la GitHub CLI (`gh pr create`, `gh pr merge`).
* **Conventional Commits**: Todo commit debe seguir la especificación oficial v1.0.0 (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).

---

## 5. Actualización Obligatoria de Documentación (`README.md`)
* **Regla tras cada `feat`**: Tras implementar cada nueva funcionalidad o cambio de comportamiento, **es obligatorio actualizar el archivo `README.md`** del repositorio antes de dar por concluida la tarea o fusionar el Pull Request.
* El `README.md` debe ser siempre el reflejo exacto y actualizado de cómo configurar, ejecutar y operar el bot.

---

## 6. Seguridad y Credenciales (DPAPI Obligatorio)
* **Cero contraseñas en código o `.env` planos**: Toda clave o token de portales debe gestionarse mediante Windows Credential Manager (DPAPI) usando `keyring` a través de `config/security.py`.
* **Sanitización de URLs**: Toda navegación web debe validar protocolo HTTPS y pertenencia a dominios autorizados mediante `validate_url()`.
* **Protección de Datos Sensibles**: Nunca exponer en logs, pantallas ni reportes de chat contraseñas o tokens. Usar placeholders (`<SECRET>`, `<API_KEY>`).

---

## 7. Idempotencia y Tolerancia a Fallos
* **Memoria en SQLite (`bot_memory.db`)**: Antes de interactuar con el navegador para un registro o ID, el orquestador **debe** consultar `db.is_already_completed(item_id)`. Si ya fue completado exitosamente, debe omitirse (*SKIPPED*) salvo que se use el flag `--force`.
* **Registro Inmediato**: Cada resultado (éxito o fallo) se persiste en base de datos inmediatamente tras su intento, garantizando que si el bot se interrumpe, pueda reanudarse exactamente donde quedó.

---

## 8. Calidad de Código y Pruebas
* **Convención de Nombres**: Clases, métodos y variables en inglés técnico (`SamplePortalPage`, `process_items`).
* **Type Hints**: Obligatorios en todos los argumentos y retornos de función.
* **Verificación de Linters**: Ejecutar `ruff check .` y `pytest` confirmando 100% de éxito antes de hacer commit.
