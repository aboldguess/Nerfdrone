"""Mini README: Modules implementing NeRF-based reconstruction workflows.

Provides high-level interfaces for initiating training or rendering of
Neural Radiance Fields using ingested footage. Designed for extension
with more sophisticated schedulers or hardware accelerators.
"""

from .reconstruction import NeRFPipeline, ReconstructionResult

__all__ = ["NeRFPipeline", "ReconstructionResult"]
