"""Mini README: Asset classification subsystem for reconstructed scenes.

Exports base classifier abstractions and default implementations. The
module aims to be easily replaceable with more sophisticated models
without altering the surrounding orchestration code.
"""

from .classifier import AssetClassification, SceneClassifier

__all__ = ["SceneClassifier", "AssetClassification"]
