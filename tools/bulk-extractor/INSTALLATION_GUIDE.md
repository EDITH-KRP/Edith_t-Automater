# Bulk Extractor Installation Guide for Windows

## Option 1: Download Pre-compiled Windows Executable

1. **Download from official source:**
   - Visit: https://github.com/simsong/bulk_extractor/releases
   - Download the latest Windows release (bulk_extractor-x.x.x-win32.zip or similar)
   - Extract the zip file

2. **Place the executable:**
   - Copy `bulk_extractor.exe` to this directory: `E:\Github-adhi982\Edith_t-Automater\tools\bulk-extractor\`
   - The final path should be: `E:\Github-adhi982\Edith_t-Automater\tools\bulk-extractor\bulk_extractor.exe`

## Option 2: Install via Package Manager

### Using Chocolatey (if available):
```powershell
choco install bulk-extractor
```

### Using Windows Subsystem for Linux (WSL):
```bash
sudo apt-get update
sudo apt-get install bulk-extractor
```

## Option 3: Compile from Source (Advanced)

1. Install Visual Studio with C++ support
2. Clone the repository: `git clone https://github.com/simsong/bulk_extractor.git`
3. Follow the Windows compilation instructions in the repository

## Verification

After installation, test by running:
```powershell
cd "E:\Github-adhi982\Edith_t-Automater\tools\bulk-extractor"
.\bulk_extractor.exe -V
```

## Current Status

✅ **Autopsy**: Fully working with SleuthKit tools  
❌ **Bulk Extractor**: Needs executable installation  
✅ **ExifTool**: Fully working  
✅ **HashDeep**: Fully working  
✅ **Volatility**: Working (some Python path issues but functional)