# -*- mode: python ; coding: utf-8 -*-
# PyInstaller Build Spec for EDITH-Automater
# Build command: pyinstaller EDITH-Automater.spec
# Output: Single portable executable for Windows/Mac/Linux

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ============================================================================
# ANALYSIS CONFIGURATION
# ============================================================================

a = Analysis(
    ['orchestrator/launcher.py'],  # Entry point (will create this)
    pathex=[os.getcwd()],
    binaries=[],
    datas=[
        # Include report templates
        ('reports/Reports html', 'reports/Reports html'),
        # Include case templates
        ('case_templates', 'case_templates'),
        # Include all tools subdirectories
        ('tools/autopsy', 'tools/autopsy'),
        ('tools/bulk-extractor', 'tools/bulk-extractor'),
        ('tools/exiftool', 'tools/exiftool'),
        ('tools/hashdeep', 'tools/hashdeep'),
        ('tools/volatility', 'tools/volatility'),
        ('tools/Scripts', 'tools/Scripts'),
        ('tools/ftk_metadata', 'tools/ftk_metadata'),
        ('tools/analysis_reporter', 'tools/analysis_reporter'),
        # Configuration files
        ('config.json', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        # Forensic tools
        'autopsy',
        'exiftool',
        'volatility',
        'volatility3',
        # FTK modules
        'tools.ftk_metadata',
        'tools.ftk_metadata.ftk_image_analyzer',
        'tools.ftk_metadata.ftk_integration',
        # Analysis reporter
        'tools.analysis_reporter',
        'tools.analysis_reporter.analyze_tool_outputs',
        'tools.analysis_reporter.generate_analysis_report',
        'tools.analysis_reporter.analysis_reporter_integration',
        # Standard library modules we use
        'json', 'pathlib', 'datetime', 'subprocess', 'asyncio',
        're', 'hashlib', 'struct', 'threading', 'shutil',
        # Optional external libraries (if installed)
        'pyewf', 'pytsk3', 'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# PYZ - Python ZIP Archive
# ============================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ============================================================================
# EXE - Executable (Single File)
# ============================================================================

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EDITH-Automater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Icon file not included
)

# ============================================================================
# APP - macOS App Bundle (Only on macOS)
# ============================================================================
# Uncomment this section if building on macOS

# app = BUNDLE(
#     exe,
#     name='EDITH-Automater.app',
#     icon='icon.icns',
#     bundle_identifier='com.edith.forensics.automater',
#     info_plist={
#         'NSPrincipalClass': 'NSApplication',
#         'NSHighResolutionCapable': 'True',
#         'CFBundleDisplayName': 'EDITH-Automater',
#         'CFBundleVersion': '1.0.0',
#     },
# )
