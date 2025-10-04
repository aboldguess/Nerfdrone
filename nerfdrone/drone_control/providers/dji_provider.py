"""Mini README: Example DJI drone provider integration.

Structure:
    * DJIProvider - concrete implementation using the DJI SDK facade.

The implementation is intentionally simulated so that the application can
be tested without physical hardware while preserving the extension
patterns needed for real SDK bindings.
"""

from __future__ import annotations

import time
from typing import Iterable

from ..base import DroneControlProvider, FlightCommand
from ..registry import REGISTRY
from ...logging_utils import get_logger

LOGGER = get_logger(__name__)


class DJIProvider(DroneControlProvider):
    """Basic mock provider illustrating how the registry is extended."""

    provider_name = "dji"

    def connect(self) -> None:  # pragma: no cover - demonstration only
        LOGGER.info("Connecting to DJI drone with connection '%s'", self.connection_string)
        time.sleep(0.1)

    def disconnect(self) -> None:  # pragma: no cover - demonstration only
        LOGGER.info("Disconnecting DJI drone")
        time.sleep(0.05)

    def send_commands(self, commands: Iterable[FlightCommand]) -> None:
        for command in commands:
            LOGGER.info("DJI command: %s -> %s", command.action, command.parameters)
            time.sleep(command.duration_seconds)


REGISTRY.register(DJIProvider)
