"""Mini README: Provider registry enabling extensible drone integrations.

Structure:
    * DroneProviderRegistry - manages registration and instantiation of
      ``DroneControlProvider`` implementations.

The registry supports runtime discovery, enabling future packages to plug
into the system via standard Python entry points or manual registration.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Type

from .base import DroneControlProvider
from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


class DroneProviderRegistry:
    """Simple registry for mapping provider identifiers to classes."""

    def __init__(self) -> None:
        self._providers: Dict[str, Type[DroneControlProvider]] = {}

    def register(self, provider: Type[DroneControlProvider]) -> None:
        """Register a new provider class with the registry."""

        identifier = provider.provider_name.lower()
        LOGGER.debug("Registering provider '%s'", identifier)
        self._providers[identifier] = provider

    def available_providers(self) -> Iterable[str]:
        """Return iterable of provider identifiers for display."""

        return sorted(self._providers.keys())

    def create(self, identifier: str, *, connection_string: Optional[str] = None) -> DroneControlProvider:
        """Instantiate a provider matching the identifier."""

        provider_cls = self._providers.get(identifier.lower())
        if not provider_cls:
            raise KeyError(f"Unknown drone provider '{identifier}'")
        LOGGER.info("Creating provider '%s'", identifier)
        return provider_cls(connection_string=connection_string)


REGISTRY = DroneProviderRegistry()
