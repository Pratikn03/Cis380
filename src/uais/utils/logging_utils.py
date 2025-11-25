"""Logging configuration helpers."""
import logging
from pathlib import Path
from typing import Optional

from .paths import LOGS_DIR, ensure_directories


def setup_logging(name: str, level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Create a module-specific logger with optional file handler."""
    ensure_directories()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = LOGS_DIR / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


__all__ = ["setup_logging"]
