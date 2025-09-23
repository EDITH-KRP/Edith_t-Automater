# EDITH-Automater PowerShell Launcher
# This script launches the GUI interface for the forensics automation tool

param(
    [string]$CaseId = "",
    [string]$EvidencePath = ""
)

Write-Host "EDITH-Automater - Digital Forensics Automation Tool" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python not found. Please install Python 3.7 or later." -ForegroundColor Red
    exit 1
}

# Set working directory to script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "Working directory: $ScriptDir" -ForegroundColor Yellow

# Launch the orchestrator
if ($CaseId -and $EvidencePath) {
    Write-Host "Launching with Case ID: $CaseId and Evidence: $EvidencePath" -ForegroundColor Green
    python orchestrator.py --case $CaseId --evidence $EvidencePath
} else {
    Write-Host "Interactive mode - GUI will launch shortly..." -ForegroundColor Yellow
    # TODO: Launch GUI interface
    python orchestrator.py --help
}

Write-Host "Launcher completed." -ForegroundColor Cyan