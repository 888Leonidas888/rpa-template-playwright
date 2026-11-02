# Reglas Obligatorias y Estándar de Desarrollo para Bots RPA (STN Framework)

Este documento define las directrices y restricciones obligatorias que **todo agente de IA o desarrollador** debe acatar sin excepción al crear, modificar o extender bots en este repositorio o en proyectos derivados de esta plantilla.

---

## 1. Cero Sobreingeniería y Simplicidad Radical (KISS / YAGNI)
* **Preguntar antes de asumir**: Si un requerimiento o flujo no queda 100% claro, es obligatorio preguntar al usuario y **nunca tomar decisiones técnicas en solitario**.
* **Economía de código**: Si una solución se puede implementar en 3 líneas de código, queda prohibido extenderla a 20. Buscar siempre la sencillez técnica.
* **Cero fallbacks silenciosos no solicitados**: Prohibido implementar mecanismos de fallback heurísticos, cascadas de consulta o valores inventados que no hayan sido expresamente solicitados por el usuario. Si algo falla o no se encuentra, fallar de forma controlada (*fail-fast*).

---

## 2. Responsabilidad Única (SRP) y Modularidad
* **Una función hace una sola tarea**: Cada función, método y clase debe tener un propósito único y bien delimitado.
* **Control de tamaño de archivos**: Prohibido crear archivos monolíticos o inmensos.
* **Alerta de refactorización**: Si para mantener el orden, la legibilidad o desacoplar componentes es necesario refactorizar archivos existentes, se debe alertar y notificar previamente de tal hecho.

---

## 3. Documentación en Español y Código Autoleíble
* **Idioma de documentación**: Toda la documentación de proyecto (`README.md`, `MEMORY.md`, manuales) y los docstrings del código deben redactarse en **español**.
* **Comentarios estrictamente necesarios**: El código debe ser limpio y autoleíble. No escribir comentarios obvios que repitan lo que el código hace. Reservar comentarios únicamente para explicar decisiones de negocio complejas o no evidentes.
* **Nombres de símbolos en inglés técnico**: Nombres de clases, variables, funciones y métodos se redactan en inglés técnico (`process_items`, `BotDatabase`, etc.).

---

## 4. Calidad de Código y Linters Obligatorios
* **Ejecución previa a commits**: Antes de confirmar cualquier cambio, es obligatorio ejecutar el linter (`ruff check .`) y la suite de pruebas (`pytest`), ajustando el código a sus estándares.
* **Criterio de omisión**: Solo se permite omitir advertencias del linter cuando exista una justificación técnica real y explícita, sin convertirse en un bloqueador dogmático.

---

## 5. Directrices de Interfaz de Usuario (UI / Máscara Web)
* **Stack Vanilla**: De requerirse una interfaz o máscara visual de usuario, se debe utilizar exclusivamente **HTML5, CSS3 y JavaScript Vanilla** nativo (sin frameworks pesados innecesarios).
* **Prohibición de Emoticones (Emojis)**: Queda terminantemente prohibido usar emoticones o emojis Unicode (🚀, 💾, ⚙️, ❌) en botones, etiquetas, tablas o consola.
* **Iconografía Profesional**: Utilizar siempre iconos vectoriales profesionales de **Font Awesome Free** (`<i class="fa-solid fa-nombre-icono"></i>`) o Bootstrap Icons.
* **Estilo Visual Oscuro (Dark Theme)**: La máscara debe tener una estética moderna, limpia y minimalista con paleta oscura inspirada en la interfaz del chat de Gemini (`#131314` de fondo, `#1e1f20` en tarjetas/superficies, bordes `#3c4043` y acentos `#a8c7fa`).

---

## 6. Gestión de Credenciales y Menú Interactivo en `auth`
* **Menú de Selección**: Al ejecutar `python main.py auth`, debe desplegarse un menú interactivo en consola para elegir qué servicio configurar:
  1. App Web (Portal objetivo)
  2. App SIGE (Sistema interno)
  3. Conexión de Base de Datos
  4. Microsoft Graph API
  5. Destinatarios Microsoft Outlook Local
* **Cero secretos en código o `.env`**: Toda clave se cifra mediante Windows Credential Manager (DPAPI) con `keyring`.

---

## 7. Sistema de Notificaciones Dual (`--notify-graph` y `--notify-outlook`)
* **Flag `--notify-graph` (Microsoft Graph API)**:
  * Despacha reportes por correo corporativo en la nube (Azure AD).
  * Los correos destinatarios se separan exclusivamente por punto y coma (`;`).
  * **Validación estricta (Fail-Fast)**: Si no se proporcionan correos válidos (vía `--emails` o DPAPI), el bot debe notificar del error y cerrarse inmediatamente sin procesar nada.
* **Flag `--notify-outlook` (Microsoft Outlook Local)**:
  * Envía el reporte utilizando la configuración/perfil actual de Outlook del equipo cliente.
  * **No requiere que Outlook esté abierto**: La automatización se comunica en segundo plano vía COM sin esperar a que el usuario tenga la aplicación visible.

---

## 8. Estrategia de Navegación y Argumento `--headless`
* **Navegadores Nativos**: Usar por defecto Google Chrome (`channel="chrome"`). Si no está disponible, conmutar automáticamente a Microsoft Edge (`channel="msedge"`). Si ninguno existe, fallar con `BrowserNotFoundError` y notificar el error.
* **Flag `--headless` Obligatorio**: Todo comando `run` debe incluir `--headless`. Por defecto corre con ventana visible (`False`); si se invoca el flag, corre en segundo plano (`True`).

---

## 9. Control de Versiones, Ramas e Higiene de Repositorio
* **Protección de `main`**: Nunca trabajar ni hacer commits directamente sobre `main` o `master`.
* **Ramas desde `main`**: Crear siempre ramas de trabajo específicas desde `main` en español kebab-case (`caracteristica/...`, `mejora/...`, `correccion/...`, `refactor/...`).
* **Gestión de PRs con `gh`**: Subir cambios y fusionarlos mediante la GitHub CLI (`gh pr create`, `gh pr merge`).
* **Higiene estricta de `.gitignore`**: Todo archivo o carpeta que no forme parte del core del repositorio debe estar ignorado en `.gitignore` o almacenado dentro de la carpeta `.trash/` (expresamente ignorada).

---

## 10. Memoria Operativa Continua (`MEMORY.md`)
* Es obligatorio crear y mantener siempre actualizado el archivo **`MEMORY.md`** en la raíz del repositorio, reflejando el flujo de ejecución, las decisiones de diseño y el estado actual del bot.
