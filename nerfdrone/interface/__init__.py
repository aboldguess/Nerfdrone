"""Mini README: Interactive interfaces (web/CLI) for Nerfdrone.

Exports the FastAPI application factory that powers the browser-based
control panel. Future interface modules (e.g. CLI dashboards) should live
alongside this module.
"""

from .web_app import create_application

__all__ = ["create_application"]
