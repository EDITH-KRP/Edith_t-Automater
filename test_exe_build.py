#!/usr/bin/env python3
"""
Test script to verify all dependencies before building EXE
Run this before using PyInstaller to check for issues
"""

import sys
import os
from pathlib import Path

print("="*60)
print("EDITH-Automater EXE Build Test")
print("="*60)

# Test 1: Check Python version
print(f"\n[1] Python Version: {sys.version}")
if sys.version_info < (3, 8):
    print("    ⚠️  WARNING: Python 3.8+ recommended")
else:
    print("    ✓ Python version OK")

# Test 2: Check required modules
print("\n[2] Checking Required Modules:")
required_modules = [
    'asyncio', 'argparse', 'logging', 'subprocess', 'pathlib',
    'exifread', 'PIL', 'pandas', 'mutagen', 'hachoir', 'magic',
    'PyPDF2', 'coloredlogs', 'ujson', 'tqdm', 'psutil', 'rich',
    'capstone', 'Crypto', 'pefile', 'yara', 'jsonschema'
]

missing_modules = []
for module in required_modules:
    try:
        __import__(module)
        print(f"    ✓ {module}")
    except ImportError:
        print(f"    ✗ {module} - MISSING")
        missing_modules.append(module)

if missing_modules:
    print(f"\n    ⚠️  Missing {len(missing_modules)} modules. Install with:")
    print(f"    pip install {' '.join(missing_modules)}")
else:
    print("\n    ✓ All modules available")

# Test 3: Check project structure
print("\n[3] Checking Project Structure:")
required_paths = [
    'orchestrator.py',
    'tools/Scripts/q_script.py',
    'tools/Scripts/script_3.py',
    'tools/Scripts/report_gen.py',
    'tools/hashdeep/create_hashdeep_drive.py',
    'tools/exiftool/exiftool_auto.py',
    'tools/exiftool/bin/exiftool.exe',
    'tools/volatility/auto_vol.py',
    'tools/autopsy/auto.py',
    'tools/bulk-extractor/run_bulk_extractor.py',
]

missing_files = []
for path in required_paths:
    full_path = Path(path)
    if full_path.exists():
        print(f"    ✓ {path}")
    else:
        print(f"    ✗ {path} - MISSING")
        missing_files.append(path)

if missing_files:
    print(f"\n    ⚠️  Missing {len(missing_files)} files")
else:
    print("\n    ✓ All required files present")

# Test 4: Check if PyInstaller is installed
print("\n[4] Checking PyInstaller:")
try:
    import PyInstaller
    print(f"    ✓ PyInstaller version: {PyInstaller.__version__}")
except ImportError:
    print("    ✗ PyInstaller not installed")
    print("    Install with: pip install pyinstaller")

# Test 5: Try importing orchestrator
print("\n[5] Testing Orchestrator Import:")
try:
    # Add project root to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Try importing
    import orchestrator
    print("    ✓ Orchestrator imports successfully")
    
    # Try creating instance
    orch = orchestrator.EDITHOrchestrator()
    print("    ✓ EDITHOrchestrator instantiates successfully")
    
except Exception as e:
    print(f"    ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check Results directory
print("\n[6] Checking Results Directory:")
results_dir = Path("Results")
if results_dir.exists():
    print(f"    ✓ Results directory exists")
else:
    print(f"    ⚠️  Results directory doesn't exist (will be created)")

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

issues = []
if sys.version_info < (3, 8):
    issues.append("Python version < 3.8")
if missing_modules:
    issues.append(f"{len(missing_modules)} missing Python modules")
if missing_files:
    issues.append(f"{len(missing_files)} missing project files")

if issues:
    print("⚠️  ISSUES FOUND:")
    for issue in issues:
        print(f"   - {issue}")
    print("\nFix these issues before building EXE")
else:
    print("✓ All checks passed! Ready to build EXE")
    print("\nTo build, run:")
    print("   pyinstaller build_exe.spec")

print("="*60)
input("\nPress Enter to exit...")