# Directrices Obligatorias para Agentes de IA (STN RPA Playwright Bot Framework)

Bienvenido. Este repositorio define la plantilla y marco de trabajo estándar para bots RPA corporativos con Python y Playwright.

Al trabajar en este proyecto o en cualquier bot derivado de él, debes seguir estrictamente las 10 reglas fundamentales documentadas en [.agents/rules/rpa_standard.md](.agents/rules/rpa_standard.md):

---

### Resumen Operativo de las 10 Reglas:

1. **Cero Sobreingeniería**:
   - Preguntar antes de asumir; prohibido tomar decisiones técnicas en solitario.
   - Si una solución cabe en 3 líneas, no hacerla en 20 (KISS).
   - Prohibidos los fallbacks silenciosos no solicitados.
2. **Responsabilidad Única (SRP)**:
   - Una función hace una tarea. No crear archivos monolíticos inmensos.
   - Alertar al usuario si es necesario refactorizar para mantener el orden.
3. **Documentación en Español y Código Autoleíble**:
   - Documentación (`README.md`, `MEMORY.md`) y docstrings en español.
   - Comentarios estrictamente necesarios; el código debe ser autoleíble por sí mismo.
4. **Linters y Formato con Rich**:
   - Ejecutar `ruff check .` y `pytest` antes de confirmar cualquier cambio.
   - Todas las tablas, paneles y salidas CLI deben utilizar la librería `rich` (sin emoticones).
5. **Máscara Web (UI)**:
   - De requerirse interfaz, usar únicamente **HTML5, CSS y JavaScript Vanilla**.
6. **Cero Emoticones (Iconos Profesionales)**:
   - Prohibido emojis en UI o consola; usar exclusivamente **Font Awesome** o Bootstrap Icons.
7. **Estilo Dark Theme**:
   - Colores oscuros estilo Gemini (`#131314` fondo, `#1e1f20` tarjetas, `#a8c7fa` acentos).
8. **Menú de Credenciales en `auth` y Ocultamiento de Datos**:
   - Menú interactivo para configurar App Web, App SIGE, Base de Datos, Microsoft Graph (correos con `;`) y Outlook local en Windows DPAPI.
   - Ocultar nombres de infraestructura interna en consola. Configurar bajo la cuenta que ejecutará la tarea programada.
9. **Notificaciones Duales y Validación Estricta**:
   - `--notify-graph`: Envia por Graph API; requiere correos separados por `;` (cierre inmediato con error si faltan).
   - `--notify-outlook`: Envia por Outlook local en segundo plano (sin esperar que Outlook esté abierto).
10. **Higiene de Repositorio y `MEMORY.md`**:
    - Ignorar todo archivo no-core en `.gitignore` o moverlo a la carpeta `.trash/` (ignorada).
    - Mantener siempre actualizado `MEMORY.md` y `README.md` tras cada `feat`.
    - Nunca trabajar sobre `main`; usar ramas kebab-case desde `main` y gestionar cambios con `gh`.
