<#
Mini README: Windows setup helper for the Nerfdrone platform.
Validates prerequisites, provisions a virtual environment, installs dependencies
or extras, and prints clear follow-up instructions for operators.

Usage:
  pwsh -File scripts/setup_environment.ps1 [-Python python.exe] [-VenvDir .venv] [-Extras nerf]

Environment variables PYTHON, VENV_DIR, and EXTRAS mirror the parameters.
#>

[CmdletBinding()]
Param(
    [string]$Python = $env:PYTHON,
    [string]$VenvDir = $env:VENV_DIR,
    [string[]]$Extras = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Log {
    param(
        [Parameter(Mandatory)][ValidateSet('INFO', 'WARN', 'ERROR')][string]$Level,
        [Parameter(Mandatory)][string]$Message
    )
    Write-Host "[Nerfdrone][$Level] $Message"
}

function Ensure-Command {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$FriendlyName
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$FriendlyName '$Name' is not available. Install it or provide an alternative via -Python."
    }
}

try {
    if (-not $Python) { $Python = 'python' }
    if (-not $VenvDir) { $VenvDir = '.venv' }
    if (-not $Extras -and $env:EXTRAS) { $Extras = $env:EXTRAS -split ',' }

    $scriptName = Split-Path -Leaf $PSCommandPath

    if (-not (Test-Path -Path 'pyproject.toml')) {
        throw "pyproject.toml not found. Run $scriptName from the Nerfdrone repository root."
    }

    Ensure-Command -Name $Python -FriendlyName 'Python interpreter'

    Write-Log -Level INFO -Message "Using Python interpreter: $Python"

    & $Python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
    if ($LASTEXITCODE -ne 0) {
        throw 'Nerfdrone requires Python 3.10 or newer.'
    }

    $pythonVersion = & $Python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    Write-Log -Level INFO -Message "Detected Python version: $pythonVersion"

    if (Test-Path -Path $VenvDir) {
        Write-Log -Level INFO -Message "Virtual environment directory $VenvDir already exists; reusing it."
    } else {
        Write-Log -Level INFO -Message "Creating virtual environment at $VenvDir"
        & $Python -m venv $VenvDir
    }

    $venvPython = Join-Path $VenvDir 'Scripts/python.exe'
    if (-not (Test-Path -Path $venvPython)) {
        $venvPython = Join-Path $VenvDir 'Scripts/python'
    }

    if (-not (Test-Path -Path $venvPython)) {
        throw "Virtual environment Python executable not found at $venvPython."
    }

    Write-Log -Level INFO -Message 'Upgrading pip inside the virtual environment'
    & $venvPython -m pip install --upgrade pip

    $extrasClean = @()
    foreach ($item in $Extras) {
        if ($item) { $extrasClean += $item.Trim() }
    }

    $extrasLower = @()
    foreach ($item in $extrasClean) {
        if ($item) { $extrasLower += $item.ToLowerInvariant() }
    }

    if ($extrasLower -contains 'nerf') {
        Write-Log -Level INFO -Message "Validating Open3D wheels are available for Python $pythonVersion"
        try {
            & $venvPython -m pip index versions open3d | Out-Null
        }
        catch {
            Write-Log -Level WARN -Message 'pip index query failed; upgrade pip (python -m pip install --upgrade pip) if wheel resolution fails.'
        }
    }

    $installTarget = '.'
    if ($extrasClean.Count -gt 0) {
        $extrasArgument = $extrasClean -join ','
        $installTarget = ".[$extrasArgument]"
        Write-Log -Level INFO -Message "Installing Nerfdrone with extras: $extrasArgument"
    } else {
        Write-Log -Level INFO -Message 'Installing core Nerfdrone dependencies'
    }

    & $venvPython -m pip install -e $installTarget

    $activateScript = Join-Path $VenvDir 'Scripts/Activate.ps1'
    Write-Log -Level INFO -Message "Setup complete. Activate with: . $activateScript"
    Write-Log -Level INFO -Message 'Launch UI with: python main_control_centre.py --host 0.0.0.0 --port 8000'
}
catch {
    Write-Log -Level ERROR -Message $_.Exception.Message
    exit 1
}
