@echo off
REM ==============================
REM Build EDITH-Automater EXE
REM ==============================

title Building EDITH-Automater EXE
cls

echo.
echo =====================================
echo   EDITH-Automater EXE Builder
echo =====================================
echo.

REM Change to project directory
cd /d "D:\B.Tech Engineering\1. Internship\Zetpeak\Automate\test\Edith_t-Automater"

REM Set Python path
set PYTHON_PATH="C:\Users\Anirudh\AppData\Local\Programs\Python\Python312\python.exe"

REM Check if Python exists
if not exist %PYTHON_PATH% (
    echo ERROR: Python not found at %PYTHON_PATH%
    echo Please update the path in this .bat file.
    pause
    exit /b
)

echo Step 1: Running pre-build tests...
echo -------------------------------------
%PYTHON_PATH% test_exe_build.py
echo.

echo.
echo Do you want to continue with the build? (Y/N)
set /p continue="Enter choice: "

if /i not "%continue%"=="Y" (
    echo Build cancelled.
    pause
    exit /b
)

echo.
echo Step 2: Installing/Updating PyInstaller...
echo -------------------------------------
%PYTHON_PATH% -m pip install --upgrade pyinstaller
echo.

echo.
echo Step 3: Cleaning previous build...
echo -------------------------------------
if exist "dist" (
    rmdir /s /q "dist"
    echo Removed old dist folder
)
if exist "build" (
    rmdir /s /q "build"
    echo Removed old build folder
)
echo.

echo.
echo Step 4: Building EXE with PyInstaller...
echo -------------------------------------
%PYTHON_PATH% -m PyInstaller build_exe.spec --clean
echo.

echo.
echo =====================================
echo Build Process Complete!
echo =====================================
echo.

if exist "dist\EDITH-Automater\EDITH-Automater.exe" (
    echo SUCCESS: EXE created successfully!
    echo Location: dist\EDITH-Automater\
    echo.
    echo You can now:
    echo 1. Test the EXE by running: dist\EDITH-Automater\EDITH-Automater.exe
    echo 2. Copy the entire "EDITH-Automater" folder to distribute
    echo.
    echo Opening dist folder...
    explorer "dist\EDITH-Automater"
) else (
    echo ERROR: EXE was not created!
    echo Check the output above for errors.
    echo.
    echo Common issues:
    echo - Missing Python modules (run: pip install -r tools\requirements.txt)
    echo - Antivirus blocking PyInstaller
    echo - Insufficient disk space
)

echo.
pause