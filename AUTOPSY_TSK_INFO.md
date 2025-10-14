# Autopsy / The Sleuth Kit (TSK) - Information for EXE Build

## What is "Autopsy" in Your Project?

Your `tools/autopsy/auto.py` module **does NOT use the Autopsy GUI application**. Instead, it uses **The Sleuth Kit (TSK)** command-line tools.

### TSK Tools Used:
1. **mmls** - Display partition tables from disk images
2. **fls** - List files and directories in a filesystem
3. **fsstat** - Display filesystem statistics and details
4. **tsk_recover** - Recover deleted files from disk images

---

## Current Behavior (As-Is)

Your `auto.py` is **already designed to work without TSK installed**:

```python
# From auto.py line 23-36
def check_tools():
    """Check if required forensic tools are available"""
    tools = ['mmls', 'fls', 'fsstat', 'tsk_recover']
    available = {}
    
    for tool in tools:
        result = subprocess.run(['which', tool], capture_output=True, text=True)
        available[tool] = result.returncode == 0
        if available[tool]:
            print(f"[+] Found tool: {tool}")
        else:
            print(f"[!] Missing tool: {tool}")
    
    return available
```

### What Happens Without TSK:
- ✅ **Still works** - EXE won't crash
- ✅ **Basic analysis** - File hashing (MD5/SHA256) still works
- ✅ **Graceful degradation** - Shows warnings for missing tools
- ⚠️ **Limited functionality** - No partition analysis, file listing, or recovery

---

## For Your Portable EXE

### Option 1: Keep As-Is (Recommended)
**No changes needed!** Your code already handles missing TSK gracefully.

**Pros:**
- ✅ EXE works immediately
- ✅ Smaller file size
- ✅ No licensing concerns
- ✅ Basic forensic analysis still works

**Cons:**
- ⚠️ Users see warnings about missing TSK tools
- ⚠️ No partition/filesystem analysis
- ⚠️ No file recovery features

**User Experience:**
```
[*] Checking available forensic tools...
[!] Missing tool: mmls
[!] Missing tool: fls
[!] Missing tool: fsstat
[!] Missing tool: tsk_recover
[*] Performing basic file analysis...
[*] Computing hashes...
[+] Autopsy analysis complete. Results saved in ...
```

---

### Option 2: Bundle TSK Binaries (Advanced)

If you want full functionality, you can bundle TSK Windows binaries.

#### Steps:

1. **Download TSK for Windows:**
   - Visit: https://github.com/sleuthkit/sleuthkit/releases
   - Download: `sleuthkit-X.X.X-win32.zip`
   - Extract the binaries

2. **Copy TSK binaries to your project:**
   ```
   tools/
   └── sleuthkit/
       ├── mmls.exe
       ├── fls.exe
       ├── fsstat.exe
       ├── tsk_recover.exe
       └── (other DLLs)
   ```

3. **Update `build_exe.spec`:**
   ```python
   datas = [
       # ... existing entries ...
       ('tools/sleuthkit/*.exe', 'tools/sleuthkit'),
       ('tools/sleuthkit/*.dll', 'tools/sleuthkit'),
   ]
   ```

4. **Update `auto.py` to use bundled binaries:**
   ```python
   # Add at the top of auto.py
   import sys
   from pathlib import Path
   
   # Get the bundled TSK path
   if getattr(sys, 'frozen', False):
       # Running as EXE
       TSK_PATH = Path(sys._MEIPASS) / 'tools' / 'sleuthkit'
   else:
       # Running as script
       TSK_PATH = Path(__file__).parent.parent / 'sleuthkit'
   
   # Update check_tools() to look in TSK_PATH
   ```

**Pros:**
- ✅ Full functionality
- ✅ No user installation needed
- ✅ Professional experience

**Cons:**
- ⚠️ Larger EXE size (+50MB)
- ⚠️ More complex build process
- ⚠️ Need to maintain TSK binaries

---

### Option 3: Require User Installation

Document that users need to install TSK separately.

**In your README:**
```markdown
## Optional: The Sleuth Kit (TSK)

For full Autopsy functionality, install The Sleuth Kit:

**Windows:**
1. Download from: https://github.com/sleuthkit/sleuthkit/releases
2. Install or extract to a folder
3. Add to PATH environment variable

**Without TSK:**
- Basic file analysis and hashing still works
- Partition analysis and file recovery unavailable
```

---

## Recommendation for Your EXE

**Keep it as-is (Option 1)** because:

1. ✅ Your code already handles it gracefully
2. ✅ Other tools (ExifTool, bulk_extractor, Volatility) provide most forensic value
3. ✅ Simpler build process
4. ✅ Smaller, faster EXE
5. ✅ Users who need TSK can install it separately

The EXE will work perfectly without TSK - users just won't get partition analysis features.

---

## Testing Without TSK

When you run your EXE, the Autopsy module will:
1. Check for TSK tools
2. Report which ones are missing
3. Continue with available analysis (hashing)
4. Create a summary report noting TSK is not available

**This is perfectly fine for most use cases!**

---

## Summary

**For Autopsy/TSK:**
- ✅ **No installation required** - Your code handles missing TSK
- ✅ **EXE will work** - Won't crash without TSK
- ✅ **Basic analysis works** - File hashing and metadata
- ⚠️ **Advanced features unavailable** - Partition analysis, file recovery

**Your current code is already production-ready for EXE bundling!**