"""Mini README: Tests for the route planner module.

Validates the grid survey generation to ensure deterministic outputs.
"""

from nerfdrone.route_planning import RoutePlanner


def test_grid_survey_produces_waypoints():
    planner = RoutePlanner(altitude=10.0, spacing=0.0005)
    path = planner.grid_survey((0.0, 0.0, 0.001, 0.001))
    assert len(path.waypoints) > 0
    commands = path.as_commands(cruise_speed=5.0)
    assert commands[0]["action"] == "navigate_to"
