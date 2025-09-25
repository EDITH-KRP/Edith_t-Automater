#!/usr/bin/env python3
"""
ExifTool Interactive Command Prompt Interface
============================================

This script provides a user-friendly command prompt interface for ExifTool
metadata extraction. It prompts the user for input file location and creates
output in the exiftool directory.

Usage:
    python exiftool_prompt.py

Features:
- Interactive file selection
- Automatic case ID generation
- Output in exiftool directory
- Support for image files and .dd files
- User-friendly progress display

Author: ADITHYA N T
Version: 1.0
Date: September 2025
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from integrated_runner import create_runner
    from metadata_extractor import MetadataExtractor
except ImportError as e:
    print(f"Error: Required modules not found: {e}")
    print("Please ensure all required files are in the exiftool directory.")
    sys.exit(1)

def print_banner():
    """Print application banner"""
    print("=" * 70)
    print("             EXIFTOOL METADATA EXTRACTION TOOL")
    print("                 Interactive Command Interface")
    print("=" * 70)
    print("This tool extracts metadata from image files and disk images (.dd)")
    print("Output will be saved in the exiftool/output directory")
    print("=" * 70)
    print()

def get_user_input():
    """
    Get input from user via command prompt
    
    Returns:
        tuple: (input_path, case_id)
    """
    print("Please provide the following information:")
    print("-" * 40)
    
    # Get input file path
    while True:
        print("\nFile/Directory Input:")
        print("  - Image files (jpg, png, tiff, etc.)")
        print("  - Disk images (.dd, .img, .raw, etc.)")
        print("  - Directories containing multiple files")
        
        input_path = input("\nEnter full path to file or directory: ").strip()
        
        if not input_path:
            print("❌ Error: Please enter a valid path.")
            continue
            
        # Clean up the path (remove quotes if present)
        input_path = input_path.strip('"').strip("'")
        
        # Convert to Path object and check if exists
        path_obj = Path(input_path)
        if not path_obj.exists():
            print(f"❌ Error: Path '{input_path}' does not exist.")
            retry = input("Do you want to try again? (y/n): ").strip().lower()
            if retry not in ['y', 'yes']:
                print("Operation cancelled by user.")
                sys.exit(0)
            continue
        
        # Validate file types for single files
        if path_obj.is_file():
            supported_extensions = {
                '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp',
                '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
                '.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma',
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.dd', '.img', '.raw', '.bin', '.001', '.e01'
            }
            
            file_ext = path_obj.suffix.lower()
            if file_ext and file_ext not in supported_extensions:
                print(f"⚠️  Warning: '{file_ext}' files may not contain extractable metadata.")
                proceed = input("Do you want to proceed anyway? (y/n): ").strip().lower()
                if proceed not in ['y', 'yes']:
                    continue
        
        print(f"✓ Valid path: {input_path}")
        break
    
    # Get case ID
    print(f"\nCase Information:")
    case_id = input("Enter Case ID (optional, press Enter for auto-generated): ").strip()
    
    if not case_id:
        case_id = f"EXIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"✓ Auto-generated Case ID: {case_id}")
    else:
        # Clean case ID (remove invalid characters)
        import re
        case_id = re.sub(r'[^\w\-_]', '_', case_id)
        print(f"✓ Case ID: {case_id}")
    
    return input_path, case_id

def show_analysis_info(input_path, case_id, output_dir):
    """
    Show analysis information before starting
    
    Args:
        input_path (str): Input file/directory path
        case_id (str): Case identifier
        output_dir (str): Output directory path
    """
    print("\n" + "=" * 50)
    print("ANALYSIS CONFIGURATION")
    print("=" * 50)
    print(f"Input Path: {input_path}")
    print(f"Case ID: {case_id}")
    print(f"Output Directory: {output_dir}")
    
    # Show file information
    path_obj = Path(input_path)
    if path_obj.is_file():
        file_size = path_obj.stat().st_size
        print(f"File Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        print(f"File Type: {path_obj.suffix.upper() or 'No extension'}")
    elif path_obj.is_dir():
        file_count = len([f for f in path_obj.rglob("*") if f.is_file()])
        print(f"Directory Contents: {file_count} files")
    
    print("=" * 50)

def run_extraction(input_path, case_id):
    """
    Run the metadata extraction process
    
    Args:
        input_path (str): Path to analyze
        case_id (str): Case identifier
        
    Returns:
        dict: Extraction results
    """
    try:
        print("\n🔄 Initializing ExifTool...")
        
        # Create runner with case ID
        runner = create_runner(case_id)
        
        # Ensure output is in exiftool directory
        runner.config["output"]["base_dir"] = "output"
        runner.setup_working_directories()
        
        output_dir = runner.case_output_dir
        
        # Show configuration
        show_analysis_info(input_path, case_id, output_dir)
        
        # Final confirmation
        confirm = input("\nProceed with metadata extraction? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Operation cancelled by user.")
            return None
        
        print("\n🚀 Starting metadata extraction...")
        print("⏳ This may take a few moments depending on file size...")
        print("-" * 50)
        
        # Run the analysis
        result = runner.run_analysis(input_path)
        
        return result, runner
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return None

def display_results(result, runner):
    """
    Display extraction results to user
    
    Args:
        result (dict): Extraction results
        runner: ExifTool runner instance
    """
    print("-" * 50)
    
    if result["status"] == "SUCCESS":
        print("✅ METADATA EXTRACTION COMPLETED SUCCESSFULLY!")
        print()
        
        # Show extraction statistics
        extraction_data = result.get("extraction", {})
        print("📊 EXTRACTION STATISTICS:")
        print(f"   Files Processed: {extraction_data.get('files_processed', 0)}")
        print(f"   Execution Time: {extraction_data.get('execution_time', 0):.2f} seconds")
        print(f"   Extraction Method: {extraction_data.get('extraction_method', 'unknown')}")
        print(f"   Output Directory: {runner.case_output_dir}")
        print()
        
        # List generated files
        if runner.case_output_dir.exists():
            print("📁 GENERATED FILES:")
            file_count = 0
            for file_path in runner.case_output_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(runner.case_output_dir)
                    file_size = file_path.stat().st_size
                    print(f"   - {relative_path} ({file_size:,} bytes)")
                    file_count += 1
            
            if file_count == 0:
                print("   - No output files generated")
            print()
        
        # Show file statistics if available
        file_stats = extraction_data.get("file_statistics", {})
        if file_stats:
            print("📈 FILE STATISTICS:")
            print(f"   Total Files: {file_stats.get('total_files', 0)}")
            print(f"   Total Size: {file_stats.get('total_size_mb', 0):.2f} MB")
            
            file_types = file_stats.get('file_types', {})
            if file_types:
                print("   File Types:")
                for ext, count in sorted(file_types.items()):
                    print(f"     {ext}: {count} files")
            print()
        
        # Ask if user wants detailed results
        show_detailed = input("Do you want to see detailed extraction results? (y/n): ").strip().lower()
        if show_detailed in ['y', 'yes']:
            print("\n" + "=" * 70)
            print("DETAILED EXTRACTION RESULTS")
            print("=" * 70)
            print(json.dumps(result, indent=2))
            
    else:
        print("❌ METADATA EXTRACTION FAILED!")
        print(f"Error: {result.get('error_message', 'Unknown error occurred')}")
        
        # Show error details if available
        if "extraction" in result and "error" in result["extraction"]:
            print(f"Details: {result['extraction']['error']}")

def main():
    """Main function for interactive ExifTool interface"""
    try:
        # Print banner
        print_banner()
        
        # Get user input
        input_path, case_id = get_user_input()
        
        # Run extraction
        extraction_result = run_extraction(input_path, case_id)
        
        if extraction_result:
            result, runner = extraction_result
            
            # Display results
            display_results(result, runner)
            
            # Ask about opening output directory
            print("\n" + "=" * 50)
            open_dir = input("Do you want to open the output directory? (y/n): ").strip().lower()
            if open_dir in ['y', 'yes']:
                try:
                    import subprocess
                    subprocess.run(['explorer', str(runner.case_output_dir)], shell=True)
                except Exception as e:
                    print(f"Could not open directory: {e}")
                    print(f"Output location: {runner.case_output_dir}")
        
        print("\n" + "=" * 70)
        print("Thank you for using ExifTool Metadata Extraction Tool!")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your input and try again.")
    
    # Wait for user before closing (if running in Windows command prompt)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()