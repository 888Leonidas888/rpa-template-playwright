"""Modelos de dominio y definiciones de estado de ejecucion para tareas RPA."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ExecutionStatus(str, Enum):
    """Estado de ejecucion para una tarea o elemento de trabajo RPA."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    INVALID = "INVALID"


@dataclass
class TaskItem:
    """Representa un elemento de trabajo de entrada para ser procesado por el bot.

    Atributos:
        item_id: Identificador unico del elemento (ej. numero de factura, orden de compra PO, codigo).
        item_type: Categoria o etiqueta (ej. 'invoice', 'report', 'query').
        payload: Metadatos o contexto adicional requerido para el procesamiento.
        created_at: Marca de tiempo de creacion (timestamp).
    """

    item_id: str
    item_type: str = "generic"
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ExecutionResult:
    """Resultado del procesamiento de un unico TaskItem.

    Atributos:
        item_id: Identificador del elemento procesado.
        status: Estado final del procesamiento.
        output_files: Rutas de archivos descargados o generados.
        details: Mensaje informativo o resumen de la ejecucion.
        error_message: Descripcion del error si el estado es FAILED.
        attempts: Numero de intentos realizados.
        duration_seconds: Tiempo transcurrido de ejecucion en segundos.
        processed_at: Marca de tiempo de finalizacion (timestamp).
    """

    item_id: str
    status: ExecutionStatus
    output_files: list[Path] = field(default_factory=list)
    details: str = ""
    error_message: str | None = None
    attempts: int = 1
    duration_seconds: float = 0.0
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
