"""Mini README: Survey management utilities package for Nerfdrone.

This package groups helper classes that curate historical capture metadata,
allow comparisons between survey runs, and expose overlays suitable for the
web control centre. The `manager` module contains the primary public API.
"""

from .manager import CaptureComparison, SurveyAsset, SurveyCapture, SurveyManager

__all__ = [
    "CaptureComparison",
    "SurveyAsset",
    "SurveyCapture",
    "SurveyManager",
]
