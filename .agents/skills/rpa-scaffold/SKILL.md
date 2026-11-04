---
name: rpa-scaffold
description: >-
  Guía operativa y procedimental para extender, crear páginas POM, orquestar flujos y empaquetar bots RPA bajo la arquitectura estándar desacoplada (Playwright + Python + DPAPI + PyInstaller).
---

# Skill: Desarrollo y Extensión de Bots RPA Estandarizados

Esta Skill describe el flujo paso a paso para desarrollar nuevas funcionalidades o crear nuevos bots basados en esta plantilla, asegurando consistencia arquitectónica y modularidad.

---

## 1. Verificación Previa (DRY - Don't Repeat Yourself)
Antes de crear nuevas utilidades o funciones:
1. Inspeccionar `pages/base_page.py` para reutilizar métodos seguros de interacción (`safe_click`, `safe_fill`, `wait_for_element`, etc.).
2. Inspeccionar `core/database.py`, `config/security.py` e `infrastructure/browser_manager.py` para evitar duplicar lógica existente.

---

## 2. Flujo de Trabajo para Agregar una Nueva Automatización

### Paso 1: Definir los Selectores y Acciones Web en `pages/`
Cree un nuevo archivo `pages/<portal_name>_page.py` heredando de `BasePage`:

```python
from pages.base_page import BasePage
from playwright.sync_api import Page

class MiPortalPage(BasePage):
    # Selectores centralizados
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

### Paso 2: Adaptar el Modelo de Tarea en `core/models.py`
Si los datos de entrada o salida tienen campos específicos, defina un DTO claro o extienda `TaskItem` / `ExecutionResult`.

### Paso 3: Orquestar en `services/`
Incorpore la lógica de negocio en `services/bot_service.py`:
1. Comprobar si el registro ya está completado en `self.db.is_already_completed(item.item_id)` (solo si la persistencia está habilitada; es opcional).
2. Invocar los métodos del Page Object correspondiente.
3. Capturar archivos descargados con `self.capture_download(...)`.
4. Registrar el resultado inmediatamente si la base de datos está activa (`if self.db: self.db.save_record(result)`).

### Paso 4: Exponer Parámetros en `cli/commands.py`
Añada los flags o argumentos necesarios al parser de `run` (ej. `--excel`, `--fecha-inicio`, `--tipo-documento`).

---

## 3. Gestión de Credenciales en Producción
Para configurar credenciales de forma interactiva en Windows Credential Manager:
```powershell
python main.py auth setup
```
Para verificar las credenciales existentes sin revelarlas:
```powershell
python main.py auth verify
```

---

## 4. Ejecución, Calidad y Empaquetado

1. **Navegador del Sistema**:
   El bot utiliza de forma nativa Google Chrome o Microsoft Edge instalados en el sistema operativo. No se requiere descargar ni distribuir un navegador empaquetado.

2. **Ejecutar Pruebas Automatizadas**:
   ```powershell
   pytest
   ```

3. **Verificar Calidad de Código**:
   ```powershell
   ruff check .
   ```

4. **Compilar a Ejecutable (.exe)**:
   ```powershell
   .\build.ps1
   ```
   El binario independiente quedará generado en `dist/rpa-bot/` listo para distribución.
