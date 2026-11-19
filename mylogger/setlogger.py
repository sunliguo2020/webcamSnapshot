"""Compatibility entry point for the application's logger configuration."""

import logging

from utils.log_config import setup_logging


def configure_logger():
    """Configure the shared logger using the application's rotating handler."""
    setup_logging()


if __name__ == "__main__":
    configure_logger()
    logger = logging.getLogger("camera_logger")
    logger.debug("debug")
