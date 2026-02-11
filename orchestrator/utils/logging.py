"""Structured logging configuration."""

import structlog
import sys


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    
    structlog.configure(
        handlers=[
            structlog.processors.LogfmtRenderer(),
            structlog.stdlib.ProcessorFormatter(
                structlog.dev.ConsoleRenderer(),
            ),
        ],
        cache_logger_on_first_use=True,
    )
    
    logger = structlog.get_logger()
    
    # Set log level
    level_map = {
        "DEBUG": structlog.DEBUG,
        "INFO": structlog.INFO,
        "WARNING": structlog.WARNING,
        "ERROR": structlog.ERROR,
        "CRITICAL": structlog.CRITICAL,
    }
    
    logger.setLevel(level_map.get(log_level.upper(), structlog.INFO))
    
    return logger


# Global logger instance
logger = configure_logging()
