"""Repositorio SQLite para persistencia del historial, trazabilidad e idempotencia."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from config.logger_config import get_logger
from config.settings import DB_PATH
from core.models import ExecutionResult, ExecutionStatus

logger = get_logger()


class BotDatabase:
    """Manejador de la base de datos local SQLite para auditoria, memoria e idempotencia.

    Esta tabla almacena metricas de ejecucion con fecha y hora local de forma informativa.
    Su operacion no bloquea ni interrumpe la ejecucion principal del bot en caso de fallo.
    """

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
        """Inicializa tablas, indices y columnas requeridas si no existen."""
        try:
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
                        started_at TEXT,
                        finished_at TEXT,
                        created_at TEXT,
                        updated_at TEXT
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_task_status ON task_records(status)
                    """
                )

                # Migracion segura si la tabla venia de una version previa sin estas columnas
                cursor.execute("PRAGMA table_info(task_records)")
                columns = [row["name"] for row in cursor.fetchall()]
                for col in ("started_at", "finished_at", "created_at", "updated_at"):
                    if col not in columns:
                        cursor.execute(f"ALTER TABLE task_records ADD COLUMN {col} TEXT")

                conn.commit()
        except Exception as e:
            logger.warning("Aviso no bloqueante al inicializar la base de datos SQLite: %s", e)

    def save_record(self, result: ExecutionResult) -> None:
        """Inserta o actualiza el registro de ejecucion con marcas de tiempo locales.

        En caso de fallo de escritura, registra una advertencia sin interrumpir el bot.

        Args:
            result: Objeto ExecutionResult con el estado y metricas de la tarea.
        """
        try:
            output_files_str = ";".join(str(p) for p in result.output_files) if result.output_files else None
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            started_at_str = result.started_at.strftime("%Y-%m-%d %H:%M:%S")
            finished_at_str = result.finished_at.strftime("%Y-%m-%d %H:%M:%S")

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO task_records (
                        item_id, status, output_files, details, error_message,
                        attempts, duration_seconds, started_at, finished_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(item_id) DO UPDATE SET
                        status = excluded.status,
                        output_files = excluded.output_files,
                        details = excluded.details,
                        error_message = excluded.error_message,
                        attempts = excluded.attempts,
                        duration_seconds = excluded.duration_seconds,
                        started_at = excluded.started_at,
                        finished_at = excluded.finished_at,
                        updated_at = excluded.updated_at
                    """,
                    (
                        result.item_id,
                        result.status.value,
                        output_files_str,
                        result.details,
                        result.error_message,
                        result.attempts,
                        result.duration_seconds,
                        started_at_str,
                        finished_at_str,
                        now_str,
                        now_str,
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Aviso informativo: No se pudo persistir el registro del item '%s' en SQLite: %s", result.item_id, e)

    def get_record(self, item_id: str) -> dict[str, Any] | None:
        """Recupera el registro de un item por su identificador unico."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM task_records WHERE item_id = ?",
                    (item_id,),
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.warning("Aviso al consultar registro '%s' en SQLite: %s", item_id, e)
            return None

    def is_already_completed(self, item_id: str) -> bool:
        """Determina si un item ya fue completado exitosamente o clasificado como omitido/invalido.

        Utilizado como mecanismo de fallback para retomar procesos interrumpidos (idempotencia).

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
        """Retorna todos los registros de tareas ordenados por fecha de inicio descendente."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM task_records ORDER BY started_at DESC, created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning("Aviso al listar registros de SQLite: %s", e)
            return []

    def get_summary_stats(self) -> dict[str, int]:
        """Calcula el conteo de ejecuciones desglosado por estado.

        Returns:
            dict[str, int]: Diccionario con conteo por estado y TOTAL.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, COUNT(*) as count FROM task_records GROUP BY status")
                stats = {row["status"]: row["count"] for row in cursor.fetchall()}
                cursor.execute("SELECT COUNT(*) FROM task_records")
                stats["TOTAL"] = cursor.fetchone()[0]
                return stats
        except Exception as e:
            logger.warning("Aviso al calcular estadisticas de SQLite: %s", e)
            return {"TOTAL": 0}

    def clear_memory(self) -> int:
        """Elimina todos los registros del historial de la base de datos."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM task_records")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM task_records")
                conn.commit()
                return int(count)
        except Exception as e:
            logger.warning("Aviso al limpiar registros de SQLite: %s", e)
            return 0
