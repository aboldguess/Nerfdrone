#!/usr/bin/env bash
# Mini README: Cross-platform Nerfdrone bootstrapper for Linux/macOS/Raspberry Pi.
# Validates prerequisites, creates a virtual environment, installs dependencies,
# and prints follow-up instructions. Supports overriding interpreter, venv path,
# and optional extras via flags or environment variables.

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"

# shellcheck disable=SC2034  # Documented mini README already describes structure.
read -r -d '' MINI_USAGE <<'USAGE' || true
Usage: scripts/setup_environment.sh [--python PATH] [--venv DIR] [--extras LIST]

Options:
  --python PATH   Python interpreter to use (default: $PYTHON or python3)
  --venv DIR      Virtual environment directory (default: $VENV_DIR or .venv)
  --extras LIST   Optional extras to install, e.g. "nerf" or "dev,nerf"
  -h, --help      Show this help message and exit

Environment variables:
  PYTHON, VENV_DIR, EXTRAS mirror their respective flags.
USAGE

log() {
  # Structured logger to keep messaging consistent and parseable.
  local level=$1 message=$2
  printf '[Nerfdrone][%s] %s\n' "$level" "$message"
}

fatal() {
  log "ERROR" "$1"
  exit 1
}

usage() {
  printf '%s\n' "$MINI_USAGE"
}

# Defaults honour environment variables so CI or power users can override easily.
python_cmd="${PYTHON:-python3}"
venv_dir="${VENV_DIR:-.venv}"
extras_raw="${EXTRAS:-}"

# Parse minimal flag set for clarity and to avoid unnecessary dependencies.
while (($#)); do
  case "$1" in
    --python)
      [[ $# -ge 2 ]] || fatal "--python flag requires an argument"
      python_cmd=$2
      shift 2
      ;;
    --venv)
      [[ $# -ge 2 ]] || fatal "--venv flag requires an argument"
      venv_dir=$2
      shift 2
      ;;
    --extras)
      [[ $# -ge 2 ]] || fatal "--extras flag requires an argument"
      extras_raw=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fatal "Unknown argument: $1. Run --help for usage."
      ;;
  esac
done

# Compact helper ensuring required tools are present before performing work.
require_command() {
  local command=$1 friendly=$2
  if ! command -v "$command" >/dev/null 2>&1; then
    fatal "$friendly '$command' is not available. Install it or provide an alternative via --python."
  fi
}

require_command "$python_cmd" "Python interpreter"

# Ensure we are executed from the repository root to guarantee correct relative paths.
if [[ ! -f "pyproject.toml" ]]; then
  fatal "pyproject.toml not found. Run $SCRIPT_NAME from the Nerfdrone repository root."
fi

log "INFO" "Using Python interpreter: $python_cmd"

# Guard against unsupported Python versions early to save time.
if ! "$python_cmd" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
  fatal "Nerfdrone requires Python 3.10 or newer."
fi

python_version="$($python_cmd -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
log "INFO" "Detected Python version: $python_version"

# Create or reuse the requested virtual environment.
if [[ -d "$venv_dir" ]]; then
  log "INFO" "Virtual environment directory $venv_dir already exists; reusing it."
else
  log "INFO" "Creating virtual environment at $venv_dir"
  "$python_cmd" -m venv "$venv_dir"
fi

venv_python="$venv_dir/bin/python"
if [[ ! -x "$venv_python" ]]; then
  fatal "Expected virtual environment Python at $venv_python but it was not found."
fi

log "INFO" "Upgrading pip inside the virtual environment"
"$venv_python" -m pip install --upgrade pip

# Normalise extras to remove whitespace so pip receives a clean target string.
extras_clean=${extras_raw// /}
extras_lower=$(printf '%s' "$extras_clean" | tr '[:upper:]' '[:lower:]')
if [[ ",$extras_lower," == *",nerf,"* ]]; then
  log "INFO" "Validating Open3D wheels are available for Python $python_version"
  "$venv_python" -m pip index versions open3d >/dev/null 2>&1 || log "WARN" "pip index query failed; ensure pip>=25.2 so Open3D 0.19 wheels are detected."
fi
install_target="."
if [[ -n "$extras_clean" ]]; then
  install_target=".[${extras_clean}]"
  log "INFO" "Installing Nerfdrone with extras: $extras_clean"
else
  log "INFO" "Installing core Nerfdrone dependencies"
fi

"$venv_python" -m pip install -e "$install_target"

log "INFO" "Setup complete. Activate with: source ${venv_dir}/bin/activate"
log "INFO" "Launch UI with: python main_control_centre.py --host 0.0.0.0 --port 8000"
