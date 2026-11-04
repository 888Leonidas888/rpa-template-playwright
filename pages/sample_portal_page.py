"""Implementacion de referencia de un Page Object Model para un portal web."""

from pathlib import Path

from playwright.sync_api import Page

from config.logger_config import get_logger
from config.settings import DOWNLOADS_DIR
from pages.base_page import BasePage

logger = get_logger()


class SamplePortalPage(BasePage):
    """Page Object de ejemplo que demuestra autenticacion y descarga de reportes."""

    # Definicion centralizada de selectores
    LOGIN_USER_INPUT = "input[name='username'], #txtUser"
    LOGIN_PASS_INPUT = "input[name='password'], #txtPassword"
    LOGIN_SUBMIT_BTN = "button[type='submit'], #btnLogin"
    DASHBOARD_INDICATOR = ".dashboard-header, #userProfile"
    SEARCH_INPUT = "#searchQuery"
    DOWNLOAD_BUTTON = "#btnExportExcel, .btn-download"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def login(self, username: str, password: str, login_url: str = "https://example.com/login") -> bool:
        """Ejecuta el flujo de autenticacion en el portal objetivo.

        Args:
            username: Credencial de usuario.
            password: Password de usuario.
            login_url: URL de inicio de sesion.

        Returns:
            bool: True si el login fue exitoso (pantalla principal cargada).
        """
        logger.info("Ejecutando flujo de autenticacion para usuario: %s", username)
        self.navigate(login_url)

        self.safe_fill(self.LOGIN_USER_INPUT, username)
        self.safe_fill(self.LOGIN_PASS_INPUT, password)
        self.safe_click(self.LOGIN_SUBMIT_BTN)

        # Confirmar login exitoso mediante presencia de elemento del dashboard
        success = self.wait_for_element(self.DASHBOARD_INDICATOR, timeout_ms=10000)
        if success:
            logger.info("Autenticacion completada exitosamente.")
        else:
            logger.warning("No se detecto el elemento de confirmacion tras intentar login.")
            self.take_screenshot("failed_login.png")
        return success

    def download_report_by_id(self, item_id: str, output_dir: Path = DOWNLOADS_DIR) -> Path | None:
        """Busca un elemento y captura el archivo de reporte descargado.

        Args:
            item_id: Identificador de consulta o documento.
            output_dir: Carpeta de destino para el archivo descargado.

        Returns:
            Path | None: Ruta del archivo si la descarga fue exitosa, None en caso contrario.
        """
        logger.info("Buscando reporte para item: %s", item_id)
        self.safe_fill(self.SEARCH_INPUT, item_id)

        try:
            downloaded_file = self.capture_download(
                trigger_action=lambda: self.safe_click(self.DOWNLOAD_BUTTON),
                target_dir=output_dir,
                suggested_name=f"report_{item_id}.xlsx",
                timeout_ms=30000,
            )
            return downloaded_file
        except Exception as e:
            logger.error("Fallo la descarga para el item '%s': %s", item_id, e)
            self.take_screenshot(f"download_error_{item_id}.png")
            return None
