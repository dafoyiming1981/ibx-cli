# install_windows.ps1 — Install ibx-cli via venv on Windows
# Usage: .\scripts\install_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== ibx-cli Windows Installer ===" -ForegroundColor Cyan

# Check Python 3.12+
Write-Host "`n[1/4] Checking Python version..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Host "ERROR: Python not found. Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
    $pythonCmd = "py"
    $pythonVersion = & $pythonCmd -3 --version 2>&1
} else {
    $pythonCmd = "python"
    $pythonVersion = & $pythonCmd --version 2>&1
}

Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Extract version number
$versionMatch = [regex]::Match($pythonVersion, "Python (\d+)\.(\d+)")
if (-not $versionMatch.Success) {
    Write-Host "ERROR: Could not parse Python version." -ForegroundColor Red
    exit 1
}
$major = [int]$versionMatch.Groups[1].Value
$minor = [int]$versionMatch.Groups[2].Value
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
    Write-Host "ERROR: Python 3.9+ required. Found $pythonVersion" -ForegroundColor Red
    exit 1
}

# Determine project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Check if wheel exists in dist/
$wheelPath = Get-ChildItem -Path (Join-Path $projectRoot "dist") -Filter "ibx_cli-*.whl" -ErrorAction SilentlyContinue | Select-Object -Last 1

# Create venv
$envPath = Join-Path $env:USERPROFILE "ibx-env"
Write-Host "`n[2/4] Creating virtual environment at $envPath..." -ForegroundColor Yellow
& $pythonCmd -m venv $envPath

# Activate venv
$activateScript = Join-Path $envPath "Scripts\Activate.ps1"
. $activateScript

# Install ibx-cli
if ($wheelPath) {
    Write-Host "`n[3/4] Installing ibx-cli from wheel: $($wheelPath.Name)..." -ForegroundColor Yellow
    pip install $wheelPath.FullName
} else {
    Write-Host "`n[3/4] No wheel found, installing from source..." -ForegroundColor Yellow
    pip install -e $projectRoot
}

# Verify installation
Write-Host "`n[4/4] Verifying installation..." -ForegroundColor Yellow
$ibxVersion = ibx --version 2>&1
Write-Host "Installed: $ibxVersion" -ForegroundColor Green

# Config directory
$configDir = Join-Path $env:USERPROFILE ".infoblox"
$configFilePath = Join-Path $configDir "config"
if (-not (Test-Path $configFilePath)) {
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir | Out-Null
    }
    Write-Host "`nConfig directory: $configDir" -ForegroundColor Yellow
    Write-Host "Create your config file at: $configFilePath" -ForegroundColor Yellow
}

Write-Host "`n=== Installation Complete ===" -ForegroundColor Green
Write-Host "Activate venv before using: . $activateScript" -ForegroundColor Cyan
Write-Host "Then run: ibx --help" -ForegroundColor Cyan
