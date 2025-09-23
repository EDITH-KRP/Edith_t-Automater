#!/usr/bin/env python3
"""
Real Drive Hash Testing Script
==============================
This script will hash your F: drive and save results to G: drive
For testing with actual drives instead of mock files.

Author: ADITHYA N T
Date: September 2025
"""

import os
import sys
import time
from pathlib import Path

# Import the main hashdeep module
from hashdeep_drive import DriveHashProcessor

def test_real_drives():
    """Test hashing real F: drive and saving to G: drive"""
    
    print("=" * 70)
    print("REAL DRIVE HASH TESTING - F: DRIVE → G: DRIVE")
    print("=" * 70)
    print("This will hash your entire F: drive and save results to G: drive")
    print()
    
    # Check if drives exist
    f_drive = Path("F:/")
    g_drive = Path("G:/")
    
    print("🔍 CHECKING DRIVES...")
    print("-" * 30)
    
    if not f_drive.exists():
        print("❌ F: drive not found!")
        print("Available drives:")
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if Path(f"{drive}:/").exists():
                print(f"   {drive}:")
        return
    else:
        print("✅ F: drive found")
    
    if not g_drive.exists():
        print("❌ G: drive not found!")
        print("Available drives:")
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if Path(f"{drive}:/").exists():
                print(f"   {drive}:")
        return
    else:
        print("✅ G: drive found")
    
    print()
    
    # Get drive information
    try:
        f_drive_info = os.statvfs(f_drive) if hasattr(os, 'statvfs') else None
        print(f"📁 F: Drive Analysis:")
        
        # Count files (sample check)
        sample_files = list(f_drive.rglob('*'))[:100]  # First 100 files for estimate
        print(f"   Sample files found: {len(sample_files)}")
        print(f"   Drive path: {f_drive}")
        
    except Exception as e:
        print(f"⚠️  Could not analyze F: drive: {e}")
    
    print()
    
    # Setup output on G: drive
    case_id = f"REAL-DRIVE-F-{int(time.time())}"
    output_path = g_drive / "HashDeep_Reports" / case_id
    
    print(f"🏷️  Case ID: {case_id}")
    print(f"📄 Output Location: {output_path}")
    print()
    
    # Warning and confirmation
    print("⚠️  WARNING:")
    print("   This will read your entire F: drive")
    print("   This may take a LONG time depending on drive size")
    print("   Results will be saved to G: drive")
    print()
    
    response = input("Continue with F: drive hashing? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Operation cancelled by user")
        return
    
    print()
    print("🚀 STARTING REAL DRIVE HASH OPERATION...")
    print("=" * 50)
    
    # Initialize processor
    try:
        processor = DriveHashProcessor(
            case_id=case_id,
            output_path=str(output_path)
        )
        print("✅ HashDeep processor initialized")
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return
    
    print()
    print("📁 HASHING F: DRIVE (This may take a while...)")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        # Hash the entire F: drive
        drive_result = processor.calculate_drive_hash(str(f_drive))
        
        elapsed_time = time.time() - start_time
        
        if drive_result.status == "SUCCESS":
            print(f"✅ F: DRIVE HASH COMPLETED!")
            print(f"   Files Processed: {drive_result.file_count:,}")
            print(f"   Total Size: {drive_result.total_size:,} bytes ({drive_result.total_size / (1024**3):.2f} GB)")
            print(f"   Processing Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.1f} minutes)")
            print()
            print("📋 DRIVE HASH VALUES:")
            print(f"   MD5:    {drive_result.md5_hash}")
            print(f"   SHA1:   {drive_result.sha1_hash}")
            print(f"   SHA256: {drive_result.sha256_hash}")
            print()
            
            # Generate report on G: drive
            print("📊 GENERATING REPORT ON G: DRIVE...")
            print("-" * 40)
            
            try:
                report_path = processor.generate_drive_report([drive_result])
                print(f"✅ Report saved successfully!")
                print(f"   Report Location: {report_path}")
                print(f"   Report Size: {Path(report_path).stat().st_size:,} bytes")
                
                # Also save a summary file
                summary_path = output_path / f"F_Drive_Hash_Summary_{case_id}.txt"
                with open(summary_path, 'w') as f:
                    f.write(f"F: Drive Hash Summary\n")
                    f.write(f"Case ID: {case_id}\n")
                    f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Files: {drive_result.file_count:,}\n")
                    f.write(f"Size: {drive_result.total_size:,} bytes\n")
                    f.write(f"MD5: {drive_result.md5_hash}\n")
                    f.write(f"SHA1: {drive_result.sha1_hash}\n")
                    f.write(f"SHA256: {drive_result.sha256_hash}\n")
                
                print(f"✅ Summary saved: {summary_path}")
                
            except Exception as e:
                print(f"❌ Report generation failed: {e}")
        
        else:
            print(f"❌ F: DRIVE HASH FAILED!")
            print(f"   Error: {drive_result.error_message}")
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"❌ HASH OPERATION FAILED after {elapsed_time:.1f} seconds")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("Real drive hash testing completed")
    print(f"All results saved to: {output_path}")
    print("=" * 70)

def quick_drive_info():
    """Show quick info about available drives"""
    print("💾 AVAILABLE DRIVES:")
    print("-" * 20)
    
    for drive_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        drive_path = Path(f"{drive_letter}:/")
        if drive_path.exists():
            try:
                # Try to get some basic info
                sample_items = list(drive_path.iterdir())[:5]  # First 5 items
                item_count = len(sample_items)
                print(f"   {drive_letter}: - Available ({item_count}+ items)")
            except:
                print(f"   {drive_letter}: - Available (access restricted)")

if __name__ == "__main__":
    try:
        print("Real Drive HashDeep Testing")
        print()
        
        # Show available drives first
        quick_drive_info()
        print()
        
        # Ask user what to do
        print("Options:")
        print("1. Hash F: drive and save to G: drive")
        print("2. Show drive info only")
        print("3. Exit")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            test_real_drives()
        elif choice == "2":
            quick_drive_info()
        else:
            print("Exiting...")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()