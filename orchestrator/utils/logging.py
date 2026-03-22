"""Structured logging configuration."""

import logging
import structlog
import sys


def configure_logging(log_level: str = "INFO"):
    """Configure structured logging for the application."""

    logging.basicConfig(
        level=log_level.upper(),
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get a logger with the new configuration
    logger = structlog.get_logger()
    return logger


# Global logger instance
logger = configure_logging()
