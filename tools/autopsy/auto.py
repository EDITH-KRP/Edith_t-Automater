#!/usr/bin/env python3
import os
import subprocess
import hashlib
import json
import datetime

def run_cmd(cmd):
    """Run a shell command and return stdout"""
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"[!] Error running: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def compute_hashes(file_path):
    """Compute MD5 & SHA256 hashes"""
    hashes = {"md5": None, "sha256": None}
    with open(file_path, "rb") as f:
        data = f.read()
        hashes["md5"] = hashlib.md5(data).hexdigest()
        hashes["sha256"] = hashlib.sha256(data).hexdigest()
    return hashes

def get_partition_offset(image_path):
    """Parse mmls output to get NTFS/ExFAT offset"""
    output = run_cmd(f"mmls {image_path}")
    offset = None
    for line in output.splitlines():
        if "NTFS" in line or "exFAT" in line:
            parts = line.split()
            offset = parts[2]  # Start sector
            break
    return offset, output

def main(image_path=None):
    """
    Main function for forensic analysis.
    If image_path is None, ask for input.
    """
    if image_path is None:
        image_path = input("Enter path to evidence image (.E01/.dd): ").strip()

    # Convert to absolute path
    image_path = os.path.abspath(image_path)

    # Check file exists
    if not os.path.exists(image_path):
        print(f"[!] Error: File not found: {image_path}")
        return

    # Setup folder
    case_folder = os.path.join("Evidence")
    os.makedirs(case_folder, exist_ok=True)

    # Hash evidence
    print("[*] Computing hashes...")
    hashes = compute_hashes(image_path)

    # Get partition offset
    print("[*] Running mmls...")
    offset, mmls_output = get_partition_offset(image_path)
    if not offset:
        print("[!] Could not detect partition offset!")
        return
    print(f"[*] Detected partition offset: {offset}")

    # Save partition table
    with open(os.path.join(case_folder, "partitions.json"), "w") as f:
        f.write(mmls_output)

    # Run fsstat
    print("[*] Running fsstat...")
    fsstat_out = run_cmd(f"fsstat -o {offset} {image_path}")
    with open(os.path.join(case_folder, "fsstat.json"), "w") as f:
        f.write(fsstat_out)

    # Run fls
    print("[*] Running fls...")
    fls_out = run_cmd(f"fls -o {offset} -r {image_path}")
    with open(os.path.join(case_folder, "files.txt"), "w") as f:
        f.write(fls_out)

    # Recover files
    print("[*] Running tsk_recover...")
    recover_dir = os.path.join(case_folder, "recovered_files")
    os.makedirs(recover_dir, exist_ok=True)
    run_cmd(f"tsk_recover -o {offset} {image_path} {recover_dir}")

    # Save metadata JSON
    metadata = {
        "image_path": image_path,
        "hashes": hashes,
        "partition_offset": offset,
        "date": datetime.datetime.now().isoformat()
    }
    with open(os.path.join(case_folder, "case_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)

    print(f"[+] Analysis complete. Results saved in {case_folder}")

# Allow running standalone
if __name__ == "__main__":
    main()
