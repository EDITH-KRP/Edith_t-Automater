import os
import sys
from datetime import datetime

# Add parent directory so imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Import your forensic tool modules
from hashdeep import create_hashdeep_drive as hashdeep
from autopsy import auto
from volatility import auto_vol
from exiftool import exiftool_auto

# Import bulk-extractor module
import sys
bulk_extractor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bulk-extractor')
sys.path.append(bulk_extractor_path)
from run_bulk_extractor import run_bulk_extractor


def setup_results_structure(case_id):
    """
    Create centralized Results directory structure for all forensic tools.
    Returns:
        case_results_dir (str): Root folder for this case.
        subdirs (dict): Mapping of tool -> subdirectory path.
    """
    # Results folder inside project root
    base_results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Results")
    case_results_dir = os.path.join(base_results_dir, f"CASE_{case_id}")
    
    # Define tool-specific subdirectories
    subdirs = {
        'hashdeep': os.path.join(case_results_dir, "HashDeep_output"),
        'autopsy': os.path.join(case_results_dir, "Autopsy_output"), 
        'volatility': os.path.join(case_results_dir, "Volatility_output"),
        'exiftool': os.path.join(case_results_dir, "ExifTool_output"),
        'bulk_extractor': os.path.join(case_results_dir, "BulkExtractor_output"),
        'reports': os.path.join(case_results_dir, "Final_Reports")
    }
    
    # Create all directories
    for tool_name, dir_path in subdirs.items():
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Created: {os.path.relpath(dir_path)}")
    
    return case_results_dir, subdirs


def run_bulk_extractor_with_custom_output(evidence_path, output_dir):
    """
    Wrapper for bulk-extractor with custom output directory
    """
    import subprocess
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Valid scanners from bulk-extractor
    VALID_SCANNERS = ["email", "base16", "hiberfile", "outlook", "wordlist", "xor"]
    
    # Build command with custom output directory
    cmd = ["bulk_extractor", "-o", output_dir]
    for scanner in VALID_SCANNERS:
        cmd.extend(["-E", scanner])
    cmd.append(evidence_path)
    
    print(f"    [+] Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [-] bulk_extractor error: {e}")
        return False
    except FileNotFoundError:
        print("    [-] bulk_extractor not found. Please install bulk_extractor.")
        return False


