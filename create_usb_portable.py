#!/usr/bin/env python3
"""
EDITH-Automater USB Portable Creator
Creates a completely portable USB version with single EXE launcher
"""
import os
import sys
import shutil
import subprocess
import fnmatch
from pathlib import Path

def install_portable_python(usb_target):
    """Download and install portable Python to USB drive"""
    print("[INFO] Installing portable Python...")
    
    python_dir = usb_target / "python-portable"
    python_dir.mkdir(exist_ok=True)
    
    try:
        # Use system Python to create a portable environment
        current_python = sys.executable
        
        # Get Python installation directory
        python_root = Path(current_python).parent
        
        # For Anaconda/Conda, the structure is different
        python_install_root = Path(sys.prefix)  # Use sys.prefix instead of guessing
        
        print(f"  Python executable: {current_python}")
        print(f"  Python root: {python_root}")
        print(f"  Python install root: {python_install_root}")
        
        # Copy Python executable
        python_exe = python_dir / "python.exe"
        shutil.copy2(current_python, python_exe)
        
        # Copy python DLL from same directory as executable
        for dll in python_root.glob("python*.dll"):
            try:
                shutil.copy2(dll, python_dir / dll.name)
                print(f"  Copied DLL: {dll.name}")
            except Exception as e:
                print(f"  Failed to copy DLL {dll.name}: {e}")
        
        # Copy essential DLLs from install root
        for dll in python_install_root.glob("*.dll"):
            try:
                shutil.copy2(dll, python_dir / dll.name)
                print(f"  Copied root DLL: {dll.name}")
            except Exception as e:
                pass  # Many DLLs may be in use
        
        # Copy Lib directory (essential Python libraries)
        lib_source = python_install_root / "Lib"
        print(f"  Looking for Lib at: {lib_source}")
        if lib_source.exists():
            lib_target = python_dir / "Lib"
            if not lib_target.exists():
                print("  Copying Python libraries...")
                # Copy essential libraries but exclude large unnecessary packages
                def ignore_large_packages(dir, files):
                    ignore_patterns = [
                        '__pycache__', '*.pyc', '*.pyo',
                        'test', 'tests', 'unittest', 
                        'idlelib', 'tkinter',
                        'turtledemo', 'pydoc_data',
                        'lib2to3', 'distutils'
                    ]
                    ignored = []
                    for pattern in ignore_patterns:
                        if '*' in pattern:
                            ignored.extend(fnmatch.filter(files, pattern))
                        elif pattern in files:
                            ignored.append(pattern)
                    return ignored
                
                try:
                    shutil.copytree(lib_source, lib_target, ignore=ignore_large_packages)
                    print(f"  Successfully copied Lib directory")
                except Exception as e:
                    print(f"  Error copying Lib: {e}")
                    # Fallback: copy critical modules manually
                    lib_target.mkdir(exist_ok=True)
            
            # Ensure critical modules are present
            critical_modules = ['encodings', 'codecs', 'collections', 'io', 'os', 're', 'sys', 'json', 'subprocess', 'pathlib']
            print("  Ensuring critical modules are present...")
            for module in critical_modules:
                module_path = lib_source / f"{module}.py"
                if module_path.exists():
                    target_path = lib_target / f"{module}.py"
                    if not target_path.exists():
                        try:
                            shutil.copy2(module_path, target_path)
                            print(f"    Copied {module}.py")
                        except:
                            pass
                        
                # Also check for module directories
                module_dir = lib_source / module
                if module_dir.exists() and module_dir.is_dir():
                    target_dir = lib_target / module
                    if not target_dir.exists():
                        try:
                            shutil.copytree(module_dir, target_dir)
                            print(f"    Copied {module}/ directory")
                        except:
                            pass
        else:
            print(f"  WARNING: Lib directory not found at {lib_source}")
        
        # Copy DLLs directory if it exists
        dlls_source = python_install_root / "DLLs"
        if dlls_source.exists():
            dlls_target = python_dir / "DLLs"
            if not dlls_target.exists():
                print("  Copying Python DLLs...")
                shutil.copytree(dlls_source, dlls_target)
        
        # Copy site-packages (important for installed packages like weasyprint)
        site_packages_source = python_install_root / "Lib" / "site-packages"
        if site_packages_source.exists():
            site_packages_target = python_dir / "Lib" / "site-packages" 
            if not site_packages_target.exists():
                print("  Copying site-packages...")
                # Copy essential packages needed for PDF generation (focus on simpler alternatives)
                essential_packages = [
                    'reportlab', 'pillow', 'PIL'  # Lightweight PDF libraries that work better in portable mode
                ]
                
                site_packages_target.mkdir(parents=True, exist_ok=True)
                
                # Copy essential packages if they exist
                for package in essential_packages:
                    package_source = site_packages_source / package
                    if package_source.exists():
                        try:
                            package_target = site_packages_target / package
                            if package_source.is_dir():
                                shutil.copytree(package_source, package_target, ignore=shutil.ignore_patterns('__pycache__'))
                                print(f"    Copied package: {package}")
                            else:
                                shutil.copy2(package_source, package_target)
                                print(f"    Copied file: {package}")
                        except Exception as e:
                            print(f"    Could not copy {package}: {e}")
                
                # Copy .pth files and other important site-packages files
                for item in site_packages_source.glob("*.pth"):
                    try:
                        shutil.copy2(item, site_packages_target / item.name)
                    except:
                        pass
        
        # Copy compiled extension modules (.pyd files)
        for pyd_file in python_install_root.rglob("*.pyd"):
            try:
                # Copy .pyd files to the main directory for easier import
                target_pyd = python_dir / pyd_file.name
                if not target_pyd.exists():
                    shutil.copy2(pyd_file, target_pyd)
                    print(f"    Copied extension: {pyd_file.name}")
            except Exception as e:
                pass  # Some files may be in use
        
        # Create python.cfg for portable mode
        python_cfg = python_dir / "python._pth"
        with open(python_cfg, 'w') as f:
            f.write("Lib\n")
            f.write("DLLs\n")
            f.write("Scripts\n")
            f.write(".\n")
            f.write("import site\n")
        
        print("✓ Portable Python installed")
        return True
        
    except Exception as e:
        print(f"[WARNING] Could not install portable Python: {e}")
        print("[INFO] USB will use system Python if available")
        return False

