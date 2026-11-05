# Reglas Obligatorias y Estándar de Desarrollo para Bots RPA

Este documento define las directrices y restricciones obligatorias que **todo agente de IA o desarrollador** debe acatar sin excepción al crear, modificar o extender bots en este repositorio o en proyectos derivados de esta plantilla.

---

## 1. Cero Sobreingeniería y Simplicidad Radical (KISS / YAGNI / DRY)
* **Preguntar antes de asumir**: Si un requerimiento o flujo no queda 100% claro, es obligatorio preguntar al usuario y **nunca tomar decisiones técnicas en solitario**.
* **Verificación previa de existencia (DRY)**: Antes de implementar cualquier componente, función o utilidad, verificar si ya existe en el repositorio para reutilizar y evitar duplicar código.
* **Economía de código**: Si una solución se puede implementar en 3 líneas de código, queda prohibido extenderla a 20. Buscar siempre la sencillez técnica.
* **Cero fallbacks silenciosos no solicitados**: Prohibido implementar mecanismos de fallback heurísticos, cascadas de consulta o valores inventados que no hayan sido expresamente solicitados por el usuario. Si algo falla o no se encuentra, fallar de forma controlada (*fail-fast*).

---

## 2. Responsabilidad Única (SRP) y Modularidad
* **Una función hace una sola tarea**: Cada función, método y clase debe tener un propósito único y bien delimitado.
* **Control de tamaño de archivos**: Prohibido crear archivos monolíticos o inmensos.
* **Alerta de refactorización**: Si para mantener el orden, la legibilidad o desacoplar componentes es necesario refactorizar archivos existentes, se debe alertar y notificar previamente de tal hecho.

---

## 3. Entornos Virtuales Obligatorios y Dependencias
* **Entornos virtuales obligatorios (`.venv`)**: Todo desarrollo, prueba y ejecución debe realizarse estrictamente dentro de un entorno virtual creado con `python -m venv .venv`.
* **Prohibición de instalaciones globales**: Queda terminantemente prohibido instalar librerías o dependencias en el intérprete global de Python del sistema.
* **Mantenimiento estricto de `requirements.txt`**: Todo paquete o dependencia nueva debe registrarse de inmediato en `requirements.txt` con su versión correspondiente para asegurar reproducibilidad.

---

## 4. Documentación en Español y Código Autoleíble
* **Idioma de documentación**: Toda la documentación de proyecto (`README.md`, `MEMORY.md`, manuales) y los docstrings del código deben redactarse en **español** (manteniendo en inglés únicamente términos técnicos estándar como *timeout*, *payload*, *headless*, *channel*, etc.).
* **Comentarios estrictamente necesarios**: El código debe ser limpio y autoleíble. No escribir comentarios obvios que repitan lo que el código hace. Reservar comentarios únicamente para explicar decisiones de negocio complejas o no evidentes.
* **Nombres de símbolos en inglés técnico**: Nombres de clases, variables, funciones y métodos se redactan en inglés técnico (`process_items`, `BotDatabase`, etc.).

---

## 5. Calidad de Código, Linters y Salida de Consola con Rich
* **Ejecución previa a commits**: Antes de confirmar cualquier cambio, es obligatorio ejecutar el linter (`ruff check .`) y la suite de pruebas (`pytest`), ajustando el código a sus estándares.
* **Librería Rich Obligatoria**: Todas las tablas de resumen, paneles de alerta y estados de ejecución en terminal deben construirse con **`rich`** (`Console`, `Table`, `Panel`), manteniendo formato sobrio y profesional sin emoticones.
* **Criterio de omisión**: Solo se permite omitir advertencias del linter cuando exista una justificación técnica real y explícita, sin convertirse en un bloqueador dogmático.

---

## 6. Directrices de Interfaz de Usuario (UI / Máscara Web)
* **Stack Vanilla**: De requerirse una interfaz o máscara visual de usuario, se debe utilizar exclusivamente **HTML5, CSS3 y JavaScript Vanilla** nativo (sin frameworks pesados innecesarios).
* **Prohibición de Emoticones (Emojis)**: Queda terminantemente prohibido usar emoticones o emojis Unicode en botones, etiquetas, tablas o consola.
* **Iconografía Profesional**: Utilizar siempre iconos vectoriales profesionales de **Font Awesome Free** (`<i class="fa-solid fa-nombre-icono"></i>`) o Bootstrap Icons.
* **Estilo Visual Oscuro (Dark Theme)**: La máscara debe tener una estética moderna, limpia y minimalista con paleta oscura inspirada en la interfaz del chat de Gemini (`#131314` de fondo, `#1e1f20` en tarjetas/superficies, bordes `#3c4043` y acentos `#a8c7fa`).

---

## 7. Gestión de Credenciales en Windows DPAPI y Aislamiento por Bot
* **Menú de Selección**: Al ejecutar `python main.py auth`, debe desplegarse un menú interactivo en consola para elegir qué servicio configurar:
  1. App Web (Portal objetivo)
  2. App Interna / ERP (Sistema interno)
  3. Conexión de Base de Datos
  4. Microsoft Graph API
  5. Destinatarios Microsoft Outlook Local
