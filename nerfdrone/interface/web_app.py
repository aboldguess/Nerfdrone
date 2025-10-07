"""Mini README: FastAPI-powered control centre for Nerfdrone.

Structure:
    * create_application - application factory wiring routes and templates.
    * Dashboard state - in-memory mock used to demonstrate interactions.
    * Finance ledger - lightweight helper to simulate budgeting workflows.

The interface presents instructions, allows selection of drone providers,
initiates demo route planning, accepts video uploads for ingestion, and now
exposes a budgeting utility so recurring income or expenses can be duplicated
quickly. It prioritises clarity for users while remaining modular for
expansion.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..classification import SceneClassifier
from ..drone_control import REGISTRY
from ..drone_control.providers import DJIProvider  # noqa: F401  # ensure registration
from ..finance import FinanceLedger
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
    finance_ledger = FinanceLedger()
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
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "providers": providers,
                "messages": dashboard_state["messages"],
                "supported_labels": classifier.export_labels(),
                "survey_captures": survey_manager.list_captures(),
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

    @app.get("/finance/transactions")
    async def finance_transactions() -> JSONResponse:
        """Return grouped income and expense data for the UI tables."""

        snapshot = finance_ledger.export_snapshot()
        LOGGER.debug(
            "Returning %s income and %s expense entries",
            len(snapshot["income"]),
            len(snapshot["expenses"]),
        )
        return JSONResponse(snapshot)

    @app.post("/finance/duplicate")
    async def finance_duplicate(
        source_transaction_id: str = Form(...),
        description: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        amount: Optional[str] = Form(None),
        occurred_on: Optional[str] = Form(None),
        transaction_type: Optional[str] = Form(None),
        metadata: Optional[str] = Form(None),
    ) -> JSONResponse:
        """Duplicate a transaction, applying provided overrides."""

        overrides: Dict[str, object] = {}
        if description:
            overrides["description"] = description
        if category:
            overrides["category"] = category
        if amount not in (None, ""):
            try:
                overrides["amount"] = float(amount)
            except ValueError as error:  # pragma: no cover - defensive path
                raise HTTPException(status_code=400, detail="Amount must be numeric") from error
        if occurred_on:
            try:
                overrides["occurred_on"] = date.fromisoformat(occurred_on)
            except ValueError as error:
                raise HTTPException(status_code=400, detail="Date must be ISO formatted (YYYY-MM-DD)") from error
        if transaction_type:
            overrides["transaction_type"] = transaction_type
        if metadata:
            try:
                metadata_payload = json.loads(metadata)
            except json.JSONDecodeError as error:
                raise HTTPException(status_code=400, detail="Metadata must be valid JSON") from error
            if not isinstance(metadata_payload, dict):
                raise HTTPException(status_code=400, detail="Metadata JSON must describe an object")
            overrides["metadata"] = metadata_payload

        try:
            duplicated = finance_ledger.duplicate_transaction(
                source_transaction_id, overrides=overrides or None
            )
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        LOGGER.info("Finance duplicate created: %s", duplicated.transaction_id)
        return JSONResponse({
            "transaction": duplicated.as_dict(),
            "snapshot": finance_ledger.export_snapshot(),
        })

    return app
