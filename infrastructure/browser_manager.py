"""Gestion del ciclo de vida del navegador con Playwright utilizando Chrome y Edge nativos."""

from pathlib import Path

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from config.logger_config import get_logger
from config.settings import (
    DOWNLOADS_DIR,
    NAVIGATION_TIMEOUT_MS,
    PAGE_TIMEOUT_MS,
    USER_DATA_DIR,
)

logger = get_logger()


class BrowserNotFoundError(Exception):
    """Excepcion disparada cuando ni Google Chrome ni Microsoft Edge estan instalados."""


class BrowserManager:
    """Administra la creacion, configuracion y cierre de la sesion del navegador Playwright.

    Aplica una estrategia de inicio resiliente:
    1. Primario: Google Chrome nativo (`channel='chrome'`).
    2. Fallback: Microsoft Edge nativo (`channel='msedge'`).
    3. Error: Dispara BrowserNotFoundError si no se encuentra ningun navegador.
    """

    def __init__(
        self,
        headless: bool = False,
        preferred_channel: str | None = None,
        user_data_dir: Path = USER_DATA_DIR,
        downloads_dir: Path = DOWNLOADS_DIR,
    ) -> None:
        """Inicializa BrowserManager con los flags de ejecucion y rutas operativas.

        Args:
            headless: Si es True, ejecuta el navegador sin interfaz grafica visible.
            preferred_channel: Canal especifico opcional ('chrome', 'msedge') para forzar.
            user_data_dir: Directorio para persistir cookies de sesion y estado.
            downloads_dir: Directorio donde se guardaran las descargas del navegador.
        """
        self.headless = headless
        self.preferred_channel = preferred_channel
        self.user_data_dir = user_data_dir
        self.downloads_dir = downloads_dir

        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._active_channel: str | None = None

    @property
    def active_channel(self) -> str | None:
        """Retorna el canal de navegador actualmente activo ('chrome' o 'msedge')."""
        return self._active_channel

    def start(self) -> Page:
        """Inicializa Playwright y crea un contexto persistente probando Chrome y luego Edge.

        Returns:
            Page: Pagina activa de Playwright lista para interaccion.

        Raises:
            BrowserNotFoundError: Si ni Chrome ni Edge estan instalados en el sistema.
        """
        logger.info(
            "Iniciando sesion de navegador (headless=%s, preferido=%s, cache=%s)",
            self.headless,
            self.preferred_channel,
            self.user_data_dir.name,
        )

        self._playwright = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
        ]

        if self.preferred_channel:
            channels_to_try = [self.preferred_channel]
        else:
            channels_to_try = ["chrome", "msedge"]

        self._context = None
        last_exception: Exception | None = None

        for channel in channels_to_try:
            try:
                logger.info("Intentando iniciar navegador con canal: '%s'", channel)
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    channel=channel,
                    headless=self.headless,
                    args=launch_args,
                    accept_downloads=True,
                    viewport={"width": 1366, "height": 768},
                )
                self._active_channel = channel
                logger.info("Navegador iniciado exitosamente con canal: '%s'", channel)
                break
            except Exception as e:
                logger.warning("No se pudo iniciar el navegador con canal '%s': %s", channel, e)
                last_exception = e

        if self._context is None:
            error_msg = (
                "No se pudo iniciar ni Google Chrome ni Microsoft Edge. "
                "Verifique que Google Chrome o Microsoft Edge esten instalados en el equipo."
            )
            logger.error(error_msg)
            if self._playwright:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
                self._playwright = None
            raise BrowserNotFoundError(error_msg) from last_exception

        self._context.set_default_timeout(PAGE_TIMEOUT_MS)
        self._context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

        pages = self._context.pages
        self._page = pages[0] if pages else self._context.new_page()

        return self._page

    def is_alive(self) -> bool:
        """Comprueba si el contexto del navegador y la pagina activa siguen abiertos."""
        if not self._playwright or not self._context or not self._page:
            return False
        try:
            return not self._page.is_closed()
        except Exception:
            return False

    def restart(self) -> Page:
        """Reinicia de forma segura el contexto del navegador y retorna una nueva pagina."""
        logger.info("Reiniciando contexto del navegador...")
        self.stop()
        return self.start()

    def stop(self) -> None:
        """Cierra ordenadamente la pagina, el contexto y finaliza Playwright."""
        logger.info("Cerrando sesion del navegador...")
        if self._context:
            try:
                self._context.close()
            except Exception as e:
                logger.warning("Error al cerrar el contexto del navegador: %s", e)
            self._context = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning("Error al detener Playwright: %s", e)
            self._playwright = None

        self._page = None
        self._active_channel = None
        logger.info("Sesion de navegador finalizada.")

    def __enter__(self) -> Page:
        return self.start()

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()
