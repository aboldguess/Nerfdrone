"""Mini README: Centralised configuration models and helpers for Nerfdrone.

Structure:
    * NerfdroneSettings - Pydantic model describing runtime configuration.
    * get_settings - cached accessor for environment-aware settings.

Usage:
    Import ``get_settings`` to read environment variables, toggle production
    behaviour, and specify service ports. The configuration is cached so the
    cost of validation is incurred only once per process.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class NerfdroneSettings(BaseSettings):
    """Runtime configuration for the Nerfdrone platform."""

    environment: str = Field(
        "development",
        description="Environment label controlling debug toggles and logging levels.",
    )
    data_directory: Path = Field(
        Path("data"),
        description="Default directory where ingested data and artefacts are stored.",
    )
    interface_host: str = Field(
        "0.0.0.0",
        description="Network interface for the interactive service to bind to.",
    )
    interface_port: int = Field(
        8000,
        description="Default port the interactive service exposes.",
        ge=1,
        le=65535,
    )
    google_maps_api_key: Optional[str] = Field(
        None,
        description=(
            "API key used to enable the Google Maps basemap within the dashboard."
            " Leave unset to rely solely on OpenStreetMap."
        ),
    )

    class Config:
        env_prefix = "NERFDRONE_"
        env_file = ".env"
        case_sensitive = False

    @validator("data_directory", pre=True)
    def _expand_path(cls, value: Optional[str | Path]) -> Path:
        """Ensure configured paths expand user directories and exist."""

        path = Path(value).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> NerfdroneSettings:
    """Return cached settings, ensuring consistent configuration across modules."""

    return NerfdroneSettings()
