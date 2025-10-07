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
                flight_time_minutes=60.0,
                data_volume_gb=10.0,
            ),
            SurveyCapture(
                capture_id="b",
                name="Test B",
                captured_on=date(2024, 5, 1),
                bounds=(0.0, 0.0, 1.0, 1.0),
                assets=[],
                point_cloud_path="/tmp/b.ply",
                flight_time_minutes=72.0,
                data_volume_gb=12.5,
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
                flight_time_minutes=55.0,
                data_volume_gb=8.0,
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
                flight_time_minutes=65.0,
                data_volume_gb=9.2,
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


def test_summarise_metrics_returns_expected_totals() -> None:
    """Dashboard summaries should aggregate acreage, hours, and assets."""

    manager = SurveyManager(
        captures=[
            SurveyCapture(
                capture_id="demo_one",
                name="Alpha",
                captured_on=date(2024, 6, 1),
                bounds=(10.0, 20.0, 10.01, 20.01),
                assets=[
                    SurveyAsset(
                        asset_id="asset_a",
                        classification="bridge",
                        representative_point=(10.005, 20.005),
                        volume_cubic_m=100.0,
                    )
                ],
                point_cloud_path="/tmp/alpha.ply",
                flight_time_minutes=45.0,
                data_volume_gb=5.0,
            ),
            SurveyCapture(
                capture_id="demo_two",
                name="Beta",
                captured_on=date(2024, 6, 15),
                bounds=(10.0, 20.0, 10.02, 20.02),
                assets=[
                    SurveyAsset(
                        asset_id="asset_b",
                        classification="road",
                        representative_point=(10.015, 20.015),
                        volume_cubic_m=120.0,
                    ),
                    SurveyAsset(
                        asset_id="asset_c",
                        classification="river",
                        representative_point=(10.018, 20.018),
                        volume_cubic_m=200.0,
                    ),
                ],
                point_cloud_path="/tmp/beta.ply",
                flight_time_minutes=75.0,
                data_volume_gb=7.5,
            ),
        ]
    )

    metrics = manager.summarise_metrics()
    assert metrics["total_surveys"] == 2
    assert metrics["total_flight_hours"] == pytest.approx((45.0 + 75.0) / 60.0)
    assert metrics["total_data_gb"] == pytest.approx(12.5)
    assert metrics["average_assets_per_survey"] == pytest.approx(1.5)
    assert metrics["latest_capture_name"] == "Beta"
    assert metrics["latest_capture_date"] == date(2024, 6, 15).isoformat()
