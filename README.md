# Nerfdrone Platform

Nerfdrone is a modular toolkit for planning drone missions, ingesting aerial footage,
reconstructing 3D scenes with Neural Radiance Fields (NeRF), classifying assets, and
exporting point clouds. The project is designed with extensibility and security in
mind so new hardware providers or analysis modules can be added with minimal effort.

## Features

- **Pluggable drone provider architecture** – integrate vendor SDKs via a central registry.
- **Mission route planning** – generate grid surveys or custom paths with validation and map-based drawing.
- **Footage ingestion pipeline** – test the full workflow with mobile uploads or existing files.
- **NeRF reconstruction facade** – orchestrate nerfstudio-powered training where available.
- **Asset classification** – extensible classifier that can be replaced with advanced models.
- **Point cloud exporting** – persist selected assets as PLY files for downstream tooling.
- **Modern web control centre** – FastAPI dashboard with map overlays, survey comparisons, and clear on-screen guidance.

## Quickstart

These instructions work on Linux, Windows, and Raspberry Pi devices. Replace `python`
with `python3` if required by your environment.

### 1. Clone the repository

```bash
git clone https://github.com/your-org/nerfdrone.git
cd nerfdrone
```

### 2. Create a virtual environment

#### Linux / macOS / Raspberry Pi

```bash
python -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -e .
```

To enable NeRF training with nerfstudio, install the optional extras:

```bash
pip install -e .[nerf]
```

### 4. Configure environment (optional)

Copy `.env.example` to `.env` and adjust values if you want to override defaults such as
storage directories or server ports.

```bash
cp .env.example .env
```

#### Enable Google Maps (optional)

To switch between OpenStreetMap and Google Maps in the dashboard, supply a Google Maps
JavaScript API key. Add the following line to your `.env` file (replace the placeholder
with your key):

```
NERFDRONE_GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"
```

Restart the control centre after updating the environment file so the new key is loaded.

### 5. Launch the control centre

```bash
python main_control_centre.py --host 0.0.0.0 --port 8000
```

Add `--production` to disable auto-reload when deploying to servers.

### 6. Run tests

```bash
pytest
```

## Dashboard overview

When you browse to the control centre you will find on-screen instructions for every
task. Highlights include:

- **Basemap toggle** – draw survey areas using OpenStreetMap or Google Maps (if enabled).
- **Survey day explorer** – browse historical captures, load their GeoJSON overlays,
  and open exported point clouds.
- **Change detection** – compare two survey dates and focus on specific assets to see
  volumetric deltas.
- **Inline annotations** – capture operator notes per asset so investigations are
  auditable.

Debug panels on each card show raw JSON responses to simplify troubleshooting in the
field.

## Directory structure

```
nerfdrone/
  classification/    # Asset classification logic
  drone_control/     # Provider abstractions and implementations
  export/            # Point cloud exporting utilities
  ingestion/         # Video ingestion pipeline
  interface/         # FastAPI app, templates, and static files
  nerf_pipeline/     # NeRF orchestration
  route_planning/    # Mission route planning
  utils/             # Shared helpers (e.g. plugin loader)
main_control_centre.py   # CLI entry point for launching the web UI
scripts/                 # Environment setup helpers
tests/                   # Pytest suite
```

## Setup scripts

- `scripts/setup_environment.sh` – validates prerequisites, bootstraps a virtual environment, and installs dependencies on Linux/macOS/Raspberry Pi.
- `scripts/setup_environment.ps1` – Windows PowerShell equivalent with identical safety checks.

Example usage:

```bash
# Linux / macOS / Raspberry Pi
EXTRAS=nerf bash scripts/setup_environment.sh --python python3.11 --venv .venv
```

```powershell
# Windows PowerShell
pwsh -File scripts/setup_environment.ps1 -Python python.exe -VenvDir .venv -Extras nerf
```

Both scripts ensure Python ≥ 3.10 is available, reuse existing virtual environments when present,
and print clear activation plus launch instructions.

## Security and logging

- Sensitive configuration is sourced from environment variables, namespaced with
  `NERFDRONE_`.
- Logging is enabled across modules and prints timestamps, log levels, and module names
  to aid debugging.

## Future enhancements

- Live telemetry integration for popular drone SDKs (DJI, Parrot, Skydio, etc.).
- Advanced route planning using terrain data and no-fly zone constraints.
- Automated segmentation and instance identification on NeRF outputs.
- Rich asset management workflow with auditing and approvals.

## Contributing

Pull requests are welcome. Please run tests (`pytest`) and adhere to the documented
module structure and inline documentation style.
