"""Centralized logging configuration with rotating file and console handlers."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.settings import LOGS_DIR

_logger: logging.Logger | None = None


def setup_logger(log_level: int = logging.INFO) -> logging.Logger:
    """Configures and returns the application logger.

    Args:
        log_level: Logging severity level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        logging.Logger: The configured singleton logger.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("rpa_bot")
    logger.setLevel(log_level)
    logger.propagate = False

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler (Max 10MB per file, up to 5 backups)
    log_file_path: Path = LOGS_DIR / "bot.log"
    file_handler = RotatingFileHandler(
        str(log_file_path),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return _logger


def get_logger() -> logging.Logger:
    """Retrieves the active application logger, initializing if needed."""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger
