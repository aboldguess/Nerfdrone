"""Mini README: Data ingestion helpers for Nerfdrone pipelines.

Convenience exports for ingesting footage and sample data sources. This
package will grow to include live stream adapters alongside file-based
uploads.
"""

from .video_ingestor import IngestionSource, VideoIngestor

__all__ = ["VideoIngestor", "IngestionSource"]
