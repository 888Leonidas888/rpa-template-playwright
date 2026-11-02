"""Repositorio SQLite para persistencia del historial, trazabilidad e idempotencia."""

import sqlite3
from pathlib import Path
from typing import Any

from config.settings import DB_PATH
from core.models import ExecutionResult, ExecutionStatus


class BotDatabase:
    """Manejador de la base de datos local SQLite para auditoria, memoria e idempotencia."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Abre y retorna una conexion SQLite configurada con WAL mode y timeout para alta concurrencia."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        return conn

    def _init_db(self) -> None:
        """Inicializa tablas e indices en la base de datos si no existen."""
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
        """Inserta o actualiza el registro de ejecucion de un item en la base de datos.

        Args:
            result: Objeto ExecutionResult con el estado y metricas del item.
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
        """Recupera el registro de un item por su identificador unico.

        Args:
            item_id: Identificador unico del documento o item.

        Returns:
            dict[str, Any] | None: Registro encontrado o None si no existe.
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
        """Determina si un item ya fue completado exitosamente o clasificado como omitido/invalido.

        Args:
            item_id: Identificador del item.

        Returns:
            bool: True si ya esta completado (no reprocesar), False en caso contrario.
        """
        record = self.get_record(item_id)
        if not record:
            return False
        status = record.get("status")
        return status in (
            ExecutionStatus.SUCCESS.value,
            ExecutionStatus.SKIPPED.value,
            ExecutionStatus.INVALID.value,
        )

    def get_all_records(self) -> list[dict[str, Any]]:
        """Retorna todos los registros de tareas ordenados por fecha descendente."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_records ORDER BY processed_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_stats(self) -> dict[str, int]:
        """Calcula el conteo de ejecuciones desglosado por estado.

        Returns:
            dict[str, int]: Diccionario con conteo por estado y TOTAL.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) as count FROM task_records GROUP BY status")
            stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            cursor.execute("SELECT COUNT(*) FROM task_records")
            stats["TOTAL"] = cursor.fetchone()[0]
            return stats

    def clear_memory(self) -> int:
        """Elimina todos los registros del historial de la base de datos.

        Returns:
            int: Cantidad de registros eliminados.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM task_records")
            count = cursor.fetchone()[0]
            cursor.execute("DELETE FROM task_records")
            conn.commit()
            return int(count)
