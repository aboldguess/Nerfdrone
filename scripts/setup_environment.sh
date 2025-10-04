#!/usr/bin/env bash
# Mini README: Helper script to set up Nerfdrone on Linux/macOS/Raspberry Pi.
# Creates a virtual environment, installs dependencies, and prints usage tips.

set -euo pipefail

python_version="${PYTHON:-python3}"
venv_dir="${VENV_DIR:-.venv}"

echo "[Nerfdrone] Using Python interpreter: ${python_version}"
"${python_version}" -m venv "${venv_dir}"
# shellcheck source=/dev/null
echo "[Nerfdrone] Activating virtual environment"
# shellcheck disable=SC1090
source "${venv_dir}/bin/activate"

pip install --upgrade pip
pip install -e .

echo "[Nerfdrone] Setup complete. Activate with: source ${venv_dir}/bin/activate"
echo "[Nerfdrone] Launch UI: python main_control_centre.py --port 8000"
