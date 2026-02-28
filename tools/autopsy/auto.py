#!/usr/bin/env python3
import os
import subprocess
import hashlib
import json
import datetime

def run_cmd(cmd):
    """Run a shell command and return stdout"""
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)  # 1 minute timeout
        if result.returncode != 0:
            print(f"[!] Error running: {cmd}\n{result.stderr}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"[!] Command timed out: {cmd}")
        return None
    except Exception as e:
        print(f"[!] Exception running {cmd}: {e}")
        return None

def check_tools():
    """Check if required forensic tools are available"""
    import shutil
    # Primary: SleuthKit bundled next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sleuthkit_bin = os.path.join(script_dir, "sleuthkit-4.12.1-win32", "bin")

    # Fallback 1: the script may be running from a copied/USB location but
    # SleuthKit lives in the original C: project tree.  Walk up from __file__
    # up to 4 levels looking for the bundled bin dir.
    if not os.path.isdir(sleuthkit_bin):
        check = os.path.abspath(__file__)
        for _ in range(6):
            check = os.path.dirname(check)
            candidate = os.path.join(check, "tools", "autopsy",
                                     "sleuthkit-4.12.1-win32", "bin")
            if os.path.isdir(candidate):
                sleuthkit_bin = candidate
                break

    tools = ['mmls.exe', 'fls.exe', 'fsstat.exe', 'tsk_recover.exe']
    available = {}

    for tool in tools:
        tool_path = os.path.join(sleuthkit_bin, tool)
        if os.path.exists(tool_path):
            available[tool] = True
            print(f"[+] Found tool: {tool} at {tool_path}")
        else:
            # Fallback 2: check system PATH
            which = shutil.which(tool) or shutil.which(tool.replace(".exe", ""))
            if which:
                available[tool] = True
                # redirect the bin dir so subsequent calls use the right path
                sleuthkit_bin = os.path.dirname(which)
                print(f"[+] Found tool: {tool} on PATH at {which}")
            else:
                available[tool] = False
                print(f"[!] Missing tool: {tool} (checked {tool_path})")

    return available, sleuthkit_bin

def compute_hashes(file_path):
    """Compute MD5 & SHA256 hashes using chunked reading to avoid loading entire file into RAM"""
    CHUNK = 8 * 1024 * 1024  # 8 MB chunks
    md5  = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            md5.update(chunk)
            sha256.update(chunk)
    return {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}

def get_partition_offset(image_path, sleuthkit_bin):
    """Parse mmls output to get NTFS/ExFAT offset.
    Falls back to offset 0 if the image is a raw partition or unsupported type."""
    mmls_path = os.path.join(sleuthkit_bin, "mmls.exe")
    output = run_cmd(f'"{mmls_path}" "{image_path}"')
    offset = None

    if output:
        for line in output.splitlines():
            upper = line.upper()
            if "NTFS" in upper or "EXFAT" in upper or "FAT" in upper or "EXT" in upper:
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        offset = parts[2].lstrip('0') or '0'
                        break
                    except Exception:
                        pass
        if offset is None:
            # Try any allocated partition
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[0].endswith(':'):
                    try:
                        offset = parts[2].lstrip('0') or '0'
                        break
                    except Exception:
                        pass

    if offset is None:
        # mmls failed or no partition found — try direct offset 0
        # (handles raw partitions, single-partition images, memory dumps)
        fsstat_path = os.path.join(sleuthkit_bin, "fsstat.exe")
        probe = run_cmd(f'"{fsstat_path}" -o 0 "{image_path}"')
        if probe:
            print("[*] No partition table found — treating as raw partition at offset 0")
            offset = '0'
            output = output or "(no partition table — direct access)"
        else:
            print("[!] Cannot determine partition structure. Image may be a memory dump or unsupported format.")

    return offset, output

def main(image_path=None, output_dir=None):
    """
    Main function for forensic analysis.
    If image_path is None, ask for input.
    If output_dir is None, use default "Evidence" folder.
    """
    if image_path is None:
        image_path = input("Enter path to evidence image (.E01/.dd): ").strip()

    # Convert to absolute path
    image_path = os.path.abspath(image_path)

    # Check file exists
    if not os.path.exists(image_path):
        print(f"[!] Error: File not found: {image_path}")
        return

    # Setup folder - use provided output_dir or default
    if output_dir:
        case_folder = os.path.abspath(output_dir)
    else:
        case_folder = os.path.join("Evidence")
    
    os.makedirs(case_folder, exist_ok=True)
    print(f"[*] Using output directory: {case_folder}")

    # Check available tools
    print("[*] Checking available forensic tools...")
    available_tools, sleuthkit_bin = check_tools()
    
    # Basic file analysis (always possible)
    print("[*] Performing basic file analysis...")
    file_info = {
        "file_path": image_path,
        "file_size": os.path.getsize(image_path),
        "file_exists": True,
        "timestamp": datetime.datetime.now().isoformat()
    }

    # Hash evidence
    print("[*] Computing hashes...")
    hashes = compute_hashes(image_path)
    file_info["hashes"] = hashes

    # Try TSK tools if available
    if available_tools.get('mmls.exe', False):
        # Get partition offset (with raw-partition fallback)
        print("[*] Running mmls / partition detection...")
        offset, mmls_output = get_partition_offset(image_path, sleuthkit_bin)
        if offset is not None:
            print(f"[*] Using partition offset: {offset}")
            file_info["partition_offset"] = offset
            if mmls_output:
                with open(os.path.join(case_folder, "partitions.txt"), "w", encoding='utf-8') as f:
                    f.write(mmls_output)
        else:
            print("[!] Could not determine partition offset — skipping TSK analysis")
            file_info["partition_offset"] = None
    else:
        print("[!] mmls not available - skipping partition analysis")
        offset = None

    if available_tools.get('fsstat.exe', False) and offset:
        # Run fsstat
        print("[*] Running fsstat...")
        fsstat_path = os.path.join(sleuthkit_bin, "fsstat.exe")
        fsstat_out = run_cmd(f'"{fsstat_path}" -o {offset} "{image_path}"')
        if fsstat_out:
            with open(os.path.join(case_folder, "fsstat.txt"), "w", encoding='utf-8') as f:
                f.write(fsstat_out)
    else:
        print("[!] fsstat not available or no partition offset - skipping filesystem analysis")

    if available_tools.get('fls.exe', False) and offset:
        # Run fls
        print("[*] Running fls...")
        fls_path = os.path.join(sleuthkit_bin, "fls.exe")
        fls_out = run_cmd(f'"{fls_path}" -o {offset} -r "{image_path}"')
        if fls_out:
            with open(os.path.join(case_folder, "files.txt"), "w", encoding='utf-8') as f:
                f.write(fls_out)
    else:
        print("[!] fls not available or no partition offset - skipping file listing")

    if available_tools.get('tsk_recover.exe', False) and offset:
        # Recover files
        print("[*] Running tsk_recover...")
        recover_dir = os.path.join(case_folder, "recovered_files")
        os.makedirs(recover_dir, exist_ok=True)
        tsk_recover_path = os.path.join(sleuthkit_bin, "tsk_recover.exe")
        run_cmd(f'"{tsk_recover_path}" -o {offset} "{image_path}" "{recover_dir}"')
    else:
        print("[!] tsk_recover not available or no partition offset - skipping file recovery")

    # Always save metadata JSON
    with open(os.path.join(case_folder, "autopsy_analysis.json"), "w", encoding='utf-8') as f:
        json.dump(file_info, f, indent=4)

    # Create summary report
    summary_file = os.path.join(case_folder, "autopsy_summary.txt")
    any_tsk_available = any(available_tools.values())
    with open(summary_file, "w", encoding='utf-8') as f:
        f.write("EDITH-Automater Autopsy Analysis Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Evidence File: {image_path}\n")
        f.write(f"File Size: {file_info['file_size']} bytes\n")
        f.write(f"MD5 Hash:    {hashes['md5']}\n")
        f.write(f"SHA256 Hash: {hashes['sha256']}\n")
        f.write(f"Analysis Date: {file_info['timestamp']}\n")
        f.write("\nTools Available:\n")
        for tool, available in available_tools.items():
            status = "[+]" if available else "[-]"
            f.write(f"  {status} {tool}\n")

        if not any_tsk_available:
            f.write("\n[NOTE] SleuthKit (TSK) binaries not found.\n")
            f.write("  Full disk-image analysis (partition table, filesystem, file listing)\n")
            f.write("  requires the SleuthKit binaries placed at:\n")
            f.write(f"  {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sleuthkit-4.12.1-win32', 'bin')}\n")
            f.write("  Ubuntu/Debian: sudo apt install sleuthkit\n")
            f.write("  CentOS/RHEL:   sudo yum install sleuthkit\n")
            f.write("  Windows:       https://github.com/sleuthkit/sleuthkit/releases\n")
            f.write("\n[COMPLETED WITHOUT TSK] Basic analysis performed:\n")
            f.write(f"  * File existence and integrity verified\n")
            f.write(f"  * MD5 and SHA-256 hashes computed\n")
            f.write(f"  * File metadata recorded (size, path, timestamp)\n")
            f.write(f"  * Results saved to: {case_folder}\n")

    print(f"[+] Autopsy analysis complete. Results saved in {case_folder}")
    print(f"[+] Summary report: {summary_file}")
    
    return True

# Allow running standalone
if __name__ == "__main__":
    main()
