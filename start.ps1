# Start the API locally (Windows)
# Usage: .\start.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    .\.venv\Scripts\pip install -r requirements.txt
}

Write-Host "Starting API at http://127.0.0.1:8000/docs ..."
.\.venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
