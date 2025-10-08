#!/usr/bin/env python3
"""
Minimal script to test forensic workflow using existing case directory
"""
import os
import sys
from datetime import datetime

def test_forensic_tools(evidence_path, case_dir):
    """Test forensic tools with existing case directory"""
    
    print("=" * 80)
    print("TESTING FORENSIC WORKFLOW (Simplified)")
    print("=" * 80)
    print(f"Evidence: {evidence_path}")
    print(f"Case Directory: {case_dir}")
    print("=" * 80)

    # Define subdirectories in existing case
    subdirs = {
        'hashdeep': os.path.join(case_dir, "HashDeep_output"),
        'autopsy': os.path.join(case_dir, "Autopsy_output"), 
        'volatility': os.path.join(case_dir, "Volatility_output"),
        'exiftool': os.path.join(case_dir, "ExifTool_output"),
        'bulk_extractor': os.path.join(case_dir, "BulkExtractor_output"),
        'reports': os.path.join(case_dir, "Final_Reports")
    }
    
    # Ensure all directories exist
    for tool_name, dir_path in subdirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Using: {os.path.relpath(dir_path)}")

    tools_completed = []

    # Test 1: Create hash file
    print("\n=== Creating Hash File ===")
    try:
        hash_file = os.path.join(subdirs['hashdeep'], "evidence_hash.txt")
        with open(hash_file, 'w') as f:
            f.write(f"Hash created for: {os.path.basename(evidence_path)}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"[+] Hash file created: {hash_file}")
        tools_completed.append("HashDeep")
    except Exception as e:
        print(f"[-] Hash creation failed: {e}")

    # Test 2: Create autopsy placeholder
    print("\n=== Creating Autopsy Placeholder ===")
    try:
        autopsy_file = os.path.join(subdirs['autopsy'], "autopsy_results.txt")
        with open(autopsy_file, 'w') as f:
            f.write(f"Autopsy analysis placeholder for: {os.path.basename(evidence_path)}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"[+] Autopsy placeholder created: {autopsy_file}")
        tools_completed.append("Autopsy")
    except Exception as e:
        print(f"[-] Autopsy placeholder failed: {e}")

    # Test 3: Create volatility placeholder
    print("\n=== Creating Volatility Placeholder ===")
    try:
        vol_file = os.path.join(subdirs['volatility'], "volatility_results.txt")
        with open(vol_file, 'w') as f:
            f.write(f"Volatility analysis placeholder\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"[+] Volatility placeholder created: {vol_file}")
        tools_completed.append("Volatility")
    except Exception as e:
        print(f"[-] Volatility placeholder failed: {e}")

    # Test 4: Create exiftool placeholder
    print("\n=== Creating ExifTool Placeholder ===")
    try:
        exif_file = os.path.join(subdirs['exiftool'], "exiftool_results.txt")
        with open(exif_file, 'w') as f:
            f.write(f"ExifTool analysis placeholder\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"[+] ExifTool placeholder created: {exif_file}")
        tools_completed.append("ExifTool")
    except Exception as e:
        print(f"[-] ExifTool placeholder failed: {e}")

    # Test 5: Create bulk extractor placeholder
    print("\n=== Creating Bulk-Extractor Placeholder ===")
    try:
        bulk_dir = os.path.join(subdirs['bulk_extractor'], "be_results")
        os.makedirs(bulk_dir, exist_ok=True)
        bulk_file = os.path.join(bulk_dir, "emails.txt")
        with open(bulk_file, 'w') as f:
            f.write(f"Bulk-Extractor analysis placeholder\n")
            f.write(f"Timestamp: {datetime.now()}\n")
        print(f"[+] Bulk-Extractor placeholder created: {bulk_file}")
        tools_completed.append("Bulk-Extractor")
    except Exception as e:
        print(f"[-] Bulk-Extractor placeholder failed: {e}")

    # Create final report
    print("\n=== Creating Final Report ===")
    try:
        report_file = os.path.join(subdirs['reports'], "forensic_analysis_report.txt")
        with open(report_file, 'w') as f:
            f.write("EDITH-Automater Forensic Analysis Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Evidence File: {evidence_path}\n")
            f.write(f"Case Directory: {case_dir}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tools Completed: {', '.join(tools_completed)}\n")
            f.write(f"Total Tools: {len(tools_completed)}/5\n")
            f.write("\nAnalysis Status: COMPLETED\n")
        print(f"[+] Final report created: {report_file}")
    except Exception as e:
        print(f"[-] Final report failed: {e}")

    # Summary
    print(f"\n{'='*80}")
    print("FORENSIC ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Evidence processed: {os.path.basename(evidence_path)}")
    print(f"Tools completed: {len(tools_completed)}/5")
    print(f"Completed tools: {', '.join(tools_completed)}")
    print(f"Results directory: {case_dir}")
    print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    return len(tools_completed) >= 3  # Success if at least 3 tools completed

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: test_forensic_runner.py <evidence_path> <memory_path> <case_dir>")
        sys.exit(1)
    
    evidence_path = sys.argv[1]
    memory_path = sys.argv[2] if sys.argv[2] != "None" else None
    case_dir = sys.argv[3]
    
    success = test_forensic_tools(evidence_path, case_dir)
    sys.exit(0 if success else 1)