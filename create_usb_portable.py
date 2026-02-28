#!/usr/bin/env python3
"""
EDITH-Automater USB Portable Creator
=====================================
Copies the entire EDITH-Automater project (including the 2011-10-19-Sample.E01
evidence file) to a USB drive so it can be demonstrated on any Windows PC with
Python 3 installed.

Usage:
    python create_usb_portable.py            # prompts for USB drive letter
    python create_usb_portable.py E           # copies to E:\\EDITH-Automater
    python create_usb_portable.py E:\\MyFolder # copies to that exact path

The target folder is completely rebuilt on each run (old contents removed).
"""

import os
import sys
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Directories / files to copy from the project root
# ---------------------------------------------------------------------------

COPY_DIRS = [
    "orchestrator",
    "tools",
    "case_templates",
    "reports",
    "evidence",          # <-- includes 2011-10-19-Sample.E01
]

COPY_FILES = [
    "config.json",
    "README.md",
    "run_pipeline.bat",      # already fixed to use relative paths
    "QUICKSTART.py",
    "check_dependencies.py",
    "EyezOn.png",
    "EyezOn.ico",
]

# Never copy these into the USB (build artefacts, dev files)
IGNORE_PATTERNS = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo",
    ".git", ".vs", ".vscode",
    "build", "dist", "*.spec",
    "Results",           # case output stays local
    "*.log",
)

# ---------------------------------------------------------------------------
# USB README written at root of the USB folder
# ---------------------------------------------------------------------------

USB_README = r"""
EDITH-Automater  --  USB Portable Edition
==========================================

Pre-loaded evidence: evidence\2011-10-19-Sample.E01
  * Windows XP NTFS image, Case HMG-99999-11, Subject: Craig Wilson

REQUIREMENTS
  * Windows 10 / 11
  * Python 3.8 or newer (python.org/downloads)

QUICK START (double-click or from Command Prompt)
  1.  plug in the USB
  2.  double-click  run_pipeline.bat
      -- the 2011 evidence is used automatically
  3.  wait ~2 minutes for all tools to finish
  4.  a browser tab opens with the Case Dashboard
  5.  explore Timeline, integrity proof, BulkExtractor artefacts, etc.

CUSTOM EVIDENCE
  run_pipeline.bat  "X:\path\to\your.E01"

TOOLS INCLUDED
  * SleuthKit / Autopsy  (fls, mmls, img_stat)
  * HashDeep             (MD5 + SHA256 hashing)
  * ExifTool             (metadata extraction)
  * Bulk Extractor       (email, URL, phone, CC patterns)
  * Timeline Correlator  (interactive HTML + Case Dashboard)

RESULTS
  All case output is written to  Results\CASE_<timestamp>\
"""

# ---------------------------------------------------------------------------

def resolve_target(arg):
    """Turn a user-supplied drive letter or path into an absolute Path."""
    if arg is None:
        raw = input("  Enter USB drive letter or full path (e.g.  E  or  E:\\EDITH): ").strip()
    else:
        raw = str(arg).strip()

    if not raw:
        print("[ERROR] No destination provided.")
        sys.exit(1)

    # Single letter => <LETTER>:\EDITH-Automater
    if len(raw) == 1 and raw.isalpha():
        return Path("{}:\\EDITH-Automater".format(raw.upper()))

    # Drive letter with colon => <LETTER>:\EDITH-Automater
    if len(raw) == 2 and raw[1] == ":":
        return Path("{}\\EDITH-Automater".format(raw.upper()))

    # Full path given
    p = Path(raw)
    if p.stem.upper() == "EDITH-AUTOMATER":
        return p
    return p / "EDITH-Automater"


def copy_item(src, dst, label):
    """Copy a single file or directory tree with status output."""
    if not src.exists():
        print("  [SKIP] {} not found at {}".format(label, src))
        return

    try:
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=IGNORE_PATTERNS)
            n = sum(1 for _ in dst.rglob("*") if _.is_file())
            print("  [OK]  {:<30} ({} files)".format(label, n))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            size_kb = src.stat().st_size // 1024
            print("  [OK]  {:<30} ({:,} KB)".format(label, size_kb))
    except Exception as exc:
        print("  [ERR] {}: {}".format(label, exc))


def main():
    print()
    print("=" * 60)
    print("    EDITH-Automater  --  USB Portable Creator")
    print("=" * 60)

    # --- Locate project root (this script lives in the project root) -------
    project_root = Path(__file__).resolve().parent
    print("\n  Source project : {}".format(project_root))

    # --- Resolve destination ----------------------------------------------
    user_arg = sys.argv[1] if len(sys.argv) > 1 else None
    target = resolve_target(user_arg)
    print("  Destination    : {}".format(target))
    print()

    # Sanity check: do not overwrite source
    try:
        if target.resolve() == project_root.resolve():
            print("[ERROR] Destination is the same as the source project. Aborting.")
            sys.exit(1)
    except Exception:
        pass

    # --- Wipe and recreate destination ------------------------------------
    if target.exists():
        print("  Removing existing folder: {}".format(target))
        try:
            shutil.rmtree(target)
        except Exception as exc:
            print("  [WARN] Could not fully remove old folder: {}".format(exc))

    target.mkdir(parents=True, exist_ok=True)

    # --- Copy directories -------------------------------------------------
    print("  Copying directories ...")
    for d in COPY_DIRS:
        copy_item(project_root / d, target / d, d + "/")

    # --- Copy individual files --------------------------------------------
    print("  Copying files ...")
    for f in COPY_FILES:
        src = project_root / f
        if src.exists():
            copy_item(src, target / f, f)

    # --- Create empty Results directory -----------------------------------
    (target / "Results").mkdir(exist_ok=True)
    print("  [OK]  {:<30} (ready for cases)".format("Results/"))

    # --- Write USB README -------------------------------------------------
    readme_path = target / "USB_README.txt"
    readme_path.write_text(USB_README.lstrip(), encoding="utf-8")
    print("  [OK]  USB_README.txt")

    # --- Summary ----------------------------------------------------------
    total_files = sum(1 for _ in target.rglob("*") if _.is_file())
    total_mb = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / (1024 * 1024)

    print()
    print("=" * 60)
    print("    USB COPY COMPLETE!")
    print("=" * 60)
    print("  Location : {}".format(target))
    print("  Files    : {:,}".format(total_files))
    print("  Size     : {:.1f} MB".format(total_mb))
    print()
    print("  To run the demo:")
    print("  > {}\\run_pipeline.bat".format(target))
    print()


if __name__ == "__main__":
    main()
