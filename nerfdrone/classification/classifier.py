"""Mini README: Simplified scene classification for Nerfdrone outputs.

Structure:
    * AssetClassification - dataclass summarising classification results.
    * SceneClassifier - pluggable classifier with extensible label set.

The default implementation relies on scikit-learn to demonstrate
extensibility. Production deployments can swap the estimator with a deep
learning model or an API call without changing the consuming code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer

from ..logging_utils import get_logger

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class AssetClassification:
    """Represents the classification of a segmented asset."""

    asset_id: str
    labels: Sequence[str]
    confidence: float


class SceneClassifier:
    """Perform naive classification using engineered features."""

    def __init__(self, *, supported_labels: Optional[List[str]] = None) -> None:
        if supported_labels is None:
            supported_labels = [
                "building",
                "road",
                "railway",
                "field",
                "trees",
                "water",
            ]
        self.supported_labels = supported_labels
        self.label_binarizer = MultiLabelBinarizer(classes=supported_labels)
        self.label_binarizer.fit([supported_labels])
        LOGGER.debug("SceneClassifier initialised with labels: %s", supported_labels)

    def classify(self, embedding_vectors: Dict[str, Iterable[float]]) -> List[AssetClassification]:
        """Classify assets given feature embeddings."""

        results: List[AssetClassification] = []
        for asset_id, features in embedding_vectors.items():
            vector = np.array(list(features))
            if vector.size == 0:
                LOGGER.warning("Asset %s has no features; skipping", asset_id)
                continue
            # Toy scoring: choose labels deterministically based on vector stats.
            mean_value = float(np.mean(vector))
            std_dev = float(np.std(vector))
            LOGGER.debug(
                "Asset %s mean %.3f std %.3f -> heuristics for label selection",
                asset_id,
                mean_value,
                std_dev,
            )
            candidate_labels = []
            if mean_value > 0.6:
                candidate_labels.append("building")
            if std_dev < 0.1:
                candidate_labels.append("road")
            if 0.2 < mean_value < 0.5:
                candidate_labels.append("field")
            if std_dev > 0.4:
                candidate_labels.append("trees")
            if not candidate_labels:
                candidate_labels.append("water")
            results.append(
                AssetClassification(
                    asset_id=asset_id,
                    labels=candidate_labels,
                    confidence=min(0.99, mean_value + 0.1),
                )
            )
        return results

    def export_labels(self) -> List[str]:
        """Expose supported labels for UI consumption."""

        return list(self.supported_labels)
