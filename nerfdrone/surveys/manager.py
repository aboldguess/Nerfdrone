"""Mini README: Survey data management and comparison helpers.

Structure:
    * SurveyAsset - represents a classified object detected within a survey.
    * SurveyCapture - captures metadata about a specific survey day.
    * CaptureComparison - structured diff between two captures.
    * SurveyManager - orchestrates retrieval, overlay generation, and notes.

The manager centralises GIS-style overlays that are used by the control
centre. It stores lightweight demo data in-memory so the interface can
showcase workflows without external dependencies. Future implementations can
swap in persistent storage or advanced analytics while reusing this API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import math
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


def _default_overlay(bounds: Tuple[float, float, float, float]) -> Dict:
    """Build a GeoJSON polygon from bounding coordinates."""

    lat_min, lon_min, lat_max, lon_max = bounds
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [lon_min, lat_min],
                    [lon_max, lat_min],
                    [lon_max, lat_max],
                    [lon_min, lat_max],
                    [lon_min, lat_min],
                ]
            ],
        },
        "properties": {},
    }


@dataclass(slots=True)
class SurveyAsset:
    """Classified asset with optional annotations."""

    asset_id: str
    classification: str
    representative_point: Tuple[float, float]
    volume_cubic_m: float
    annotations: List[str] = field(default_factory=list)


@dataclass(slots=True)
class SurveyCapture:
    """Summary of a survey mission's captured data."""

    capture_id: str
    name: str
    captured_on: date
    bounds: Tuple[float, float, float, float]
    assets: List[SurveyAsset]
    point_cloud_path: str
    flight_time_minutes: float
    data_volume_gb: float
    notes: List[str] = field(default_factory=list)

    @property
    def acreage(self) -> float:
        """Approximate surveyed acres derived from bounding coordinates."""

        return _estimate_acres(self.bounds)

    def to_geojson(self) -> Dict:
        """Return a GeoJSON Feature for map overlays."""

        feature = _default_overlay(self.bounds)
        feature["properties"] = {
            "name": self.name,
            "capture_id": self.capture_id,
            "captured_on": self.captured_on.isoformat(),
        }
        return feature


@dataclass(slots=True)
class CaptureComparison:
    """Difference summary between two survey captures."""

    base_capture: SurveyCapture
    target_capture: SurveyCapture
    asset_differences: Dict[str, Dict[str, float]]
    narrative: str


def _estimate_acres(bounds: Tuple[float, float, float, float]) -> float:
    """Approximate acreage represented by the provided bounds."""

    lat_min, lon_min, lat_max, lon_max = bounds
    mean_lat_radians = math.radians((lat_min + lat_max) / 2)
    lat_distance_m = abs(lat_max - lat_min) * 111_320
    lon_distance_m = abs(lon_max - lon_min) * (111_320 * math.cos(mean_lat_radians))
    area_sq_m = lat_distance_m * lon_distance_m
    return area_sq_m * 0.000247105


