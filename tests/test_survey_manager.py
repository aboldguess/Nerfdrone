"""Mini README: Tests for survey manager and GeoJSON utilities.

These tests confirm that survey captures are returned in the expected order,
comparisons compute sensible deltas, and the GeoJSON helper validates
incoming polygons before route planning is executed.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from nerfdrone.surveys import SurveyAsset, SurveyCapture, SurveyManager
from nerfdrone.utils.geojson import bounds_from_geojson


def test_list_captures_returns_descending_order() -> None:
    """Ensure captures are sorted by date descending for UI rendering."""

    manager = SurveyManager(
        captures=[
            SurveyCapture(
                capture_id="a",
                name="Test A",
                captured_on=date(2023, 5, 1),
                bounds=(0.0, 0.0, 1.0, 1.0),
                assets=[],
                point_cloud_path="/tmp/a.ply",
            ),
            SurveyCapture(
                capture_id="b",
                name="Test B",
                captured_on=date(2024, 5, 1),
                bounds=(0.0, 0.0, 1.0, 1.0),
                assets=[],
                point_cloud_path="/tmp/b.ply",
            ),
        ]
    )

    captures = manager.list_captures()
    assert [capture.capture_id for capture in captures] == ["b", "a"]


def test_compare_captures_highlights_new_asset() -> None:
    """Comparisons should flag newly detected assets with positive deltas."""

    manager = SurveyManager(
        captures=[
            SurveyCapture(
                capture_id="first",
                name="Test",
                captured_on=date(2024, 1, 1),
                bounds=(0, 0, 1, 1),
                assets=[
                    SurveyAsset(
                        asset_id="bridge",
                        classification="bridge",
                        representative_point=(0.1, 0.1),
                        volume_cubic_m=100.0,
                    )
                ],
                point_cloud_path="/tmp/first.ply",
            ),
            SurveyCapture(
                capture_id="second",
                name="Test",
                captured_on=date(2024, 2, 1),
                bounds=(0, 0, 1, 1),
                assets=[
                    SurveyAsset(
                        asset_id="bridge",
                        classification="bridge",
                        representative_point=(0.1, 0.1),
                        volume_cubic_m=110.0,
                    ),
                    SurveyAsset(
                        asset_id="road",
                        classification="road",
                        representative_point=(0.2, 0.2),
                        volume_cubic_m=50.0,
                    ),
                ],
                point_cloud_path="/tmp/second.ply",
            ),
        ]
    )

    comparison = manager.compare_captures("first", "second")
    assert comparison.asset_differences["bridge"]["delta_volume_cubic_m"] == pytest.approx(10.0)
    assert comparison.asset_differences["road"]["target_volume_cubic_m"] == pytest.approx(50.0)
    assert "road" in comparison.narrative


def test_bounds_from_geojson_validates_polygon() -> None:
    """The helper should convert polygons to bounds and reject invalid payloads."""

    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0],
                [1.0, 0.0],
                [1.0, 1.0],
                [0.0, 1.0],
                [0.0, 0.0],
            ]
        ],
    }
    bounds = bounds_from_geojson(json.dumps(polygon))
    assert bounds == (0.0, 0.0, 1.0, 1.0)

    with pytest.raises(ValueError):
        bounds_from_geojson("{}")
