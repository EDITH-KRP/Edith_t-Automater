@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  EDITH-Automater  --  One-click forensic pipeline launcher
::  Works from the project folder OR from a USB drive.
::
::  Usage:  run_pipeline.bat
::      or: run_pipeline.bat "path\to\evidence.E01"
::      or: run_pipeline.bat "path\to\evidence.E01" "path\to\memory.vmem"
:: ============================================================

:: -- Resolve project root (wherever this bat lives) --------
set "PROJ=%~dp0"
:: Remove trailing backslash for clean concatenation
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"

:: -- Default evidence: same drive/folder as this bat -------
set "DEFAULT_EVIDENCE=%PROJ%\evidence\2011-10-19-Sample.E01"

:: Use first argument if provided, otherwise default
if "%~1"=="" (
    set "EVIDENCE=%DEFAULT_EVIDENCE%"
) else (
    set "EVIDENCE=%~1"
)

set "MEMORY="
if not "%~2"=="" set "MEMORY=%~2"

:: ── Banner ────────────────────────────────────────────────
echo.
echo  ===================================================
echo   EDITH-Automater  ^|  Digital Forensics Pipeline
echo  ===================================================
echo   Evidence : %EVIDENCE%
if not "!MEMORY!"=="" echo   Memory   : !MEMORY!
echo  ---------------------------------------------------
echo.

:: ── Validate evidence file ────────────────────────────────
if not exist "%EVIDENCE%" (
    echo  [ERROR] Evidence file not found:
    echo          %EVIDENCE%
    echo.
    echo  Usage: run_pipeline.bat "C:\path\to\evidence.E01"
    echo.
    pause
    exit /b 1
)

:: ── Locate Python ─────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found on PATH.
    echo  Install Python 3.8+ and try again.
    pause
    exit /b 1
)

:: ── Change to project root ────────────────────────────────
cd /d "%~dp0"

:: ── Run ───────────────────────────────────────────────────
echo  [*] Starting pipeline...  (this may take a few minutes)
echo.

if "!MEMORY!"=="" (
    python orchestrator\orchestrator.py sequential-auto --evidence %EVIDENCE%
) else (
    python orchestrator\orchestrator.py sequential-auto --evidence %EVIDENCE% --memory !MEMORY!
)

set "RC=%errorlevel%"

:: ── Final summary ─────────────────────────────────────────
echo.
echo  ===================================================
if %RC%==0 (
    echo   [+] Pipeline complete  ^(exit 0^)
) else (
    echo   [!] Pipeline finished with warnings  ^(exit %RC%^)
)
echo  ---------------------------------------------------

:: Find the most recent case directory
for /f "delims=" %%D in ('dir /b /o-d /ad "Results\CASE_*" 2^>nul') do (
    set "LATEST=Results\%%D"
    goto :found_case
)
goto :no_case

:found_case
echo   Results   : %CD%\!LATEST!
echo   Dashboard : %CD%\!LATEST!\case_dashboard.html
echo   Timeline  : %CD%\!LATEST!\Timeline\investigation_timeline.html
echo   PDFs      : %CD%\!LATEST!\Reports pdf\
echo   Hashes    : %CD%\!LATEST!\HashDeep_output\verification\integrity_verification.txt
echo  ===================================================
echo.
goto :end

:no_case
echo   Results   : no case directory found
echo  ===================================================
echo.

:end
endlocal
