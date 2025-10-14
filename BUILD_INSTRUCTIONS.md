# EDITH-Automater - EXE Build Instructions

## Prerequisites

### 1. Install All Python Dependencies
```powershell
pip install -r tools\requirements.txt
pip install pyinstaller
```

### 2. Verify Your Setup
Run the test script to check if everything is ready:
```powershell
python test_exe_build.py
```

This will check:
- ✓ Python version (3.8+ required)
- ✓ All required Python modules
- ✓ Project file structure
- ✓ PyInstaller installation
- ✓ Orchestrator can be imported

Fix any issues reported before proceeding.

---

## Building the EXE

### Option 1: Automated Build (Recommended)
Simply double-click: **`build_exe.bat`**

This will:
1. Run pre-build tests
2. Install/update PyInstaller
3. Clean previous builds
4. Build the EXE
5. Open the output folder

### Option 2: Manual Build
```powershell
# Clean previous builds
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Build using the spec file
pyinstaller build_exe.spec --clean
```

---

## What Gets Bundled

### ✅ Included in EXE:
- All Python code (orchestrator.py, all scripts)
- All Python libraries from requirements.txt
- ExifTool binary (`tools/exiftool/bin/exiftool.exe`)
- bulk_extractor binary (if present)
- All Python-based forensic tools

### ⚠️ NOT Included (Optional):
- **The Sleuth Kit (TSK)** tools (mmls, fls, fsstat, tsk_recover)
  - The EXE will work without these
  - Autopsy module will show warnings if TSK is not installed
  - To include TSK: Download Windows binaries and add to spec file

---

## Output Structure

After building, you'll find:
```
dist/
└── EDITH-Automater/
    ├── EDITH-Automater.exe    ← Main executable
    ├── tools/                  ← Forensic tools and scripts
    │   ├── exiftool/
    │   │   └── bin/
    │   │       └── exiftool.exe
    │   ├── bulk-extractor/
    │   ├── Scripts/
    │   └── ...
    ├── _internal/              ← Python runtime and libraries
    └── Results/                ← Created on first run
```

**Important:** Distribute the **entire `EDITH-Automater` folder**, not just the .exe file!

---

## Testing the EXE

1. Navigate to `dist\EDITH-Automater\`
2. Double-click `EDITH-Automater.exe`
3. You should see the menu with workflow options

### If the EXE crashes immediately:

1. **Run from Command Prompt** to see error messages:
   ```cmd
   cd dist\EDITH-Automater
   EDITH-Automater.exe
   ```

2. **Common Issues:**
   - **Missing DLLs**: Install Visual C++ Redistributable
   - **Antivirus blocking**: Add exception for the EXE
   - **Path issues**: Make sure you're running from the correct folder
   - **Missing modules**: Rebuild after installing all requirements

3. **Check the log file** (if created) for error details

---

## Troubleshooting

### Issue: "Failed to execute script orchestrator"
**Solution:** Missing Python dependencies
```powershell
pip install -r tools\requirements.txt
# Then rebuild
```

### Issue: EXE opens and closes immediately
**Solution:** Run from command prompt to see the error:
```cmd
cd dist\EDITH-Automater
EDITH-Automater.exe
```

### Issue: "Cannot find tools/Scripts/..."
**Solution:** The spec file didn't bundle the scripts correctly
- Check that all files exist in the source
- Rebuild with `--clean` flag

### Issue: ExifTool not working
**Solution:** 
- Verify `tools/exiftool/bin/exiftool.exe` exists in source
- Check it's included in `dist/EDITH-Automater/tools/exiftool/bin/`

### Issue: Large EXE size (>500MB)
**Solution:** This is normal for bundled forensic tools
- Python runtime: ~50MB
- Libraries (pandas, PIL, etc.): ~200MB
- ExifTool: ~20MB
- Your code: ~10MB

To reduce size:
- Use `--onefile` mode (slower startup)
- Exclude unused libraries in spec file
- Use UPX compression (already enabled)

---

## Distribution

### For End Users:
1. Zip the entire `dist\EDITH-Automater` folder
2. Share the zip file
3. Users extract and run `EDITH-Automater.exe`

### Optional: Create Installer
Use tools like:
- **Inno Setup** (free, recommended)
- **NSIS**
- **WiX Toolset**

---

## Notes

- **Console Window:** The EXE runs with a console window (required for interactive workflows)
- **First Run:** May take 10-20 seconds to start (Python runtime initialization)
- **Antivirus:** Some antivirus software may flag PyInstaller EXEs as suspicious (false positive)
- **TSK Tools:** If users need full Autopsy functionality, they must install The Sleuth Kit separately

---

## Build Environment

This build was configured for:
- **OS:** Windows 11
- **Python:** 3.12
- **PyInstaller:** Latest version
- **Architecture:** x64

For different environments, update paths in `build_exe.bat` and `build_exe.spec`.