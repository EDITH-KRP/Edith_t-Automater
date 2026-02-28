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
    ['orchestrator/launcher.py'],  # Entry point
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
        # Timeline correlator & AI Analyst
        ('tools/timeline', 'tools/timeline'),
        ('tools/ai_analyst', 'tools/ai_analyst'),
        # Configuration files
        ('config.json', '.'),
        ('README.md', '.'),
        # Application icon assets
        ('EyezOn.png', '.'),
        ('EyezOn.ico', '.'),
    ],
    hiddenimports=[
        # Timeline correlator (imported as 'timeline.timeline_correlator')
        'timeline',
        'timeline.timeline_correlator',
        # AI Analyst
        'ai_analyst',
        'ai_analyst.ai_analyst',
        'ollama',
        # Forensic tools
        'autopsy',
        'exiftool',
        'volatility',
        'volatility3',
        # FTK modules
        'ftk_metadata',
        'ftk_metadata.ftk_image_analyzer',
        'ftk_metadata.ftk_integration',
        # Analysis reporter
        'analysis_reporter',
        'analysis_reporter.analyze_tool_outputs',
        'analysis_reporter.generate_analysis_report',
        'analysis_reporter.analysis_reporter_integration',
        # Standard library modules we use
        'json', 'pathlib', 'datetime', 'subprocess', 'asyncio',
        're', 'hashlib', 'struct', 'threading', 'shutil',
        # Third-party packages used in pipeline
        'colorama',
        'webbrowser',
        # Optional external libraries (if installed)
        'pyewf', 'pytsk3', 'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    a.datas,
    [],
    name='EDITH-Automater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='EyezOn.ico',
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
