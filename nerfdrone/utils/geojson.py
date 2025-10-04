"""Mini README: GeoJSON helper utilities for Nerfdrone.

This module provides lightweight helpers for validating GeoJSON payloads and
extracting bounding boxes. Keeping the logic isolated avoids importing web
framework dependencies when running unit tests or reusing the helper in other
modules.
"""

from __future__ import annotations

import json
from typing import Tuple


def bounds_from_geojson(area_geojson: str) -> Tuple[float, float, float, float]:
    """Validate GeoJSON and return bounding coordinates as (lat_min, lon_min, lat_max, lon_max)."""

    try:
        geojson = json.loads(area_geojson)
    except json.JSONDecodeError as error:
        raise ValueError("GeoJSON payload is invalid JSON") from error

    if geojson.get("type") == "Feature":
        geometry = geojson.get("geometry", {})
    else:
        geometry = geojson

    if geometry.get("type") != "Polygon":
        raise ValueError("Only polygon GeoJSON payloads are supported")

    coordinates = geometry.get("coordinates")
    if not coordinates:
        raise ValueError("Polygon coordinates are required")

    flattened = [point for ring in coordinates for point in ring]
    lons = [float(point[0]) for point in flattened]
    lats = [float(point[1]) for point in flattened]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    return (lat_min, lon_min, lat_max, lon_max)
