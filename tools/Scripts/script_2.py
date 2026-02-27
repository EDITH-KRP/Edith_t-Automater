#!/usr/bin/env python3
"""
EDITH-Automater — Digital Evidence Collection / Image Creation (script_2.py)
Guides the examiner through creating a forensic image with FTK Imager or dd,
verifies the image with SHA-256, and records chain-of-custody information.
"""

import os
import sys
import hashlib
import subprocess
import shutil
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr(char="=", width=60):
    print(char * width)


def _prompt(msg, default=None):
    """Prompt with optional default."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{msg}{suffix}: ").strip()
    return value if value else (default or "")


def _sha256_chunked(file_path: str, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Compute SHA-256 of a file using chunked reading (handles large images)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _md5_chunked(file_path: str, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Compute MD5 of a file using chunked reading."""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _find_tool(*candidates):
    """Return the first executable found, or None."""
    for name in candidates:
        path = shutil.which(name)
        if path:
            return path
    return None


# ---------------------------------------------------------------------------
# Image-creation backends
# ---------------------------------------------------------------------------

def _acquire_with_ftk(source, dest_dir, case_id, examiner):
    """Attempt to call FTK Imager CLI (ftkimager) if present."""
    ftkimager = _find_tool("ftkimager", "ftkimager.exe")
    if not ftkimager:
        # Try next to this script
        local = Path(__file__).parent.parent / "ftkimager" / "ftkimager.exe"
        if local.exists():
            ftkimager = str(local)

    if not ftkimager:
        return None, "FTK Imager CLI (ftkimager) not found in PATH."

    dest_base = Path(dest_dir) / case_id
    dest_base.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ftkimager, source,
        str(dest_base),
        "--e01",
        f"--case-number={case_id}",
        f"--evidence-number=1",
        f"--examiner={examiner}",
        "--compress-level=0",
        "--verify",
    ]
    print("[INFO] Running FTK Imager CLI …")
    print(f"       Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, text=True)

    image_file = str(dest_base) + ".E01"
    if result.returncode == 0 and Path(image_file).exists():
        return image_file, None
    return None, f"ftkimager exited with code {result.returncode}"


def _acquire_with_dd(source, dest_dir, case_id):
    """Attempt dd/dc3dd/dcfldd if available."""
    for tool in ("dc3dd", "dcfldd", "dd"):
        dd = _find_tool(tool, tool + ".exe")
        if not dd:
            continue

        dest_file = str(Path(dest_dir) / f"{case_id}.dd")
        Path(dest_dir).mkdir(parents=True, exist_ok=True)

        cmd = [dd, f"if={source}", f"of={dest_file}", "bs=512", "conv=noerror,sync"]
        print(f"[INFO] Running {tool} …")
        print(f"       Command: {' '.join(cmd)}")
        result = subprocess.run(cmd)

        if result.returncode == 0 and Path(dest_file).exists():
            return dest_file, None

    return None, "No dd-compatible tool found (dd / dc3dd / dcfldd)."


def _guided_manual_copy(source, dest_dir, case_id):
    """
    Fallback: if no imaging tool is installed, guide the user to provide an
    already-created image file and still compute hashes + record custody info.
    """
    _hr()
    print("No automated imaging tool was found on this system.")
    print("Please create a forensic image manually (FTK Imager GUI, Arsenal Image Mounter,")
    print("Guymager, etc.) and then enter the path to the resulting image file below.")
    _hr("-")
    image_path = _prompt("Path to existing image file (.E01 / .dd / .raw)")
    if not image_path or not Path(image_path).exists():
        return None, f"Image file not found: {image_path}"
    return image_path, None


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def main():
    """Image-creation and chain-of-custody recording workflow."""
    _hr()
    print("  EDITH-Automater — Digital Evidence Collection (Image Creation)")
    _hr()
    print()

    # ---- Case metadata ----
    case_id   = _prompt("Case number / ID",
                        default=f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    examiner  = _prompt("Examiner name", default="EDITH-Automater")
    officer   = _prompt("Authorising officer")
    notes     = _prompt("Notes / description (optional)")

    # ---- Source device / file ----
    _hr("-")
    print("SOURCE EVIDENCE")
    _hr("-")
    print("Enter the source to image.  Examples:")
    print("  Windows physical drive  : \\\\.\\PhysicalDrive0")
    print("  Linux block device      : /dev/sdb")
    print("  Existing image to copy  : C:\\Evidence\\original.E01")
    source = _prompt("Source path")
    if not source:
        print("[ERROR] No source provided.  Aborting.")
        return

    # ---- Destination ----
    script_dir   = Path(__file__).parent
    default_dest = str(script_dir.parent.parent / "Results" / case_id / "Image_output")
    dest_dir = _prompt("Destination directory", default=default_dest)
    Path(dest_dir).mkdir(parents=True, exist_ok=True)

    # ---- Choose acquisition method ----
    _hr("-")
    print("ACQUISITION METHOD")
    _hr("-")
    print("1. FTK Imager CLI (ftkimager)  — produces .E01")
    print("2. dd / dc3dd / dcfldd         — produces raw .dd")
    print("3. Manual / pre-existing image — record hashes only")
    method_choice = _prompt("Choice", default="1")

    start_time = datetime.now()
    print(f"\n[{start_time.strftime('%H:%M:%S')}] Starting acquisition …\n")

    image_path = None
    error      = None

    if method_choice == "1":
        image_path, error = _acquire_with_ftk(source, dest_dir, case_id, examiner)
        if error:
            print(f"[WARNING] FTK acquisition failed ({error}). Trying dd …")
            image_path, error = _acquire_with_dd(source, dest_dir, case_id)
    elif method_choice == "2":
        image_path, error = _acquire_with_dd(source, dest_dir, case_id)
    else:
        image_path, error = _guided_manual_copy(source, dest_dir, case_id)

    if error or not image_path:
        print(f"\n[ERROR] Image acquisition failed: {error or 'Unknown error'}")
        # Still write a custody record with the failure noted
        _write_custody_record(
            case_id, examiner, officer, notes, source, dest_dir,
            image_path=None, md5=None, sha256=None,
            start_time=start_time, end_time=datetime.now(),
            acquisition_status="FAILED", acquisition_error=str(error)
        )
        return

    end_time = datetime.now()
    elapsed  = (end_time - start_time).total_seconds()
    print(f"\n[{end_time.strftime('%H:%M:%S')}] Acquisition finished in {elapsed:.1f} s")
    print(f"[INFO] Image file: {image_path}")

    # ---- Hash verification ----
    _hr("-")
    print("COMPUTING HASHES  (this may take several minutes for large images) …")
    print("  MD5   …", end="", flush=True)
    md5_hash = _md5_chunked(image_path)
    print(f" {md5_hash}")

    print("  SHA-256 …", end="", flush=True)
    sha256_hash = _sha256_chunked(image_path)
    print(f" {sha256_hash}")

    # ---- Chain-of-custody record ----
    _write_custody_record(
        case_id, examiner, officer, notes, source, dest_dir,
        image_path=image_path,
        md5=md5_hash, sha256=sha256_hash,
        start_time=start_time, end_time=end_time,
        acquisition_status="SUCCESS"
    )

    _hr()
    print("   Image creation and chain-of-custody recording complete.")
    _hr()
    print(f"  Image : {image_path}")
    print(f"  MD5   : {md5_hash}")
    print(f"  SHA-256: {sha256_hash}")
    _hr()


def _write_custody_record(case_id, examiner, officer, notes,
                          source, dest_dir, image_path, md5, sha256,
                          start_time, end_time,
                          acquisition_status="SUCCESS",
                          acquisition_error=None):
    """Write a text-based chain-of-custody record alongside the image."""
    record_dir = Path(dest_dir)
    record_dir.mkdir(parents=True, exist_ok=True)
    record_path = record_dir / f"chain_of_custody_{case_id}.txt"

    with open(record_path, "w", encoding="utf-8") as f:
        f.write("CHAIN OF CUSTODY — DIGITAL EVIDENCE ACQUISITION\n")
        f.write("=" * 60 + "\n")
        f.write(f"Case ID          : {case_id}\n")
        f.write(f"Examiner         : {examiner}\n")
        f.write(f"Officer          : {officer}\n")
        f.write(f"Notes            : {notes}\n")
        f.write(f"Source           : {source}\n")
        f.write(f"Destination Dir  : {dest_dir}\n")
        f.write(f"Image File       : {image_path or 'N/A'}\n")
        f.write(f"Start Time       : {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"End Time         : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration         : {(end_time - start_time).total_seconds():.1f} s\n")
        f.write(f"Status           : {acquisition_status}\n")
        if acquisition_error:
            f.write(f"Error            : {acquisition_error}\n")
        f.write("\nCRYPTOGRAPHIC HASHES\n")
        f.write("-" * 40 + "\n")
        f.write(f"MD5    : {md5 or 'N/A'}\n")
        f.write(f"SHA-256: {sha256 or 'N/A'}\n")
        f.write("\nNOTE: SHA-256 is the recommended algorithm (NIST SP 800-131A).\n")
        f.write("      MD5 and SHA-1 are considered cryptographically weak.\n")
        f.write("=" * 60 + "\n")
        f.write(f"Record created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"[INFO] Chain-of-custody record saved: {record_path}")


if __name__ == "__main__":
    main()
