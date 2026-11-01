"""Lifecycle management for Playwright browser instance and persistent context."""

import os
from pathlib import Path

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from config.logger_config import get_logger
from config.settings import (
    BROWSERS_DIR,
    DOWNLOADS_DIR,
    NAVIGATION_TIMEOUT_MS,
    PAGE_TIMEOUT_MS,
    USER_DATA_DIR,
)

logger = get_logger()


class BrowserManager:
    """Manages the creation, configuration, and destruction of the Playwright browser session."""

    def __init__(
        self,
        headless: bool = True,
        use_system_chrome: bool = False,
        user_data_dir: Path = USER_DATA_DIR,
        downloads_dir: Path = DOWNLOADS_DIR,
    ) -> None:
        """Initializes BrowserManager with execution flags and runtime paths.

        Args:
            headless: Whether to run the browser without a visible GUI window.
            use_system_chrome: Use installed Google Chrome instead of bundled Chromium.
            user_data_dir: Directory to persist session cookies, cache, and state.
            downloads_dir: Directory where browser downloads will be saved.
        """
        self.headless = headless
        self.use_system_chrome = use_system_chrome
        self.user_data_dir = user_data_dir
        self.downloads_dir = downloads_dir

        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> Page:
        """Initializes Playwright and creates a persistent context with stealth settings.

        Returns:
            Page: The ready-to-use active Playwright page.
        """
        # If frozen portable browser folder exists, prioritize it
        if BROWSERS_DIR.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)
            logger.debug("Using portable browser path: %s", BROWSERS_DIR)

        logger.info(
            "Starting browser session (headless=%s, system_chrome=%s, cache=%s)",
            self.headless,
            self.use_system_chrome,
            self.user_data_dir.name,
        )

        self._playwright = sync_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
        ]

        channel = "chrome" if self.use_system_chrome else None

        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            channel=channel,
            headless=self.headless,
            args=launch_args,
            accept_downloads=True,
            viewport={"width": 1366, "height": 768},
        )

        self._context.set_default_timeout(PAGE_TIMEOUT_MS)
        self._context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)

        pages = self._context.pages
        self._page = pages[0] if pages else self._context.new_page()

        logger.info("Browser session started successfully.")
        return self._page

    def is_alive(self) -> bool:
        """Checks if the browser context and active page are open."""
        if not self._playwright or not self._context or not self._page:
            return False
        try:
            return not self._page.is_closed()
        except Exception:
            return False

    def restart(self) -> Page:
        """Safely stops and restarts the browser context, returning a new page."""
        logger.info("Restarting browser context...")
        self.stop()
        return self.start()

    def stop(self) -> None:
        """Gracefully closes page, context, and terminates Playwright."""
        logger.info("Stopping browser session...")
        if self._context:
            try:
                self._context.close()
            except Exception as e:
                logger.warning("Error while closing browser context: %s", e)
            self._context = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning("Error while stopping Playwright: %s", e)
            self._playwright = None

        self._page = None
        logger.info("Browser session terminated.")

    def __enter__(self) -> Page:
        return self.start()

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()
