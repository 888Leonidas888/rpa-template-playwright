"""SQLite database manager for execution history, state tracking, and idempotency."""

import sqlite3
from pathlib import Path
from typing import Any

from config.settings import DB_PATH
from core.models import ExecutionResult, ExecutionStatus


class BotDatabase:
    """Manages the local SQLite database for auditing, state memory, and idempotency."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Opens and returns a SQLite connection with dictionary row access."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS task_records (
                    item_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    output_files TEXT,
                    details TEXT,
                    error_message TEXT,
                    attempts INTEGER DEFAULT 1,
                    duration_seconds REAL DEFAULT 0.0,
                    processed_at TIMESTAMP NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_task_status ON task_records(status)
                """
            )
            conn.commit()

    def save_record(self, result: ExecutionResult) -> None:
        """Inserts or updates an execution record in the database.

        Args:
            result: The ExecutionResult object containing item status and details.
        """
        output_files_str = ";".join(str(p) for p in result.output_files) if result.output_files else None
        timestamp = result.processed_at.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO task_records (
                    item_id, status, output_files, details, error_message, attempts, duration_seconds, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.item_id,
                    result.status.value,
                    output_files_str,
                    result.details,
                    result.error_message,
                    result.attempts,
                    result.duration_seconds,
                    timestamp,
                ),
            )
            conn.commit()

    def get_record(self, item_id: str) -> dict[str, Any] | None:
        """Retrieves an execution record by item identifier.

        Args:
            item_id: Unique identifier of the item.

        Returns:
            Optional[dict[str, Any]]: Record dictionary if found, None otherwise.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM task_records WHERE item_id = ?",
                (item_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def is_already_completed(self, item_id: str) -> bool:
        """Determines if an item has already been successfully processed or marked invalid.

        Args:
            item_id: Item identifier to check.

        Returns:
            bool: True if already completed, False if it needs processing.
        """
        record = self.get_record(item_id)
        if not record:
            return False
        status = record.get("status")
        # Idempotency rule: do not reprocess if already successful, skipped, or invalid
        return status in (
            ExecutionStatus.SUCCESS.value,
            ExecutionStatus.SKIPPED.value,
            ExecutionStatus.INVALID.value,
        )

    def get_all_records(self) -> list[dict[str, Any]]:
        """Returns all recorded task executions ordered by timestamp descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_records ORDER BY processed_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self) -> dict[str, int]:
        """Calculates count breakdown by execution status.

        Returns:
            dict[str, int]: Mapping of status names to record counts.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as count FROM task_records GROUP BY status")
            stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) FROM task_records")
            stats["TOTAL"] = cursor.fetchone()[0]
            return stats

    def clear_memory(self) -> int:
        """Deletes all task execution history from the database.

        Returns:
            int: Number of deleted records.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM task_records")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM task_records")
            conn.commit()
            return int(count)
