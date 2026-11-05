"""Pruebas del repositorio de estado e historial SQLite en BotDatabase."""

from datetime import datetime
from pathlib import Path

import pytest

from core.database import BotDatabase
from core.models import ExecutionResult, ExecutionStatus


@pytest.fixture
def temp_db(tmp_path: Path) -> BotDatabase:
    """Provee una instancia limpia y aislada de BotDatabase en directorio temporal."""
    db_file = tmp_path / "test_memory.db"
    return BotDatabase(db_path=db_file)


def test_database_initialization(temp_db: BotDatabase) -> None:
    """Verifica que el archivo de base de datos y sus tablas se creen correctamente."""
    assert temp_db.db_path.exists()
    records = temp_db.get_all_records()
    assert len(records) == 0


def test_save_and_get_record(temp_db: BotDatabase) -> None:
    """Prueba el guardado y recuperacion de un registro de tarea con marcas de tiempo locales."""
    now_local = datetime.now()
    result = ExecutionResult(
        item_id="DOC-001",
        status=ExecutionStatus.SUCCESS,
        output_files=[Path("downloads/test.pdf")],
        details="Download completed successfully",
        attempts=1,
        duration_seconds=1.45,
        started_at=now_local,
        finished_at=now_local,
    )
    temp_db.save_record(result)

    record = temp_db.get_record("DOC-001")
    assert record is not None
    assert record["item_id"] == "DOC-001"
    assert record["status"] == ExecutionStatus.SUCCESS.value
    assert record["details"] == "Download completed successfully"
    assert "test.pdf" in record["output_files"]
    assert record["started_at"] is not None
    assert record["finished_at"] is not None
    assert record["created_at"] is not None
    assert record["updated_at"] is not None


def test_idempotency_check(temp_db: BotDatabase) -> None:
    """Verifica que is_already_completed detecte correctamente tareas finalizadas vs no finalizadas."""
    assert not temp_db.is_already_completed("DOC-002")

    # Registrar un resultado exitoso
    res_success = ExecutionResult(
        item_id="DOC-002",
        status=ExecutionStatus.SUCCESS,
    )
    temp_db.save_record(res_success)
    assert temp_db.is_already_completed("DOC-002")

    # Registrar un resultado fallido
    res_failed = ExecutionResult(
        item_id="DOC-003",
        status=ExecutionStatus.FAILED,
        error_message="Network timeout",
    )
    temp_db.save_record(res_failed)
    # Un item fallido NO debe considerarse completado (permite reintento)
    assert not temp_db.is_already_completed("DOC-003")


def test_clear_memory(temp_db: BotDatabase) -> None:
    """Prueba el vaciado de la base de datos de memoria."""
    res = ExecutionResult(item_id="DOC-004", status=ExecutionStatus.SUCCESS)
    temp_db.save_record(res)
    assert len(temp_db.get_all_records()) == 1

    deleted_count = temp_db.clear_memory()
    assert deleted_count == 1
    assert len(temp_db.get_all_records()) == 0
