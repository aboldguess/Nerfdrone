<#
Mini README: Helper script to configure Nerfdrone on Windows.
Creates a virtual environment, installs dependencies, and prints guidance.
#>

Param(
    [string]$Python = "python",
    [string]$VenvDir = ".venv"
)

Write-Host "[Nerfdrone] Using Python interpreter: $Python"
& $Python -m venv $VenvDir

$activateScript = Join-Path $VenvDir "Scripts/Activate.ps1"
Write-Host "[Nerfdrone] Activating virtual environment"
& $activateScript

pip install --upgrade pip
pip install -e .

Write-Host "[Nerfdrone] Setup complete. Activate with: . $activateScript"
Write-Host "[Nerfdrone] Launch UI: python main_control_centre.py --port 8000"
