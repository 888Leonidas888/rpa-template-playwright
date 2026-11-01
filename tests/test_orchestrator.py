"""Tests for BotOrchestratorService workflow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.database import BotDatabase
from core.models import ExecutionStatus, TaskItem
from services.bot_service import BotOrchestratorService


@pytest.fixture
def temp_db(tmp_path: Path) -> BotDatabase:
    """Provides an isolated BotDatabase."""
    return BotDatabase(db_path=tmp_path / "test_orchestrator.db")


def test_orchestrator_skips_completed_items(temp_db: BotDatabase) -> None:
    """Verifies already processed items are skipped idempotently."""
    mock_browser = MagicMock()
    mock_browser.__enter__.return_value = MagicMock()

    orchestrator = BotOrchestratorService(db=temp_db, browser_manager=mock_browser)

    # Pre-mark item as completed
    with patch("services.bot_service.get_portal_credentials", return_value=("user", "pass")):
        items = [TaskItem(item_id="PO-1001")]
        results = orchestrator.process_items(items)
        assert len(results) == 1
        assert results[0].status == ExecutionStatus.SUCCESS

        # Running again with the same item without force flag should return SKIPPED
        results_second = orchestrator.process_items(items, force_reprocess=False)
        assert len(results_second) == 1
        assert results_second[0].status == ExecutionStatus.SKIPPED


def test_orchestrator_raises_when_credentials_missing(temp_db: BotDatabase) -> None:
    """Verifies orchestrator fails fast when credentials are not present."""
    mock_browser = MagicMock()
    orchestrator = BotOrchestratorService(db=temp_db, browser_manager=mock_browser)

    with patch("services.bot_service.get_portal_credentials", return_value=None):
        items = [TaskItem(item_id="NEW-ITEM")]
        with pytest.raises(ValueError, match="credentials are not configured"):
            orchestrator.process_items(items)
