"""Lifecycle management for Playwright browser instance with Chrome and Edge fallback."""

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


class BrowserNotFoundError(Exception):
    """Raised when neither Google Chrome nor Microsoft Edge is available on the system."""


class BrowserManager:
    """Manages the creation, configuration, and destruction of the Playwright browser session.

    Implements a resilient launch strategy:
    1. Primary: Google Chrome (`channel='chrome'`).
    2. Fallback: Microsoft Edge (`channel='msedge'`).
    3. Failure: Raises BrowserNotFoundError if neither browser is found.
    """

    def __init__(
        self,
        headless: bool = False,
        preferred_channel: str | None = None,
        user_data_dir: Path = USER_DATA_DIR,
        downloads_dir: Path = DOWNLOADS_DIR,
    ) -> None:
        """Initializes BrowserManager with execution flags and runtime paths.

        Args:
            headless: Whether to run the browser without a visible GUI window.
            preferred_channel: Optional specific channel ('chrome', 'msedge') to force.
            user_data_dir: Directory to persist session cookies, cache, and state.
            downloads_dir: Directory where browser downloads will be saved.
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
        """Returns the browser channel currently active ('chrome' or 'msedge')."""
        return self._active_channel

    def start(self) -> Page:
        """Initializes Playwright and creates a persistent context trying Chrome then Edge.

        Returns:
            Page: The ready-to-use active Playwright page.

        Raises:
            BrowserNotFoundError: If neither Chrome nor Edge is installed.
        """
        # If a portable browser folder exists locally, allow it as additional fallback
        if BROWSERS_DIR.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(BROWSERS_DIR)

        logger.info(
            "Starting browser session (headless=%s, preferred=%s, cache=%s)",
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

        # Determine channels to attempt in order
        if self.preferred_channel:
            channels_to_try = [self.preferred_channel]
        else:
            channels_to_try = ["chrome", "msedge"]

        self._context = None
        last_exception: Exception | None = None

        for channel in channels_to_try:
            try:
                logger.info("Attempting to launch browser with channel: '%s'", channel)
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    channel=channel,
                    headless=self.headless,
                    args=launch_args,
                    accept_downloads=True,
                    viewport={"width": 1366, "height": 768},
                )
                self._active_channel = channel
                logger.info("Successfully launched browser using channel: '%s'", channel)
                break
            except Exception as e:
                logger.warning("Could not launch browser with channel '%s': %s", channel, e)
                last_exception = e

        if self._context is None:
            error_msg = (
                "Neither Google Chrome nor Microsoft Edge could be launched. "
                "Please verify that Google Chrome or Microsoft Edge is installed."
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
        self._active_channel = None
        logger.info("Browser session terminated.")

    def __enter__(self) -> Page:
        return self.start()

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()
