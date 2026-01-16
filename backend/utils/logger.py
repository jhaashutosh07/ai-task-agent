"""
Centralized logging configuration for AI Task Agent.
Provides structured JSON logging with rotation support.
"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured logs"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data

        return json.dumps(log_entry)


class ContextLogger(logging.LoggerAdapter):
    """Logger adapter that adds context to all log messages"""

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        extra = kwargs.get("extra", {})
        extra["extra_data"] = {**self.extra, **extra.get("extra_data", {})}
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(
    log_dir: str = "./logs",
    log_level: str = "INFO",
    json_format: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Set up centralized logging configuration.

    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Use JSON formatting for logs
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    # Console handler (always human-readable for development)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    root_logger.addHandler(console_handler)

    # File handler with rotation (JSON format)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "app.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_path / "errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    root_logger.info("Logging initialized", extra={"extra_data": {"log_level": log_level}})


def get_logger(name: str, **context: Any) -> ContextLogger:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all log messages

    Returns:
        ContextLogger: Logger adapter with context
    """
    logger = logging.getLogger(name)
    return ContextLogger(logger, context)
