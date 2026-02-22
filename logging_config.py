"""
Centralized logging configuration for MNN Pipeline.

Provides structured logging with request IDs and consistent formatting.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict
from contextvars import ContextVar

# Context variable for request ID tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data['request_id'] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""
        request_id = request_id_var.get()
        request_part = f"[{request_id}] " if request_id else ""

        return (
            f"{datetime.now(timezone.utc).isoformat()} "
            f"{record.levelname:8s} "
            f"{request_part}"
            f"{record.name}:{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}"
        )


def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configure application-wide logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json" for structured, "text" for human-readable)
    """
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))

    # Set formatter
    if log_format.lower() == "json":
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def get_request_id() -> str:
    """Get the request ID for the current context."""
    return request_id_var.get()
