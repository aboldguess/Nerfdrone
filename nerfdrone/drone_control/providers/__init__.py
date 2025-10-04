"""Mini README: Concrete drone provider implementations.

The package demonstrates how vendor APIs can plug into the registry. New
providers should export a subclass of ``DroneControlProvider`` and call
``REGISTRY.register`` during module import to keep the system discoverable.
"""

from .dji_provider import DJIProvider

__all__ = ["DJIProvider"]
