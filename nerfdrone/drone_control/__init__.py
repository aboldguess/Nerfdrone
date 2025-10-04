"""Mini README: Drone control subsystem package initialiser.

Re-exports key abstractions to simplify imports for command modules and
web handlers. The package is divided into ``base`` for abstract classes,
``registry`` for plugin management, and ``providers`` for concrete vendor
implementations.
"""

from .base import DroneControlProvider, FlightCommand
from .registry import DroneProviderRegistry, REGISTRY
from . import providers  # noqa: F401  # ensure built-in providers register on import

__all__ = [
    "DroneControlProvider",
    "DroneProviderRegistry",
    "FlightCommand",
    "REGISTRY",
]