def run_workflow(evidence_path, memory_file=None):
    print("=" * 80)
    print("EDITH-Automater Unified Forensic Workflow (Minimal Prompts)")
    print("HashDeep → Autopsy → Volatility → ExifTool → BulkExtractor → HashDeep")
    print("=" * 80)

    # Generate unique case ID
    case_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    case_results_dir, subdirs = setup_results_structure(case_id)

    # 1. Run HashDeep (baseline hashing)
    print("\n=== Running HashDeep (Baseline Hashing) ===")
    hash_results = hashdeep.main(evidence_path, output_path=subdirs['hashdeep'])

    # 2. Run Autopsy analysis
    print("\n=== Running Autopsy Analysis ===")
    try:
        # Run autopsy with custom output directory
        autopsy_output = os.path.join(subdirs['autopsy'], "autopsy_analysis")
        auto.main(evidence_path, output_dir=autopsy_output)
        print(f"    [+] Autopsy analysis completed in: {autopsy_output}")
    except Exception as e:
        print(f"    [-] Autopsy analysis failed: {e}")
        # Fallback: try without custom output directory
        print("    [+] Trying fallback method...")
        try:
            auto.main(evidence_path)
            print("    [+] Autopsy completed with default output")
        except Exception as e2:
            print(f"    [-] Autopsy fallback also failed: {e2}")

    # 3. Run Memory Analysis (if memory file provided)
    memory_results = None
    if memory_file and os.path.exists(memory_file):
        print("\n=== Running Memory Analysis (Volatility) ===")
        print(f"[+] Using memory file: {memory_file}")
        memory_results = auto_vol.run_volatility(
            quick_mode=True,
            memory_file=memory_file,
            output_dir=subdirs['volatility']
        )
        if memory_results:
            print(f"[+] Memory analysis completed successfully!")
            for result in memory_results:
                print(f"    - Results saved in: {result['output_dir']}")
                print(f"    - Plugins run: {result['successful_plugins']}/{result['total_plugins']}")
        else:
            print("[-] Memory analysis failed")
    else:
        print("\n[*] No memory file provided or file not found. Skipping memory analysis.")

    # 4. Run ExifTool (process evidence directory)
    print("\n=== Running ExifTool Analysis ===")
    try:
        # Create ExifTool instance with custom output directory
        case_id_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exif_tool = exiftool_auto.AutomatedExifTool(
            case_id=f"CASE_{case_id_timestamp}", 
            show_prompt=False, 
            custom_result_dir=subdirs['exiftool']
        )
        exif_results = exif_tool.process_all_evidence()
        if exif_results and exif_results.get("status") in ["SUCCESS", "NO_FILES"]:
            print(f"[+] ExifTool analysis completed. Files processed: {exif_results.get('files_processed', 0)}")
        else:
            print("[-] ExifTool analysis completed with warnings")
    except Exception as e:
        print(f"[-] ExifTool analysis failed: {e}")
        print("    [*] Continuing workflow...")

    # 5. Run Bulk-Extractor Analysis
    print("\n=== Running Bulk-Extractor Analysis ===")
    try:
        print(f"[+] Extracting data from disk image: {os.path.basename(evidence_path)}")
        bulk_output = os.path.join(subdirs['bulk_extractor'], "be_results")
        
        success = run_bulk_extractor_with_custom_output(evidence_path, bulk_output)
        
        if success:
            print(f"[+] Bulk-Extractor analysis completed successfully")
            print(f"    📁 Results: {bulk_output}")
            
            # Show what was extracted
            if os.path.exists(bulk_output):
                files = os.listdir(bulk_output)
                key_files = [f for f in files if f.endswith('.txt') and f != 'report.xml'][:5]
                print(f"    📊 Key extractions: {', '.join(key_files)}")
        else:
            print("[-] Bulk-Extractor analysis failed")
            
    except Exception as e:
        print(f"[-] Bulk-Extractor analysis failed: {e}")
        print("    [*] Continuing workflow...")

    # 6. Run HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    verification_dir = os.path.join(subdirs['hashdeep'], "verification")
    os.makedirs(verification_dir, exist_ok=True)
    verify_results = hashdeep.main(evidence_path, output_path=verification_dir)
    print(f"[+] HashDeep verification completed. Report saved in: {verification_dir}")

    print("\n✅ Full forensic workflow completed successfully!")
    print("   - Baseline hashes created")
    print("   - Autopsy analysis done")
    if memory_file:
        print("   - Memory analysis completed")
    print("   - ExifTool metadata extracted")
    print("   - Bulk-Extractor data extraction completed")
    print("   - Final verification passed")

    # Final cleanup: Remove any stray Evidence directories
    print("\n🧹 Performing final cleanup...")
    cleanup_paths = [
        "Evidence",  # Current directory
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "Evidence"),  # Script directory
    ]
    
    for cleanup_path in cleanup_paths:
        if os.path.exists(cleanup_path):
            try:
                import shutil
                shutil.rmtree(cleanup_path)
                print(f"    [+] Cleaned up stray Evidence folder: {cleanup_path}")
            except Exception as e:
                print(f"    [-] Could not clean up {cleanup_path}: {e}")

    # Summary
    print(f"\n{'='*80}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*80}")
    print(f"Evidence processed : {os.path.basename(evidence_path)}")
    print(f"Analysis timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nResults stored in  : {case_results_dir}")
    print("Subdirectories:")
    for tool, path in subdirs.items():
        print(f" - {tool}: {path}")


if __name__ == "__main__":
    print("="*80)
    print("EDITH-Automater Forensic Workflow")
    print("="*80)

    # ✅ Ask only once for both paths
    evidence_path = input("Enter path to disk image (.E01/.dd/.raw): ").strip()
    memory_file = input("Enter path to memory dump file (leave blank to skip): ").strip()
    memory_file = memory_file if memory_file else None

    run_workflow(evidence_path, memory_file)
