@echo off
setlocal EnableDelayedExpansion
REM ==============================
REM Run Edith_t Automater Project
REM ==============================

title Edith_t Automater
cls

REM Change directory to your project folder
cd /d "D:\B.Tech Engineering\1. Internship\Zetpeak\Automate\test\Edith_t-Automater"

REM Use full Python path (change version if needed)
set PYTHON_PATH="C:\Users\Anirudh\AppData\Local\Programs\Python\Python312\python.exe"

REM Check if Python exists
if not exist %PYTHON_PATH% (
    echo ERROR: Python not found at %PYTHON_PATH%
    echo Please update the path in this .bat file.
    pause
    exit /b
)

:MENU
cls
echo.
echo =====================================
echo   EDITH-t Automater - Main Menu
echo =====================================
echo.
echo Please select a workflow:
echo.
echo 1. Evidence Collection Only (Interactive)
echo 2. Evidence Collection Only (Automated)
echo 3. List All Cases
echo 4. Forensic Analysis Only (Interactive)
echo 5. Forensic Analysis Only (Automated)
echo 6. Sequential Workflow (Interactive)
echo 7. Sequential Workflow (Automated)
echo 8. Simultaneous Workflow (Automated)
echo 9. Report Generation Only
echo 10. Run All Workflows Sequentially
echo 0. Show Help / Exit
echo.
echo =====================================
echo.

set /p choice="Enter your choice (0-10): "

if "%choice%"=="1" goto EVIDENCE_INTERACTIVE
if "%choice%"=="2" goto EVIDENCE_AUTO
if "%choice%"=="3" goto LIST_CASES
if "%choice%"=="4" goto FORENSIC_INTERACTIVE
if "%choice%"=="5" goto FORENSIC_AUTO
if "%choice%"=="6" goto SEQUENTIAL_INTERACTIVE
if "%choice%"=="7" goto SEQUENTIAL_AUTO
if "%choice%"=="8" goto SIMULTANEOUS
if "%choice%"=="9" goto REPORT_ONLY
if "%choice%"=="10" goto RUN_ALL
if "%choice%"=="0" goto HELP
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:EVIDENCE_INTERACTIVE
cls
echo.
echo =====================================
echo Running Evidence Collection (Interactive)...
echo =====================================
echo.
%PYTHON_PATH% orchestrator.py evidence-only
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:EVIDENCE_AUTO
cls
echo.
echo =====================================
echo Running Evidence Collection (Automated)...
echo =====================================
echo.
%PYTHON_PATH% orchestrator.py evidence-auto
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:LIST_CASES
cls
echo.
echo =====================================
echo Listing All Cases...
echo =====================================
echo.
%PYTHON_PATH% orchestrator.py list-cases
echo.
echo =====================================
echo.
pause
goto MENU

:FORENSIC_INTERACTIVE
cls
echo.
echo =====================================
echo Forensic Analysis (Interactive)
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
echo.
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py forensic-only --evidence "%evidence_path%"
) else (
    %PYTHON_PATH% orchestrator.py forensic-only --evidence "%evidence_path%" --memory "%memory_path%"
)
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:FORENSIC_AUTO
cls
echo.
echo =====================================
echo Forensic Analysis (Automated)
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
set /p case_id="Enter case ID (or press Enter to create new): "
echo.
if "%memory_path%"=="" (
    if "%case_id%"=="" (
        %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%"
    ) else (
        %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%" --case "%case_id%"
    )
) else (
    if "%case_id%"=="" (
        %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%" --memory "%memory_path%"
    ) else (
        %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%" --memory "%memory_path%" --case "%case_id%"
    )
)
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:SEQUENTIAL_INTERACTIVE
cls
echo.
echo =====================================
echo Sequential Workflow (Interactive)
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
echo.
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py sequential --evidence "%evidence_path%"
) else (
    %PYTHON_PATH% orchestrator.py sequential --evidence "%evidence_path%" --memory "%memory_path%"
)
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:SEQUENTIAL_AUTO
cls
echo.
echo =====================================
echo Sequential Workflow (Automated)
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
echo.
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py sequential-auto --evidence "%evidence_path%"
) else (
    %PYTHON_PATH% orchestrator.py sequential-auto --evidence "%evidence_path%" --memory "%memory_path%"
)
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:SIMULTANEOUS
cls
echo.
echo =====================================
echo Simultaneous Workflow (Automated)
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
echo.
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py simultaneous --evidence "%evidence_path%"
) else (
    %PYTHON_PATH% orchestrator.py simultaneous --evidence "%evidence_path%" --memory "%memory_path%"
)
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:REPORT_ONLY
cls
echo.
echo =====================================
echo Report Generation Only
echo =====================================
echo.
set /p case_id="Enter case ID: "
echo.
%PYTHON_PATH% orchestrator.py report-only --case "%case_id%"
echo.
echo =====================================
echo Process completed!
echo =====================================
pause
goto MENU

:RUN_ALL
cls
echo.
echo =====================================
echo Running Full Workflow Suite
_echo All workflows will run sequentially using the same inputs_
echo =====================================
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (press Enter to skip): "
set /p case_id="Enter case ID (press Enter to create new where applicable): "
echo.

