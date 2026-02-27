# EDITH-Automater Build Guide
## Creating Portable Executables for Windows, macOS, and Linux

---

## Overview

This guide explains how to build EDITH-Automater into standalone, portable executables for all major operating systems. Each resulting executable is self-contained and requires no installation or dependencies - users simply download and run.

**Final Products:**
- `EDITH-Automater-Windows.exe` (450+ MB)
- `EDITH-Automater-MacOS.dmg` (400+ MB)
- `EDITH-Automater-Linux.AppImage` (380+ MB)

---

## Prerequisites

### All Platforms

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org)
   - Verify: `python --version`

2. **PyInstaller**
   - Install: `pip install pyinstaller`
   - Verify: `pyinstaller --version`

3. **Required Python Packages**
   - Install: `pip install -r tools/requirements.txt`

### Windows Specific

- Windows 7 or later
- Administrator privileges for build
- Optionally: UPX for executable compression

### macOS Specific

- macOS 10.13 or later
- Xcode Command Line Tools: `xcode-select --install`
- Optional: `create-dmg` for DMG packaging
  ```bash
  brew install create-dmg
  ```
- Optional: Apple Developer certificate for code signing

### Linux Specific

- Any major Linux distribution (Ubuntu, Fedora, Arch, etc.)
- Build dependencies: `gcc`, `libffi-dev`, `libssl-dev`
  ```bash
  # Ubuntu/Debian
  sudo apt-get install build-essential libffi-dev libssl-dev python3-dev
  
  # Fedora/RHEL
  sudo dnf groupinstall "Development Tools"
  sudo dnf install libffi-devel openssl-devel python3-devel
  
  # Arch
  sudo pacman -S base-devel
  ```
- Optional: `appimagetool` for AppImage creation
  ```bash
  sudo apt install appimage-builder
  ```

---

## Building on Windows

### Quick Build (Recommended)

Simply run the build batch file:

```bash
build_windows.bat
```

This will:
1. Verify Python and PyInstaller installation
2. Install required packages
3. Build the executable
4. Place result in `dist\EDITH-Automater.exe`

### Manual Build

If the batch file doesn't work, build manually:

```bash
# Install dependencies
pip install -r tools/requirements.txt

# Build with PyInstaller
pyinstaller EDITH-Automater.spec -y

# Output will be in: dist\EDITH-Automater.exe
```

### Testing the Build

After building:

```bash
# Run directly
dist\EDITH-Automater.exe

# Or from command line
cd dist
EDITH-Automater.exe
```

### Troubleshooting Windows Build

**Issue: "PyInstaller not found"**
```bash
pip install pyinstaller --upgrade
```

**Issue: "ModuleNotFoundError"**
- Ensure all required packages are installed
- Check `tools/requirements.txt`
- Run: `pip install -r tools/requirements.txt --upgrade`

**Issue: "Access Denied" during build**
- Close any antivirus software temporarily
- Run Command Prompt as Administrator
- Try build again

**Issue: Executable very large (>1GB)**
- This is normal for first build
- Includes Python runtime (~100MB) + all dependencies
- Subsequent builds may use cached files

---

## Building on macOS

### Quick Build (Recommended)

Make the script executable and run:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

This will:
1. Verify Python and PyInstaller
2. Create application bundle
3. Code sign the app (if certificate available)
4. Create DMG distribution file

### Manual Build

If the script doesn't work:

```bash
# Install dependencies
pip3 install -r tools/requirements.txt

# Build with PyInstaller
python3 -m PyInstaller EDITH-Automater.spec -y

# Output will be the .app bundle in: dist/EDITH-Automater.app
```

### Testing the Build

```bash
# Run directly
open dist/EDITH-Automater.app

# Or from terminal
dist/EDITH-Automater.app/Contents/MacOS/EDITH-Automater
```

### Code Signing (Professional)

For distribution outside your organization:

```bash
# View available certificates
security find-identity -v -p codesigning

# Sign the app (replace IDENTITY with your certificate)
IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
codesign --deep --force --verify --verbose --sign "$IDENTITY" dist/EDITH-Automater.app
```

