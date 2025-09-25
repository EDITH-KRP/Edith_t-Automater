#!/usr/bin/env python3
"""
HashDeep Drive Verification Module for EDITH-Automater
=====================================================

This module verifies the integrity of disk images and directories by comparing
current hash values with previously calculated reference hashes. It ensures
that digital evidence has not been tampered with or corrupted.

Key Functions:
- Hash integrity verification
- Evidence tampering detection
- Chain of custody validation
- Forensic verification reports

Author: ADITHYA N T
Version: 1.0 - Drive Verification
Date: September 2025
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the hashdeep directory to Python path for importing
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from create_hashdeep_drive import DriveHashProcessor, DriveVerification
except ImportError as e:
    print(f"Error importing create_hashdeep_drive module: {e}")
    print("Make sure create_hashdeep_drive.py is in the same directory as this script.")
    sys.exit(1)

def load_reference_hashes_from_report(report_path: str) -> Optional[Dict[str, str]]:
    """
    Load reference hash values from a previously generated forensic report
    
    Args:
        report_path (str): Path to the forensic report file
        
    Returns:
        dict: Dictionary containing MD5, SHA1, SHA256 hashes or None if failed
    """
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse hash values from the report
        hashes = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('MD5:'):
                hashes['md5'] = line.split('MD5:')[1].strip()
            elif line.startswith('SHA1:'):
                hashes['sha1'] = line.split('SHA1:')[1].strip()
            elif line.startswith('SHA256:'):
                hashes['sha256'] = line.split('SHA256:')[1].strip()
        
        # Validate that all hashes were found
        if len(hashes) == 3 and all(hashes.values()):
            return hashes
        else:
            print(f"Error: Could not parse all hash values from report {report_path}")
            return None
            
    except Exception as e:
        print(f"Error reading report file {report_path}: {str(e)}")
        return None

def search_file_locations(filename: str) -> Optional[str]:
    """
    Dynamically search for a file across common locations
    
    Args:
        filename (str): The filename to search for
        
    Returns:
        str: First found path or None if not found
    """
    # Common search locations (add more as needed)
    search_locations = [
        "C:\\Users\\adhii\\Downloads",
        "C:\\Users\\adhii\\Desktop", 
        "C:\\Users\\adhii\\Documents",
        "D:\\",
        "E:\\",
        "F:\\",
        "C:\\Evidence",
        "C:\\ForensicImages",
        "C:\\Temp",
        "C:\\Users\\Public\\Downloads"
    ]
    
    print(f"🔍 Searching for '{filename}' across multiple locations...")
    
    # Search in each location
    for location in search_locations:
        if os.path.exists(location):
            try:
                # Direct search in the location
                full_path = os.path.join(location, filename)
                if os.path.exists(full_path):
                    print(f"✅ Found: {full_path}")
                    return full_path
                
                # Search in subdirectories (limited depth for performance)
                for root, dirs, files in os.walk(location):
                    # Limit search depth to avoid long scans
                    depth = root.replace(location, '').count(os.sep)
                    if depth < 3:  # Max 3 levels deep
                        if filename.lower() in [f.lower() for f in files]:
                            found_path = os.path.join(root, filename)
                            print(f"✅ Found: {found_path}")
                            return found_path
                        # Limit subdirectory traversal
                        dirs[:] = dirs[:5]  # Only check first 5 subdirs
                    else:
                        dirs[:] = []  # Stop going deeper
                        
            except (PermissionError, OSError) as e:
                # Skip locations we can't access
                continue
    
    print(f"❌ File '{filename}' not found in any search locations")
    return None

def find_all_existing_reports() -> List[Dict[str, str]]:
    """
    Find all existing forensic reports and dynamically locate their target files
    
    Returns:
        list: List of dictionaries containing report info {'report_path': str, 'target_path': str, 'filename': str}
    """
    # Get the main hash output directory
    hash_output_dir = Path("e:/Github-adhi982/Edith_t-Automater/tools/hashdeep/Initial_Hash_output")
    
    if not hash_output_dir.exists():
        return []
    
    reports_info = []
    
    # Find all hash reports
    for report_file in hash_output_dir.glob("DriveHash_Report_CASE_*.txt"):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract original target path and filename from the report
            original_target_path = None
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('Evidence Path:'):
                    original_target_path = line.split('Evidence Path:')[1].strip()
                    break
            
            if original_target_path:
                filename = os.path.basename(original_target_path)
                
                # First try the original path
                current_target_path = None
                if os.path.exists(original_target_path):
                    current_target_path = original_target_path
                    print(f"✅ Found at original location: {original_target_path}")
                else:
                    print(f"⚠️  Original path no longer exists: {original_target_path}")
                    # Dynamically search for the file
                    current_target_path = search_file_locations(filename)
                
                if current_target_path:
                    reports_info.append({
                        'report_path': str(report_file),
                        'target_path': current_target_path,
                        'original_path': original_target_path,
                        'filename': filename,
                        'mod_time': os.path.getmtime(report_file)
                    })
                else:
                    print(f"❌ Could not locate file '{filename}' for report {report_file.name}")
                    
        except Exception as e:
            print(f"Warning: Could not read report {report_file}: {e}")
            continue
    
    # Sort by modification time (newest first)
    reports_info.sort(key=lambda x: x['mod_time'], reverse=True)
    return reports_info

def load_reference_hashes_manual() -> Dict[str, str]:
    """
    Get reference hash values from manual user input
    
    Returns:
        dict: Dictionary containing MD5, SHA1, SHA256 hashes
    """
    print("Enter the reference hash values for verification:")
    print("(These should be the original hashes from when the evidence was first acquired)")
    print()
    
    hashes = {}
    
    while True:
        md5_hash = input("Enter MD5 hash: ").strip().lower()
        if len(md5_hash) == 32 and all(c in '0123456789abcdef' for c in md5_hash):
            hashes['md5'] = md5_hash
            break
        else:
            print("Invalid MD5 hash format. Please enter a 32-character hexadecimal string.")
    
    while True:
        sha1_hash = input("Enter SHA1 hash: ").strip().lower()
        if len(sha1_hash) == 40 and all(c in '0123456789abcdef' for c in sha1_hash):
            hashes['sha1'] = sha1_hash
            break
        else:
            print("Invalid SHA1 hash format. Please enter a 40-character hexadecimal string.")
    
    while True:
        sha256_hash = input("Enter SHA256 hash: ").strip().lower()
        if len(sha256_hash) == 64 and all(c in '0123456789abcdef' for c in sha256_hash):
            hashes['sha256'] = sha256_hash
            break
        else:
            print("Invalid SHA256 hash format. Please enter a 64-character hexadecimal string.")
    
    return hashes

def display_verification_results(verification: DriveVerification, target_path: str):
    """
    Display verification results in a clear, forensic format
    
    Args:
        verification (DriveVerification): Verification results
        target_path (str): Path to verified target
    """
    print("\n" + "=" * 80)
    print("HASH INTEGRITY VERIFICATION RESULTS")
    print("=" * 80)
    
    # Overall status
    if verification.integrity_maintained:
        status_symbol = "✓"
        status_text = "VERIFIED"
        status_color = ""  # Green in terminal
    else:
        status_symbol = "✗"
        status_text = "COMPROMISED"
        status_color = ""  # Red in terminal
    
    print(f"Overall Status: {status_symbol} {status_text}")
    print(f"Target: {target_path}")
    print(f"Verification Time: {verification.timestamp}")
    print()
    
    # Individual hash comparisons
    print("HASH COMPARISON DETAILS")
    print("-" * 40)
    
    print("MD5 Verification:")
    print(f"  Original:  {verification.original_md5}")
    print(f"  Current:   {verification.current_md5}")
    print(f"  Status:    {'✓ MATCH' if verification.details['md5_match'] else '✗ MISMATCH'}")
    print()
    
    print("SHA1 Verification:")
    print(f"  Original:  {verification.original_sha1}")
    print(f"  Current:   {verification.current_sha1}")
    print(f"  Status:    {'✓ MATCH' if verification.details['sha1_match'] else '✗ MISMATCH'}")
    print()
    
    print("SHA256 Verification:")
    print(f"  Original:  {verification.original_sha256}")
    print(f"  Current:   {verification.current_sha256}")
    print(f"  Status:    {'✓ MATCH' if verification.details['sha256_match'] else '✗ MISMATCH'}")
    print()
    
    # Forensic interpretation
    print("FORENSIC INTERPRETATION")
    print("-" * 40)
    
    if verification.integrity_maintained:
        print("✓ EVIDENCE INTEGRITY MAINTAINED")
        print("  - All cryptographic hashes match the original values")
        print("  - No tampering or corruption detected")
        print("  - Evidence is suitable for forensic analysis")
        print("  - Chain of custody integrity confirmed")
    else:
        print("✗ EVIDENCE INTEGRITY COMPROMISED")
        print("  - One or more hash values do not match")
        print("  - Possible tampering, corruption, or transfer error")
        print("  - Evidence may not be suitable for forensic analysis")
        print("  - Chain of custody may be broken")
        
        # Detailed analysis of what changed
        print("\n  DETAILED ANALYSIS:")
        if not verification.details['md5_match']:
            print("    - MD5 hash mismatch detected")
        if not verification.details['sha1_match']:
            print("    - SHA1 hash mismatch detected")
        if not verification.details['sha256_match']:
            print("    - SHA256 hash mismatch detected")
    
    print("\n" + "=" * 80)

def main():
    """Fully automated verification workflow"""
    print("=" * 80)
    print("EDITH-Automater HashDeep Drive Verification Module")
    print("=" * 80)
    print("Automated Integrity Verification - No User Input Required")
    print("=" * 80)
    print()
    
    # Automatically find all existing reports
    print("Scanning for existing forensic reports...")
    all_reports = find_all_existing_reports()
    
    if not all_reports:
        print("❌ No existing forensic reports found in Initial_Hash_output folder.")
        print("Please run the main hash generation module first to create baseline hashes.")
        return
    
    print(f"✅ Found {len(all_reports)} existing forensic report(s)")
    print()
    
    # Process each report automatically
    verification_count = 0
    success_count = 0
    
    for i, report_info in enumerate(all_reports, 1):
        target_path = report_info['target_path']
        original_path = report_info.get('original_path', target_path)
        report_path = report_info['report_path']
        filename = report_info['filename']
        
        print("=" * 60)
        print(f"VERIFICATION {i}/{len(all_reports)}: {filename}")
        print("=" * 60)
        
        # Show path resolution information
        if original_path != target_path:
            print(f"Original Path: {original_path}")
            print(f"Current Path:  {target_path}")
            print("📍 File location automatically resolved!")
        else:
            print(f"Target Path: {target_path}")
        
        # Check if target still exists (this should always pass now due to dynamic search)
        if not os.path.exists(target_path):
            print(f"❌ Target file/directory no longer exists: {target_path}")
            print("Skipping verification...")
            print()
            continue
        
        # Get file/directory info
        if os.path.isfile(target_path):
            file_size = os.path.getsize(target_path)
            print(f"File Size: {file_size:,} bytes ({file_size / (1024**3):.2f} GB)")
        elif os.path.isdir(target_path):
            print("Target Type: Directory")
        
        print(f"Reference Report: {os.path.basename(report_path)}")
        
        # Load reference hashes
        reference_hashes = load_reference_hashes_from_report(report_path)
        if not reference_hashes:
            print(f"❌ Failed to load reference hashes from report")
            print("Skipping verification...")
            print()
            continue
        
        print("✅ Reference hashes loaded successfully")
        print(f"Original MD5:    {reference_hashes['md5']}")
        print(f"Original SHA1:   {reference_hashes['sha1']}")
        print(f"Original SHA256: {reference_hashes['sha256']}")
        print()
        
        # Generate case ID for verification
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        case_id = f"VERIFY_{filename}_{timestamp}".replace(".", "_")
        
        # Set output path
        output_path = r"e:\Github-adhi982\Edith_t-Automater\tools\hashdeep\Final_Hash_Verification_output"
        
        print(f"Verification Case ID: {case_id}")
        print()
        print("🔄 Starting automated integrity verification...")
        print("Progress will be displayed during hash calculation.")
        print()
        
        # Initialize processor and perform verification
        try:
            processor = DriveHashProcessor(case_id, output_path)
            verification_result = processor.verify_drive_integrity(target_path, reference_hashes)
            
            # Count this verification attempt
            verification_count += 1
            
            # Display results
            display_verification_results(verification_result, target_path)
            
            # Generate verification report
            current_hash_result = processor.calculate_drive_hash(target_path)
            if current_hash_result.status == "SUCCESS":
                report_path = processor.generate_drive_report([current_hash_result], [verification_result])
                print(f"📄 Verification report saved to: {os.path.basename(report_path)}")
            
            if verification_result.integrity_maintained:
                success_count += 1
                print("✅ VERIFICATION SUCCESSFUL - Evidence integrity maintained!")
            else:
                print("❌ VERIFICATION FAILED - Evidence integrity compromised!")
                
        except Exception as e:
            print(f"❌ Error during verification: {str(e)}")
            verification_count += 1  # Count the attempt even if it failed
        
        print()
    
    # Final summary
    print("=" * 80)
    print("AUTOMATED VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"Total Reports Found: {len(all_reports)}")
    print(f"Verifications Performed: {verification_count}")
    print(f"Successful Verifications: {success_count}")
    print(f"Failed Verifications: {verification_count - success_count}")
    print()
    
    if success_count == verification_count:
        print("🎉 ALL VERIFICATIONS PASSED - Complete evidence integrity maintained!")
    elif success_count > 0:
        print("⚠️  PARTIAL SUCCESS - Some evidence files may be compromised!")
    else:
        print("🚨 ALL VERIFICATIONS FAILED - Evidence integrity compromised!")
    
    print("=" * 80)

if __name__ == "__main__":
    main()