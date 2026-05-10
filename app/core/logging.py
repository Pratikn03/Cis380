"""
Sentifargo Production Logging Configuration
Structured logging with JSON output for production environments
"""

import logging
import sys
import json
import threading
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import traceback


class CustomJsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: str = "%",
        include_extra: bool = True,
        app_name: str = "Sentifargo",
    ):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.include_extra = include_extra
        self.app_name = app_name
        self._skip_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "taskName",
            "message",
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app": self.app_name,
        }

        # Add location info
        log_record["location"] = {
            "file": record.filename,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add process/thread info
        log_record["process"] = {
            "id": record.process,
            "name": record.processName,
        }
        log_record["thread"] = {
            "id": record.thread,
            "name": record.threadName,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": (
                    traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
                ),
            }

        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in self._skip_fields:
                    try:
                        json.dumps(value)  # Check if serializable
                        log_record[key] = value
                    except (TypeError, ValueError):
                        log_record[key] = str(value)

        return json.dumps(log_record, default=str)


class ProductionLogFormatter(logging.Formatter):
    """Production-ready formatter with color support for console."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcfromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level = f"{color}{level:8}{self.RESET}"
        else:
            level = f"{level:8}"

        msg = f"{timestamp} | {level} | {record.name:30} | {record.getMessage()}"

        if record.exc_info:
            msg += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return msg


def get_logger(
    name: str,
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level
        json_output: Whether to use JSON formatting
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper()))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        if json_output:
            console_handler.setFormatter(CustomJsonFormatter())
        else:
            use_colors = sys.stdout.isatty()
            console_handler.setFormatter(ProductionLogFormatter(use_colors=use_colors))

        logger.addHandler(console_handler)

        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(CustomJsonFormatter())
            logger.addHandler(file_handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


def configure_root_logger(
    level: str = "INFO",
    json_output: bool = False,
    log_file: Optional[str] = None,
):
    """Configure the root logger for the application."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    if json_output:
        console_handler.setFormatter(CustomJsonFormatter())
    else:
        use_colors = sys.stdout.isatty()
        console_handler.setFormatter(ProductionLogFormatter(use_colors=use_colors))

    root.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(CustomJsonFormatter())
        root.addHandler(file_handler)

    # Configure third-party loggers to be less verbose
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)


# Thread-local stack so concurrent requests each maintain their own context
# without racing on the global log record factory.
_log_context_local: threading.local = threading.local()


def _get_context_extras() -> list[dict]:
    return getattr(_log_context_local, "extras", [])


def _sentifargo_log_factory(*args, **kwargs) -> logging.LogRecord:  # type: ignore[misc]
    """Module-level factory installed once; reads per-thread extras stack."""
    record = _sentifargo_log_factory._base_factory(*args, **kwargs)  # type: ignore[attr-defined]
    for extra in _get_context_extras():
        for key, value in extra.items():
            setattr(record, key, value)
    return record


# Install once at import time; avoids repeated setLogRecordFactory calls.
_sentifargo_log_factory._base_factory = logging.getLogRecordFactory()  # type: ignore[attr-defined]
logging.setLogRecordFactory(_sentifargo_log_factory)


class LogContext:
    """Thread-safe context manager for adding extra fields to log records.

    Uses a per-thread extras stack instead of replacing the global factory
    on every __enter__, which was not thread-safe under concurrent requests.
    """

    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra = kwargs

    def __enter__(self):
        stack = getattr(_log_context_local, "extras", [])
        _log_context_local.extras = stack + [self.extra]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        stack = getattr(_log_context_local, "extras", [])
        _log_context_local.extras = stack[:-1]
        return False


# Request logging adapter
class RequestLogAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request context to logs."""

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra["request_id"] = self.extra.get("request_id", "-")
        extra["user_id"] = self.extra.get("user_id", "-")
        extra["method"] = self.extra.get("method", "-")
        extra["path"] = self.extra.get("path", "-")
        return msg, kwargs


def get_request_logger(
    name: str,
    request_id: str,
    user_id: Optional[str] = None,
    method: str = "-",
    path: str = "-",
) -> RequestLogAdapter:
    """Get a logger with request context."""
    logger = get_logger(name)
    return RequestLogAdapter(
        logger,
        {
            "request_id": request_id,
            "user_id": user_id or "-",
            "method": method,
            "path": path,
        },
    )


# Export commonly used items
__all__ = [
    "get_logger",
    "configure_root_logger",
    "CustomJsonFormatter",
    "ProductionLogFormatter",
    "LogContext",
    "RequestLogAdapter",
    "get_request_logger",
]


# Initialize module-level logger
_module_logger = get_logger(__name__)

if __name__ == "__main__":
    # Demo the logging
    configure_root_logger(level="DEBUG", json_output=False)

    logger = get_logger("demo")

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    try:
        raise ValueError("Sample exception")
    except Exception:
        logger.exception("An exception occurred")

    # With request context
    req_logger = get_request_logger(
        "demo.request", request_id="abc123", user_id="user_42", method="POST", path="/api/chat"
    )
    req_logger.info("Processing chat request")
