"""Tests for BrowserManager Chrome and Edge fallback strategy."""

from unittest.mock import MagicMock, patch

import pytest

from infrastructure.browser_manager import BrowserManager, BrowserNotFoundError


def test_browser_manager_launches_chrome_first() -> None:
    """Verifies that BrowserManager attempts Chrome first."""
    mock_playwright = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_context.pages = [mock_page]
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context

    with patch("infrastructure.browser_manager.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_playwright

        bm = BrowserManager(headless=True)
        page = bm.start()

        assert page == mock_page
        assert bm.active_channel == "chrome"
        mock_playwright.chromium.launch_persistent_context.assert_called_once()
        args, kwargs = mock_playwright.chromium.launch_persistent_context.call_args
        assert kwargs["channel"] == "chrome"


def test_browser_manager_falls_back_to_edge_when_chrome_fails() -> None:
    """Verifies that BrowserManager falls back to Microsoft Edge if Chrome fails."""
    mock_playwright = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    mock_context.pages = [mock_page]

    # First call (chrome) raises Exception, second call (msedge) succeeds
    mock_playwright.chromium.launch_persistent_context.side_effect = [
        Exception("Chrome executable not found"),
        mock_context,
    ]

    with patch("infrastructure.browser_manager.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_playwright

        bm = BrowserManager(headless=True)
        page = bm.start()

        assert page == mock_page
        assert bm.active_channel == "msedge"
        assert mock_playwright.chromium.launch_persistent_context.call_count == 2


def test_browser_manager_raises_error_when_neither_browser_found() -> None:
    """Verifies that BrowserManager raises BrowserNotFoundError if both Chrome and Edge fail."""
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch_persistent_context.side_effect = Exception("Browser not found")

    with patch("infrastructure.browser_manager.sync_playwright") as mock_sync:
        mock_sync.return_value.start.return_value = mock_playwright

        bm = BrowserManager(headless=True)
        with pytest.raises(BrowserNotFoundError, match="Neither Google Chrome nor Microsoft Edge"):
            bm.start()
