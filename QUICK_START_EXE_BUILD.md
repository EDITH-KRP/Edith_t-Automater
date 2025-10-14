# Quick Start: Building EDITH-Automater EXE

## 🚀 Fast Track (3 Steps)

### Step 1: Install Dependencies
```powershell
pip install -r tools\requirements.txt
pip install pyinstaller
```

### Step 2: Test Your Setup
Double-click: **`test_exe_build.py`**
- Fix any issues reported
- All checks should pass ✓

### Step 3: Build the EXE
Double-click: **`build_exe.bat`**
- Wait for build to complete (~2-5 minutes)
- Find your EXE in: `dist\EDITH-Automater\`

---

## 📦 What You Get

After building, you'll have:
```
dist/EDITH-Automater/
├── EDITH-Automater.exe    ← Double-click to run
├── tools/                  ← All forensic tools
│   ├── exiftool/
│   │   └── bin/
│   │       └── exiftool.exe
│   ├── bulk-extractor/
│   ├── Scripts/
│   └── ...
└── _internal/              ← Python runtime (don't touch)
```

**Important:** Distribute the **entire folder**, not just the .exe!

---

## ✅ What's Included (No Installation Needed)

Your EXE bundles:
- ✅ Python runtime
- ✅ All Python libraries
- ✅ ExifTool (metadata extraction)
- ✅ bulk_extractor (data carving)
- ✅ Volatility (memory analysis)
- ✅ HashDeep (file hashing)
- ✅ All your Python scripts

---

## ⚠️ What's NOT Included (Optional)

### The Sleuth Kit (TSK) - For Autopsy Module
- **Status:** Optional, not required
- **Impact:** Autopsy module shows warnings but still works
- **What works without TSK:** File hashing, basic analysis
- **What doesn't work:** Partition analysis, file recovery

**Your EXE will work fine without TSK!**

See `AUTOPSY_TSK_INFO.md` for details.

---

## 🐛 Troubleshooting

### Issue: EXE crashes immediately

**Solution 1:** Run from Command Prompt to see errors
```cmd
cd dist\EDITH-Automater
EDITH-Automater.exe
```

**Solution 2:** Check for missing dependencies
```powershell
python test_exe_build.py
```

**Solution 3:** Rebuild with clean flag
```powershell
pyinstaller build_exe.spec --clean
```

---

### Issue: "Failed to execute script"

**Cause:** Missing Python modules

**Solution:**
```powershell
pip install -r tools\requirements.txt
# Then rebuild
```

---

### Issue: Antivirus blocks the EXE

**Cause:** PyInstaller EXEs sometimes trigger false positives

**Solution:**
1. Add exception in your antivirus
2. Or submit to antivirus vendor as false positive
3. Or code-sign the EXE (advanced)

---

### Issue: EXE is very large (>500MB)

**Cause:** This is normal! Includes Python + all libraries

**Breakdown:**
- Python runtime: ~50MB
- Scientific libraries (pandas, PIL): ~200MB
- Forensic tools: ~50MB
- Your code: ~10MB

**This is expected for a full forensic toolkit!**

---

## 📝 Previous Build Failed?

If you tried building before and it failed:

### Why it failed:
1. ❌ Missing Python dependencies
2. ❌ Wrong paths in spec file
3. ❌ Console window closed too fast to see error

### How we fixed it:
1. ✅ Created `test_exe_build.py` - Tests everything first
2. ✅ Created `build_exe.spec` - Proper PyInstaller configuration
3. ✅ Created `build_exe.bat` - Automated build process
4. ✅ Console stays open - You can see errors now

---

## 🎯 Next Steps

### After Building:

1. **Test the EXE:**
   ```cmd
   cd dist\EDITH-Automater
   EDITH-Automater.exe
   ```
   - Should show the menu
   - Try option 3 (List Cases)

2. **Test a Workflow:**
   - Try option 2 (Evidence Collection - Automated)
   - Should create a case in Results folder

3. **Distribute:**
   - Zip the entire `dist\EDITH-Automater` folder
   - Share with users
   - Users extract and run the .exe

---

## 📚 Additional Resources

- **Full build guide:** `BUILD_INSTRUCTIONS.md`
- **TSK/Autopsy info:** `AUTOPSY_TSK_INFO.md`
- **PyInstaller spec:** `build_exe.spec`
- **Test script:** `test_exe_build.py`

---

## 💡 Pro Tips

1. **Always test before building:**
   ```powershell
   python test_exe_build.py
   ```

2. **Clean build if you make changes:**
   ```powershell
   pyinstaller build_exe.spec --clean
   ```

3. **Test the EXE on a clean machine** (without Python installed)

4. **Keep the console window** - Helps users see what's happening

5. **Include a README** in the dist folder for users

---

## ✨ You're Ready!

Your project is **already configured** for EXE building. Just run:

1. `test_exe_build.py` - Check everything
2. `build_exe.bat` - Build the EXE
3. Test in `dist\EDITH-Automater\`

**That's it!** 🎉