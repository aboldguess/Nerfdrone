"""Mini README: Entry point CLI for launching the Nerfdrone control centre.

This script exposes a Typer CLI that allows operators to start the FastAPI
application with configurable host, port, and production flags. It ensures
consistent logging and draws settings from environment variables when
available.
"""

from __future__ import annotations

import typer
import uvicorn

from nerfdrone.configuration import get_settings
from nerfdrone.interface import create_application
from nerfdrone.logging_utils import configure_root_logger

cli = typer.Typer(help="Launch and manage the Nerfdrone web control centre.")


@cli.command()
def run(
    host: str = typer.Option(None, help="Host interface to bind."),
    port: int = typer.Option(None, help="Port to listen on."),
    production: bool = typer.Option(
        False, help="Use production server settings (disable auto-reload)."
    ),
) -> None:
    """Start the FastAPI application using uvicorn."""

    settings = get_settings()
    effective_host = host or settings.interface_host
    effective_port = port or settings.interface_port
    configure_root_logger()

    # Provide human-friendly guidance on which URL to open in a browser. Binding to
    # 0.0.0.0 is useful for exposing the service, but browsers cannot navigate to
    # that sentinel address directly. We therefore surface localhost (or the chosen
    # host) so operators avoid the ERR_ADDRESS_INVALID issue seen when pasting
    # 0.0.0.0 into the URL bar.
    browser_host = "127.0.0.1" if effective_host in {"0.0.0.0", "::"} else effective_host
    typer.echo(
        "Starting Nerfdrone on "
        f"{effective_host}:{effective_port}.\n"
        "Open your browser at "
        f"http://{browser_host}:{effective_port}"
        + (
            " (use your machine's IP address for remote access)."
            if effective_host in {"0.0.0.0", "::"}
            else ""
        )
    )
    uvicorn.run(
        "nerfdrone.interface.web_app:create_application",
        host=effective_host,
        port=effective_port,
        factory=True,
        reload=not production,
    )


if __name__ == "__main__":
    cli()
