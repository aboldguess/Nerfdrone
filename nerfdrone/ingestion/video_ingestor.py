"""Mini README: Unified video ingestion workflows for Nerfdrone.

Structure:
    * IngestionSource - enumeration of supported input channels.
    * VideoIngestor - class responsible for preparing footage for processing.

The ingestion process performs validation, metadata extraction, and stores
files within the configured data directory. It is built to support both
mobile device testing and production drone feeds.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency guard
    import cv2  # type: ignore
except Exception:  # pragma: no cover - handled gracefully
    cv2 = None  # type: ignore

from ..configuration import get_settings
from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


class IngestionSource(str, Enum):
    """Supported footage ingestion sources."""

    MOBILE_UPLOAD = "mobile_upload"
    FILE_UPLOAD = "file_upload"
    LIVE_STREAM = "live_stream"


@dataclass(slots=True)
class IngestedVideo:
    """Metadata representing the stored video asset."""

    path: Path
    frame_rate: float
    frame_count: int
    source: IngestionSource


class VideoIngestor:
    """Persist uploaded footage and extract summary metadata."""

    def __init__(self, *, storage_directory: Optional[Path] = None) -> None:
        settings = get_settings()
        self.storage_directory = storage_directory or settings.data_directory / "videos"
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        LOGGER.debug("Video storage directory set to %s", self.storage_directory)

    def ingest(self, file_path: Path, *, source: IngestionSource) -> IngestedVideo:
        """Copy footage into managed storage and compute metadata."""

        destination = self.storage_directory / file_path.name
        shutil.copy2(file_path, destination)
        LOGGER.info("Ingested video copied to %s", destination)
        frame_rate = 0.0
        frame_count = 0
        if cv2 is None:
            LOGGER.warning("OpenCV not available; skipping metadata extraction")
        else:
            capture = cv2.VideoCapture(str(destination))  # type: ignore[attr-defined]
            if not capture.isOpened():
                raise ValueError(f"Unable to open video file: {destination}")
            frame_rate = capture.get(cv2.CAP_PROP_FPS) or 0.0  # type: ignore[attr-defined]
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)  # type: ignore[attr-defined]
            capture.release()
            LOGGER.debug(
                "Video metadata - frame_rate: %s frame_count: %s", frame_rate, frame_count
            )
        return IngestedVideo(
            path=destination,
            frame_rate=frame_rate,
            frame_count=frame_count,
            source=source,
        )
