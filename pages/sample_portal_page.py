"""Reference implementation of a portal Page Object Model."""

from pathlib import Path

from playwright.sync_api import Page

from config.logger_config import get_logger
from config.settings import DOWNLOADS_DIR
from pages.base_page import BasePage

logger = get_logger()


class SamplePortalPage(BasePage):
    """Example Page Object demonstrating authentication and report download."""

    # Selectors central definition
    LOGIN_USER_INPUT = "input[name='username'], #txtUser"
    LOGIN_PASS_INPUT = "input[name='password'], #txtPassword"
    LOGIN_SUBMIT_BTN = "button[type='submit'], #btnLogin"
    DASHBOARD_INDICATOR = ".dashboard-header, #userProfile"
    SEARCH_INPUT = "#searchQuery"
    DOWNLOAD_BUTTON = "#btnExportExcel, .btn-download"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def login(self, username: str, password: str, login_url: str = "https://example.com/login") -> bool:
        """Performs authentication flow on the target portal.

        Args:
            username: User credential.
            password: Password credential.
            login_url: Target login URL.

        Returns:
            bool: True if login succeeded (dashboard reached).
        """
        logger.info("Executing login flow for user: %s", username)
        self.navigate(login_url)

        self.safe_fill(self.LOGIN_USER_INPUT, username)
        self.safe_fill(self.LOGIN_PASS_INPUT, password)
        self.safe_click(self.LOGIN_SUBMIT_BTN)

        # Confirm successful login via presence of dashboard element
        success = self.wait_for_element(self.DASHBOARD_INDICATOR, timeout_ms=10000)
        if success:
            logger.info("Login succeeded.")
        else:
            logger.warning("Dashboard element not detected after login attempt.")
            self.take_screenshot("failed_login.png")
        return success

    def download_report_by_id(self, item_id: str, output_dir: Path = DOWNLOADS_DIR) -> Path | None:
        """Searches for an item and captures the downloaded report file.

        Args:
            item_id: Query or document identifier.
            output_dir: Destination folder for the downloaded file.

        Returns:
            Optional[Path]: File path if downloaded successfully, None otherwise.
        """
        logger.info("Searching report for item: %s", item_id)
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
            logger.error("Download failed for item '%s': %s", item_id, e)
            self.take_screenshot(f"download_error_{item_id}.png")
            return None
