"""Mini README: Abstract base classes describing drone control capabilities.

Structure:
    * FlightCommand - dataclass describing atomic control instructions.
    * DroneControlProvider - abstract interface implemented by vendors.

The module ensures a consistent API surface for controlling drones while
allowing vendor-specific providers to implement proprietary behaviour.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class FlightCommand:
    """Representation of a drone movement or action command."""

    action: str
    parameters: Dict[str, float]
    duration_seconds: float = 0.0


class DroneControlProvider(ABC):
    """Base interface for drone provider integrations."""

    provider_name: str = "generic"

    def __init__(self, connection_string: Optional[str] = None) -> None:
        self.connection_string = connection_string
        LOGGER.debug(
            "Initialising %s provider with connection '%s'", self.provider_name, connection_string
        )

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection with the drone hardware or simulator."""

    @abstractmethod
    def disconnect(self) -> None:
        """Safely terminate the connection and release resources."""

    @abstractmethod
    def send_commands(self, commands: Iterable[FlightCommand]) -> None:
        """Dispatch a sequence of flight commands to the drone."""

    def emergency_land(self) -> None:
        """Optional hook for triggering emergency land procedures."""

        LOGGER.warning("Emergency landing triggered for provider %s", self.provider_name)

    def metadata(self) -> Dict[str, str]:
        """Return diagnostic metadata for UI displays."""

        return {
            "provider": self.provider_name,
            "connection": self.connection_string or "not configured",
        }