### Creating DMG for Distribution

```bash
brew install create-dmg

create-dmg \
    --volname "EDITH-Automater" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "EDITH-Automater.app" 150 190 \
    --hide-extension "EDITH-Automater.app" \
    --app-drop-link 450 190 \
    "dist/EDITH-Automater.dmg" \
    "dist/EDITH-Automater.app"
```

### Troubleshooting macOS Build

**Issue: "command not found: python3"**
```bash
brew install python3
```

**Issue: "code signature invalid" on launch**
- Remove signature: `codesign --remove-signature dist/EDITH-Automater.app`
- Or code sign properly with your certificate

**Issue: "App is damaged"**
- Occurs with unsigned apps on newer macOS
- Code sign the app before distribution
- Or use: `xattr -d com.apple.quarantine EDITH-Automater.app`

---

## Building on Linux

### Quick Build (Recommended)

Make the script executable and run:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

This will:
1. Verify Python and dependencies
2. Build the binary
3. Create AppImage (if appimagetool available)
4. Output in `dist/EDITH-Automater` or `dist/EDITH-Automater-Linux.AppImage`

### Manual Build

```bash
# Install dependencies (Ubuntu/Debian example)
sudo apt-get install python3 python3-pip python3-dev build-essential

# Install Python packages
pip3 install -r tools/requirements.txt

# Build
python3 -m PyInstaller EDITH-Automater.spec -y

# Output: dist/EDITH-Automater (binary)
```

### Testing the Build

```bash
# Make executable
chmod +x dist/EDITH-Automater

# Run
./dist/EDITH-Automater
```

### Creating AppImage for Distribution

```bash
# Install appimagetool
sudo apt install appimage-builder

# Run build script (includes AppImage creation)
./build_linux.sh

# Or manually create AppImage
appimagetool dist/EDITH-Automater dist/EDITH-Automater-Linux.AppImage
```

### Distributing AppImage

AppImage can be distributed as single file:

```bash
# Users simply need to:
chmod +x EDITH-Automater-Linux.AppImage
./EDITH-Automater-Linux.AppImage
```

### Troubleshooting Linux Build

**Issue: "python3: command not found"**
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# Fedora/RHEL
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

**Issue: "ModuleNotFoundError: pyewf" or similar**
```bash
pip3 install -r tools/requirements.txt --upgrade
```

**Issue: "appimagetool: command not found"**
```bash
# Install appimagetool
sudo apt install appimage-builder

# Or build binary without AppImage (still portable)
```

---

## Build Configuration

### Customizing the Build

Edit `EDITH-Automater.spec` to:

1. **Change output name:**
   ```python
   name='EDITH-Automater-v1.0.0',  # Change here
   ```

2. **Add additional data files:**
   ```python
   datas=[
       ('path/to/data', 'destination'),
       # Add your files here
   ]
   ```

3. **Include additional modules:**
   ```python
   hiddenimports=[
       'your_module',
       'another_module',
   ]
   ```

4. **Add application icons:**
   - Windows: Add `icon='path/to/icon.ico'`
   - macOS: Add `icon='path/to/icon.icns'`
   - Linux: Include PNG file for AppImage

### Reducing File Size

1. **Enable UPX compression** (Windows):
   ```python
   upx=True,
   ```

2. **Exclude unnecessary modules:**
   ```python
   excludedimports=['your_unused_module'],
   ```

3. **Strip debug symbols** (Linux/macOS):
   ```python
   strip=True,
   ```

---

## Distribution

### Recommended Structure

```
EDITH-Automater-Release-v1.0.0/
├── EDITH-Automater-Windows.exe
├── EDITH-Automater-MacOS.dmg
├── EDITH-Automater-Linux.AppImage
├── README.txt
├── INSTALL.txt
├── LICENSE
└── RELEASE_NOTES.txt
```

### GitHub Releases

1. Create a release on GitHub
2. Upload all three executables
3. Add release notes with features/fixes

### Website Distribution

```
https://your-domain.com/downloads/
├── EDITH-Automater-Windows.exe (450 MB)
├── EDITH-Automater-MacOS.dmg (400 MB)
├── EDITH-Automater-Linux.AppImage (380 MB)
└── SHA256-checksums.txt
```

