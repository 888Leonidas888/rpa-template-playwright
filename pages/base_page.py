"""Base Page Object Model providing resilient web interaction methods."""

import time
from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Download, Locator, Page

from config.logger_config import get_logger
from config.settings import LOGS_DIR, PAGE_TIMEOUT_MS

logger = get_logger()


class BasePage:
    """Base class for all Page Object Model representations.

    Encapsulates resilient interactions, retry loops, screenshots on failure,
    and download handling.
    """

    def __init__(self, page: Page) -> None:
        """Initializes the Page Object with an active Playwright page.

        Args:
            page: Active Playwright Page instance.
        """
        self.page = page

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigates to the specified URL with logging."""
        logger.info("Navigating to: %s", url)
        self.page.goto(url, wait_until=wait_until)  # type: ignore

    def safe_click(
        self,
        selector: str,
        timeout_ms: int = PAGE_TIMEOUT_MS,
        retries: int = 2,
    ) -> None:
        """Clicks an element with retry logic and error screenshot capture.

        Args:
            selector: CSS or XPath selector of the element.
            timeout_ms: Maximum wait time for element to be clickable.
            retries: Number of retry attempts if click fails.
        """
        for attempt in range(1, retries + 1):
            try:
                locator: Locator = self.page.locator(selector).first
                locator.wait_for(state="visible", timeout=timeout_ms)
                locator.click(timeout=timeout_ms)
                return
            except Exception as e:
                logger.warning(
                    "Click attempt %s/%s failed on selector '%s': %s",
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
        """Fills an input field after ensuring visibility.

        Args:
            selector: CSS or XPath selector of the input element.
            value: Text string to type.
            timeout_ms: Maximum wait time for element.
        """
        try:
            locator: Locator = self.page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout_ms)
            locator.fill(value)
        except Exception as e:
            logger.error("Failed to fill selector '%s': %s", selector, e)
            self.take_screenshot(f"error_fill_{int(time.time())}.png")
            raise

    def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout_ms: int = PAGE_TIMEOUT_MS,
    ) -> bool:
        """Waits for an element state and returns True if found, False on timeout.

        Args:
            selector: CSS or XPath selector.
            state: Desired state ('visible', 'attached', 'detached', 'hidden').
            timeout_ms: Timeout in milliseconds.

        Returns:
            bool: True if element reached state within timeout, False otherwise.
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
        """Executes a trigger action, waits for the browser download, and saves it.

        Args:
            trigger_action: A callable function/lambda that initiates the download (e.g. click).
            target_dir: Target directory to save the downloaded file.
            suggested_name: Optional custom filename override.
            timeout_ms: Timeout in milliseconds to wait for the download event.

        Returns:
            Path: Local path of the saved file.
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        with self.page.expect_download(timeout=timeout_ms) as download_info:
            trigger_action()

        download: Download = download_info.value
        filename = suggested_name or download.suggested_filename
        final_path = target_dir / filename
        download.save_as(str(final_path))
        logger.info("Download completed and saved to: %s", final_path)
        return final_path

    def take_screenshot(self, filename: str) -> Path:
        """Takes a full page screenshot and saves it to the logs directory.

        Args:
            filename: Screenshot image filename (e.g., 'error_login.png').

        Returns:
            Path: Path of the generated screenshot image.
        """
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        screenshot_path = LOGS_DIR / filename
        try:
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info("Screenshot captured at: %s", screenshot_path)
        except Exception as e:
            logger.warning("Failed to capture screenshot: %s", e)
        return screenshot_path
