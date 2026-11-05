# Directrices Obligatorias para Agentes de IA (RPA Playwright Bot Framework)

Bienvenido. Este repositorio define la plantilla y marco de trabajo estándar para bots RPA corporativos con Python y Playwright.

Al trabajar en este proyecto o en cualquier bot derivado de él, debes seguir estrictamente las 12 reglas fundamentales documentadas en [.agents/rules/rpa_standard.md](.agents/rules/rpa_standard.md):

---

### Resumen Operativo de las 12 Reglas:

1. **Cero Sobreingeniería y DRY**:
   - Preguntar antes de asumir; prohibido tomar decisiones técnicas en solitario.
   - Antes de implementar cualquier componente, función o utilidad, verificar si ya existe en el repositorio para evitar duplicar código (DRY).
   - Si una solución cabe en 3 líneas, no hacerla en 20 (KISS).
   - Prohibidos los fallbacks silenciosos no solicitados (*fail-fast*).
2. **Responsabilidad Única (SRP)**:
   - Una función hace una tarea. No crear archivos monolíticos inmensos.
   - Alertar al usuario si es necesario refactorizar para mantener el orden.
3. **Entornos Virtuales Obligatorios (`.venv`) y Dependencias**:
   - Trabajar siempre sobre `python -m venv .venv`; nunca instalar librerías globalmente.
   - Mantener rigurosamente actualizado `requirements.txt`.
4. **Documentación en Español y Código Autoleíble**:
   - Documentación (`README.md`, `MEMORY.md`) y docstrings en español.
   - Comentarios estrictamente necesarios; el código debe ser autoleíble por sí mismo.
5. **Linters y Formato con Rich**:
   - Ejecutar `ruff check .` y `pytest` antes de confirmar cualquier cambio.
   - Todas las tablas, paneles y salidas CLI deben utilizar la librería `rich` (sin emoticones).
6. **Máscara Web (UI)**:
   - De requerirse interfaz, usar únicamente **HTML5, CSS y JavaScript Vanilla**.
   - Prohibido emojis en UI o consola; usar exclusivamente **Font Awesome** o Bootstrap Icons.
   - Estilo visual oscuro Gemini (`#131314` fondo, `#1e1f20` tarjetas, `#a8c7fa` acentos).
7. **Menú de Credenciales en `auth` y Aislamiento DPAPI**:
   - Menú interactivo para configurar App Web, App Interna / ERP, Base de Datos, Microsoft Graph (correos con `;`) y Outlook local en Windows DPAPI.
   - Cada bot debe definir sus propios nombres de servicio únicos con prefijo en `config/settings.py` para aislar sus credenciales en Windows Credential Manager.
   - Ocultar nombres de infraestructura interna en consola.
8. **Notificaciones Duales**:
   - `--notify-graph`: Envía por Graph API; requiere correos separados por `;` (cierre inmediato con error si faltan).
   - `--notify-outlook`: Envía por Outlook local en segundo plano (sin esperar que Outlook esté abierto).
9. **Navegador Nativo del Sistema**:
   - Uso de Google Chrome o Microsoft Edge instalados en el sistema (sin navegadores portables).
   - Flag `--headless` por defecto `False`, si se especifica pasa a `True`.
10. **Memoria Local y Persistencia Arquitectural**:
    - Persistencia SQLite es una decisión de arquitectura inicial (para reanudar tareas o idempotencia), no un flag CLI (`--no-db` eliminado).
    - Registro de memoria con fecha/hora local del sistema (`started_at`, `finished_at`, `created_at`, `updated_at`).
    - Guardado informativo y no bloqueante: fallos en SQLite jamás detienen el bot.
11. **Compilación Limpia con PyInstaller (Sin `*.spec`)**:
    - Compilación directa por línea de comandos sin mantener archivos `*.spec`.
    - Inclusión obligatoria del icono corporativo (`--icon "assets/icons/python.ico"`).
12. **Higiene de Repositorio, `MEMORY.md` y `README.md` Estandarizado**:
    - `README.md` estructurado en sus 8 secciones fijas.
    - Ignorar todo archivo no-core en `.gitignore` o moverlo a `.trash/` (ignorada).
    - Mantener siempre actualizado `MEMORY.md` tras cada `feat` o refactor.
    - Nunca trabajar sobre `main`; usar ramas kebab-case desde `main` y gestionar cambios con `gh`.
