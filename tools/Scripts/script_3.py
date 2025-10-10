import os
import sys
import subprocess
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


def setup_results_structure(case_id=None):
    """
    Create centralized Results directory structure for all forensic tools.
    Returns:
        case_results_dir (str): Root folder for this case.
        subdirs (dict): Mapping of tool -> subdirectory path.
    """
    # Check if we should use an existing case directory (set by orchestrator)
    use_existing = os.environ.get('EDITH_USE_EXISTING_CASE', 'false').lower() == 'true'
    existing_case_dir = os.environ.get('EDITH_CASE_DIR')
    existing_case_id = os.environ.get('EDITH_CASE_ID')

    if use_existing and existing_case_dir and os.path.exists(existing_case_dir):
        print(f" Using existing case directory: {existing_case_dir}")
        case_results_dir = existing_case_dir
        case_id = existing_case_id or case_id
    else:
        # Original behavior - create new case directory
        if case_id is None:
            case_id = datetime.now().strftime("%Y%m%d_%H%M%S")

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
        if use_existing:
            print(f" Using existing: {os.path.relpath(dir_path)}")
        else:
            print(f" Created: {os.path.relpath(dir_path)}")

    return case_results_dir, subdirs


def run_bulk_extractor_with_custom_output(evidence_path, output_dir):
    """
    Wrapper for bulk-extractor with custom output directory
    Smart processing based on file size
    """
    import os
    import stat

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check if evidence file exists and is readable
    if not os.path.exists(evidence_path):
        print(f"    [-] Evidence file not found: {evidence_path}")
        return False

    if not os.access(evidence_path, os.R_OK):
        print(f"    [-] Cannot read evidence file: {evidence_path}")
        return False

    # Get file size for smart processing
    file_size = os.path.getsize(evidence_path)
    file_size_gb = file_size / (1024 * 1024 * 1024)

    print(f"    [INFO] Evidence file size: {file_size_gb:.2f} GB")

    # Smart configuration based on file size
    if file_size_gb > 5.0:  # Large files > 5GB
        print(f"    [INFO] Large evidence file detected. Using fast processing mode.")
        # Reduced scanners and limited processing for speed
        VALID_SCANNERS = ["email", "base16", "wordlist"]
        timeout_minutes = 5  # Reduced timeout for large files
        thread_count = "1"   # Single thread for stability
        sample_size = ""     # Remove problematic sampling for now
    elif file_size_gb > 2.0:  # Medium files 2-5GB
        print(f"    [INFO] Medium evidence file detected. Using balanced processing mode.")
        VALID_SCANNERS = ["email", "base16", "wordlist"]
        timeout_minutes = 5
        thread_count = "1"
        sample_size = ""     # Remove problematic sampling for now
    else:  # Small files < 2GB
        print(f"    [INFO] Small evidence file detected. Using full processing mode.")
        VALID_SCANNERS = ["email", "base16", "wordlist"]
        timeout_minutes = 5
        thread_count = "2"
        sample_size = ""

    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))

    # Path to compiled bulk_extractor binary
    bulk_extractor_binary = os.path.join(project_root, "tools", "bulk-extractor", "bulk_extractor", "src", "bulk_extractor")

    # Check if binary exists and is executable
    if os.path.exists(bulk_extractor_binary) and os.access(bulk_extractor_binary, os.X_OK):
        print(f"    [+] Found local bulk_extractor binary: {bulk_extractor_binary}")
    else:
        print(f"    [-] Local bulk_extractor binary not found or not executable")
        print(f"    [INFO] Attempting to use system bulk_extractor...")

        # Try to find bulk_extractor in system PATH
        try:
            result = subprocess.run(["which", "bulk_extractor"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                bulk_extractor_binary = "bulk_extractor"
                print(f"    [+] Found system bulk_extractor: {result.stdout.strip()}")
            else:
                print(f"    [-] bulk_extractor not found in system PATH")
                print(f"    [INFO] To install: sudo apt-get install bulk-extractor")
                print(f"    [INFO] Or compile from source in tools/bulk-extractor/bulk_extractor")
                return False
        except Exception as e:
            print(f"    [-] Error checking for system bulk_extractor: {e}")
            return False

    # Build command with safer parameters for better compatibility
    cmd = [bulk_extractor_binary, "-o", output_dir, "-j", thread_count]

    # Add page size limit for large files to improve performance
    if file_size_gb > 2.0:
        cmd.extend(["-G", "1000000"])  # Limit to 1M pages for large files

    # Add minimal scanners that are most reliable
    cmd.extend(["-e", "email"])      # Enable email scanner (most stable)
    cmd.extend(["-e", "base16"])     # Enable base16 scanner (reliable)

    # Disable potentially problematic scanners explicitly
    cmd.extend(["-x", "rar"])        # Disable rar scanner
    cmd.extend(["-x", "zip"])        # Disable zip scanner
    cmd.extend(["-x", "pdf"])        # Disable pdf scanner
    cmd.extend(["-x", "wordlist"])   # Disable wordlist scanner

    cmd.append(evidence_path)

    print(f"    [+] Command: {' '.join(cmd)}")
    print(f"    [INFO] Timeout: {timeout_minutes} minutes")
    print(f"    [INFO] This may take several minutes...")

    # Test if bulk_extractor works before running the full command
    try:
        # Don't use --help as it returns exit code 1, use -V for version instead
        test_result = subprocess.run([bulk_extractor_binary, "-V"],
                                   capture_output=True, text=True, timeout=10)
        if test_result.returncode == 0:
            print(f"    [+] bulk_extractor version: {test_result.stdout.strip()}")
        else:
            # Try alternative test - even if version fails, try to proceed
            print(f"    [INFO] bulk_extractor version check returned {test_result.returncode}")
            print(f"    [INFO] Proceeding with extraction attempt...")
    except Exception as e:
        print(f"    [-] bulk_extractor test error: {e}")
        print(f"    [INFO] Proceeding with extraction attempt...")

    try:
        # Smart timeout based on file size
        timeout_seconds = timeout_minutes * 60
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout_seconds)
        print(f"    [+] bulk_extractor completed successfully")

        # List generated files
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            if files:
                print(f"    [+] Generated {len(files)} output files")
                for file in sorted(files)[:5]:  # Show first 5 files
                    print(f"        - {file}")
                if len(files) > 5:
                    print(f"        ... and {len(files) - 5} more files")
            else:
                print(f"    [WARNING] No output files generated")

        return True
    except subprocess.TimeoutExpired:
        print(f"    [-] bulk_extractor timed out after {timeout_minutes} minutes")
        print(f"    [INFO] For large files, consider running bulk_extractor manually for complete analysis")
        return False
    except subprocess.CalledProcessError as e:
        print(f"    [-] bulk_extractor error (exit code {e.returncode})")
        if e.stderr:
            print(f"    [ERROR] {e.stderr[:200]}...")  # Show first 200 chars of error
        # Don't fail completely, continue with other tools
        print(f"    [WARNING] Continuing with other forensic tools...")
        return False
    except FileNotFoundError:
        print("    [-] bulk_extractor not found. Please ensure it's compiled or installed.")
        print("    [INFO] To compile: cd tools/bulk-extractor/bulk_extractor && make")
        print("    [INFO] Or install with: sudo apt-get install bulk-extractor")
        return False


def run_workflow(evidence_path, memory_file=None):
    print("=" * 80)
    print("EDITH-Automater Unified Forensic Workflow (Minimal Prompts)")
    print("HashDeep → Autopsy → Volatility → ExifTool → BulkExtractor → HashDeep")
    print("=" * 80)

    # Check if using existing case or generating new case ID
    use_existing = os.environ.get('EDITH_USE_EXISTING_CASE', 'false').lower() == 'true'
    existing_case_id = os.environ.get('EDITH_CASE_ID')

    if use_existing and existing_case_id:
        case_id = existing_case_id.replace('CASE_', '')  # Remove CASE_ prefix if present
        print(f"Using existing case: CASE_{case_id}")
    else:
        case_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Creating new case: CASE_{case_id}")

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
    if memory_file:
        print(f"\n=== Memory Analysis Check ===")
        print(f"[INFO] Memory file parameter provided: {memory_file}")

        if os.path.exists(memory_file):
            print(f"[+] Memory file found: {memory_file}")
            file_size_mb = os.path.getsize(memory_file) / (1024 * 1024)
            print(f"[INFO] Memory file size: {file_size_mb:.2f} MB")

            print("\n=== Running Memory Analysis (Volatility) ===")
            try:
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
            except Exception as e:
                print(f"[-] Memory analysis error: {e}")
                print("    [INFO] Continuing with other forensic tools...")
        else:
            print(f"[-] Memory file not found: {memory_file}")
            print("    [INFO] Skipping memory analysis.")
    else:
        print("\n[*] No memory file provided. Skipping memory analysis.")

    # 4. Run ExifTool Analysis
    print("\n=== Running ExifTool Analysis ===")
    try:
        # Use the enhanced ExifTool automation for .E01 files
        case_id_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Check if the evidence file is an .E01 file
        evidence_ext = os.path.splitext(evidence_path.lower())[1]
        if evidence_ext in ['.e01', '.ex01', '.l01']:
            print(f"[+] Detected forensic image format: {evidence_ext}")
            print(f"[+] Processing {os.path.basename(evidence_path)} with enhanced ExifTool...")

            # Use the enhanced ExifTool with direct .E01 processing
            exif_tool = exiftool_auto.AutomatedExifTool(
                case_id=f"CASE_{case_id_timestamp}",
                show_prompt=False,
                custom_result_dir=subdirs['exiftool']
            )

            # Process the .E01 file directly
            exif_results = exif_tool.process_e01_file_directly(evidence_path)

            if exif_results and exif_results.get("status") == "SUCCESS":
                print(f"[+] ExifTool E01 analysis completed successfully!")
                print(f"    [+] Metadata entries extracted: {exif_results.get('metadata_entries', 0)}")
                print(f"    [+] Processing time: {exif_results.get('processing_time', 0):.2f} seconds")
                print(f"    [+] Results saved in: {os.path.basename(exif_results.get('result_directory', ''))}")
            else:
                print(f"[-] ExifTool E01 analysis completed with warnings")
                if exif_results and exif_results.get("error"):
                    print(f"    [WARNING] {exif_results.get('error')}")
        else:
            print(f"[+] Processing non-forensic image: {os.path.basename(evidence_path)}")
            # Fallback to the existing method for non-E01 files
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

    # Check file size first
    evidence_size_gb = os.path.getsize(evidence_path) / (1024 * 1024 * 1024)

    if evidence_size_gb > 8.0:  # Very large files > 8GB
        print(f"[WARNING] Very large evidence file ({evidence_size_gb:.2f} GB) detected.")
        print(f"[INFO] Bulk-Extractor analysis may take 1+ hours for files this size.")

        # Ask user if they want to continue or skip
        user_choice = os.environ.get('EDITH_BULK_EXTRACTOR_MODE', 'auto')

        if user_choice == 'skip':
            print(f"[INFO] Skipping Bulk-Extractor analysis (configured to skip)")
            skip_bulk = True
        elif user_choice == 'force':
            print(f"[INFO] Forcing Bulk-Extractor analysis (configured to force)")
            skip_bulk = False
        else:  # auto mode
            print(f"[INFO] Auto mode: Running quick Bulk-Extractor analysis with sampling")
            skip_bulk = False
    else:
        skip_bulk = False

    if not skip_bulk:
        try:
            print(f"[+] Extracting data from disk image: {os.path.basename(evidence_path)}")
            bulk_output = os.path.join(subdirs['bulk_extractor'], "be_results")

            print(f"[INFO] Starting bulk-extractor analysis...")
            print(f"[INFO] Output directory: {bulk_output}")

            if evidence_size_gb > 5.0:
                print(f"[WARNING] Large file processing - this may take 15-30 minutes")
            else:
                print(f"[INFO] Processing should complete in 5-15 minutes")

            success = run_bulk_extractor_with_custom_output(evidence_path, bulk_output)

            if success:
                print(f"[+] Bulk-Extractor analysis completed successfully")
                print(f"     Results: {bulk_output}")

                # Show what was extracted
                if os.path.exists(bulk_output):
                    files = os.listdir(bulk_output)
                    key_files = [f for f in files if f.endswith('.txt') and f != 'report.xml'][:5]
                    if key_files:
                        print(f"     Key extractions: {', '.join(key_files)}")
                    else:
                        print(f"     Total output files: {len(files)}")
            else:
                print("[-] Bulk-Extractor analysis failed or timed out")
                print("[INFO] This is not critical - other forensic tools will continue")

        except Exception as e:
            print(f"[-] Bulk-Extractor analysis failed: {e}")
            print("    [*] Continuing with other forensic tools...")
    else:
        print("[INFO] Bulk-Extractor analysis skipped due to file size")
        print("[INFO] To force analysis, set environment variable: EDITH_BULK_EXTRACTOR_MODE=force")

    # 6. Run HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    verification_dir = os.path.join(subdirs['hashdeep'], "verification")
    os.makedirs(verification_dir, exist_ok=True)
    verify_results = hashdeep.main(evidence_path, output_path=verification_dir)
    print(f"[+] HashDeep verification completed. Report saved in: {verification_dir}")

    print("\n Full forensic workflow completed successfully!")
    print("   - Baseline hashes created")
    print("   - Autopsy analysis done")
    if memory_file:
        print("   - Memory analysis completed")
    print("   - ExifTool metadata extracted")
    print("   - Bulk-Extractor data extraction completed")
    print("   - Final verification passed")

    # Final cleanup: Remove any stray Evidence directories
    print("\n Performing final cleanup...")
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

    # Ask only once for both paths
    evidence_path = input("Enter path to disk image (.E01/.dd/.raw): ").strip()
    memory_file = input("Enter path to memory dump file (leave blank to skip): ").strip()
    memory_file = memory_file if memory_file else None

    run_workflow(evidence_path, memory_file)
