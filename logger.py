"""
Logging configuration for Email Sorter
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import (
    LOG_FILE,
    LOG_LEVEL,
    LOG_MAX_SIZE,
    LOG_BACKUP_COUNT,
    ENABLE_LOGGING
)


def setup_logger(name: str = "email_sorter") -> logging.Logger:
    """
    Set up logger with file and console handlers

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set base level
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.DEBUG)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )

    # File handler (if logging enabled)
    if ENABLE_LOGGING:
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=LOG_MAX_SIZE,
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}")

    # Console handler (only WARNING and above to keep terminal clean)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only show warnings/errors in console
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    return logger


def log_exception(logger: logging.Logger, message: str, exc: Exception):
    """
    Log an exception with full traceback

    Args:
        logger: Logger instance
        message: Context message
        exc: Exception to log
    """
    logger.error(f"{message}: {str(exc)}", exc_info=True)


# Create default logger
default_logger = setup_logger()


# Convenience functions
def debug(msg: str):
    """Log debug message"""
    default_logger.debug(msg)


def info(msg: str):
    """Log info message"""
    default_logger.info(msg)


def warning(msg: str):
    """Log warning message"""
    default_logger.warning(msg)


def error(msg: str):
    """Log error message"""
    default_logger.error(msg)


def critical(msg: str):
    """Log critical message"""
    default_logger.critical(msg)


def exception(msg: str, exc: Optional[Exception] = None):
    """Log exception with traceback"""
    if exc:
        log_exception(default_logger, msg, exc)
    else:
        default_logger.exception(msg)


if __name__ == "__main__":
    # Test logging
    logger = setup_logger()

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        log_exception(logger, "Test exception logging", e)

    print(f"\n✓ Logging test complete. Check {LOG_FILE} for output.")
