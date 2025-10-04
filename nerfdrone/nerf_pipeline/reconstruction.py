"""Mini README: Orchestrates NeRF reconstruction workflows.

Structure:
    * ReconstructionResult - dataclass summarising outputs.
    * NeRFPipeline - facade around NeRF training/rendering routines.

The implementation uses ``nerfstudio`` where available, but gracefully
handles environments without GPU acceleration by returning structured
messages that describe what would occur. Hooks are present for future
automation such as batch processing or integration with task queues.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)

try:  # pragma: no cover - heavy dependency optional
    from nerfstudio.scripts.train import train as nerfstudio_train
except Exception:  # pragma: no cover - optional dependency handling
    nerfstudio_train = None


@dataclass(slots=True)
class ReconstructionResult:
    """Summary of a reconstruction job."""

    output_directory: Path
    frames_processed: int
    notes: str


class NeRFPipeline:
    """High-level interface for running NeRF reconstructions."""

    def __init__(self, *, workspace: Optional[Path] = None) -> None:
        self.workspace = workspace or Path("artifacts/nerf_outputs")
        self.workspace.mkdir(parents=True, exist_ok=True)
        LOGGER.debug("NeRF workspace set to %s", self.workspace)

    def reconstruct(self, video_path: Path, *, config_path: Optional[Path] = None) -> ReconstructionResult:
        """Run NeRF training for the provided footage."""

        output_dir = self.workspace / video_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        LOGGER.info("Starting reconstruction for %s", video_path)
        if nerfstudio_train:
            args = {"data": str(video_path), "output-dir": str(output_dir)}
            if config_path:
                args["load-config"] = str(config_path)
            LOGGER.debug("Nerfstudio arguments: %s", json.dumps(args, indent=2))
            nerfstudio_train(cli_args=args)  # type: ignore[arg-type]
            notes = "Reconstruction executed via nerfstudio"
        else:
            LOGGER.warning("nerfstudio not available; skipping heavy reconstruction")
            notes = "nerfstudio not installed; generated placeholder artefacts"
        summary_path = output_dir / "summary.json"
        summary_data: Dict[str, str | int] = {
            "video": str(video_path),
            "frames_processed": 0,
            "notes": notes,
        }
        summary_path.write_text(json.dumps(summary_data, indent=2))
        return ReconstructionResult(
            output_directory=output_dir,
            frames_processed=summary_data["frames_processed"],
            notes=notes,
        )