REM Evidence workflows
REM Run interactive evidence collection so the operator can enter case details
%PYTHON_PATH% orchestrator.py evidence-only
echo.
REM During automated evidence collection we reuse the existing case
set "auto_case_id="
set "auto_case_dir="
for /f "tokens=1* delims=" %%A in ('%PYTHON_PATH% orchestrator.py evidence-auto') do (
    echo %%A
    if not defined auto_case_id (
        echo %%A| findstr /i "Case ID" >nul
        if not errorlevel 1 (
            for /f "tokens=3 delims=: " %%B in ("%%A") do (
                set "auto_case_id=%%B"
                set "auto_case_dir=%~dp0Results\%%B"
            )
        )
    )
)
if not defined auto_case_id (
    echo WARNING: Automated evidence collection did not return a case ID.
)

REM Case listing
%PYTHON_PATH% orchestrator.py list-cases

REM Forensic workflows
set "active_case_id=%auto_case_id%"
set "active_case_dir=%auto_case_dir%"
if "%active_case_id%"=="" (
    REM If user provided case ID earlier, reuse it
    if not "%case_id%"=="" (
        set "active_case_id=%case_id%"
        set "active_case_dir=%~dp0Results\%case_id%"
    )
)
if "%active_case_id%"=="" (
    REM Fall back to the latest case created in Results directory
    for /f "delims=" %%A in ('dir /ad /b /o-d "%~dp0Results" 2^>nul') do (
        if not defined active_case_id (
            set "active_case_id=%%A"
            set "active_case_dir=%~dp0Results\%%A"
        )
    )
)
if "%active_case_id%"=="" (
    echo No existing case found. Creating a fresh case for forensic workflows...
    call :CREATE_CASE_FROM_AUTOMATED "active_case_id" "active_case_dir"
)
if "%active_case_id%"=="" (
    echo ERROR: Unable to determine a case ID for forensic workflows.
    goto RUN_ALL_END
)

echo Using case !active_case_id! located at !active_case_dir! for remaining workflows.
if not exist "!active_case_dir!" (
    echo Case directory not found locally. Creating structure at !active_case_dir! ...
    call :ENSURE_CASE_DIRECTORY "!active_case_dir!"
)

if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py forensic-only --evidence "%evidence_path%"
    %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%"
) else (
    %PYTHON_PATH% orchestrator.py forensic-only --evidence "%evidence_path%" --memory "%memory_path%"
    %PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%" --memory "%memory_path%"
)

REM Sequential workflows
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py sequential --evidence "%evidence_path%" --case "!active_case_id!"
    %PYTHON_PATH% orchestrator.py sequential-auto --evidence "%evidence_path%" --case "!active_case_id!"
) else (
    %PYTHON_PATH% orchestrator.py sequential --evidence "%evidence_path%" --memory "%memory_path%" --case "!active_case_id!"
    %PYTHON_PATH% orchestrator.py sequential-auto --evidence "%evidence_path%" --memory "%memory_path%" --case "!active_case_id!"
)

REM Simultaneous workflow
if "%memory_path%"=="" (
    %PYTHON_PATH% orchestrator.py simultaneous --evidence "%evidence_path%" --case "!active_case_id!"
) else (
    %PYTHON_PATH% orchestrator.py simultaneous --evidence "%evidence_path%" --memory "%memory_path%" --case "!active_case_id!"
)

REM Report generation
if "%active_case_id%"=="" (
    echo Skipping report generation: no case ID available.
) else (
    %PYTHON_PATH% orchestrator.py report-only --case "!active_case_id!"
)

echo.
echo =====================================
echo All workflows completed!
echo =====================================
pause
goto MENU

REM Helper to create a case by calling orchestrator and parsing output
:CREATE_CASE_FROM_AUTOMATED
set "RET_CASE_ID="
set "RET_CASE_DIR="
for /f "tokens=1* delims=" %%A in ('%PYTHON_PATH% orchestrator.py forensic-auto --evidence "%evidence_path%" --memory "%memory_path%"') do (
    echo %%A
    if not defined RET_CASE_ID (
        echo %%A| findstr /i "Case ID" >nul
        if not errorlevel 1 (
            for /f "tokens=3 delims=: " %%B in ("%%A") do (
                set "RET_CASE_ID=%%B"
                set "RET_CASE_DIR=%~dp0Results\%%B"
            )
        )
    )
)
for %%P in (%1) do set "%%~P=%RET_CASE_ID%"
for %%P in (%2) do set "%%~P=%RET_CASE_DIR%"
exit /b

REM Helper to ensure case directory exists locally
:ENSURE_CASE_DIRECTORY
set "TARGET_DIR=%~1"
if "%TARGET_DIR%"=="" exit /b
if exist "%TARGET_DIR%" exit /b

echo Creating case directory structure at %TARGET_DIR%
for %%D in (Questions HashDeep_output Autopsy_output Volatility_output ExifTool_output BulkExtractor_output Final_Reports) do (
    mkdir "%TARGET_DIR%\%%D" 2>nul
)
exit /b

:HELP
cls
echo.
%PYTHON_PATH% orchestrator.py help
echo.
echo =====================================
echo Press any key to exit...
echo =====================================
pause
exit /b
