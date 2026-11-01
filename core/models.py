"""Domain models and execution status definitions for RPA tasks."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ExecutionStatus(str, Enum):
    """Execution status for an RPA task or item."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    INVALID = "INVALID"


@dataclass
class TaskItem:
    """Represents an input work item to be processed by the bot.

    Attributes:
        item_id: Unique identifier for the item (e.g. invoice number, PO number, code).
        item_type: Category or label (e.g. 'invoice', 'report', 'query').
        payload: Additional metadata or context required for processing.
        created_at: Creation timestamp.
    """

    item_id: str
    item_type: str = "generic"
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ExecutionResult:
    """Outcome of processing a single TaskItem.

    Attributes:
        item_id: Identifier of the processed work item.
        status: Final status of the processing.
        output_files: Paths to downloaded or generated files.
        details: Optional human-readable message or summary.
        error_message: Error description if status is FAILED.
        attempts: Number of retry attempts made.
        duration_seconds: Elapsed execution time in seconds.
        processed_at: Completion timestamp.
    """

    item_id: str
    status: ExecutionStatus
    output_files: list[Path] = field(default_factory=list)
    details: str = ""
    error_message: str | None = None
    attempts: int = 1
    duration_seconds: float = 0.0
    processed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
