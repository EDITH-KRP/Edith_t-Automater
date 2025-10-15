@echo off
setlocal EnableDelayedExpansion
REM ==============================
REM EDITH-Automater Clean Menu
REM ==============================

title EDITH-Automater
cls

REM Change directory to your project folder
cd /d "E:\Github-adhi982\Edith_t-Automater"

REM Use full Python path (change version if needed)
set PYTHON_PATH="E:\Github-adhi982\Edith_t-Automater\.venv\Scripts\python.exe"

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
echo      EDITH-Automater Main Menu      
echo =====================================
echo.
echo Main Menu - Choose Your Forensic Workflow:
echo.
echo  1. Sequential Workflow
echo     Interactive evidence collection -> Automated forensic analysis
echo.
echo  2. Case Management
echo     List, view, and manage existing cases
echo.
echo  3. Help ^& Documentation
echo     User guide and command reference
echo.
echo  4. Exit
echo     Close EDITH-Automater
echo.
echo =====================================
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto SEQUENTIAL_WORKFLOW
if "%choice%"=="2" goto CASE_MANAGEMENT
if "%choice%"=="3" goto HELP
if "%choice%"=="4" goto EXIT
echo Invalid choice. Please try again.
timeout /t 2 >nul
goto MENU

:SEQUENTIAL_WORKFLOW
cls
echo.
echo =====================================
echo   Sequential Workflow - EDITH-Automater
echo =====================================
echo.
echo This workflow will:
echo  1. Interactive evidence collection (forms and prompts)
echo  2. Automated forensic analysis (all tools)
echo.
echo Forensic tools that will run automatically:
echo  - HashDeep (file integrity verification)
echo  - Autopsy (disk image analysis)
echo  - Volatility (memory analysis, if memory file provided)
echo  - ExifTool (metadata extraction)
echo  - Bulk Extractor (pattern extraction)
echo  - Final report generation
echo.
set /p evidence_path="Enter path to evidence file (.E01/.dd/.raw): "
set /p memory_path="Enter path to memory dump (or press Enter to skip): "
echo.
echo Starting Sequential Workflow...
echo =====================================
if "%memory_path%"=="" (
    powershell.exe -ExecutionPolicy Bypass -File "orchestrator\launcher.ps1" -Command sequential -EvidencePath "%evidence_path%"
) else (
    powershell.exe -ExecutionPolicy Bypass -File "orchestrator\launcher.ps1" -Command sequential -EvidencePath "%evidence_path%" -MemoryPath "%memory_path%"
)
echo.
echo =====================================
echo Sequential Workflow Completed!
echo =====================================
pause
goto MENU

:CASE_MANAGEMENT
cls
echo.
echo =====================================
echo     Case Management - EDITH-Automater
echo =====================================
echo.
echo Available case management options:
echo.
echo  1. List all cases
echo  2. View case details
echo  3. Return to main menu
echo.
set /p case_choice="Enter your choice (1-3): "

if "%case_choice%"=="1" (
    echo.
    echo Listing all forensic cases...
    echo =====================================
    powershell.exe -ExecutionPolicy Bypass -File "orchestrator\launcher.ps1" -Command list-cases
    echo.
    pause
    goto CASE_MANAGEMENT
)
if "%case_choice%"=="2" (
    echo.
    echo Case details can be viewed by browsing the Results folder
    echo Location: E:\Github-adhi982\Edith_t-Automater\Results\
    echo.
    echo Opening Results folder...
    explorer "E:\Github-adhi982\Edith_t-Automater\Results"
    echo.
    pause
    goto CASE_MANAGEMENT
)
if "%case_choice%"=="3" goto MENU

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto CASE_MANAGEMENT

:HELP
cls
echo.
echo =====================================
echo    Help ^& Documentation - EDITH-Automater
echo =====================================
echo.
echo EDITH-Automater Digital Forensics Tool
echo Version: 2.0
echo.
echo WORKFLOW DESCRIPTIONS:
echo.
echo 1. SEQUENTIAL WORKFLOW
echo    - Interactive evidence collection with forms
echo    - Automated analysis using all forensic tools:
echo      * HashDeep (file integrity)
echo      * Autopsy (disk analysis)
echo      * Volatility (memory analysis)
echo      * ExifTool (metadata extraction)
echo      * Bulk Extractor (pattern extraction)
echo      * Automated report generation
echo.
echo 2. CASE MANAGEMENT
echo    - View all created forensic cases
echo    - Browse case details and results
echo    - Access result files and reports
echo.
echo SUPPORTED FILE FORMATS:
echo    - Disk Images: .E01, .Ex01, .L01, .dd, .raw
echo    - Memory Dumps: .mem, .vmem, .dmp
echo.
echo RESULTS LOCATION:
echo    - All results saved in: Results\CASE_YYYYMMDD_HHMMSS\
echo    - Each case contains subdirectories for each tool
echo    - HTML reports generated automatically
echo.
echo SYSTEM REQUIREMENTS:
echo    - Windows 10/11
echo    - Python 3.8+ (Anaconda recommended)
echo    - 8GB+ RAM for large evidence files
echo    - 50GB+ free disk space
echo.
echo For technical support, refer to README.md
echo =====================================
echo.
pause
goto MENU

:EXIT
cls
echo.
echo =====================================
echo     Thank you for using EDITH-Automater
echo =====================================
echo.
echo All forensic analysis results are saved in:
echo E:\Github-adhi982\Edith_t-Automater\Results\
echo.
echo Goodbye!
echo.
timeout /t 3 >nul
exit