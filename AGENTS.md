# Instrucciones para Agentes de IA (STN RPA Playwright Bot Framework)

Bienvenido. Este repositorio define la plantilla y marco estándar para bots RPA corporativos con Python y Playwright.

Al trabajar en este proyecto o en cualquier bot derivado de él, debes seguir estrictamente las directrices documentadas en [.agents/rules/rpa_standard.md](.agents/rules/rpa_standard.md).

---

## Directrices Críticas de Cumplimiento Inmediato:

1. **Arquitectura en 7 Capas**:
   - `cli/`, `config/`, `core/`, `infrastructure/`, `pages/`, `services/`, `tests/`.
   - Ningún selector web fuera de `pages/` (Page Object Model).

2. **Estrategia de Navegación**:
   - Google Chrome por defecto (`channel="chrome"`).
   - Microsoft Edge como fallback automático (`channel="msedge"`).
   - Fallo controlado con excepción `BrowserNotFoundError` y notificación si ninguno está disponible.
   - Prohibido forzar navegadores congelados o descargas innecesarias.

3. **Argumento CLI `--headless`**:
   - Por defecto: Ejecución visible (`headless=False`).
   - Con flag: Ejecución en segundo plano (`headless=True`).

4. **Flujo Git y GitHub CLI**:
   - NUNCA comitear en `main`.
   - SIEMPRE crear ramas descriptivas desde `main` (`caracteristica/...`, `mejora/...`, `correccion/...`).
   - Gestionar commits bajo Conventional Commits v1.0.0.
   - Gestionar Pull Requests y subidas con `gh` (`gh pr create`, `gh pr merge`).

5. **Documentación Obligatoria**:
   - Tras CADA nueva funcionalidad (`feat`) o modificación, es obligatorio actualizar el `README.md`.

6. **Seguridad DPAPI y Calidad**:
   - Credenciales exclusivamente en Windows DPAPI (`keyring` / `config/security.py`).
   - Verificar siempre `pytest` y `ruff check .` antes de finalizar cualquier tarea.