### USB Distribution

Create bootable/portable USB:

```
USB Drive (32GB+)/
├── EDITH-Automater-Windows.exe
├── EDITH-Automater-MacOS.dmg
├── EDITH-Automater-Linux.AppImage
├── README.txt (instructions)
└── cases/ (empty folder for investigations)
```

Users insert USB, select their OS, run executable.

---

## Verification

### Checksums for Integrity

Generate checksums for distribution:

```bash
# Windows
certutil -hashfile EDITH-Automater.exe SHA256

# macOS/Linux
sha256sum EDITH-Automater-MacOS.dmg
sha256sum EDITH-Automater-Linux.AppImage
```

### Antivirus False Positives

PyInstaller executables may trigger antivirus warnings because:
- They bundle a Python interpreter
- They extract code at runtime
- Antivirus software doesn't recognize them

Solutions:
1. **Code signing** with trusted certificate
2. **Submit to antivirus vendors** for whitelisting
3. **Provide source code** for verification
4. **Publish checksums** for user verification

### First-Run Performance

First run may be slow (5-10 seconds) as:
- Python runtime initializes
- Libraries load into memory
- Temp files extract

Subsequent runs are faster as caches warm up.

---

## Automation with CI/CD

### GitHub Actions Example

Create `.github/workflows/build.yml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: bash build_windows.bat
      - uses: actions/upload-artifact@v2
        with:
          name: windows-executable
          path: dist/EDITH-Automater.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: bash build_macos.sh
      - uses: actions/upload-artifact@v2
        with:
          name: macos-executable
          path: dist/EDITH-Automater.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: bash build_linux.sh
      - uses: actions/upload-artifact@v2
        with:
          name: linux-executable
          path: dist/EDITH-Automater-Linux.AppImage
```

---

## Troubleshooting

### Common Issues

| Error | Solution |
|-------|----------|
| "PyInstaller not found" | `pip install pyinstaller` |
| "Module not found" | `pip install -r tools/requirements.txt` |
| "Permission denied" | Run with `sudo` or admin rights |
| "File in use" | Close all Python processes, antivirus |
| "Out of disk space" | Need ~2GB for build process |
| "Timeout" | Increase build timeout (large files) |

### Getting Help

1. Check the build script output carefully
2. Run manual PyInstaller command with verbose flag
3. Check `build/EDITH-Automater.build.log`
4. Consult PyInstaller documentation: https://pyinstaller.org

---

## Advanced Topics

### Adding Auto-Updates

Implement update checking in launcher.py:

```python
def check_for_updates():
    """Check if newer version available"""
    current_version = "1.0.0"
    latest_url = "https://api.github.com/repos/your/repo/releases/latest"
    # Fetch and compare versions
    # Prompt user to download if update available
```

### Collecting Forensic Data

Add forensic collection before packaging:

```python
# Build forensic data collection
forensic_hashes = {
    "executable": calculate_hash("dist/EDITH-Automater.exe"),
    "build_date": datetime.now().isoformat(),
    "python_version": sys.version,
}
```

### Version Management

Update version in multiple places:

1. `orchestrator/orchestrator.py`
2. `EDITH-Automater.spec`
3. Build script output messages
4. `config.json`

---

## Summary

| Step | Windows | macOS | Linux |
|------|---------|-------|-------|
| 1. Install Python | ✅ | ✅ | ✅ |
| 2. Install PyInstaller | ✅ | ✅ | ✅ |
| 3. Install dependencies | ✅ | ✅ | ✅ |
| 4. Run build script | `build_windows.bat` | `./build_macos.sh` | `./build_linux.sh` |
| 5. Output | `dist/EDITH-Automater.exe` | `dist/EDITH-Automater.dmg` | `dist/EDITH-Automater-Linux.AppImage` |
| 6. Test | Run `.exe` | Open `.app` | Run binary |
| 7. Distribute | Upload to website | Upload to website | Upload to website |

---

**Last Updated:** February 7, 2026  
**EDITH-Automater Build System v1.0**
