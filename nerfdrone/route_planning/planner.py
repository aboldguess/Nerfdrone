"""Mini README: Lightweight flight route planning utilities.

Structure:
    * FlightWaypoint - dataclass capturing GPS and altitude.
    * FlightPath - container aggregating waypoints and metadata.
    * RoutePlanner - sample planner using heuristics to generate paths.

The module lays groundwork for more advanced planners (e.g. terrain-aware
or weather-informed). It currently supports generating simple grid
patterns suitable for photogrammetry captures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Sequence

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


def _frange(start: float, stop: float, step: float) -> Iterable[float]:
    """Yield a range of floats inclusive of the stop boundary."""

    value = start
    while value <= stop:
        yield round(value, 6)
        value += step


@dataclass(slots=True)
class FlightWaypoint:
    """Single waypoint coordinate."""

    latitude: float
    longitude: float
    altitude: float


@dataclass(slots=True)
class FlightPath:
    """Ordered collection of waypoints forming a mission path."""

    waypoints: List[FlightWaypoint] = field(default_factory=list)
    description: str = ""

    def as_commands(self, cruise_speed: float) -> List[dict]:
        """Convert waypoints to command dictionaries for UI previews."""

        commands: List[dict] = []
        for waypoint in self.waypoints:
            commands.append(
                {
                    "action": "navigate_to",
                    "latitude": waypoint.latitude,
                    "longitude": waypoint.longitude,
                    "altitude": waypoint.altitude,
                    "cruise_speed": cruise_speed,
                }
            )
        return commands


class RoutePlanner:
    """Generate routes for imagery capture using survey style grids."""

    def __init__(self, *, altitude: float = 50.0, spacing: float = 0.0003) -> None:
        self.altitude = altitude
        self.spacing = spacing
        LOGGER.debug(
            "Initialised RoutePlanner with altitude=%s spacing=%s", altitude, spacing
        )

    def grid_survey(self, bounds: Sequence[float]) -> FlightPath:
        """Create a lawnmower pattern covering the bounding box."""

        if len(bounds) != 4:
            raise ValueError("Bounds must be (lat_min, lon_min, lat_max, lon_max)")
        lat_min, lon_min, lat_max, lon_max = bounds
        LOGGER.info(
            "Generating grid survey for bounds %s with spacing %s",
            bounds,
            self.spacing,
        )
        waypoints: List[FlightWaypoint] = []
        reverse = False
        for latitude in _frange(lat_min, lat_max, self.spacing):
            longitudes = list(_frange(lon_min, lon_max, self.spacing))
            if reverse:
                longitudes.reverse()
            reverse = not reverse
            for longitude in longitudes:
                waypoints.append(FlightWaypoint(latitude=latitude, longitude=longitude, altitude=self.altitude))
        return FlightPath(waypoints=waypoints, description="Grid survey pattern")

    def custom_path(self, waypoints: Iterable[FlightWaypoint]) -> FlightPath:
        """Wrap manually provided waypoints into a flight path."""

        waypoints_list = list(waypoints)
        if not waypoints_list:
            raise ValueError("At least one waypoint is required")
        LOGGER.info("Constructed custom path with %s waypoints", len(waypoints_list))
        return FlightPath(waypoints=waypoints_list, description="Custom path")
