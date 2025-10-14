# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for EDITH-Automater
This bundles the orchestrator and all forensic tools into a portable EXE
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the project root directory
project_root = os.path.abspath('.')

# Collect all submodules from tools directory
hidden_imports = [
    'asyncio',
    'argparse',
    'logging',
    'subprocess',
    'pathlib',
    'datetime',
    'json',
    'hashlib',
    'shutil',
    'exifread',
    'PIL',
    'pandas',
    'mutagen',
    'hachoir',
    'magic',
    'PyPDF2',
    'coloredlogs',
    'ujson',
    'tqdm',
    'psutil',
    'rich',
    'capstone',
    'Crypto',
    'pefile',
    'yara',
    'jsonschema',
]

# Data files to include
datas = [
    # Include all Python scripts from tools
    ('tools/Scripts/*.py', 'tools/Scripts'),
    ('tools/hashdeep/*.py', 'tools/hashdeep'),
    ('tools/exiftool/*.py', 'tools/exiftool'),
    ('tools/volatility/*.py', 'tools/volatility'),
    ('tools/autopsy/*.py', 'tools/autopsy'),
    ('tools/bulk-extractor/*.py', 'tools/bulk-extractor'),
    
    # Include ExifTool binary and its files
    ('tools/exiftool/bin/exiftool.exe', 'tools/exiftool/bin'),
    ('tools/exiftool/bin/exiftool_files', 'tools/exiftool/bin/exiftool_files'),
    
    # Include bulk_extractor binary (if it exists)
    ('tools/bulk-extractor/bulk_extractor*', 'tools/bulk-extractor'),
    
    # Include README files
    ('tools/*/README*', 'tools'),
    
    # Include requirements files
    ('tools/requirements.txt', 'tools'),
]

# Binaries to include
binaries = []

# Analysis
a = Analysis(
    ['orchestrator.py'],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EDITH-Automater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console window open to see errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add your icon path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDITH-Automater',
)