# EDITH-Automater Build Quick Start

This directory contains everything needed to build portable executables for Windows, macOS, and Linux.

## 📋 Quick Start

### For Windows Users
```bash
# Simply run:
build_windows.bat

# Output: dist\EDITH-Automater.exe
```

### For macOS Users
```bash
# Make executable first
chmod +x build_macos.sh

# Then run:
./build_macos.sh

# Output: dist/EDITH-Automater.app
```

### For Linux Users
```bash
# Make executable first
chmod +x build_linux.sh

# Then run:
./build_linux.sh

# Output: dist/EDITH-Automater or dist/EDITH-Automater-Linux.AppImage
```

---

## 📁 Files Overview

### Build Scripts
- **`build_windows.bat`** - Windows build automation
- **`build_macos.sh`** - macOS build automation
- **`build_linux.sh`** - Linux build automation

### Configuration
- **`EDITH-Automater.spec`** - PyInstaller configuration
- **`BUILD_GUIDE.md`** - Complete build documentation
- **`orchestrator/launcher.py`** - Entry point for executable

### Requirements
- **`tools/requirements.txt`** - Python dependencies

---

## 🚀 Build Process Overview

```
1. Verify Python Installation
   ↓
2. Install PyInstaller & Dependencies
   ↓
3. Prepare Source Code
   ↓
4. Run PyInstaller
   ↓
5. Package Executable
   ↓
6. Create Distribution File
   ↓
7. Output: Portable Executable
```

---

## ⏱️ Build Times (Approximate)

| OS | Time | Size |
|----|------|------|
| Windows | 3-5 min | 450 MB |
| macOS | 3-5 min | 400 MB |
| Linux | 3-5 min | 380 MB |

First build takes longer. Subsequent builds are faster.

---

## ✅ Prerequisites Checklist

Before building, ensure you have:

- [ ] Python 3.8+ installed
  - Test: `python --version` (or `python3 --version` on Mac/Linux)
  
- [ ] PyInstaller installed
  - Test: `pip show pyinstaller`
  - If not: `pip install pyinstaller`

- [ ] Dependencies installed
  - Run: `pip install -r tools/requirements.txt`

- [ ] Sufficient disk space
  - Need: ~2GB for build process
  - Output: 350-450MB per OS

- [ ] Administrator/sudo access (for some operations)

---

## 🐛 Troubleshooting

### "Python not found"
```bash
# Install Python 3.8+ from python.org
# Or use package manager:
# macOS: brew install python3
# Ubuntu: sudo apt-get install python3
# Fedora: sudo dnf install python3
```

### "PyInstaller not found"
```bash
pip install pyinstaller --upgrade
```

### "Permission denied" (Mac/Linux)
```bash
chmod +x build_macos.sh
chmod +x build_linux.sh
```

### Build fails halfway
- Close antivirus software
- Free up disk space (need 2GB+)
- Run script with admin/sudo privileges
- Check BUILD_GUIDE.md for detailed troubleshooting

---

## 📦 Output Structure

After successful build:

```
dist/
├── EDITH-Automater.exe              (Windows)
├── EDITH-Automater.app/             (macOS)
│   ├── Contents/
│   │   ├── MacOS/
│   │   ├── Resources/
│   │   └── Info.plist
│   └── ...
└── EDITH-Automater                  (Linux)
    └── (executable binary)
```

---

## 🎯 Next Steps

1. **Run build for your OS** (Windows/Mac/Linux)
2. **Test the executable** - run it to verify it works
3. **Move to USB drive** - copy to portable media
4. **Distribute** - share with other Income Tax officers

---

## 🔗 Complete Documentation

See **`BUILD_GUIDE.md`** for:
- Detailed step-by-step instructions
- Customization options
- Advanced configuration
- Troubleshooting guide
- CI/CD automation setup
- Professional distribution methods

---

## 💡 Tips

- **First build slower**: Initial run extracts all files, caches compiled Python
- **Save space**: Delete `build/` directory after successful build
- **Faster builds**: Keep PyInstaller cache `--onefile` generates cached files
- **Testing**: Always test executable on actual target OS before distribution

---

## 📊 Build Status

Track your build progress:

```
Windows Build: [ ] Setup [ ] Building [ ] Testing [ ] Complete
macOS Build:   [ ] Setup [ ] Building [ ] Testing [ ] Complete  
Linux Build:   [ ] Setup [ ] Building [ ] Testing [ ] Complete
```

---

## 📧 Support

For issues not covered here:
1. Check `BUILD_GUIDE.md` for detailed troubleshooting
2. Review PyInstaller docs: https://pyinstaller.org
3. Check build script error messages
4. Review `build/` log files for details

---

**Ready? Start with your operating system above! ↑**
