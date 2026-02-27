#!/usr/bin/env python3
"""
HashDeep Drive-Level Module for EDITH-Automater
===============================================

This module provides drive-level cryptographic hash verification for digital forensics.
It calculates MD5, SHA1, and SHA256 hash values for entire drives, directories, or disk images
to ensure overall evidence integrity.

Key Functions:
- Drive-level integrity verification
- Disk image validation
- Directory hashing
- Chain of custody documentation

Author: ADITHYA N T
Version: 2.0 - Drive Level Only
Date: September 2025
"""

import os
import sys
import json
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

# Configure logging (console only - case-specific file logging handled separately)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [HashDeep-Drive] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DriveHashResult:
    """Data structure for storing drive-level hash results"""
    target_path: str
    target_type: str  # 'file', 'directory', 'drive'
    total_size: int
    file_count: int
    md5_hash: str
    sha1_hash: str
    sha256_hash: str
    timestamp: str
    processing_time: float
    status: str  # 'SUCCESS', 'ERROR'
    error_message: Optional[str] = None

@dataclass
class DriveVerification:
    """Data structure for drive verification results"""
    original_md5: str
    original_sha1: str
    original_sha256: str
    current_md5: str
    current_sha1: str
    current_sha256: str
    integrity_maintained: bool
    timestamp: str
    details: Dict[str, bool]

