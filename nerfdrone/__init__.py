"""Mini README: Core package initializer for the Nerfdrone platform.

This module exposes convenience imports that allow other parts of the
application to access high-level services without needing to know the
exact module structure. The file is intentionally lightweight so that
package metadata can be centralised here without introducing heavy
runtime dependencies.
"""

from .logging_utils import get_logger

__all__ = ["get_logger"]
