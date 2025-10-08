#!/usr/bin/env python3
import sys
import os
from datetime import datetime

# Add path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the original script_3 module
import script_3

# Override setup_results_structure to use existing case directory
def use_existing_case_directory(existing_case_dir):
    case_results_dir = existing_case_dir
    
    subdirs = {
        'hashdeep': os.path.join(case_results_dir, "HashDeep_output"),
        'autopsy': os.path.join(case_results_dir, "Autopsy_output"), 
        'volatility': os.path.join(case_results_dir, "Volatility_output"),
        'exiftool': os.path.join(case_results_dir, "ExifTool_output"),
        'bulk_extractor': os.path.join(case_results_dir, "BulkExtractor_output"),
        'reports': os.path.join(case_results_dir, "Final_Reports")
    }
    
    # Ensure all directories exist
    for tool_name, dir_path in subdirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Using existing: {os.path.relpath(dir_path)}")
    
    return case_results_dir, subdirs

# Modified workflow function
def run_workflow_existing(evidence_path, memory_file, case_dir):
    print("=" * 80)
    print("EDITH-Automater Unified Forensic Workflow (Using Existing Case)")
    print("HashDeep → Autopsy → Volatility → ExifTool → BulkExtractor → HashDeep")
    print("=" * 80)

    print(f"Using existing case directory: {case_dir}")
    
    case_results_dir, subdirs = use_existing_case_directory(case_dir)

    # Import required modules from script_3
    from hashdeep import create_hashdeep_drive as hashdeep
    from autopsy import auto
    from volatility import auto_vol
    from exiftool import exiftool_auto
    import subprocess

    # 1. HashDeep
    print("\n=== Running HashDeep (Baseline Hashing) ===")
    try:
        hash_results = hashdeep.main(evidence_path, output_path=subdirs['hashdeep'])
    except Exception as e:
        print(f"[-] HashDeep failed: {e}")

    # 2. Autopsy
    print("\n=== Running Autopsy Analysis ===")
    try:
        autopsy_output = os.path.join(subdirs['autopsy'], "autopsy_analysis")
        auto.main(evidence_path, output_dir=autopsy_output)
        print(f"[+] Autopsy analysis completed in: {autopsy_output}")
    except Exception as e:
        print(f"[-] Autopsy analysis failed: {e}")

    # 3. Memory Analysis
    if memory_file and os.path.exists(memory_file):
        print("\n=== Running Memory Analysis (Volatility) ===")
        try:
            memory_results = auto_vol.run_volatility(
                quick_mode=True,
                memory_file=memory_file,
                output_dir=subdirs['volatility']
            )
            if memory_results:
                print(f"[+] Memory analysis completed!")
        except Exception as e:
            print(f"[-] Memory analysis failed: {e}")
    else:
        print("\n[*] No memory file provided or file not found.")

    # 4. ExifTool
    print("\n=== Running ExifTool Analysis ===")
    try:
        exif_tool = exiftool_auto.AutomatedExifTool(
            case_id="CASE_AUTO", 
            show_prompt=False, 
            custom_result_dir=subdirs['exiftool']
        )
        exif_results = exif_tool.process_all_evidence()
        print(f"[+] ExifTool analysis completed.")
    except Exception as e:
        print(f"[-] ExifTool analysis failed: {e}")

    # 5. Bulk-Extractor
    print("\n=== Running Bulk-Extractor Analysis ===")
    try:
        bulk_output = os.path.join(subdirs['bulk_extractor'], "be_results")
        success = script_3.run_bulk_extractor_with_custom_output(evidence_path, bulk_output)
        if success:
            print(f"[+] Bulk-Extractor completed successfully")
    except Exception as e:
        print(f"[-] Bulk-Extractor failed: {e}")

    # 6. HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    try:
        verification_dir = os.path.join(subdirs['hashdeep'], "verification")
        os.makedirs(verification_dir, exist_ok=True)
        verify_results = hashdeep.main(evidence_path, output_path=verification_dir)
        print(f"[+] HashDeep verification completed.")
    except Exception as e:
        print(f"[-] HashDeep verification failed: {e}")

    print("\n✅ Forensic workflow completed!")
    print(f"Results stored in: {case_results_dir}")

# Run the workflow
if __name__ == "__main__":
    evidence_path = "/home/shirish/Project/Zetpeak/Autopsy/charlie.E01"
    memory_file = "/home/shirish/Downloads/memory.mem" if "/home/shirish/Downloads/memory.mem" != "None" else None
    case_dir = "/home/shirish/Project/Zetpeak/Edith_t-Automater/Results/CASE_20251008_215332"
    
    run_workflow_existing(evidence_path, memory_file, case_dir)
