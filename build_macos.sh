#!/bin/bash
# ============================================================================
# EDITH-Automater macOS Build Script
# Build: EDITH-Automater-MacOS.dmg (Signed app bundle)
# Run: bash build_macos.sh
# ============================================================================

set -e

echo ""
echo "============================================================================"
echo "EDITH-Automater macOS Build Script"
echo "============================================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org or Homebrew"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[OK] $PYTHON_VERSION found"

# Check PyInstaller
python3 -m pip show pyinstaller &> /dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "[INSTALLING] PyInstaller..."
    python3 -m pip install pyinstaller --quiet
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
    echo "[OK] PyInstaller installed"
fi

PYINSTALLER_VERSION=$(python3 -m pip show pyinstaller | grep Version)
echo "[OK] $PYINSTALLER_VERSION"

# Check requirements
echo ""
echo "[CHECKING] Required Python packages..."
pip3 install -r tools/requirements.txt --quiet

# Get macOS info
MACOS_VERSION=$(sw_vers -productVersion)
echo "[OK] macOS $MACOS_VERSION"

# Create build directories
rm -rf build dist
mkdir -p build
mkdir -p dist

echo ""
echo "============================================================================"
echo "Building macOS Application Bundle..."
echo "============================================================================"
echo ""

# Run PyInstaller with macOS-specific settings
echo "[BUILDING] EDITH-Automater.app"
echo "This may take 3-5 minutes..."
echo ""

python3 << 'EOF'
import PyInstaller.__main__
import sys

PyInstaller.__main__.run([
    'orchestrator/launcher.py',
    '--onefile',
    '--name=EDITH-Automater',
    '--distpath=dist',
    '--workpath=build',
    '--windowed',  # No console window on macOS
    '--osx-bundle-identifier=com.edith.forensics.automater',
    '--add-data=reports/Reports html:reports/Reports html',
    '--add-data=case_templates:case_templates',
    '--add-data=config.json:.',
    '--add-data=README.md:.',
    '--hidden-import=autopsy',
    '--hidden-import=exiftool',
    '--hidden-import=volatility',
    '--hidden-import=volatility3',
    '--hidden-import=tools.ftk_metadata',
    '--hidden-import=tools.analysis_reporter',
    '--hidden-import=pyewf',
    '--hidden-import=pytsk3',
    '-y',
])
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: PyInstaller build failed"
    exit 1
fi

# Check if .app was created
if [ -d "dist/EDITH-Automater.app" ]; then
    
    # Get bundle size
    APP_SIZE=$(du -sh "dist/EDITH-Automater.app" | awk '{print $1}')
    
    echo ""
    echo "============================================================================"
    echo "SUCCESS - Application Bundle Created"
    echo "============================================================================"
    echo ""
    echo "Output: dist/EDITH-Automater.app"
    echo "Size: $APP_SIZE"
    echo ""
    
    # Code signing (if certificate available)
    echo "[INFO] Code signing setup..."
    
    # Optional: Sign with Apple Developer certificate
    # IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
    # codesign --deep --force --verify --verbose --sign "$IDENTITY" dist/EDITH-Automater.app
    # echo "[OK] Code signed"
    
    echo ""
    echo "[INFO] Creating DMG distribution..."
    
    # Create DMG file
    create-dmg \
        --volname "EDITH-Automater" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "EDITH-Automater.app" 150 190 \
        --hide-extension "EDITH-Automater.app" \
        --app-drop-link 450 190 \
        "dist/EDITH-Automater-MacOS.dmg" \
        "dist/EDITH-Automater.app"
    
    if [ $? -eq 0 ]; then
        DMG_SIZE=$(du -sh "dist/EDITH-Automater-MacOS.dmg" | awk '{print $1}')
        echo "[OK] DMG created: dist/EDITH-Automater-MacOS.dmg ($DMG_SIZE)"
        echo ""
        echo "To install:"
        echo "  1. Double-click EDITH-Automater-MacOS.dmg"
        echo "  2. Drag EDITH-Automater.app to Applications folder"
        echo "  3. Launch from Applications"
        echo ""
    else
        echo "[OPTIONAL] DMG creation skipped (create-dmg not installed)"
        echo "Install with: brew install create-dmg"
        echo ""
        echo "To use app bundle directly:"
        echo "  open dist/EDITH-Automater.app"
    fi
    
else
    echo ""
    echo "ERROR: Application bundle was not created"
    exit 1
fi

echo ""
echo "Build complete!"
