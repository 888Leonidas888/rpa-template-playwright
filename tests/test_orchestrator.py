"""Pruebas del flujo de trabajo de BotOrchestratorService."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.database import BotDatabase
from core.models import ExecutionStatus, TaskItem
from services.bot_service import BotOrchestratorService


@pytest.fixture
def temp_db(tmp_path: Path) -> BotDatabase:
    """Provee una instancia aislada de BotDatabase en directorio temporal."""
    return BotDatabase(db_path=tmp_path / "test_orchestrator.db")


def test_orchestrator_skips_completed_items(temp_db: BotDatabase) -> None:
    """Verifica que los items previamente completados se omitan por idempotencia."""
    mock_browser = MagicMock()
    mock_browser.__enter__.return_value = MagicMock()

    orchestrator = BotOrchestratorService(db=temp_db, browser_manager=mock_browser)

    with patch("services.bot_service.get_portal_credentials", return_value=("user", "pass")):
        items = [TaskItem(item_id="PO-1001")]
        results = orchestrator.process_items(items)
        assert len(results) == 1
        assert results[0].status == ExecutionStatus.SUCCESS

        # Ejecutar nuevamente con el mismo item sin forzar debe retornar SKIPPED
        results_second = orchestrator.process_items(items, force_reprocess=False)
        assert len(results_second) == 1
        assert results_second[0].status == ExecutionStatus.SKIPPED


def test_orchestrator_without_persistence() -> None:
    """Verifica que el orquestador opere correctamente con persistencia desactivada (opcional)."""
    mock_browser = MagicMock()
    mock_browser.__enter__.return_value = MagicMock()

    orchestrator = BotOrchestratorService(
        db=None,
        browser_manager=mock_browser,
        use_persistence=False,
    )

    with patch("services.bot_service.get_portal_credentials", return_value=("user", "pass")):
        items = [TaskItem(item_id="PO-2001")]
        results = orchestrator.process_items(items)
        assert len(results) == 1
        assert results[0].status == ExecutionStatus.SUCCESS

        # Al volver a procesar sin persistencia, no se omite porque no hay base de datos
        results_second = orchestrator.process_items(items)
        assert len(results_second) == 1
        assert results_second[0].status == ExecutionStatus.SUCCESS


def test_orchestrator_raises_when_credentials_missing(temp_db: BotDatabase) -> None:
    """Verifica que el orquestador falle de inmediato si no existen credenciales."""
    mock_browser = MagicMock()
    orchestrator = BotOrchestratorService(db=temp_db, browser_manager=mock_browser)

    with patch("services.bot_service.get_portal_credentials", return_value=None):
        items = [TaskItem(item_id="NEW-ITEM")]
        with pytest.raises(ValueError, match="no configuradas"):
            orchestrator.process_items(items)


def test_orchestrator_dispatches_notifications(temp_db: BotDatabase) -> None:
    """Verifica que el orquestador dispare los notificadores registrados."""
    mock_browser = MagicMock()
    mock_browser.__enter__.return_value = MagicMock()
    mock_notifier = MagicMock()

    orchestrator = BotOrchestratorService(
        db=temp_db,
        browser_manager=mock_browser,
        notifiers=[mock_notifier],
    )

    with patch("services.bot_service.get_portal_credentials", return_value=("usr", "pwd")):
        items = [TaskItem(item_id="NOTIFY-100")]
        results = orchestrator.process_items(items)
        assert len(results) == 1
        mock_notifier.send_notification.assert_called_once()