class DriveHashProcessor:
    """
    Drive-Level HashDeep processor for EDITH-Automater

    This class handles drive-level hash operations:
    - Calculating hashes for entire drives/directories
    - Verifying drive integrity
    - Generating forensic reports
    """

    def __init__(self, case_id: str, output_path: str):
        """
        Initialize Drive-Level HashDeep processor

        Args:
            case_id (str): Unique case identifier
            output_path (str): Path for output reports
        """
        self.case_id = case_id
        self.output_path = Path(output_path)
        self.verification_log = []

        # Create output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)

        # Initialize case log
        self.case_log_path = self.output_path / f"drive_hash_case_{case_id}.log"
        self._setup_case_logging()

        logger.info(f"Drive-Level HashDeep processor initialized for case: {case_id}")

    def _setup_case_logging(self):
        """Setup case-specific logging"""
        case_handler = logging.FileHandler(self.case_log_path)
        case_handler.setLevel(logging.INFO)
        case_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        case_handler.setFormatter(case_formatter)
        logger.addHandler(case_handler)

    def calculate_drive_hash(self, target_path: str) -> DriveHashResult:
        """
        Calculate hash for entire drive, directory, or disk image

        Args:
            target_path (str): Path to target (file, directory, or drive)

        Returns:
            DriveHashResult: Hash calculation results
        """
        start_time = time.time()
        target = Path(target_path)

        try:
            logger.info(f"Starting drive-level hash calculation for: {target_path}")

            # Initialize hash objects
            md5_hash = hashlib.md5()
            sha1_hash = hashlib.sha1()
            sha256_hash = hashlib.sha256()

            total_size = 0
            file_count = 0

            if target.is_file():
                # Single file (disk image)
                target_type = "file"
                file_count = 1
                total_size = target.stat().st_size

                logger.info(f"Processing disk image: {target.name} ({total_size:,} bytes)")

                with open(target, 'rb') as f:
                    chunk_size = 1024 * 1024  # 1MB chunks for large images
                    processed = 0

                    while chunk := f.read(chunk_size):
                        md5_hash.update(chunk)
                        sha1_hash.update(chunk)
                        sha256_hash.update(chunk)

                        processed += len(chunk)
                        if processed % (100 * 1024 * 1024) == 0:  # Progress every 100MB
                            progress = (processed / total_size) * 100
                            logger.info(f"Progress: {progress:.1f}% ({processed:,} / {total_size:,} bytes)")

            elif target.is_dir():
                # Directory (evidence collection)
                target_type = "directory"

                logger.info(f"Processing evidence directory: {target}")

                # Walk through all files and subdirectories
                for root, dirs, files in os.walk(target):
                    # Sort for consistent ordering
                    dirs.sort()
                    files.sort()

                    for filename in files:
                        file_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(file_path, target)

                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            file_count += 1

                            # Hash the relative path (for structure integrity)
                            path_bytes = relative_path.encode('utf-8')
                            md5_hash.update(path_bytes)
                            sha1_hash.update(path_bytes)
                            sha256_hash.update(path_bytes)

                            # Hash the file content
                            with open(file_path, 'rb') as f:
                                chunk_size = 64 * 1024  # 64KB chunks
                                while chunk := f.read(chunk_size):
                                    md5_hash.update(chunk)
                                    sha1_hash.update(chunk)
                                    sha256_hash.update(chunk)

                            if file_count % 100 == 0:  # Progress every 100 files
                                logger.info(f"Processed {file_count} files, {total_size:,} bytes total")

                        except (IOError, OSError) as e:
                            logger.warning(f"Could not read file {file_path}: {e}")
                            # Hash the error condition for consistency
                            error_bytes = f"<UNREADABLE:{relative_path}>".encode('utf-8')
                            md5_hash.update(error_bytes)
                            sha1_hash.update(error_bytes)
                            sha256_hash.update(error_bytes)

            else:
                raise ValueError(f"Target path does not exist or is not accessible: {target_path}")

            # Calculate final hashes
            processing_time = time.time() - start_time

            result = DriveHashResult(
                target_path=str(target),
                target_type=target_type,
                total_size=total_size,
                file_count=file_count,
                md5_hash=md5_hash.hexdigest(),
                sha1_hash=sha1_hash.hexdigest(),
                sha256_hash=sha256_hash.hexdigest(),
                timestamp=datetime.datetime.now().isoformat(),
                processing_time=processing_time,
                status="SUCCESS"
            )

            logger.info(f"Drive-level hash calculation completed:")
            logger.info(f"  Target: {result.target_path}")
            logger.info(f"  Type: {result.target_type}")
            logger.info(f"  Files: {result.file_count:,}")
            logger.info(f"  Size: {result.total_size:,} bytes")
            logger.info(f"  Time: {result.processing_time:.2f} seconds")
            logger.info(f"  MD5: {result.md5_hash}")
            logger.info(f"  SHA1: {result.sha1_hash}")
            logger.info(f"  SHA256: {result.sha256_hash}")

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Error calculating drive hash for {target_path}: {str(e)}"
            logger.error(error_msg)

            return DriveHashResult(
                target_path=str(target),
                target_type="unknown",
                total_size=0,
                file_count=0,
                md5_hash="",
                sha1_hash="",
                sha256_hash="",
                timestamp=datetime.datetime.now().isoformat(),
                processing_time=processing_time,
                status="ERROR",
                error_message=error_msg
            )

    def verify_drive_integrity(self, target_path: str, original_hashes: Dict[str, str]) -> DriveVerification:
        """
        Verify drive integrity by recalculating and comparing hashes

        Args:
            target_path (str): Path to target to verify
            original_hashes (dict): Original hash values {'md5': '...', 'sha1': '...', 'sha256': '...'}

        Returns:
            DriveVerification: Verification results
        """
        logger.info(f"Starting drive integrity verification for: {target_path}")

        # Recalculate current hashes
        current_result = self.calculate_drive_hash(target_path)

        if current_result.status == "ERROR":
            return DriveVerification(
                original_md5=original_hashes.get('md5', ''),
                original_sha1=original_hashes.get('sha1', ''),
                original_sha256=original_hashes.get('sha256', ''),
                current_md5="",
                current_sha1="",
                current_sha256="",
                integrity_maintained=False,
                timestamp=datetime.datetime.now().isoformat(),
                details={'error': True, 'md5_match': False, 'sha1_match': False, 'sha256_match': False}
            )

        # Compare hashes
        md5_match = current_result.md5_hash == original_hashes.get('md5', '')
        sha1_match = current_result.sha1_hash == original_hashes.get('sha1', '')
        sha256_match = current_result.sha256_hash == original_hashes.get('sha256', '')

        integrity_maintained = md5_match and sha1_match and sha256_match

        verification = DriveVerification(
            original_md5=original_hashes.get('md5', ''),
            original_sha1=original_hashes.get('sha1', ''),
            original_sha256=original_hashes.get('sha256', ''),
            current_md5=current_result.md5_hash,
            current_sha1=current_result.sha1_hash,
            current_sha256=current_result.sha256_hash,
            integrity_maintained=integrity_maintained,
            timestamp=datetime.datetime.now().isoformat(),
            details={
                'md5_match': md5_match,
                'sha1_match': sha1_match,
                'sha256_match': sha256_match,
                'error': False
            }
        )

        # Log verification results
        status = "VERIFIED" if integrity_maintained else "COMPROMISED"
        logger.info(f"Drive integrity verification completed: {status}")
        logger.info(f"  MD5 Match: {'✓' if md5_match else '✗'}")
        logger.info(f"  SHA1 Match: {'✓' if sha1_match else '✗'}")
        logger.info(f"  SHA256 Match: {'✓' if sha256_match else '✗'}")

        self.verification_log.append(verification)
        return verification

    def generate_drive_report(self, hash_results: List[DriveHashResult],
                            verification_results: List[DriveVerification] = None) -> str:
        """
        Generate comprehensive drive-level forensic report - Single Hash Only

        Args:
            hash_results: List of drive hash calculation results (only first one will be used)
            verification_results: List of verification results (optional)

        Returns:
            str: Path to generated report file
        """
        report_path = self.output_path / f"DriveHash_Report_{self.case_id}.txt"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("DRIVE-LEVEL HASHDEEP FORENSIC REPORT\n")
                f.write("=" * 80 + "\n\n")

                f.write(f"Case ID: {self.case_id}\n")
                f.write(f"Report Generated: {datetime.datetime.now().isoformat()}\n")

                # Only process the first (main) drive hash result
                if hash_results and hash_results[0].status == "SUCCESS":
                    main_result = hash_results[0]
                    f.write(f"Evidence Path: {main_result.target_path}\n")
                    f.write(f"Total Files: {main_result.file_count:,}\n")
                    f.write(f"Total Size: {main_result.total_size:,} bytes\n\n")

                    f.write("SINGLE DRIVE HASH VERIFICATION\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Target: {main_result.target_type.title()}\n")
                    f.write(f"Processing Time: {main_result.processing_time:.2f} seconds\n")
                    f.write(f"Status: {main_result.status}\n\n")

                    f.write("CRYPTOGRAPHIC HASHES\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"MD5:    {main_result.md5_hash}\n")
                    f.write(f"SHA1:   {main_result.sha1_hash}\n")
                    f.write(f"SHA256: {main_result.sha256_hash}\n")
                    f.write(f"Timestamp: {main_result.timestamp}\n")
                else:
                    f.write("Status: FAILED - No valid hash results\n")

                f.write("\n")

                # Verification Results (if any)
                if verification_results and verification_results[0].integrity_maintained:
                    f.write("INTEGRITY VERIFICATION\n")
                    f.write("-" * 40 + "\n")
                    f.write("Status: VERIFIED\n")
                    f.write("MD5 Match: PASS\n")
                    f.write("SHA1 Match: PASS\n")
                    f.write("SHA256 Match: PASS\n")
                    f.write(f"Verification Time: {verification_results[0].timestamp}\n")
                elif verification_results:
                    f.write("INTEGRITY VERIFICATION\n")
                    f.write("-" * 40 + "\n")
                    f.write("Status: COMPROMISED\n")
                    f.write(f"MD5 Match: {'PASS' if verification_results[0].details['md5_match'] else 'FAIL'}\n")
                    f.write(f"SHA1 Match: {'PASS' if verification_results[0].details['sha1_match'] else 'FAIL'}\n")
                    f.write(f"SHA256 Match: {'PASS' if verification_results[0].details['sha256_match'] else 'FAIL'}\n")
                    f.write(f"Verification Time: {verification_results[0].timestamp}\n")

                # Verification Results
                if verification_results:
                    f.write("\n\nDRIVE VERIFICATION RESULTS\n")
                    f.write("-" * 40 + "\n")

                    for i, verification in enumerate(verification_results, 1):
                        status_symbol = "✓" if verification.integrity_maintained else "✗"
                        status_text = "VERIFIED" if verification.integrity_maintained else "COMPROMISED"

                        f.write(f"\n[{i}] {status_symbol} {status_text}\n")
                        f.write(f"MD5 Match: {'✓' if verification.details['md5_match'] else '✗'}\n")
                        f.write(f"SHA1 Match: {'✓' if verification.details['sha1_match'] else '✗'}\n")
                        f.write(f"SHA256 Match: {'✓' if verification.details['sha256_match'] else '✗'}\n")
                        f.write(f"Verification Time: {verification.timestamp}\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF REPORT\n")
                f.write("=" * 80 + "\n")

            logger.info(f"Drive-level forensic report generated: {report_path}")
            return str(report_path)

        except Exception as e:
            error_msg = f"Error generating drive report: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

# Example usage and testing


def main(evidence_path: str, output_path: str = None):
    """
    Wrapper entry point for script_3.py
    Runs a single hash calculation and generates a report.
    """
    if not os.path.exists(evidence_path):
        raise FileNotFoundError(f"Evidence path not found: {evidence_path}")

    # Auto-generate case ID
    filename = os.path.basename(evidence_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    case_id = f"CASE_{filename}_{timestamp}".replace(".", "_")

    # Default output path (inside tools/hashdeep/Initial_Hash_output if not given)
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "Initial_Hash_output")

    processor = DriveHashProcessor(case_id, output_path)

    result = processor.calculate_drive_hash(evidence_path)
    report_path = None
    if result.status == "SUCCESS":
        report_path = processor.generate_drive_report([result])

    return {
        "result": result,
        "report": report_path
    }


if __name__ == "__main__":
    print("=" * 80)
    print("EDITH-Automater HashDeep Drive-Level Module")
    print("=" * 80)
    print("This tool calculates cryptographic hashes for disk images and directories")
    print("Supported formats: .E01, .DD, .IMG, directories, and other disk images")
    print()

    # Get disk image/directory path from user
    while True:
        disk_image_path = input("Enter the path to your disk image or directory: ").strip()

        # Remove quotes if user added them
        if disk_image_path.startswith('"') and disk_image_path.endswith('"'):
            disk_image_path = disk_image_path[1:-1]

        # Check if path exists
        if os.path.exists(disk_image_path):
            break
        else:
            print(f"Error: Path '{disk_image_path}' does not exist. Please try again.")
            print()

    # Auto-generate case ID based on filename and timestamp
    filename = os.path.basename(disk_image_path)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    case_id = f"CASE_{filename}_{timestamp}".replace(".", "_")

    # Set output path - use relative path from script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "Initial_Hash_output")

    print()
    print(f"Target: {disk_image_path}")
    print(f"Case ID: {case_id}")
    print(f"Output: {output_path}")
    print()

    # Get file/directory size for estimation
    if os.path.isfile(disk_image_path):
        file_size = os.path.getsize(disk_image_path)
        print(f"File Size: {file_size:,} bytes ({file_size / (1024**3):.2f} GB)")
    elif os.path.isdir(disk_image_path):
        print("Processing directory - calculating total size...")

    print("\nStarting hash calculation...")
    print("This may take several minutes for large files/directories...")
    print("Progress will be displayed every 100MB processed.")
    print()

    # Initialize processor
    processor = DriveHashProcessor(case_id, output_path)

    # Calculate hash
    result = processor.calculate_drive_hash(disk_image_path)

    # Generate report
    if result.status == "SUCCESS":
        report_path = processor.generate_drive_report([result])
        print()
        print("=" * 80)
        print("HASH CALCULATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Target: {result.target_path}")
        print(f"Type: {result.target_type.title()}")
        print(f"Files Processed: {result.file_count:,}")
        print(f"Total Size: {result.total_size:,} bytes")
        print(f"Processing Time: {result.processing_time:.2f} seconds")
        print()
        print("CRYPTOGRAPHIC HASHES:")
        print(f"MD5:    {result.md5_hash}")
        print(f"SHA1:   {result.sha1_hash}")
        print(f"SHA256: {result.sha256_hash}")
        print()
        print(f"Forensic Report: {report_path}")
        print("=" * 80)
    else:
        print()
        print("=" * 80)
        print("HASH CALCULATION FAILED!")
        print("=" * 80)
        print(f"Error: {result.error_message}")
        print("=" * 80)