class SurveyManager:
    """Manage historical survey data and lightweight annotations."""

    def __init__(self, captures: Optional[Iterable[SurveyCapture]] = None) -> None:
        if captures is None:
            captures = self._build_demo_captures()
        self._captures: Dict[str, SurveyCapture] = {capture.capture_id: capture for capture in captures}
        LOGGER.debug("Initialised SurveyManager with %s captures", len(self._captures))

    @staticmethod
    def _build_demo_captures() -> List[SurveyCapture]:
        """Create deterministic demo captures for UI previews."""

        return [
            SurveyCapture(
                capture_id="central_river_2024_03_14",
                name="Central River Basin",
                captured_on=date(2024, 3, 14),
                bounds=(51.4995, -0.1312, 51.5025, -0.1275),
                assets=[
                    SurveyAsset(
                        asset_id="bridge_east",
                        classification="bridge",
                        representative_point=(51.5007, -0.1298),
                        volume_cubic_m=2300.0,
                        annotations=["Structural joints intact", "Low vegetation"],
                    ),
                    SurveyAsset(
                        asset_id="riverbank_section_a",
                        classification="riverbank",
                        representative_point=(51.5018, -0.1301),
                        volume_cubic_m=180.0,
                    ),
                    SurveyAsset(
                        asset_id="parkland_south",
                        classification="park",
                        representative_point=(51.5002, -0.1285),
                        volume_cubic_m=75.0,
                        annotations=["Playground equipment requires inspection"],
                    ),
                ],
                point_cloud_path="/point-clouds/central-river-2024-03-14.ply",
                flight_time_minutes=82.0,
                data_volume_gb=14.4,
            ),
            SurveyCapture(
                capture_id="central_river_2024_05_22",
                name="Central River Basin",
                captured_on=date(2024, 5, 22),
                bounds=(51.4995, -0.1312, 51.5025, -0.1275),
                assets=[
                    SurveyAsset(
                        asset_id="bridge_east",
                        classification="bridge",
                        representative_point=(51.5007, -0.1298),
                        volume_cubic_m=2305.5,
                        annotations=["Slight debris accumulation"]
                    ),
                    SurveyAsset(
                        asset_id="riverbank_section_a",
                        classification="riverbank",
                        representative_point=(51.5018, -0.1301),
                        volume_cubic_m=205.0,
                        annotations=["Higher water levels recorded"],
                    ),
                    SurveyAsset(
                        asset_id="construction_zone",
                        classification="construction",
                        representative_point=(51.5004, -0.1292),
                        volume_cubic_m=450.0,
                    ),
                ],
                point_cloud_path="/point-clouds/central-river-2024-05-22.ply",
                flight_time_minutes=88.0,
                data_volume_gb=16.2,
            ),
        ]

    def list_captures(self) -> List[SurveyCapture]:
        """Return captures ordered by capture date descending."""

        return sorted(self._captures.values(), key=lambda capture: capture.captured_on, reverse=True)

    def summarise_metrics(self) -> Dict[str, Any]:
        """Aggregate survey insights for dashboard visualisation."""

        captures = self.list_captures()
        if not captures:
            return {
                "total_surveys": 0,
                "total_acres": 0.0,
                "total_flight_hours": 0.0,
                "total_data_gb": 0.0,
                "average_assets_per_survey": 0.0,
                "latest_capture_name": "",
                "latest_capture_date": "",
            }

        total_surveys = len(captures)
        total_acres = sum(capture.acreage for capture in captures)
        total_flight_hours = sum(capture.flight_time_minutes for capture in captures) / 60.0
        total_data_gb = sum(capture.data_volume_gb for capture in captures)
        average_assets = sum(len(capture.assets) for capture in captures) / total_surveys
        latest_capture = captures[0]

        return {
            "total_surveys": total_surveys,
            "total_acres": total_acres,
            "total_flight_hours": total_flight_hours,
            "total_data_gb": total_data_gb,
            "average_assets_per_survey": average_assets,
            "latest_capture_name": latest_capture.name,
            "latest_capture_date": latest_capture.captured_on.isoformat(),
        }

    def get_capture(self, capture_id: str) -> SurveyCapture:
        """Retrieve a capture, raising informative error if not known."""

        if capture_id not in self._captures:
            raise KeyError(f"Capture {capture_id} is not registered")
        return self._captures[capture_id]

    def compare_captures(
        self,
        base_capture_id: str,
        target_capture_id: str,
        *,
        focus_asset: Optional[str] = None,
    ) -> CaptureComparison:
        """Compare two captures highlighting asset deltas."""

        base_capture = self.get_capture(base_capture_id)
        target_capture = self.get_capture(target_capture_id)
        LOGGER.info(
            "Comparing captures base=%s target=%s focus_asset=%s",
            base_capture.capture_id,
            target_capture.capture_id,
            focus_asset,
        )

        base_assets = {asset.asset_id: asset for asset in base_capture.assets}
        target_assets = {asset.asset_id: asset for asset in target_capture.assets}

        relevant_assets = (
            [focus_asset]
            if focus_asset
            else sorted(set(base_assets.keys()) | set(target_assets.keys()))
        )
        asset_differences: Dict[str, Dict[str, float]] = {}
        narrative_lines: List[str] = []

        for asset_id in relevant_assets:
            base_asset = base_assets.get(asset_id)
            target_asset = target_assets.get(asset_id)
            if not base_asset and not target_asset:
                continue
            base_volume = base_asset.volume_cubic_m if base_asset else 0.0
            target_volume = target_asset.volume_cubic_m if target_asset else 0.0
            delta = target_volume - base_volume
            asset_differences[asset_id] = {
                "base_volume_cubic_m": base_volume,
                "target_volume_cubic_m": target_volume,
                "delta_volume_cubic_m": delta,
            }
            if base_asset and target_asset:
                narrative_lines.append(
                    f"Asset {asset_id} changed by {delta:+.2f} m³ between surveys."
                )
            elif base_asset and not target_asset:
                narrative_lines.append(f"Asset {asset_id} is no longer present in the target survey.")
            elif not base_asset and target_asset:
                narrative_lines.append(f"New asset {asset_id} detected with {target_volume:.2f} m³ volume.")

        narrative = " \n".join(narrative_lines) if narrative_lines else "No measurable differences detected."
        return CaptureComparison(
            base_capture=base_capture,
            target_capture=target_capture,
            asset_differences=asset_differences,
            narrative=narrative,
        )

    def append_annotation(self, capture_id: str, asset_id: str, note: str) -> SurveyAsset:
        """Record an annotation for a specific asset within a capture."""

        capture = self.get_capture(capture_id)
        for asset in capture.assets:
            if asset.asset_id == asset_id:
                asset.annotations.append(note)
                capture.notes.append(f"{asset_id}: {note}")
                LOGGER.debug(
                    "Recorded annotation for capture=%s asset=%s note=%s",
                    capture_id,
                    asset_id,
                    note,
                )
                return asset
        raise KeyError(f"Asset {asset_id} not present in capture {capture_id}")

