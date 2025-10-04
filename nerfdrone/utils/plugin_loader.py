"""Mini README: Dynamic plugin loading helpers.

Structure:
    * load_entry_point_plugins - load entry point-based extensions.

The helper simplifies discovery of third-party packages that expose
``nerfdrone.plugins`` entry points, enabling drop-in feature expansion.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


def load_entry_point_plugins(group: str = "nerfdrone.plugins") -> Iterable[object]:
    """Load and return instantiated plugin classes registered via entry points."""

    loaded_plugins = []
    discovered = entry_points().get(group, [])  # type: ignore[call-arg]
    for entry_point in discovered:
        try:
            plugin = entry_point.load()
            loaded_plugins.append(plugin)
            LOGGER.info("Loaded plugin '%s'", entry_point.name)
        except Exception as exc:  # pragma: no cover - defensive logging
            LOGGER.exception("Failed to load plugin '%s': %s", entry_point.name, exc)
    return loaded_plugins
