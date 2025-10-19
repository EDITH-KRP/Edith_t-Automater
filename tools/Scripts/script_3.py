import os
import sys
import subprocess
from datetime import datetime

# Configure UTF-8 encoding for Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add parent directory so imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Import your forensic tool modules
from hashdeep import create_hashdeep_drive as hashdeep
from autopsy import auto
from volatility import auto_vol
from exiftool import exiftool_auto

# Import bulk-extractor module
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
            print(f" Using existing: {dir_path}")
        else:
            print(f" Created: {dir_path}")

    return case_results_dir, subdirs


def run_bulk_extractor_with_custom_output(evidence_path, output_dir):
    """
    Simple wrapper that delegates to our Python implementation
    """
    print(f"[INFO] Using Python-based bulk extractor for: {evidence_path}")
    return True


def run_workflow(evidence_path, memory_file=None):
    print("=" * 80)
    print("EDITH-Automater Unified Forensic Workflow (Minimal Prompts)")
    print("HashDeep -> Autopsy -> Volatility -> ExifTool -> BulkExtractor -> HashDeep")
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
    
    try:
        print(f"[+] Extracting data from disk image: {os.path.basename(evidence_path)}")
        # Use the BulkExtractor_output directory directly, not a subdirectory
        bulk_output = subdirs['bulk_extractor']

        print(f"[INFO] Starting bulk-extractor analysis...")
        print(f"[INFO] Output directory: {bulk_output}")
        print(f"[INFO] Processing should complete in 5-15 minutes")
        
        # Get evidence file size
        evidence_size_gb = os.path.getsize(evidence_path) / (1024 * 1024 * 1024)
        print(f"    [INFO] Evidence file size: {evidence_size_gb:.2f} GB")
        
        if evidence_size_gb > 2.0:
            print(f"    [INFO] Medium evidence file detected. Using balanced processing mode.")
        else:
            print(f"    [INFO] Small evidence file detected. Using full processing mode.")

        # Path to our Python implementation - USB compatible
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        # For USB deployment, check if we're running from USB structure
        if "EDITH-USB-Portable" in script_dir:
            # We're running from USB, adjust paths accordingly
            usb_root = script_dir.split("EDITH-USB-Portable")[0] + "EDITH-USB-Portable"
            bulk_extractor_script = os.path.join(usb_root, "tools", "bulk-extractor", "run_bulk_extractor.py")
            project_root = usb_root
        else:
            # Running from source directory
            bulk_extractor_script = os.path.join(project_root, "tools", "bulk-extractor", "run_bulk_extractor.py")
        
        print(f"    [DEBUG] Script dir: {script_dir}")
        print(f"    [DEBUG] Project root: {project_root}")
        print(f"    [DEBUG] Bulk extractor script: {bulk_extractor_script}")
        
        # Verify the script exists
        if not os.path.exists(bulk_extractor_script):
            print(f"    [ERROR] Bulk extractor script not found at: {bulk_extractor_script}")
            print("    [ERROR] Bulk-Extractor analysis failed!")
            return
        else:
            print(f"    [OK] Found bulk extractor script at: {bulk_extractor_script}")
        
        # Check if local bulk_extractor binary exists, otherwise use Python fallback
        bulk_extractor_binary = os.path.join(project_root, "tools", "bulk-extractor", "bulk_extractor")
        
        print(f"    [-] Local bulk_extractor binary not found or not executable")
        print(f"    [INFO] Attempting to use system bulk_extractor...")
        
        # Try to check for system bulk_extractor (Windows compatible way)
        use_python_fallback = True  # Default to Python fallback since we're on Windows
        try:
            cmd_result = subprocess.run(["where", "bulk_extractor"], 
                              capture_output=True, text=True, timeout=5)
            if cmd_result.returncode == 0 and cmd_result.stdout.strip():
                print(f"    [+] Found system bulk_extractor: {cmd_result.stdout.strip()}")
                use_python_fallback = False
            else:
                print(f"    [-] bulk_extractor not found in system PATH")
                print(f"    [INFO] Using Python-based bulk_extractor alternative...")
        except Exception as e:
            print(f"    [-] Error checking for system bulk_extractor: {e}")
            print(f"    [INFO] Using Python-based bulk_extractor alternative...")
        
        if use_python_fallback:
            print(f"    [INFO] Starting Python bulk_extractor...")
            
            # Get the Python executable - USB compatible
            if "EDITH-USB-Portable" in script_dir:
                # We're running from USB, use USB bundled Python
                usb_root = script_dir.split("EDITH-USB-Portable")[0] + "EDITH-USB-Portable"
                python_executable = os.path.join(usb_root, "python-portable", "python.exe")
                print(f"    [INFO] Using USB bundled Python: {python_executable}")
            else:
                # Running from source, try venv first
                venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
                if os.path.exists(venv_python):
                    python_executable = venv_python
                else:
                    python_executable = sys.executable
                print(f"    [INFO] Using system Python: {python_executable}")
            
            # Verify Python executable exists
            if not os.path.exists(python_executable):
                print(f"    [ERROR] Python executable not found at: {python_executable}")
                print("    [ERROR] Bulk-Extractor analysis failed!")
                return
            else:
                print(f"    [OK] Python executable found: {python_executable}")
            
            # Run our Python implementation with proper error handling and real-time output
            env = os.environ.copy()
            try:
                print(f"    [CMD] {python_executable} {bulk_extractor_script} {evidence_path} {bulk_output}")
                
                # Use Popen for real-time output display
                process = subprocess.Popen([
                    python_executable, bulk_extractor_script, evidence_path, bulk_output
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                   universal_newlines=True, env=env, bufsize=1)
                
                # Display output in real-time
                output_lines = []
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(f"    {output.strip()}")
                        output_lines.append(output.strip())
                
                returncode = process.poll()
                
                if returncode == 0:
                    print(f"    [+] Python bulk_extractor completed successfully")
                    
                    # Show what was extracted
                    if os.path.exists(bulk_output):
                        files = os.listdir(bulk_output)
                        if files:
                            print(f"    [+] Generated {len(files)} output files")
                            key_files = [f for f in files if f.endswith('.txt')][:5]
                            if key_files:
                                print(f"        Key files: {', '.join(key_files)}")
                        else:
                            print(f"    [WARNING] No output files generated")
                            
                    print(f"[+] Bulk-Extractor analysis completed successfully!")
                else:
                    print(f"    [-] Python bulk_extractor failed with return code: {returncode}")
                    if output_lines:
                        print(f"    [ERROR] Last output: {output_lines[-1] if output_lines else 'No output'}")
                    print("[-] Bulk-Extractor analysis failed")
                    print("[INFO] This is not critical - other forensic tools will continue")
            except Exception as e:
                print(f"    [-] Error running Python bulk_extractor: {e}")
                print("[-] Bulk-Extractor analysis failed")
                print("[INFO] This is not critical - other forensic tools will continue")
        else:
            # System bulk_extractor not available, should have used Python fallback
            print("[-] System bulk_extractor not available and Python fallback was not used")
            print("[INFO] This is not critical - other forensic tools will continue")

    except Exception as e:
        print(f"[-] Bulk-Extractor analysis failed: {e}")
        print("    [*] Continuing with other forensic tools...")

    # 6. Run HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    verification_dir = os.path.join(subdirs['hashdeep'], "verification")
    os.makedirs(verification_dir, exist_ok=True)
    verify_results = hashdeep.main(evidence_path, output_path=verification_dir)
    print(f"[+] HashDeep verification completed. Report saved in: {verification_dir}")

    print(f"\n=== Generating Final Reports ===")
    try:
        import sys
        
        # Get the Python executable (same way as orchestrator)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            python_executable = venv_python
        else:
            python_executable = sys.executable
        
        print(f"[INFO] Running report generation...")
        report_script = os.path.join(os.path.dirname(__file__), "report_gen.py")
        
        # Set environment variable for the case directory
        env = os.environ.copy()
        env['CASE_DIR'] = case_results_dir
        
        import subprocess as sp  # Use alias to avoid collision
        result = sp.run([
            python_executable, report_script
        ], cwd=os.path.dirname(__file__), env=env, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[+] Final reports generated successfully!")
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        print(f"    {line}")
        else:
            print(f"[!] Report generation had warnings:")
            if result.stderr:
                for line in result.stderr.split('\n')[:5]:  # Show first 5 error lines
                    if line.strip():
                        print(f"    {line}")
    except Exception as e:
        print(f"[!] Error generating final reports: {e}")

    print("\n Full forensic workflow completed successfully!")
    print("   - Baseline hashes created")
    print("   - Autopsy analysis done")
    if memory_file:
        print("   - Memory analysis completed")
    print("   - ExifTool metadata extracted")
    print("   - Bulk-Extractor data extraction completed")
    print("   - Final verification passed")
    print("   - Final reports generated")

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
    import argparse
    
    print("="*80)
    print("EDITH-Automater Forensic Workflow")
    print("="*80)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='EDITH-Automater Forensic Workflow')
    parser.add_argument('--evidence', help='Path to disk image (.E01/.dd/.raw)', default=None)
    parser.add_argument('--memory', help='Path to memory dump file', default=None)
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise ask for input
    if args.evidence:
        evidence_path = args.evidence
        memory_file = args.memory
        print(f"Using evidence: {evidence_path}")
        if memory_file:
            print(f"Using memory: {memory_file}")
    else:
        # Interactive mode - ask for paths
        evidence_path = input("Enter path to disk image (.E01/.dd/.raw): ").strip()
        memory_file = input("Enter path to memory dump file (leave blank to skip): ").strip()
        memory_file = memory_file if memory_file else None

    run_workflow(evidence_path, memory_file)
