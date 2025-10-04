"""Mini README: Export reconstructed assets to PLY point clouds.

Structure:
    * PointCloudExporter - serialises segmented assets into PLY format.

The exporter is intentionally minimal but demonstrates how selected assets
from the classification stage can be persisted. It can be expanded to
support LAS/LAZ or other industry-standard formats.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class PointCloud:
    """Simple container for point cloud data."""

    points: np.ndarray
    colors: np.ndarray | None = None


class PointCloudExporter:
    """Persist selected asset point clouds to disk."""

    def export(self, point_cloud: PointCloud, destination: Path) -> Path:
        """Export the cloud to PLY format at the destination."""

        if point_cloud.points.ndim != 2 or point_cloud.points.shape[1] != 3:
            raise ValueError("Point cloud must be of shape (N, 3)")
        LOGGER.info("Exporting point cloud with %s points to %s", point_cloud.points.shape[0], destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", encoding="utf-8") as ply_file:
            vertex_count = point_cloud.points.shape[0]
            header = [
                "ply",
                "format ascii 1.0",
                f"element vertex {vertex_count}",
                "property float x",
                "property float y",
                "property float z",
            ]
            if point_cloud.colors is not None:
                header.extend(
                    [
                        "property uchar red",
                        "property uchar green",
                        "property uchar blue",
                    ]
                )
            header.append("end_header\n")
            ply_file.write("\n".join(header))
            for index in range(vertex_count):
                point = point_cloud.points[index]
                if point_cloud.colors is not None:
                    color = point_cloud.colors[index]
                    ply_file.write(
                        f"{point[0]} {point[1]} {point[2]} {int(color[0])} {int(color[1])} {int(color[2])}\n"
                    )
                else:
                    ply_file.write(f"{point[0]} {point[1]} {point[2]}\n")
        return destination

    def export_selected_assets(
        self,
        selected_assets: Sequence[str],
        asset_point_lookup: dict[str, np.ndarray],
        *,
        output_directory: Path,
    ) -> list[Path]:
        """Export multiple assets into separate PLY files."""

        output_directory.mkdir(parents=True, exist_ok=True)
        exported_paths: list[Path] = []
        for asset in selected_assets:
            if asset not in asset_point_lookup:
                LOGGER.warning("Asset %s not in lookup; skipping", asset)
                continue
            points = asset_point_lookup[asset]
            export_path = output_directory / f"{asset}.ply"
            exported_paths.append(self.export(PointCloud(points=points), export_path))
        return exported_paths
