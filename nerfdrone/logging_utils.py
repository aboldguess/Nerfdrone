"""Mini README: Application-wide logging helpers for Nerfdrone.

Structure:
    * get_logger - factory that configures structured logging for modules.
    * configure_root_logger - optional helper to adjust global logging level.

Usage:
    Modules import ``get_logger`` to create contextual loggers that include
    module names and debugging friendly formatting. The helpers ensure that
    logging configuration is performed exactly once, preventing duplicate
    handlers when modules are reloaded in development.
"""

from __future__ import annotations

import logging
from typing import Optional

_LOGGER_INITIALISED = False


def configure_root_logger(level: int = logging.INFO) -> None:
    """Configure the root logger with a rich, debugging friendly formatter."""

    global _LOGGER_INITIALISED
    if _LOGGER_INITIALISED:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
    _LOGGER_INITIALISED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-specific logger ensuring baseline configuration."""

    configure_root_logger()
    return logging.getLogger(name)
