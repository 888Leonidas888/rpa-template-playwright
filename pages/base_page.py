"""Page Object Model base que provee metodos seguros y resilientes de interaccion web."""

import time
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Download, Locator, Page

from config.logger_config import get_logger
from config.settings import LOGS_DIR, PAGE_TIMEOUT_MS

logger = get_logger()


class BasePage:
    """Clase base para todas las representaciones de Page Object Model.

    Encapsula interacciones resilientes, reintentos, capturas de pantalla ante errores
    y gestion de descargas.
    """

    def __init__(self, page: Page) -> None:
        """Inicializa el Page Object con la pagina activa de Playwright.

        Args:
            page: Instancia activa de la pagina Playwright.
        """
        self.page = page

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navega a la URL especificada registrando en el logger."""
        logger.info("Navegando a: %s", url)
        self.page.goto(url, wait_until=wait_until)  # type: ignore

    def safe_click(
        self,
        selector: str,
        timeout_ms: int = PAGE_TIMEOUT_MS,
        retries: int = 2,
    ) -> None:
        """Hace clic en un elemento con logica de reintentos y captura de pantalla ante fallos.

        Args:
            selector: Selector CSS o XPath del elemento.
            timeout_ms: Tiempo maximo de espera para que sea clickeable.
            retries: Cantidad de reintentos si el clic falla.
        """
        for attempt in range(1, retries + 1):
            try:
                locator: Locator = self.page.locator(selector).first
                locator.wait_for(state="visible", timeout=timeout_ms)
                locator.click(timeout=timeout_ms)
                return
            except Exception as e:
                logger.warning(
                    "Intento de clic %s/%s fallido en selector '%s': %s",
                    attempt,
                    retries,
                    selector,
                    e,
                )
                if attempt == retries:
                    self.take_screenshot(f"error_click_{int(time.time())}.png")
                    raise

    def safe_fill(
        self,
        selector: str,
        value: str,
        timeout_ms: int = PAGE_TIMEOUT_MS,
    ) -> None:
        """Escribe en un campo de texto tras asegurar su visibilidad.

        Args:
            selector: Selector CSS o XPath del campo de entrada.
            value: Texto a ingresar.
            timeout_ms: Tiempo maximo de espera para el elemento.
        """
        try:
            locator: Locator = self.page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout_ms)
            locator.fill(value)
        except Exception as e:
            logger.error("Fallo al escribir en selector '%s': %s", selector, e)
            self.take_screenshot(f"error_fill_{int(time.time())}.png")
            raise

    def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout_ms: int = PAGE_TIMEOUT_MS,
    ) -> bool:
        """Espera a que un elemento alcance un estado y retorna True si aparece, False si vence el timeout.

        Args:
            selector: Selector CSS o XPath.
            state: Estado deseado ('visible', 'attached', 'detached', 'hidden').
            timeout_ms: Tiempo maximo de espera en milisegundos.

        Returns:
            bool: True si el elemento alcanzo el estado dentro del tiempo, False en caso contrario.
        """
        try:
            self.page.locator(selector).first.wait_for(state=state, timeout=timeout_ms)  # type: ignore
            return True
        except Exception:
            return False

    def capture_download(
        self,
        trigger_action: Callable[[], None],
        target_dir: Path,
        suggested_name: str | None = None,
        timeout_ms: int = 60000,
    ) -> Path:
        """Ejecuta una accion disparadora, espera el evento de descarga y guarda el archivo.

        Args:
            trigger_action: Accion invocable (lambda/funcion) que inicia la descarga.
            target_dir: Directorio de destino para guardar el archivo.
            suggested_name: Nombre personalizado opcional para el archivo.
            timeout_ms: Tiempo maximo en milisegundos para esperar la descarga.

        Returns:
            Path: Ruta local del archivo descargado.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        with self.page.expect_download(timeout=timeout_ms) as download_info:
            trigger_action()

        download: Download = download_info.value
        filename = suggested_name or download.suggested_filename
        final_path = target_dir / filename
        download.save_as(str(final_path))
        logger.info("Descarga completada y guardada en: %s", final_path)
        return final_path

    def take_screenshot(self, filename: str) -> Path:
        """Captura una pantalla completa y la almacena en el directorio de logs.

        Args:
            filename: Nombre del archivo de imagen (ej. 'error_login.png').

        Returns:
            Path: Ruta del archivo de captura generado.
        """
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = LOGS_DIR / filename
        try:
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info("Captura de pantalla guardada en: %s", screenshot_path)
        except Exception as e:
            logger.warning("No se pudo tomar la captura de pantalla: %s", e)
        return screenshot_path