* **Aislamiento de Nombres de Servicio DPAPI**: Dado que Windows Credential Manager almacena credenciales por usuario del sistema operativo, **cada bot debe definir nombres de servicio únicos** con su propio prefijo en `config/settings.py` (ej. `BOT_SUNAT_TARGET_PORTAL`, `BOT_TRADELINK_DATABASE`) para evitar colisiones o sobrescrituras entre bots en la misma máquina.
* **Cero secretos en código o `.env`**: Toda clave sensible se cifra mediante Windows Credential Manager (DPAPI) con `keyring`.
* **Ocultamiento de Infraestructura**: En respuestas de consola (`auth verify`) y reportes, queda prohibido exponer nombres reales de servidores internos o bases de datos; mostrar únicamente si el componente está configurado.
* **Contexto de Sesión Windows**: Para tareas programadas desatendidas (Windows Task Scheduler), la configuración con `auth` debe realizarse bajo la misma cuenta de servicio que ejecutará el proceso.

---

## 8. Sistema de Notificaciones Dual (`--notify-graph` y `--notify-outlook`)
* **Flag `--notify-graph` (Microsoft Graph API)**:
  * Despacha reportes por correo corporativo en la nube (Azure AD).
  * Los correos destinatarios se separan exclusivamente por punto y coma (`;`).
  * **Validación estricta (Fail-Fast)**: Si no se proporcionan correos válidos (vía `--emails` o DPAPI), el bot debe notificar del error y cerrarse inmediatamente sin procesar nada.
* **Flag `--notify-outlook` (Microsoft Outlook Local)**:
  * Envía el reporte utilizando la configuración/perfil actual de Outlook del equipo cliente.
  * **No requiere que Outlook esté abierto**: La automatización se comunica en segundo plano vía COM sin esperar a que el usuario tenga la aplicación visible.

---

## 9. Estrategia de Navegación, Memoria Local y Persistencia
* **Navegadores Nativos Locales**: Usar por defecto Google Chrome (`channel="chrome"`). Si no está disponible, conmutar automáticamente a Microsoft Edge (`channel="msedge"`). No se requiere descargar ni distribuir navegadores congelados o portables.
* **Flag `--headless` Obligatorio**: Todo comando `run` debe incluir `--headless`. Por defecto corre con ventana visible (`False`); si se invoca el flag, corre en segundo plano (`True`). En servidores o tareas programadas desatendidas, es obligatorio incluir `--headless`.
* **Persistencia como Decisión de Arquitectura (Sin flag en ejecución)**: La persistencia para reanudar tareas interrumpidas (fallback de recuperación) o asegurar idempotencia se define durante el diseño inicial de la solución según los requerimientos del proyecto, nunca mediante un flag de ejecución (`--no-db` eliminado).
* **Registro de Memoria con Fecha y Hora Local**:
  * Toda operación almacena en memoria (`task_records`) la fecha y hora local del sistema (`started_at`, `finished_at`, `created_at`, `updated_at`).
  * Esta tabla es de carácter **meramente informativo y de telemetría**.
  * **Operación no bloqueante**: La inserción o actualización de la memoria jamás debe detener ni hacer fallar el flujo operativo del bot si ocurre un error en la base de datos SQLite.

---

## 10. Compilación Limpia con PyInstaller (Sin archivos `*.spec`)
* **Instrucciones Obligatorias**: Todo bot debe incluir instrucciones en `README.md` y un script automatizado `build.ps1` para compilar con PyInstaller.
* **Compilación Limpia sin `.spec`**: La compilación debe ejecutarse directamente mediante comandos y flags de PyInstaller (`pyinstaller --noconfirm --onedir ...`), sin mantener ni depender de archivos `*.spec` que acumulan desincronizaciones de dependencias.
* **Icono Corporativo**: Toda compilación debe incluir el icono corporativo configurado mediante `--icon "assets/icons/python.ico"`.

---

## 11. Estructura Estándar de `README.md`
Todo `README.md` debe seguir rigurosamente las siguientes 8 secciones:
1. **Propósito y Descripción**
2. **Stack Tecnológico y Arquitectura**
3. **Prerrequisitos del Sistema**
4. **Configuración del Entorno de Desarrollo (`.venv`)**
5. **Configuración de Variables de Entorno y Credenciales (DPAPI)**
6. **Ejecución del Bot (Comandos CLI)**
7. **Estructura del Proyecto**
8. **Distribución y Configuración (Compilación limpia PyInstaller)**

---

## 12. Control de Versiones, Ramas e Higiene de Repositorio
* **Protección de `main`**: Nunca trabajar ni hacer commits directamente sobre `main` o `master`.
* **Ramas desde `main`**: Crear siempre ramas de trabajo específicas desde `main` en español kebab-case (`caracteristica/...`, `mejora/...`, `correccion/...`, `refactor/...`).
* **Gestión de PRs con `gh`**: Subir cambios y fusionarlos mediante la GitHub CLI (`gh pr create`, `gh pr merge`).
* **Higiene estricta de `.gitignore`**: Todo archivo o carpeta que no forme parte del core del repositorio debe estar ignorado en `.gitignore` o almacenado dentro de la carpeta `.trash/` (expresamente ignorada).
* **Memoria Operativa Continua (`MEMORY.md`)**: Mantener siempre actualizado `MEMORY.md` en la raíz del repositorio tras cada `feat` o refactorización.