def modify_launcher_for_usb(usb_target):
    """Modify the launcher.ps1 to use USB portable Python"""
    launcher_path = usb_target / "orchestrator" / "launcher.ps1"
    
    if not launcher_path.exists():
        print("[WARNING] launcher.ps1 not found, skipping modification")
        return
    
    try:
        # Read the original launcher
        with open(launcher_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the Test-PythonAvailable function to prioritize USB Python
        usb_python_function = '''
# Check if Python is available - USB Portable Version
function Test-PythonAvailable {
    # First priority: Check for USB portable Python
    $USBRoot = if ($env:USB_ROOT) { $env:USB_ROOT } else { Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition) }
    $PortablePython = Join-Path $USBRoot "python-portable\\python.exe"
    
    if (Test-Path $PortablePython) {
        try {
            $output = & $PortablePython --version 2>&1
            if ($output -and $output -match "Python") {
                Write-Info "USB Portable Python detected: $output"
                return $PortablePython
            }
        } catch { }
    }
    
    # Fallback: Try system Python
    try {
        $output = Invoke-Expression "python --version 2>&1"
        if ($output -and $output -match "Python") {
            Write-Info "System Python detected: $output"
            return "python"
        }
    } catch { }
    
    # Last resort: Try python3
    try {
        $output = Invoke-Expression "python3 --version 2>&1"
        if ($output -and $output -match "Python") {
            Write-Info "Python3 detected: $output"
            return "python3"
        }
    } catch { }
    
    Write-Error "No Python installation found!"
    return $null
}
'''
        
        # Find and replace the Test-PythonAvailable function
        import re
        
        # More specific pattern to match the entire function
        start_pattern = r'function Test-PythonAvailable \{'
        start_match = re.search(start_pattern, content)
        
        if start_match:
            # Find the end of the function by counting braces
            start_pos = start_match.start()
            pos = start_match.end()
            brace_count = 1
            
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            # Replace the entire function
            if brace_count == 0:
                content = content[:start_pos] + usb_python_function + content[pos:]
        
        # Also ensure the launcher uses our environment variable if set
        content = content.replace(
            '$PythonCmd = Test-PythonAvailable',
            '''$PythonCmd = if ($env:PYTHON_CMD) { 
    Write-Host "[INFO] Using USB-provided Python: $env:PYTHON_CMD"
    $env:PYTHON_CMD 
} else { 
    Test-PythonAvailable 
}'''
        )
        
        # Write back the modified launcher
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ Modified launcher.ps1 for USB use")
        
    except Exception as e:
        print(f"[WARNING] Could not modify launcher.ps1: {e}")

def create_usb_launcher_ps1(usb_target):
    """Create a portable PowerShell launcher that handles Python paths correctly"""
    launcher_content = '''# EDITH-Automater USB Portable PowerShell Launcher
# This script sets up the environment to work from USB drive

param(
    [string]$Command = "",
    [string]$EvidencePath = "",
    [string]$MemoryPath = "",
    [string]$Case = "",
    [switch]$Help = $false,
    [switch]$Interactive = $false
)

# Get USB root directory (where this script is located)
$USBRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$OrchestratorDir = Join-Path $USBRoot "orchestrator"
$OriginalLauncher = Join-Path $OrchestratorDir "launcher.ps1"

# Set environment variable for USB root
$env:USB_ROOT = $USBRoot

Write-Host "[INFO] USB Portable Launcher"
Write-Host "[INFO] USB Root: $USBRoot"

# Check if original launcher exists
if (-not (Test-Path $OriginalLauncher)) {
    Write-Error "Original launcher not found at: $OriginalLauncher"
    exit 1
}

# Set the PROJECT_ROOT environment variable to USB location
$env:PROJECT_ROOT = $USBRoot

# Try to find Python - prioritize bundled portable Python
$PythonCmd = $null

# First priority: Check for bundled portable Python
$PortablePython = Join-Path $USBRoot "python-portable\\python.exe"
if (Test-Path $PortablePython) {
    try {
        $output = & $PortablePython --version 2>$null
        if ($output -and $output -match "Python") {
            $PythonCmd = $PortablePython
            Write-Host "[INFO] Using bundled portable Python: $output"
            Write-Host "[INFO] Python path: $PortablePython"
        }
    } catch { }
}

# Second priority: Try system Python only if portable Python not found
if (-not $PythonCmd) {
    try {
        $output = python --version 2>$null
        if ($output -and $output -match "Python") {
            $PythonCmd = "python"
            Write-Host "[INFO] Using system Python: $output"
        }
    } catch { }
}

# Third priority: Try python3
if (-not $PythonCmd) {
    try {
        $output = python3 --version 2>$null
        if ($output -and $output -match "Python") {
            $PythonCmd = "python3"
            Write-Host "[INFO] Using system Python3: $output"
        }
    } catch { }
}

if (-not $PythonCmd) {
    Write-Error "No Python installation found! Cannot run forensic tools."
    Write-Host "[ERROR] Neither portable Python nor system Python available"
    exit 1
}

# Set environment variable for Python command
$env:PYTHON_CMD = $PythonCmd

# Change to USB root directory for relative paths
Set-Location $USBRoot

# Call original launcher with all parameters
Write-Host "[INFO] Calling original launcher..."

if ($Command -and $EvidencePath) {
    if ($MemoryPath) {
        & $OriginalLauncher -Command $Command -EvidencePath $EvidencePath -MemoryPath $MemoryPath
    } else {
        & $OriginalLauncher -Command $Command -EvidencePath $EvidencePath
    }
} elseif ($Help) {
    & $OriginalLauncher -Help
} elseif ($Interactive) {
    & $OriginalLauncher -Interactive
} else {
    & $OriginalLauncher
}
'''
    
    usb_launcher_path = usb_target / "usb_launcher.ps1"
    with open(usb_launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)

def create_usb_portable():
    print("=" * 60)
    print("    EDITH-Automater USB Portable Creator")
    print("=" * 60)
    
    project_dir = Path("E:/Github-adhi982/Edith_t-Automater")
    usb_target = Path("F:/EDITH-USB-Portable")  # Change this to your USB drive
    
    print(f"Source: {project_dir}")
    print(f"Target: {usb_target}")
    
    # Create USB directory structure
    if usb_target.exists():
        print("Removing existing USB directory...")
        def handle_remove_readonly(func, path, exc):
            import os
            os.chmod(path, 0o777)
            func(path)
        shutil.rmtree(usb_target, onerror=handle_remove_readonly)
    
    usb_target.mkdir(parents=True)
    
    # Copy essential files
    print("Copying project files...")
    
    # Copy tools (all forensic tools)
    shutil.copytree(project_dir / "tools", usb_target / "tools")
    print("✓ Copied tools")
    
    # Copy orchestrator
    shutil.copytree(project_dir / "orchestrator", usb_target / "orchestrator")
    
    # Install portable Python
    install_portable_python(usb_target)
    
    # Modify the copied launcher.ps1 to use USB Python
    modify_launcher_for_usb(usb_target)
    
    # Create portable PowerShell launcher that handles Python paths
    create_usb_launcher_ps1(usb_target)
    
    print("✓ Copied orchestrator")
    print("✓ Created portable PowerShell launcher")
    
    # Copy case templates and reports
    shutil.copytree(project_dir / "case_templates", usb_target / "case_templates")
    shutil.copytree(project_dir / "reports", usb_target / "reports")
    print("✓ Copied templates and reports")
    
    # Create Results directory
    (usb_target / "Results").mkdir(exist_ok=True)
    print("✓ Created Results directory")
    
    # Create portable launcher BAT file
    portable_bat = usb_target / "EDITH-Portable.bat"
    bat_content = create_portable_bat_content()
    
    with open(portable_bat, 'w') as f:
        f.write(bat_content)
    print("✓ Created portable BAT launcher")
    
    # Create portable Python CLI
    portable_cli = usb_target / "edith_usb_cli.py"
    cli_content = create_portable_cli_content()
    
    with open(portable_cli, 'w', encoding='utf-8') as f:
        f.write(cli_content)
    print("✓ Created portable Python CLI")
    
    # Create PyInstaller spec for USB EXE
    spec_content = create_usb_exe_spec()
    spec_file = usb_target / "edith_usb.spec"
    
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    print("✓ Created PyInstaller spec")
    
    # Build the portable EXE
    print("\nBuilding portable EXE...")
    os.chdir(usb_target)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", 
            "--clean", "edith_usb.spec"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ USB EXE built successfully!")
            
            # Move EXE to root
            exe_file = usb_target / "dist" / "EDITH-USB.exe"
            if exe_file.exists():
                shutil.move(exe_file, usb_target / "EDITH-USB.exe")
                print("✓ EXE moved to USB root")
            
            # Clean up build files
            shutil.rmtree(usb_target / "build", ignore_errors=True)
            shutil.rmtree(usb_target / "dist", ignore_errors=True)
            (usb_target / "edith_usb.spec").unlink(missing_ok=True)
            print("✓ Cleaned up build files")
            
        else:
            print("❌ Build failed!")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Build error: {e}")
    
    # Create README for USB
    readme_content = create_usb_readme()
    with open(usb_target / "README.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ Created USB README")
    
    print("\n" + "=" * 60)
    print("    USB PORTABLE CREATION COMPLETED!")
    print("=" * 60)
    print(f"USB Location: {usb_target}")
    print("\nUsage Options:")
    print("1. Double-click: EDITH-USB.exe (Single EXE launcher)")
    print("2. Double-click: EDITH-Portable.bat (BAT launcher)")
    print("3. Works on any Windows PC without installation!")

def create_portable_bat_content():
    return '''@echo off
setlocal EnableDelayedExpansion
title EDITH-Automater Portable USB Edition
cls

REM ==============================
REM EDITH-Automater USB Portable
REM ==============================

echo ========================================
echo    EDITH-Automater Portable Edition
echo    USB Drive - No Installation Required
echo ========================================
echo.

REM Get USB drive path automatically
set USB_ROOT=%~dp0
cd /d "%USB_ROOT%"

REM Check if this is running from USB/removable drive
echo Initializing portable environment...
echo USB Location: %USB_ROOT%

REM Try to find Python (system or portable)
set PYTHON_CMD=python
where python >nul 2>&1
if errorlevel 1 (
    echo Python not found in system PATH
    echo Checking for portable Python...
    if exist "%USB_ROOT%python-portable\\python.exe" (
        set PYTHON_CMD="%USB_ROOT%python-portable\\python.exe"
        echo [OK] Using portable Python
    ) else (
        echo [WARNING] Python not found. Some features may be limited.
        echo Will attempt to use system PowerShell only.
    )
) else (
    echo [OK] Using system Python
)

echo [OK] Environment ready
echo.

:MENU
cls
echo.
echo =====================================
echo   EDITH-Automater Portable USB Menu
echo =====================================
echo.
echo Main Menu - Choose Your Forensic Workflow:
echo.
echo  1. Sequential Workflow
echo     Interactive evidence collection -^> Automated forensic analysis
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

REM Use USB-relative paths
if "%memory_path%"=="" (
    powershell.exe -ExecutionPolicy Bypass -File "%USB_ROOT%orchestrator\\launcher.ps1" -Command sequential -EvidencePath "%evidence_path%"
) else (
    powershell.exe -ExecutionPolicy Bypass -File "%USB_ROOT%orchestrator\\launcher.ps1" -Command sequential -EvidencePath "%evidence_path%" -MemoryPath "%memory_path%"
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
    powershell.exe -ExecutionPolicy Bypass -File "%USB_ROOT%orchestrator\\launcher.ps1" -Command list-cases
    echo.
    pause
    goto CASE_MANAGEMENT
)
if "%case_choice%"=="2" (
    echo.
    echo Case details can be viewed by browsing the Results folder
    echo Location: %USB_ROOT%Results\\
    echo.
    echo Opening Results folder...
    explorer "%USB_ROOT%Results"
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
echo Version: 2.0 Portable USB Edition
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
echo PORTABLE FEATURES:
echo    - Runs from USB drive
echo    - No installation required
echo    - Works on any Windows 10/11 PC
echo    - All tools included
echo.
echo RESULTS LOCATION:
echo    - All results saved in: %USB_ROOT%Results\\
echo    - Each case contains subdirectories for each tool
echo    - HTML reports generated automatically
echo.
echo For technical support, visit:
echo https://github.com/adhi982/Edith_t-Automater
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
echo %USB_ROOT%Results\\
echo.
echo This portable version can be used on any Windows PC!
echo.
echo Goodbye!
echo.
timeout /t 3 >nul
exit
'''

def create_portable_cli_content():
    return '''#!/usr/bin/env python3
"""
EDITH-Automater USB Portable CLI
Self-contained forensic analysis tool for USB drives
"""
import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime

def get_usb_root():
    """Get the USB root directory"""
    if getattr(sys, 'frozen', False):
        # Running as EXE
        return Path(sys.executable).parent
    else:
        # Running as Python script
        return Path(__file__).parent

def main():
    usb_root = get_usb_root()
    os.chdir(usb_root)
    
    print("=" * 60)
    print("    EDITH-Automater USB Portable")
    print("=" * 60)
    print(f"USB Location: {usb_root}")
    print("Initializing portable environment...")
    
    # Check if tools exist
    tools_dir = usb_root / "tools"
    if tools_dir.exists():
        print("[OK] Forensic tools found")
    else:
        print("[WARNING] Tools directory not found")
    
    # Check PowerShell
    try:
        subprocess.run(["powershell", "-Command", "Get-Host"], 
                      capture_output=True, timeout=5)
        print("[OK] PowerShell available")
    except:
        print("[WARNING] PowerShell not available")
    
    print("[OK] Portable environment ready")
    print()
    
    while True:
        print("=" * 40)
        print("  EDITH-Automater Main Menu")
        print("=" * 40)
        print()
        print("1. Sequential Workflow")
        print("2. Case Management") 
        print("3. Help & Documentation")
        print("4. Exit")
        print()
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            run_sequential_workflow(usb_root)
        elif choice == "2":
            run_case_management(usb_root)
        elif choice == "3":
            show_help()
        elif choice == "4":
            print("\\nGoodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
            input("Press Enter to continue...")

def run_sequential_workflow(usb_root):
    """Run the sequential workflow exactly like orchestrator.bat"""
    print("\\n" + "=" * 40)
    print("  Sequential Workflow")
    print("=" * 40)
    
    evidence_path = input("Enter path to evidence file (.E01/.dd/.raw): ").strip()
    memory_path = input("Enter path to memory dump (or press Enter to skip): ").strip()
    
    if not evidence_path:
        print("Error: Evidence path is required!")
        input("Press Enter to continue...")
        return
    
    if not Path(evidence_path).exists():
        print(f"Error: Evidence file not found: {evidence_path}")
        input("Press Enter to continue...")
        return
    
    print("\\nStarting Sequential Workflow...")
    print("=" * 40)
    
    # Call USB launcher PowerShell script
    try:
        usb_launcher_path = usb_root / "usb_launcher.ps1"
        
        if memory_path and memory_path.strip():
            cmd = [
                "powershell.exe", "-ExecutionPolicy", "Bypass",
                "-File", str(usb_launcher_path),
                "-Command", "sequential",
                "-EvidencePath", evidence_path,
                "-MemoryPath", memory_path
            ]
        else:
            cmd = [
                "powershell.exe", "-ExecutionPolicy", "Bypass",
                "-File", str(usb_launcher_path),
                "-Command", "sequential",
                "-EvidencePath", evidence_path
            ]
        
        print("[INFO] Calling USB PowerShell launcher...")
        result = subprocess.run(cmd, cwd=usb_root)
        
        print("\\n" + "=" * 40)
        print("Sequential Workflow Completed!")
        print("=" * 40)
        
    except Exception as e:
        print(f"\\n[ERROR] Workflow failed: {e}")
    
    input("\\nPress Enter to continue...")

def run_case_management(usb_root):
    """Case management functionality"""
    print("\\n" + "=" * 40)
    print("  Case Management")
    print("=" * 40)
    
    results_dir = usb_root / "Results"
    
    if results_dir.exists():
        cases = [d.name for d in results_dir.iterdir() if d.is_dir()]
        if cases:
            print("\\nExisting cases:")
            for case in sorted(cases):
                print(f"  - {case}")
        else:
            print("\\nNo cases found.")
    else:
        print("\\nResults directory not found.")
    
    print(f"\\nResults location: {results_dir}")
    
    choice = input("\\nOpen Results folder? (y/n): ").strip().lower()
    if choice in ['y', 'yes']:
        try:
            subprocess.run(["explorer", str(results_dir)])
        except:
            print("Could not open folder automatically.")
    
    input("Press Enter to continue...")

def show_help():
    """Show help information"""
    print("\\n" + "=" * 60)
    print("  EDITH-Automater Help & Documentation")
    print("=" * 60)
    print()
    print("PORTABLE USB EDITION")
    print("Version: 2.0")
    print()
    print("FEATURES:")
    print("- Complete digital forensics suite")
    print("- Runs from USB drive")
    print("- No installation required")
    print("- Works on any Windows PC")
    print()
    print("TOOLS INCLUDED:")
    print("- HashDeep (file integrity)")
    print("- Autopsy (disk analysis)")
    print("- Volatility (memory analysis)")
    print("- ExifTool (metadata extraction)")
    print("- Bulk Extractor (pattern extraction)")
    print()
    print("SUPPORTED FORMATS:")
    print("- Disk Images: .E01, .dd, .raw")
    print("- Memory Dumps: .mem, .vmem, .dmp")
    print()
    print("For technical support:")
    print("https://github.com/adhi982/Edith_t-Automater")
    print("=" * 60)
    
    input("Press Enter to continue...")

if __name__ == "__main__":
    main()
'''

def create_usb_exe_spec():
    return '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['edith_usb_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('orchestrator', 'orchestrator'),
        ('tools', 'tools'),
        ('case_templates', 'case_templates'),
        ('reports', 'reports'),
    ],
    hiddenimports=[
        'subprocess',
        'shutil',
        'json',
        'pathlib',
        'datetime'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EDITH-USB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
'''

def create_usb_readme():
    return '''
================================================================================
                    EDITH-Automater Portable USB Edition
================================================================================

QUICK START:
1. Plug in USB drive to any Windows PC
2. Double-click: EDITH-USB.exe
3. Select "Sequential Workflow"
4. Enter evidence file path
5. Let EDITH-Automater do the rest!

WHAT'S INCLUDED:
- Complete digital forensics suite
- All forensic tools (HashDeep, Autopsy, Volatility, ExifTool, Bulk Extractor)
- Evidence collection forms
- Automated report generation
- Case management system

USAGE OPTIONS:

Option 1: Single EXE (Recommended)
   -> Double-click: EDITH-USB.exe
   -> Everything bundled in one file
   -> Automatically extracts tools when needed

Option 2: BAT Launcher
   -> Double-click: EDITH-Portable.bat
   -> Uses system PowerShell
   -> Faster startup

SYSTEM REQUIREMENTS:
- Windows 10/11 (any PC)
- 8GB+ RAM recommended
- 20GB+ free space for large evidence files
- PowerShell (built into Windows)

RESULTS:
All analysis results are saved in the "Results" folder on this USB drive.
Each case gets its own timestamped folder with complete analysis outputs.

TROUBLESHOOTING:
- If tools don't work: Try running as Administrator
- If PowerShell blocked: Right-click -> Run as Administrator
- For large files: Ensure sufficient free space on USB drive

SUPPORT:
GitHub: https://github.com/adhi982/Edith_t-Automater
Issues: Report problems on GitHub Issues page

================================================================================
            Ready for Professional Digital Forensics Anywhere!
================================================================================
'''

if __name__ == "__main__":
    create_usb_portable()