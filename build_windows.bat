@echo off
REM ============================================================================
REM EDITH-Automater Windows Build Script
REM Build: EDITH-Automater-Windows.exe (Single portable executable)
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo EDITH-Automater Windows Build Script
echo ============================================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION% found

REM Check PyInstaller
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo [INSTALLING] PyInstaller...
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
    echo [OK] PyInstaller installed
)

for /f "tokens=*" %%i in ('python -m pip show pyinstaller ^| find "Version"') do set PYINSTALLER_VERSION=%%i
echo [OK] %PYINSTALLER_VERSION%

REM Check requirements
echo.
echo [CHECKING] Required Python packages...
python -m pip install -r tools/requirements.txt --quiet

REM Create build directory
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
mkdir build
mkdir dist

echo.
echo ============================================================================
echo Building Windows Executable...
echo ============================================================================
echo.

REM Run PyInstaller
echo [BUILDING] EDITH-Automater-Windows.exe
echo This may take 3-5 minutes...
echo.

pyinstaller EDITH-Automater.spec --distpath dist --workpath build -y

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)

REM Verify output
if exist "dist\EDITH-Automater.exe" (
    for /f %%A in ('wmic datafile where name="dist\\EDITH-Automater.exe" get size /value') do (
        for /f "tokens=2 delims==" %%B in ("%%A") do set SIZE=%%B
    )
    
    if defined SIZE (
        set /a SIZE_MB=SIZE/1048576
        echo.
        echo ============================================================================
        echo SUCCESS - Executable Created
        echo ============================================================================
        echo.
        echo Output: dist\EDITH-Automater.exe
        echo Size: !SIZE_MB! MB
        echo.
        echo To run, double-click: dist\EDITH-Automater.exe
        echo.
        
        REM Test run (optional)
        echo [INFO] Testing executable...
        timeout /t 2 /nobreak
        start "" "dist\EDITH-Automater.exe"
    )
) else (
    echo.
    echo ERROR: Executable was not created
    pause
    exit /b 1
)

echo.
echo Build complete!
pause
