"""Tests for BotDatabase SQLite state repository."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.database import BotDatabase
from core.models import ExecutionResult, ExecutionStatus


@pytest.fixture
def temp_db(tmp_path: Path) -> BotDatabase:
    """Provides a fresh isolated BotDatabase in a temporary path."""
    db_file = tmp_path / "test_memory.db"
    return BotDatabase(db_path=db_file)


def test_database_initialization(temp_db: BotDatabase) -> None:
    """Verifies that database file and tables are properly created."""
    assert temp_db.db_path.exists()
    records = temp_db.get_all_records()
    assert len(records) == 0


def test_save_and_get_record(temp_db: BotDatabase) -> None:
    """Tests saving and retrieving a task record."""
    result = ExecutionResult(
        item_id="DOC-001",
        status=ExecutionStatus.SUCCESS,
        output_files=[Path("downloads/test.pdf")],
        details="Download completed successfully",
        attempts=1,
        duration_seconds=1.45,
        processed_at=datetime.now(UTC),
    )
    temp_db.save_record(result)

    record = temp_db.get_record("DOC-001")
    assert record is not None
    assert record["item_id"] == "DOC-001"
    assert record["status"] == ExecutionStatus.SUCCESS.value
    assert record["details"] == "Download completed successfully"
    assert "test.pdf" in record["output_files"]


def test_idempotency_check(temp_db: BotDatabase) -> None:
    """Verifies is_already_completed correctly detects finished vs unfinished tasks."""
    assert not temp_db.is_already_completed("DOC-002")

    # Record a successful result
    res_success = ExecutionResult(
        item_id="DOC-002",
        status=ExecutionStatus.SUCCESS,
    )
    temp_db.save_record(res_success)
    assert temp_db.is_already_completed("DOC-002")

    # Record a failed result
    res_failed = ExecutionResult(
        item_id="DOC-003",
        status=ExecutionStatus.FAILED,
        error_message="Network timeout",
    )
    temp_db.save_record(res_failed)
    # A failed item should NOT be considered already completed (must retry)
    assert not temp_db.is_already_completed("DOC-003")


def test_clear_memory(temp_db: BotDatabase) -> None:
    """Tests clearing the memory database."""
    res = ExecutionResult(item_id="DOC-004", status=ExecutionStatus.SUCCESS)
    temp_db.save_record(res)
    assert len(temp_db.get_all_records()) == 1

    deleted_count = temp_db.clear_memory()
    assert deleted_count == 1
    assert len(temp_db.get_all_records()) == 0
