"""Mini README: Utility helper functions for Nerfdrone.

Currently exports the dynamic plugin loader which can be used by future
feature modules to discover optional dependencies at runtime.
"""

from .plugin_loader import load_entry_point_plugins

__all__ = ["load_entry_point_plugins"]
