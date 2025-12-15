"""
Complete logging configuration for Graph Builder Service.
Provides structured logging with rotation, multiple handlers, and formatting.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
import json
from datetime import datetime

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Outputs logs in JSON format for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add custom fields from extra parameter
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "lineno", "module", "msecs", "message", "pathname",
                "process", "processName", "relativeCreated", "thread", "threadName",
                "exc_info", "exc_text", "stack_info", "levelno"
            ]:
                log_data[key] = value

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.
    Makes logs easier to read in terminal.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"
            )

        # Format the message
        formatted = super().format(record)

        # Reset color at the end
        return formatted


def setup_logging(
        log_level: Optional[str] = None,
        log_file: bool = True,
        json_logs: bool = False,
        colored_console: bool = True
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Enable file logging
        json_logs: Use JSON format for file logs
        colored_console: Use colored output for console
    """
    # Get log level from settings or parameter
    level_name = log_level or settings.log_level
    level = getattr(logging, level_name.upper())

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # ========================================================================
    # Console Handler
    # ========================================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if colored_console and sys.stdout.isatty():
        console_format = (
            "%(levelname)s | "
            "%(asctime)s | "
            "%(name)s:%(funcName)s:%(lineno)d | "
            "%(message)s"
        )
        console_formatter = ColoredFormatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        console_format = (
            "%(levelname)-8s | "
            "%(asctime)s | "
            "%(name)s:%(funcName)s:%(lineno)d | "
            "%(message)s"
        )
        console_formatter = logging.Formatter(
            console_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ========================================================================
    # File Handler - General Logs
    # ========================================================================
    if log_file:
        if json_logs:
            # JSON file handler
            json_handler = RotatingFileHandler(
                filename=log_dir / "app.json",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10,
                encoding="utf-8",
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(json_handler)
        else:
            # Regular file handler with rotation by size
            file_handler = RotatingFileHandler(
                filename=log_dir / "app.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = (
                "%(levelname)-8s | "
                "%(asctime)s | "
                "%(name)s:%(funcName)s:%(lineno)d | "
                "%(message)s"
            )
            file_formatter = logging.Formatter(
                file_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

    # ========================================================================
    # Error File Handler
    # ========================================================================
    if log_file:
        error_handler = RotatingFileHandler(
            filename=log_dir / "error.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_format = (
            "%(levelname)-8s | "
            "%(asctime)s | "
            "%(name)s:%(funcName)s:%(lineno)d | "
            "%(message)s\n"
            "%(pathname)s"
        )
        error_formatter = logging.Formatter(
            error_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)

    # ========================================================================
    # Daily Rotating Handler (Optional)
    # ========================================================================
    if log_file and not settings.is_development:
        daily_handler = TimedRotatingFileHandler(
            filename=log_dir / "daily.log",
            when="midnight",
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding="utf-8",
        )
        daily_handler.setLevel(logging.INFO)

        # Choose formatter depending on JSON or not
        if json_logs:
            daily_formatter = JSONFormatter()
        else:
            daily_format = (
                "%(levelname)-8s | "
                "%(asctime)s | "
                "%(name)s:%(funcName)s:%(lineno)d | "
                "%(message)s"
            )
            daily_formatter = logging.Formatter(
                daily_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )

        daily_handler.setFormatter(daily_formatter)
        root_logger.addHandler(daily_handler)
     
    # ========================================================================
    # Configure Third-Party Loggers
    # ========================================================================

    # Uvicorn
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # FastAPI
    logging.getLogger("fastapi").setLevel(logging.INFO)

    # SQLAlchemy (reduce verbosity)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    # Neo4j
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("neo4j.io").setLevel(logging.ERROR)

    # Httpx (for async requests)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Set DEBUG for our application in development
    if settings.is_development:
        logging.getLogger("app").setLevel(logging.DEBUG)

    # Log startup message
    root_logger.info(f"Logging initialized - Level: {level_name}")
    root_logger.info(f"Environment: {settings.environment}")
    root_logger.info(f"Log files: {log_dir.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exc: Exception, context: Optional[dict] = None):
    """
    Log an exception with context.

    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context data
    """
    extra = context or {}
    logger.exception(
        f"Exception occurred: {type(exc).__name__}: {str(exc)}",
        extra=extra,
        exc_info=True
    )


# Initialize logging on import
setup_logging(
    json_logs=settings.is_production,  # JSON logs in production
    colored_console=settings.is_development  # Colors in development
)
