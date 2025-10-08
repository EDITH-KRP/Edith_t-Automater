#!/usr/bin/env python3
"""
Simple script runner that uses existing case directory
"""
import os
import sys
from datetime import datetime

# Add paths
script_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(script_dir)
base_dir = os.path.dirname(tools_dir)
sys.path.append(base_dir)

def run_script3_with_existing_case(evidence_path, memory_path, case_dir):
    """Run script_3 workflow using existing case directory"""
    
    print("=" * 80)
    print("EDITH-Automater Forensic Workflow (Using Existing Case)")
    print("=" * 80)
    print(f"Evidence: {evidence_path}")
    print(f"Memory: {memory_path}")
    print(f"Case Directory: {case_dir}")
    print("=" * 80)

    # Import required modules
    try:
        from hashdeep import create_hashdeep_drive as hashdeep
        from autopsy import auto
        from volatility import auto_vol
        from exiftool import exiftool_auto
        sys.path.append(os.path.join(tools_dir, 'bulk-extractor'))
        from run_bulk_extractor import run_bulk_extractor
        import subprocess
    except ImportError as e:
        print(f"Error importing modules: {e}")
        return False

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

    success_count = 0
    total_tools = 6

    # 1. HashDeep
    print("\n=== Running HashDeep (Baseline Hashing) ===")
    try:
        hash_results = hashdeep.main(evidence_path, output_path=subdirs['hashdeep'])
        print("[+] HashDeep baseline completed")
        success_count += 1
    except Exception as e:
        print(f"[-] HashDeep failed: {e}")

    # 2. Autopsy
    print("\n=== Running Autopsy Analysis ===")
    try:
        autopsy_output = os.path.join(subdirs['autopsy'], "autopsy_analysis")
        auto.main(evidence_path, output_dir=autopsy_output)
        print(f"[+] Autopsy completed: {autopsy_output}")
        success_count += 1
    except Exception as e:
        print(f"[-] Autopsy failed: {e}")

    # 3. Memory Analysis
    if memory_path and os.path.exists(memory_path):
        print("\n=== Running Memory Analysis (Volatility) ===")
        try:
            memory_results = auto_vol.run_volatility(
                quick_mode=True,
                memory_file=memory_path,
                output_dir=subdirs['volatility']
            )
            if memory_results:
                print("[+] Memory analysis completed")
                success_count += 1
        except Exception as e:
            print(f"[-] Memory analysis failed: {e}")
    else:
        print("\n[*] No memory file - skipping volatility")
        success_count += 1  # Count as success if no memory file

    # 4. ExifTool
    print("\n=== Running ExifTool Analysis ===")
    try:
        exif_tool = exiftool_auto.AutomatedExifTool(
            case_id="CASE_AUTO", 
            show_prompt=False, 
            custom_result_dir=subdirs['exiftool']
        )
        exif_results = exif_tool.process_all_evidence()
        print("[+] ExifTool completed")
        success_count += 1
    except Exception as e:
        print(f"[-] ExifTool failed: {e}")

    # 5. Bulk-Extractor
    print("\n=== Running Bulk-Extractor Analysis ===")
    try:
        bulk_output = os.path.join(subdirs['bulk_extractor'], "be_results")
        
        # Simple bulk extractor command
        cmd = ["bulk_extractor", "-o", bulk_output, evidence_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[+] Bulk-Extractor completed")
            success_count += 1
        else:
            print("[-] Bulk-Extractor failed")
    except Exception as e:
        print(f"[-] Bulk-Extractor failed: {e}")

    # 6. HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    try:
        verification_dir = os.path.join(subdirs['hashdeep'], "verification")
        os.makedirs(verification_dir, exist_ok=True)
        verify_results = hashdeep.main(evidence_path, output_path=verification_dir)
        print("[+] HashDeep verification completed")
        success_count += 1
    except Exception as e:
        print(f"[-] HashDeep verification failed: {e}")

    # Summary
    print(f"\n{'='*80}")
    print("FORENSIC ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Evidence processed: {os.path.basename(evidence_path)}")
    print(f"Tools completed: {success_count}/{total_tools}")
    print(f"Results directory: {case_dir}")
    print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_count >= (total_tools // 2)  # Success if at least half completed

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: simple_script3_runner.py <evidence_path> <memory_path> <case_dir>")
        sys.exit(1)
    
    evidence_path = sys.argv[1]
    memory_path = sys.argv[2] if sys.argv[2] != "None" else None
    case_dir = sys.argv[3]
    
    success = run_script3_with_existing_case(evidence_path, memory_path, case_dir)
    sys.exit(0 if success else 1)