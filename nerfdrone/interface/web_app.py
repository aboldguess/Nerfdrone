"""Mini README: FastAPI-powered control centre for Nerfdrone.

Structure:
    * create_application - application factory wiring routes and templates.
    * Dashboard state - in-memory mock used to demonstrate interactions.

The interface presents instructions, allows selection of drone providers,
initiates demo route planning, and accepts video uploads for ingestion.
It prioritises clarity for users while remaining modular for expansion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..classification import SceneClassifier
from ..drone_control import REGISTRY
from ..drone_control.providers import DJIProvider  # noqa: F401  # ensure registration
from ..ingestion import IngestionSource, VideoIngestor
from ..logging_utils import get_logger
from ..route_planning import RoutePlanner
from ..surveys import SurveyManager
from ..configuration import get_settings
from ..utils.geojson import bounds_from_geojson

LOGGER = get_logger(__name__)


def create_application() -> FastAPI:
    """Create the FastAPI application with routes and dependencies."""

    app = FastAPI(title="Nerfdrone Control Centre", version="0.2.0")
    templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
    static_directory = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")

    planner = RoutePlanner()
    classifier = SceneClassifier()
    ingestor = VideoIngestor()
    provider_registry = REGISTRY
    survey_manager = SurveyManager()
    settings = get_settings()

    dashboard_state: Dict[str, List[str]] = {
        "messages": [
            "Upload sample footage or pick a provider to begin.",
            "Plan routes using the survey generator or import your own.",
        ]
    }

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request) -> HTMLResponse:
        """Render the main dashboard with quick start instructions."""

        providers = list(provider_registry.available_providers())
        LOGGER.debug("Rendering dashboard with providers: %s", providers)
        metrics = survey_manager.summarise_metrics()
        LOGGER.debug(
            "Dashboard metrics -> surveys: %s acres: %.2f hours: %.2f data_gb: %.2f",
            metrics["total_surveys"],
            metrics["total_acres"],
            metrics["total_flight_hours"],
            metrics["total_data_gb"],
        )
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "providers": providers,
                "messages": dashboard_state["messages"],
                "supported_labels": classifier.export_labels(),
                "survey_captures": survey_manager.list_captures(),
                "metrics": metrics,
                "google_maps_key": settings.google_maps_api_key,
            },
        )

    @app.post("/plan-route")
    async def plan_route(
        lat_min: float = Form(...),
        lon_min: float = Form(...),
        lat_max: float = Form(...),
        lon_max: float = Form(...),
        area_geojson: Optional[str] = Form(None),
    ) -> JSONResponse:
        """Return a generated route for the provided bounds."""

        bounds = (lat_min, lon_min, lat_max, lon_max)
        if area_geojson:
            try:
                bounds = bounds_from_geojson(area_geojson)
            except ValueError as error:
                raise HTTPException(status_code=400, detail=str(error)) from error
        flight_path = planner.grid_survey(bounds)
        LOGGER.info("Generated route with %s waypoints", len(flight_path.waypoints))
        return JSONResponse({"commands": flight_path.as_commands(cruise_speed=6.5)})

    @app.post("/ingest-footage")
    async def ingest_footage(
        source: IngestionSource = Form(...),
        video: UploadFile = File(...),
    ) -> JSONResponse:
        """Handle video uploads and return metadata."""

        data = await video.read()
        temp_path = Path("/tmp") / video.filename
        temp_path.write_bytes(data)
        LOGGER.info("Received video upload %s (%s bytes)", video.filename, len(data))
        ingested = ingestor.ingest(temp_path, source=source)
        return JSONResponse(
            {
                "path": str(ingested.path),
                "frame_rate": ingested.frame_rate,
                "frame_count": ingested.frame_count,
                "source": ingested.source.value,
            }
        )

    @app.get("/classify-demo")
    async def classify_demo() -> JSONResponse:
        """Run a demo classification using pseudo-random vectors."""

        demo_vectors = {
            "asset_001": [0.7, 0.72, 0.71],
            "asset_002": [0.1, 0.15, 0.11],
            "asset_003": [0.4, 0.45, 0.5],
        }
        classifications = classifier.classify(demo_vectors)
        LOGGER.info("Demo classification generated %s entries", len(classifications))
        payload = [
            {
                "asset_id": result.asset_id,
                "labels": list(result.labels),
                "confidence": result.confidence,
            }
            for result in classifications
        ]
        return JSONResponse({"classifications": payload})

    @app.get("/survey-days")
    async def survey_days() -> JSONResponse:
        """Return survey captures along with GeoJSON overlays."""

        captures = [
            {
                "capture_id": capture.capture_id,
                "name": capture.name,
                "captured_on": capture.captured_on.isoformat(),
                "point_cloud_path": capture.point_cloud_path,
                "asset_count": len(capture.assets),
                "notes": capture.notes,
                "overlay": capture.to_geojson(),
                "assets": [
                    {
                        "asset_id": asset.asset_id,
                        "classification": asset.classification,
                        "volume_cubic_m": asset.volume_cubic_m,
                        "annotations": asset.annotations,
                    }
                    for asset in capture.assets
                ],
            }
            for capture in survey_manager.list_captures()
        ]
        LOGGER.debug("Returning %s survey captures", len(captures))
        return JSONResponse({"captures": captures})

    @app.post("/compare-captures")
    async def compare_captures(
        base_capture: str = Form(...),
        target_capture: str = Form(...),
        focus_asset: Optional[str] = Form(None),
    ) -> JSONResponse:
        """Compare two survey captures and return differences."""

        try:
            comparison = survey_manager.compare_captures(
                base_capture,
                target_capture,
                focus_asset=focus_asset,
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        payload = {
            "base_capture": comparison.base_capture.capture_id,
            "target_capture": comparison.target_capture.capture_id,
            "asset_differences": comparison.asset_differences,
            "narrative": comparison.narrative,
        }
        LOGGER.info(
            "Comparison generated for base=%s target=%s", base_capture, target_capture
        )
        return JSONResponse(payload)

    @app.post("/annotate-asset")
    async def annotate_asset(
        capture_id: str = Form(...),
        asset_id: str = Form(...),
        note: str = Form(...),
    ) -> JSONResponse:
        """Append an operator annotation to an asset."""

        try:
            asset = survey_manager.append_annotation(capture_id, asset_id, note)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        LOGGER.debug(
            "Annotation recorded for capture=%s asset=%s", capture_id, asset_id
        )
        return JSONResponse(
            {
                "capture_id": capture_id,
                "asset_id": asset.asset_id,
                "annotations": asset.annotations,
                "note": note,
            }
        )

    return app
