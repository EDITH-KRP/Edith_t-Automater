#!/usr/bin/env python3
import os
import subprocess
import hashlib
import json
import datetime

def run_cmd(cmd):
    """Run a shell command and return stdout"""
    try:
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
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
    available_tools = check_tools()
    
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
    if available_tools.get('mmls', False):
        # Get partition offset
        print("[*] Running mmls...")
        offset, mmls_output = get_partition_offset(image_path)
        if offset:
            print(f"[*] Detected partition offset: {offset}")
            file_info["partition_offset"] = offset
            
            # Save partition table
            with open(os.path.join(case_folder, "partitions.txt"), "w") as f:
                f.write(mmls_output)
        else:
            print("[!] Could not detect partition offset!")
            file_info["partition_offset"] = None
    else:
        print("[!] mmls not available - skipping partition analysis")
        offset = None

    if available_tools.get('fsstat', False) and offset:
        # Run fsstat
        print("[*] Running fsstat...")
        fsstat_out = run_cmd(f"fsstat -o {offset} {image_path}")
        if fsstat_out:
            with open(os.path.join(case_folder, "fsstat.txt"), "w") as f:
                f.write(fsstat_out)
    else:
        print("[!] fsstat not available or no partition offset - skipping filesystem analysis")

    if available_tools.get('fls', False) and offset:
        # Run fls
        print("[*] Running fls...")
        fls_out = run_cmd(f"fls -o {offset} -r {image_path}")
        if fls_out:
            with open(os.path.join(case_folder, "files.txt"), "w") as f:
                f.write(fls_out)
    else:
        print("[!] fls not available or no partition offset - skipping file listing")

    if available_tools.get('tsk_recover', False) and offset:
        # Recover files
        print("[*] Running tsk_recover...")
        recover_dir = os.path.join(case_folder, "recovered_files")
        os.makedirs(recover_dir, exist_ok=True)
        run_cmd(f"tsk_recover -o {offset} {image_path} {recover_dir}")
    else:
        print("[!] tsk_recover not available or no partition offset - skipping file recovery")

    # Always save metadata JSON
    with open(os.path.join(case_folder, "autopsy_analysis.json"), "w") as f:
        json.dump(file_info, f, indent=4)

    # Create summary report
    summary_file = os.path.join(case_folder, "autopsy_summary.txt")
    with open(summary_file, "w") as f:
        f.write("EDITH-Automater Autopsy Analysis Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Evidence File: {image_path}\n")
        f.write(f"File Size: {file_info['file_size']} bytes\n")
        f.write(f"MD5 Hash: {hashes['md5']}\n")
        f.write(f"SHA256 Hash: {hashes['sha256']}\n")
        f.write(f"Analysis Date: {file_info['timestamp']}\n")
        f.write("\nTools Available:\n")
        for tool, available in available_tools.items():
            status = "✓" if available else "✗"
            f.write(f"  {status} {tool}\n")
        
        if not any(available_tools.values()):
            f.write("\nNOTE: No TSK tools found. Install 'sleuthkit' package for full analysis.\n")
            f.write("Ubuntu/Debian: sudo apt install sleuthkit\n")
            f.write("CentOS/RHEL: sudo yum install sleuthkit\n")

    print(f"[+] Autopsy analysis complete. Results saved in {case_folder}")
    print(f"[+] Summary report: {summary_file}")
    
    return True

# Allow running standalone
if __name__ == "__main__":
    main()
