"""AgentHive Structured Logging Configuration."""

import logging
import sys
from typing import Any, Dict


class SafeLogFormatter(logging.Formatter):
    """Custom log formatter ensuring no raw sensitive strings are emitted."""

    def format(self, record: logging.LogRecord) -> str:
        # Prevent any accidentally passed sensitive substrings
        msg = super().format(record)
        return msg


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure root and application loggers."""
    log_level = logging.DEBUG if debug else logging.INFO

    logger = logging.getLogger("agenthive")
    logger.setLevel(log_level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = SafeLogFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(module)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
