#!/usr/bin/env python3
"""
Automated forensic analysis runner
Simplified version of script_3.py for orchestrator use
"""

import os
import sys
import glob
from datetime import datetime

# Add parent directory so imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Add shared utilities
shared_dir = os.path.join(os.path.dirname(BASE_DIR), "shared")
sys.path.append(shared_dir)
from case_utils import case_manager

# Import your forensic tool modules
from hashdeep import create_hashdeep_drive as hashdeep
from autopsy import auto
from volatility import auto_vol
from exiftool import exiftool_auto

def run_automated_forensic_analysis(evidence_path, memory_file=None, case_id=None):
    """
    Run automated forensic analysis without user interaction
    """
    print("="*84)
    print("EDITH-Automater Automated Forensic Analysis")
    print("="*84)
    
    # Get the target case directory
    if case_id:
        # Use specific case
        script_dir = os.path.dirname(os.path.abspath(__file__))
        results_base = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Results")
        case_dir = os.path.join(results_base, case_id)
        if not os.path.exists(case_dir):
            print(f"[ERROR] Case directory not found: {case_dir}")
            return False
        print(f"[INFO] Using specified case: {case_id}")
    else:
        # Use latest case
        case_dir, case_id = case_manager.find_latest_case_directory()
        if not case_dir:
            print("[ERROR] No case directory found")
            return False
        print(f"[INFO] Using latest case: {case_id}")
    
    # Ensure case structure exists
    subdirs = case_manager.ensure_case_structure(case_dir)
    
    print(f"[INFO] Case Directory: {case_dir}")
    print(f"[INFO] Evidence: {evidence_path}")
    if memory_file:
        print(f"[INFO] Memory: {memory_file}")
    
    # Verify evidence file exists
    if not os.path.exists(evidence_path):
        print(f"[ERROR] Evidence file not found: {evidence_path}")
        return False
    
    if memory_file and not os.path.exists(memory_file):
        print(f"[WARNING] Memory file not found: {memory_file}")
        memory_file = None
    
    print("="*84)
    
    try:
        # 1. Run HashDeep Analysis (Initial)
        print("\n=== Running Initial HashDeep Analysis ===")
        try:
            result = hashdeep.main(evidence_path, subdirs['hashdeep'])
            if result and result.get('result') and result['result'].status == "SUCCESS":
                print("[SUCCESS] HashDeep initial analysis completed")
            else:
                print("[WARNING] HashDeep initial analysis had issues")
        except Exception as e:
            print(f"[ERROR] HashDeep analysis failed: {e}")
        
        # 2. Run Autopsy Analysis
        print("\n=== Running Autopsy Analysis ===")
        try:
            auto.main(evidence_path, subdirs['autopsy'])
            print("[SUCCESS] Autopsy analysis completed")
        except Exception as e:
            print(f"[ERROR] Autopsy analysis failed: {e}")
        
        # 3. Run Volatility Analysis (if memory file provided)
        if memory_file:
            print("\n=== Running Volatility Analysis ===")
            try:
                # Copy memory file to volatility mem folder
                volatility_mem_dir = os.path.join(os.path.dirname(__file__), "..", "volatility", "mem")
                os.makedirs(volatility_mem_dir, exist_ok=True)
                
                import shutil
                mem_filename = os.path.basename(memory_file)
                target_mem_path = os.path.join(volatility_mem_dir, mem_filename)
                
                if not os.path.exists(target_mem_path):
                    print(f"[INFO] Copying memory file to volatility directory...")
                    shutil.copy2(memory_file, target_mem_path)
                
                # Run volatility
                auto_vol.main(subdirs['volatility'])
                print("[SUCCESS] Volatility analysis completed")
            except Exception as e:
                print(f"[ERROR] Volatility analysis failed: {e}")
        else:
            print("\n=== Skipping Volatility Analysis (no memory file) ===")
        
        # 4. Run ExifTool Analysis
        print("\n=== Running ExifTool Analysis ===")
        try:
            case_id_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            exif_tool = exiftool_auto.AutomatedExifTool(
                case_id=f"CASE_{case_id_timestamp}", 
                show_prompt=False, 
                custom_result_dir=subdirs['exiftool']
            )
            exif_results = exif_tool.process_all_evidence()
            if exif_results and exif_results.get("status") in ["SUCCESS", "NO_FILES"]:
                print(f"[SUCCESS] ExifTool analysis completed. Files processed: {exif_results.get('files_processed', 0)}")
            else:
                print("[WARNING] ExifTool analysis completed with warnings")
        except Exception as e:
            print(f"[ERROR] ExifTool analysis failed: {e}")
        
        # 5. Run Final HashDeep Verification
        print("\n=== Running Final HashDeep Verification ===")
        try:
            verification_dir = os.path.join(case_dir, "Final_Hash_Verification")
            os.makedirs(verification_dir, exist_ok=True)
            result = hashdeep.main(evidence_path, verification_dir)
            if result and result.get('result') and result['result'].status == "SUCCESS":
                print("[SUCCESS] Final HashDeep verification completed")
            else:
                print("[WARNING] Final HashDeep verification had issues")
        except Exception as e:
            print(f"[ERROR] Final verification failed: {e}")
        
        print("\n[SUCCESS] Automated forensic analysis completed!")
        print(f"[INFO] Results saved to: {case_dir}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Forensic analysis failed: {e}")
        return False

if __name__ == "__main__":
    # Get parameters from environment variables
    evidence_path = os.environ.get('EDITH_EVIDENCE_PATH')
    memory_file = os.environ.get('EDITH_MEMORY_PATH')
    case_id = os.environ.get('EDITH_CASE_ID')
    
    if not evidence_path:
        print("[ERROR] EDITH_EVIDENCE_PATH environment variable required")
        sys.exit(1)
    
    success = run_automated_forensic_analysis(evidence_path, memory_file, case_id)
    sys.exit(0 if success else 1)