@echo off
cd /d "%~dp0"

echo.
echo  EDITH-Automater -- USB Portable Builder
echo  -----------------------------------------
echo  Copies project + evidence to your USB drive.
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found on PATH.
    pause
    exit /b 1
)

set "DEST=%~1"

if "%DEST%"=="" (
    echo  Enter USB drive letter - example: D
    set /p DEST=  Drive: 
)

python create_usb_portable.py "%DEST%"

echo.
pause
