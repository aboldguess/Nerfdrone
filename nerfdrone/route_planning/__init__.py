"""Mini README: Route planning subsystem for drone mission design.

Exports planner classes that can be used by interfaces or scripts to
calculate flight paths. The package emphasises modularity so more complex
planning algorithms can be introduced later without breaking the API.
"""

from .planner import FlightPath, RoutePlanner

__all__ = ["RoutePlanner", "FlightPath"]
