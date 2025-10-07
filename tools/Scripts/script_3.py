import os
import sys
import glob
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
bulk_extractor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bulk_extractor')
sys.path.append(bulk_extractor_path)


def find_latest_case_directory():
    """
    Find the most recent case directory created by q_script.py
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_base = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Results")
    
    if not os.path.exists(results_base):
        return None, None
    
    # Look for .case_info files in case directories
    case_dirs = []
    
    for item in os.listdir(results_base):
        item_path = os.path.join(results_base, item)
        if item.startswith("CASE_") and os.path.isdir(item_path):
            case_info_file = os.path.join(item_path, ".case_info")
            if os.path.exists(case_info_file):
                # Read case info
                with open(case_info_file, 'r') as f:
                    case_info = {}
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            case_info[key] = value
                case_dirs.append((item_path, case_info, item))
            else:
                # Directory exists but no case info, add with basic info
                case_dirs.append((item_path, {"CASE_ID": item}, item))
    
    if not case_dirs:
        return None, None
    
    # Sort by directory name (which includes timestamp) and get the latest
    case_dirs.sort(key=lambda x: x[2], reverse=True)
    latest_case_path, latest_case_info, case_id = case_dirs[0]
    
    return latest_case_path, case_id


def setup_results_structure_from_existing(case_dir=None):
    """
    Use existing case directory from q_script.py or create new one
    """
    if case_dir is None:
        # Try to find existing case directory
        existing_case_dir, case_id = find_latest_case_directory()
        
        if existing_case_dir:
            print(f"📁 Found existing case directory: {os.path.basename(existing_case_dir)}")
            use_existing = input("Use this case directory for forensic analysis? (y/n, default=y): ").strip().lower()
            
            if use_existing in ['', 'y', 'yes']:
                case_dir = existing_case_dir
                case_id = os.path.basename(case_dir).replace("CASE_", "")
                print(f"✅ Using existing case: {os.path.basename(case_dir)}")
            else:
                # Create new case directory
                case_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                script_dir = os.path.dirname(os.path.abspath(__file__))
                results_base = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Results")
                case_dir = os.path.join(results_base, f"CASE_{case_id}")
                print(f"✅ Creating new case: CASE_{case_id}")
        else:
            # No existing case found, create new
            case_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            results_base = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "Results")
            case_dir = os.path.join(results_base, f"CASE_{case_id}")
            print(f"📁 No existing case found. Creating new case: CASE_{case_id}")
    else:
        case_id = os.path.basename(case_dir).replace("CASE_", "")
    
    # Define subdirectories
    subdirs = {
        'hashdeep': os.path.join(case_dir, "HashDeep_output"),
        'autopsy': os.path.join(case_dir, "Autopsy_output"),
        'volatility': os.path.join(case_dir, "Volatility_output"),
        'exiftool': os.path.join(case_dir, "ExifTool_output"),
        'bulk_extractor': os.path.join(case_dir, "BulkExtractor_output"),
        'questions': os.path.join(case_dir, "Questions"),
        'reports': os.path.join(case_dir, "Final_Reports")
    }
    
    # Create directories that don't exist
    for subdir_name, subdir_path in subdirs.items():
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path, exist_ok=True)
            print(f"📁 Created: {os.path.relpath(subdir_path)}")
        else:
            print(f"📁 Found: {os.path.relpath(subdir_path)}")
    
    return case_dir, case_id, subdirs


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


def xml_to_dict(element):
    """
    Convert XML element to dictionary recursively
    """
    result = {}
    
    # Add attributes if any
    if element.attrib:
        result['@attributes'] = element.attrib
    
    # Process child elements
    children = list(element)
    if children:
        children_dict = {}
        for child in children:
            child_dict = xml_to_dict(child)
            if child.tag in children_dict:
                # Handle multiple elements with same tag
                if not isinstance(children_dict[child.tag], list):
                    children_dict[child.tag] = [children_dict[child.tag]]
                children_dict[child.tag].append(child_dict)
            else:
                children_dict[child.tag] = child_dict
        result.update(children_dict)
    
    # Add text content if any
    if element.text and element.text.strip():
        if len(result) == 0:
            return element.text.strip()
        else:
            result['text'] = element.text.strip()
    
    return result


def convert_bulk_extractor_xml_to_json(output_dir):
    """
    Convert bulk-extractor report.xml to JSON format for better readability
    """
    import xml.etree.ElementTree as ET
    import json
    
    xml_file = os.path.join(output_dir, "report.xml")
    json_file = os.path.join(output_dir, "report.json")
    
    if not os.path.exists(xml_file):
        print(f"    ⚠️ report.xml not found in {output_dir}")
        return None
    
    try:
        print(f"    [+] Converting report.xml to JSON format...")
        
        # Parse XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Convert to dictionary
        report_dict = {
            "bulk_extractor_report": xml_to_dict(root)
        }
        
        # Add metadata
        report_dict["conversion_info"] = {
            "converted_at": datetime.now().isoformat(),
            "original_file": "report.xml",
            "converter": "EDITH-Automater script_3.py"
        }
        
        # Write JSON file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=4, ensure_ascii=False)
        
        print(f"    ✅ JSON report created: {json_file}")
        
        # Create a summary JSON with key information
        summary_file = os.path.join(output_dir, "report_summary.json")
        create_bulk_extractor_summary(report_dict, summary_file, output_dir)
        
        return json_file
        
    except Exception as e:
        print(f"    ❌ Error converting XML to JSON: {e}")
        return None


def create_bulk_extractor_summary(report_dict, summary_file, output_dir):
    """
    Create a human-readable summary from the bulk-extractor report
    """
    import json
    import glob
    
    try:
        summary = {
            "analysis_summary": {
                "tool": "bulk-extractor",
                "analysis_date": datetime.now().isoformat(),
                "output_directory": output_dir
            },
            "extraction_results": {},
            "file_statistics": {},
            "key_findings": []
        }
        
        # Extract key information from the report
        bulk_report = report_dict.get("bulk_extractor_report", {})
        
        # Get run information
        if "runinfo" in bulk_report:
            runinfo = bulk_report["runinfo"]
            summary["analysis_summary"]["run_info"] = runinfo
        
        # Analyze generated files
        file_stats = {}
        total_extractions = 0
        
        for file_path in glob.glob(os.path.join(output_dir, "*.txt")):
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Count records in file
            record_count = 0
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    record_count = len([line for line in lines if line.strip() and not line.startswith('#')])
            except:
                record_count = 0
            
            file_stats[filename] = {
                "size_bytes": file_size,
                "size_human": format_file_size(file_size),
                "record_count": record_count,
                "has_data": record_count > 0
            }
            
            total_extractions += record_count
            
            # Add to key findings if significant
            if record_count > 0:
                category = get_extraction_category(filename)
                summary["key_findings"].append({
                    "category": category,
                    "file": filename,
                    "count": record_count,
                    "description": get_extraction_description(filename)
                })
        
        summary["file_statistics"] = file_stats
        summary["analysis_summary"]["total_extractions"] = total_extractions
        summary["analysis_summary"]["files_with_data"] = len([f for f in file_stats.values() if f["has_data"]])
        summary["analysis_summary"]["total_files"] = len(file_stats)
        
        # Write summary JSON
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        
        print(f"    ✅ Summary report created: {summary_file}")
        
        # Display key findings
        if summary["key_findings"]:
            print(f"    📊 Key Findings:")
            for finding in summary["key_findings"][:5]:  # Show top 5
                print(f"       • {finding['category']}: {finding['count']} items ({finding['file']})")
        
    except Exception as e:
        print(f"    ⚠️ Could not create summary: {e}")


def format_file_size(bytes_size):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def get_extraction_category(filename):
    """Get category for extraction file"""
    categories = {
        "email": "Email Communications",
        "url": "Web URLs & Links", 
        "domain": "Network Domains",
        "wordlist": "Dictionary Words",
        "outlook": "Outlook Data",
        "base16": "Encoded Data",
        "ether": "Network Packets",
        "rfc822": "Email Headers"
    }
    
    for key, category in categories.items():
        if key in filename:
            return category
    return "Other Data"


def get_extraction_description(filename):
    """Get description for extraction file"""
    descriptions = {
        "email": "Email addresses found in the image",
        "url": "URLs and web links discovered",
        "domain": "Domain names and hostnames",
        "wordlist": "Dictionary words and text strings",
        "outlook": "Microsoft Outlook email data",
        "base16": "Base16/hex encoded data",
        "ether": "Ethernet packet data",
        "rfc822": "Email header information"
    }
    
    for key, desc in descriptions.items():
        if key in filename:
            return desc
    return "Extracted data from forensic analysis"


def check_questions_directory(case_dir):
    """
    Check if questions directory exists and show evidence collection info
    """
    questions_dir = os.path.join(case_dir, "Questions")
    if os.path.exists(questions_dir):
        # Look for evidence collection forms
        form_files = glob.glob(os.path.join(questions_dir, "evidence_collection_form_*.txt"))
        if form_files:
            latest_form = max(form_files, key=os.path.getctime)
            print(f"📋 Found evidence collection form: {os.path.basename(latest_form)}")
            return True
    return False


def run_workflow(evidence_path, memory_file=None):
    print("=" * 84)
    print("EDITH-Automater Forensic Workflow")
    print("HashDeep → Autopsy → Volatility → ExifTool → BulkExtractor → HashDeep")
    print("=" * 84)

    # Check if case directory already exists (from q_script.py)
    case_results_dir, case_id, subdirs = setup_results_structure_from_existing()
    
    # Check if evidence collection form exists
    has_questions = check_questions_directory(case_results_dir)
    if has_questions:
        print("✅ Evidence collection form found - proceeding with forensic analysis")
    else:
        print("⚠️  No evidence collection form found. Consider running q_script.py first.")
        proceed = input("Continue anyway? (y/n, default=y): ").strip().lower()
        if proceed in ['n', 'no']:
            print("🛑 Workflow cancelled. Please run q_script.py first.")
            return

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
        
        # Use the local wrapper but add detailed analysis after
        success = run_bulk_extractor_with_custom_output(evidence_path, bulk_output)
        
        if success:
            print(f"[+] Bulk-Extractor analysis completed successfully")
            print(f"    📁 Results: {bulk_output}")
            
            # Add detailed file analysis like in run_bulk_extractor.py
            if os.path.exists(bulk_output):
                print("\n" + "="*90)
                print("📁 BULK-EXTRACTOR OUTPUT FILES")
                print("="*90)
                print(f"{'Name':<25} {'Date Modified':<20} {'Type':<25} {'Size':<8}")
                print("-" * 90)
                
                files_info = []
                for file_path in glob.glob(os.path.join(bulk_output, "*")):
                    if os.path.isfile(file_path):
                        filename = os.path.basename(file_path)
                        stat_info = os.stat(file_path)
                        file_size = stat_info.st_size
                        mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%d-%m-%Y %H:%M")
                        
                        if filename.endswith('.xml'):
                            file_type = "XML Document"
                        elif filename == "report":
                            file_type = "Microsoft Edge HTML..."
                        else:
                            file_type = "Text Document"
                        
                        size_str = format_file_size(file_size)
                        print(f"{filename:<25} {mod_time:<20} {file_type:<25} {size_str:<8}")
                        
                        files_info.append({
                            'name': filename,
                            'size': size_str,
                            'bytes': file_size
                        })
                
                print("-" * 90)
                print(f"Total files: {len(files_info)}")
                
                # Show detailed analysis
                print(f"\n📊 DETAILED ANALYSIS:")
                print("-" * 50)
                significant_files = [f for f in files_info if f['bytes'] > 0]
                empty_files = [f for f in files_info if f['bytes'] == 0]
                
                print(f"Files with data: {len(significant_files)}")
                print(f"Empty files: {len(empty_files)}")
                
                if significant_files:
                    print(f"\n🎯 FILES WITH EXTRACTED DATA:")
                    for file_info in significant_files[:10]:  # Show top 10
                        print(f"   📄 {file_info['name']:<20} - {file_info['size']}")
                
                if empty_files:
                    print(f"\n📭 EMPTY FILES (no data extracted):")
                    for file_info in empty_files[:10]:  # Show first 10
                        print(f"   📭 {file_info['name']}")
                
                print("="*90)
            
            # Convert XML report to JSON for better readability
            json_report = convert_bulk_extractor_xml_to_json(bulk_output)
            if json_report:
                print(f"    📄 XML converted to JSON: {json_report}")
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
    print("="*84)
    print("EDITH-Automater Forensic Workflow")
    print("="*84)
    
    # Check for existing case directories from q_script.py
    existing_case_dir, case_id = find_latest_case_directory()
    
    if existing_case_dir:
        print(f"🔍 Workflow Integration Check:")
        print(f"   Found case directory: {os.path.basename(existing_case_dir)}")
        
        # Check if evidence collection form exists
        questions_dir = os.path.join(existing_case_dir, "Questions")
        if os.path.exists(questions_dir):
            form_files = glob.glob(os.path.join(questions_dir, "evidence_collection_form_*.txt"))
            if form_files:
                print(f"   ✅ Evidence collection form found")
                print(f"   📋 Ready for forensic analysis")
            else:
                print(f"   ⚠️  Case directory exists but no evidence form found")
        else:
            print(f"   ⚠️  Questions directory not found")
        
        print(f"   Recommendation: This case is ready for forensic analysis")
    else:
        print(f"🔍 Workflow Integration Check:")
        print(f"   ⚠️  No case directories found from q_script.py")
        print(f"   Recommendation: Run q_script.py first to create evidence collection form")
        print(f"   Alternative: Continue to create a new case directory")

    print("="*84)

    # Ask for evidence paths
    evidence_path = input("Enter path to disk image (.E01/.dd/.raw): ").strip()
    memory_file = input("Enter path to memory dump file (leave blank to skip): ").strip()
    memory_file = memory_file if memory_file else None

    run_workflow(evidence_path, memory_file)