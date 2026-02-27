#!/bin/bash
# ============================================================================
# EDITH-Automater Linux Build Script
# Build: EDITH-Automater-Linux.AppImage (Portable executable)
# Run: bash build_linux.sh
# ============================================================================

set -e

echo ""
echo "============================================================================"
echo "EDITH-Automater Linux Build Script"
echo "============================================================================"
echo ""

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    LINUX_DIST=$ID
    LINUX_VERSION=$VERSION_ID
    echo "[OK] Linux Distribution: $LINUX_DIST $LINUX_VERSION"
else
    LINUX_DIST="unknown"
    echo "[WARNING] Could not detect Linux distribution"
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-dev"
    echo "  Fedora/RHEL:   sudo dnf install python3 python3-pip python3-devel"
    echo "  Arch:          sudo pacman -S python python-pip"
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

# Check appimagetool availability
APPIMAGE_TOOL_NEEDED=false
if ! command -v appimagetool &> /dev/null; then
    echo "[WARNING] appimagetool not found - will create binary instead of AppImage"
    echo "Install with: sudo apt-get install appimage-builder"
    APPIMAGE_TOOL_NEEDED=true
fi

# Check requirements
echo ""
echo "[CHECKING] Required Python packages..."
pip3 install -r tools/requirements.txt --quiet

# Create build directories
rm -rf build dist
mkdir -p build
mkdir -p dist

echo ""
echo "============================================================================"
echo "Building Linux Binary..."
echo "============================================================================"
echo ""

# Run PyInstaller
echo "[BUILDING] EDITH-Automater (Linux binary)"
echo "This may take 3-5 minutes..."
echo ""

python3 << 'EOF'
import PyInstaller.__main__

PyInstaller.__main__.run([
    'orchestrator/launcher.py',
    '--onefile',
    '--name=EDITH-Automater',
    '--distpath=dist',
    '--workpath=build',
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

# Check if binary was created
if [ -f "dist/EDITH-Automater" ]; then
    
    # Make executable
    chmod +x dist/EDITH-Automater
    
    # Get binary size
    BINARY_SIZE=$(du -h "dist/EDITH-Automater" | awk '{print $1}')
    
    echo ""
    echo "============================================================================"
    echo "SUCCESS - Binary Created"
    echo "============================================================================"
    echo ""
    echo "Output: dist/EDITH-Automater"
    echo "Size: $BINARY_SIZE"
    echo ""
    
    # Create AppImage if appimagetool is available
    if [ "$APPIMAGE_TOOL_NEEDED" = false ] && command -v appimagetool &> /dev/null; then
        echo "[INFO] Creating AppImage..."
        
        # Create AppDir structure
        mkdir -p AppDir/usr/bin
        mkdir -p AppDir/usr/share/applications
        mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
        
        # Copy binary
        cp dist/EDITH-Automater AppDir/usr/bin/
        
        # Create desktop entry
        cat > AppDir/usr/share/applications/EDITH-Automater.desktop << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=EDITH-Automater
Comment=Digital Forensic Analysis System
Exec=EDITH-Automater
Icon=EDITH-Automater
Terminal=true
Categories=Utility;Forensics;Science;
DESKTOP
        
        # Copy/create icon if available
        if [ -f "icon.png" ]; then
            cp icon.png AppDir/usr/share/icons/hicolor/256x256/apps/EDITH-Automater.png
        fi
        
        # Create AppImage
        appimagetool AppDir dist/EDITH-Automater-Linux.AppImage
        
        if [ $? -eq 0 ]; then
            chmod +x dist/EDITH-Automater-Linux.AppImage
            APPIMAGE_SIZE=$(du -h "dist/EDITH-Automater-Linux.AppImage" | awk '{print $1}')
            echo "[OK] AppImage created: dist/EDITH-Automater-Linux.AppImage ($APPIMAGE_SIZE)"
            echo ""
            echo "To run:"
            echo "  ./dist/EDITH-Automater-Linux.AppImage"
        fi
        
        # Cleanup AppDir
        rm -rf AppDir
    else
        echo ""
        echo "To use the binary directly:"
        echo "  ./dist/EDITH-Automater"
        echo ""
        echo "To create AppImage:"
        echo "  Install appimagetool, then run:"
        echo "  bash -c 'appimagetool ./dist \"./dist/EDITH-Automater-Linux.AppImage\"'"
    fi
    
else
    echo ""
    echo "ERROR: Binary was not created"
    exit 1
fi

echo ""
echo "Build complete!"
