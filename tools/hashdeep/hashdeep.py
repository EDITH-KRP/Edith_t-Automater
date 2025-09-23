#!/usr/bin/env python3
"""
HashDeep Module for EDITH-Automater
====================================

This module provides cryptographic hash verification capabilities for digital forensics.
It ensures evidence integrity throughout the forensic investigation process by calculating
and verifying MD5, SHA-1, and SHA-256 hash values for files and disk images.

Key Functions:
- Evidence integrity verification
- Forensic image validation
- Individual file hashing
- Hash database creation
- Known file filtering
- Chain of custody documentation

Author: ADITHYA N T
Version: 1.0
Date: September 2025
"""

import os
import sys
import json
import hashlib
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import csv
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [HashDeep] %(message)s',
    handlers=[
        logging.FileHandler('hashdeep.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HashResult:
    """Data structure for storing hash calculation results"""
    file_path: str
    file_size: int
    md5_hash: str
    sha1_hash: str
    sha256_hash: str
    timestamp: str
    status: str  # 'SUCCESS', 'ERROR', 'MISMATCH'
    error_message: Optional[str] = None

@dataclass
class HashVerification:
    """Data structure for hash verification results"""
    original_hash: str
    current_hash: str
    algorithm: str
    verified: bool
    timestamp: str

class HashDeepProcessor:
    """
    Main HashDeep processing class for EDITH-Automater
    
    This class handles all hash-related operations including:
    - Calculating hashes for files and images
    - Verifying evidence integrity
    - Creating hash databases
    - Generating forensic reports
    """
    
    def __init__(self, case_id: str, evidence_path: str, output_path: str):
        """
        Initialize HashDeep processor
        
        Args:
            case_id (str): Unique case identifier
            evidence_path (str): Path to evidence files
            output_path (str): Path for output reports
        """
        self.case_id = case_id
        self.evidence_path = Path(evidence_path)
        self.output_path = Path(output_path)
        self.hash_database = []
        self.verification_log = []
        
        # Create output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize case log
        self.case_log_path = self.output_path / f"hashdeep_case_{case_id}.log"
        self._setup_case_logging()
        
        logger.info(f"HashDeep processor initialized for case: {case_id}")
    
    def _setup_case_logging(self):
        """Setup case-specific logging"""
        case_handler = logging.FileHandler(self.case_log_path)
        case_handler.setLevel(logging.INFO)
        case_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [CASE-{}] %(message)s'.format(self.case_id)
        )
        case_handler.setFormatter(case_formatter)
        logger.addHandler(case_handler)
    
    def calculate_file_hash(self, file_path: str, algorithms: List[str] = None) -> HashResult:
        """
        Calculate hash values for a single file
        
        Args:
            file_path (str): Path to the file
            algorithms (List[str]): Hash algorithms to use ['md5', 'sha1', 'sha256']
        
        Returns:
            HashResult: Hash calculation results
        """
        if algorithms is None:
            algorithms = ['md5', 'sha1', 'sha256']
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return HashResult(
                file_path=str(file_path),
                file_size=0,
                md5_hash="",
                sha1_hash="",
                sha256_hash="",
                timestamp=datetime.datetime.now().isoformat(),
                status="ERROR",
                error_message=error_msg
            )
        
        try:
            # Initialize hash objects
            hash_objects = {}
            if 'md5' in algorithms:
                hash_objects['md5'] = hashlib.md5()
            if 'sha1' in algorithms:
                hash_objects['sha1'] = hashlib.sha1()
            if 'sha256' in algorithms:
                hash_objects['sha256'] = hashlib.sha256()
            
            file_size = file_path.stat().st_size
            logger.info(f"Calculating hashes for: {file_path} ({file_size} bytes)")
            
            # Read file in chunks to handle large files
            chunk_size = 8192
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    for hash_obj in hash_objects.values():
                        hash_obj.update(chunk)
            
            # Get final hash values
            result = HashResult(
                file_path=str(file_path),
                file_size=file_size,
                md5_hash=hash_objects.get('md5', hashlib.md5()).hexdigest() if 'md5' in algorithms else "",
                sha1_hash=hash_objects.get('sha1', hashlib.sha1()).hexdigest() if 'sha1' in algorithms else "",
                sha256_hash=hash_objects.get('sha256', hashlib.sha256()).hexdigest() if 'sha256' in algorithms else "",
                timestamp=datetime.datetime.now().isoformat(),
                status="SUCCESS"
            )
            
            logger.info(f"Hash calculation completed for: {file_path}")
            logger.info(f"MD5: {result.md5_hash}")
            logger.info(f"SHA1: {result.sha1_hash}")
            logger.info(f"SHA256: {result.sha256_hash}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error calculating hash for {file_path}: {str(e)}"
            logger.error(error_msg)
            return HashResult(
                file_path=str(file_path),
                file_size=0,
                md5_hash="",
                sha1_hash="",
                sha256_hash="",
                timestamp=datetime.datetime.now().isoformat(),
                status="ERROR",
                error_message=error_msg
            )
    
    def verify_hash(self, file_path: str, expected_hash: str, algorithm: str = 'md5') -> HashVerification:
        """
        Verify file integrity by comparing with expected hash
        
        Args:
            file_path (str): Path to file to verify
            expected_hash (str): Expected hash value
            algorithm (str): Hash algorithm used
        
        Returns:
            HashVerification: Verification results
        """
        logger.info(f"Verifying {algorithm.upper()} hash for: {file_path}")
        
        # Calculate current hash
        hash_result = self.calculate_file_hash(file_path, [algorithm.lower()])
        
        if hash_result.status == "ERROR":
            return HashVerification(
                original_hash=expected_hash,
                current_hash="",
                algorithm=algorithm.upper(),
                verified=False,
                timestamp=datetime.datetime.now().isoformat()
            )
        
        # Get the appropriate hash value
        if algorithm.lower() == 'md5':
            current_hash = hash_result.md5_hash
        elif algorithm.lower() == 'sha1':
            current_hash = hash_result.sha1_hash
        elif algorithm.lower() == 'sha256':
            current_hash = hash_result.sha256_hash
        else:
            logger.error(f"Unsupported algorithm: {algorithm}")
            current_hash = ""
        
        # Verify hash match
        verified = current_hash.lower() == expected_hash.lower()
        
        verification = HashVerification(
            original_hash=expected_hash,
            current_hash=current_hash,
            algorithm=algorithm.upper(),
            verified=verified,
            timestamp=datetime.datetime.now().isoformat()
        )
        
        if verified:
            logger.info(f"PASS - Hash verification PASSED for: {file_path}")
        else:
            logger.error(f"FAIL - Hash verification FAILED for: {file_path}")
            logger.error(f"Expected: {expected_hash}")
            logger.error(f"Current:  {current_hash}")
        
        self.verification_log.append(verification)
        return verification
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> List[HashResult]:
        """
        Process all files in a directory and calculate hashes
        
        Args:
            directory_path (str): Path to directory
            recursive (bool): Process subdirectories recursively
        
        Returns:
            List[HashResult]: List of hash results for all files
        """
        directory = Path(directory_path)
        results = []
        
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return results
        
        logger.info(f"Processing directory: {directory} (recursive: {recursive})")
        
        # Get all files
        if recursive:
            files = list(directory.rglob('*'))
        else:
            files = list(directory.glob('*'))
        
        # Filter only files (not directories)
        files = [f for f in files if f.is_file()]
        
        total_files = len(files)
        logger.info(f"Found {total_files} files to process")
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"Processing file {i}/{total_files}: {file_path}")
            result = self.calculate_file_hash(str(file_path))
            results.append(result)
            self.hash_database.append(result)
        
        logger.info(f"Directory processing completed. Processed {len(results)} files")
        return results
    
    def create_hash_database(self, file_list: List[str]) -> str:
        """
        Create a comprehensive hash database for multiple files
        
        Args:
            file_list (List[str]): List of file paths to process
        
        Returns:
            str: Path to created database file
        """
        logger.info(f"Creating hash database for {len(file_list)} files")
        
        database_path = self.output_path / f"hashdeep_database_{self.case_id}.csv"
        
        with open(database_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'file_path', 'file_size', 'md5_hash', 'sha1_hash', 
                'sha256_hash', 'timestamp', 'status', 'error_message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for file_path in file_list:
                result = self.calculate_file_hash(file_path)
                writer.writerow({
                    'file_path': result.file_path,
                    'file_size': result.file_size,
                    'md5_hash': result.md5_hash,
                    'sha1_hash': result.sha1_hash,
                    'sha256_hash': result.sha256_hash,
                    'timestamp': result.timestamp,
                    'status': result.status,
                    'error_message': result.error_message or ''
                })
                self.hash_database.append(result)
        
        logger.info(f"Hash database created: {database_path}")
        return str(database_path)
    
    def verify_evidence_integrity(self, evidence_file: str, original_hashes: Dict[str, str]) -> Dict[str, Any]:
        """
        Verify evidence integrity for forensic purposes
        
        Args:
            evidence_file (str): Path to evidence file
            original_hashes (Dict[str, str]): Original hash values
        
        Returns:
            Dict[str, Any]: Verification report
        """
        logger.info(f"Starting evidence integrity verification for: {evidence_file}")
        
        verification_report = {
            'case_id': self.case_id,
            'evidence_file': evidence_file,
            'verification_timestamp': datetime.datetime.now().isoformat(),
            'verifications': [],
            'overall_status': 'UNKNOWN',
            'integrity_maintained': False
        }
        
        all_verified = True
        
        for algorithm, expected_hash in original_hashes.items():
            verification = self.verify_hash(evidence_file, expected_hash, algorithm)
            verification_report['verifications'].append({
                'algorithm': verification.algorithm,
                'original_hash': verification.original_hash,
                'current_hash': verification.current_hash,
                'verified': verification.verified,
                'timestamp': verification.timestamp
            })
            
            if not verification.verified:
                all_verified = False
        
        verification_report['overall_status'] = 'VERIFIED' if all_verified else 'COMPROMISED'
        verification_report['integrity_maintained'] = all_verified
        
        if all_verified:
            logger.info("PASS - EVIDENCE INTEGRITY VERIFIED - All hashes match")
        else:
            logger.error("FAIL - EVIDENCE INTEGRITY COMPROMISED - Hash mismatch detected")
        
        return verification_report
    
    def generate_forensic_report(self) -> str:
        """
        Generate comprehensive forensic hash report
        
        Returns:
            str: Path to generated report
        """
        logger.info("Generating forensic hash report")
        
        report_path = self.output_path / f"HashDeep_Forensic_Report_{self.case_id}.json"
        
        report_data = {
            'case_information': {
                'case_id': self.case_id,
                'report_generated': datetime.datetime.now().isoformat(),
                'evidence_path': str(self.evidence_path),
                'total_files_processed': len(self.hash_database),
                'total_verifications': len(self.verification_log)
            },
            'hash_database': [
                {
                    'file_path': result.file_path,
                    'file_size': result.file_size,
                    'md5_hash': result.md5_hash,
                    'sha1_hash': result.sha1_hash,
                    'sha256_hash': result.sha256_hash,
                    'timestamp': result.timestamp,
                    'status': result.status,
                    'error_message': result.error_message
                }
                for result in self.hash_database
            ],
            'verification_log': [
                {
                    'original_hash': verification.original_hash,
                    'current_hash': verification.current_hash,
                    'algorithm': verification.algorithm,
                    'verified': verification.verified,
                    'timestamp': verification.timestamp
                }
                for verification in self.verification_log
            ],
            'summary': {
                'successful_hashes': len([r for r in self.hash_database if r.status == 'SUCCESS']),
                'failed_hashes': len([r for r in self.hash_database if r.status == 'ERROR']),
                'successful_verifications': len([v for v in self.verification_log if v.verified]),
                'failed_verifications': len([v for v in self.verification_log if not v.verified])
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        # Also create human-readable text report
        text_report_path = self.output_path / f"HashDeep_Report_{self.case_id}.txt"
        with open(text_report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("HASHDEEP FORENSIC REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Case ID: {self.case_id}\n")
            f.write(f"Report Generated: {report_data['case_information']['report_generated']}\n")
            f.write(f"Evidence Path: {report_data['case_information']['evidence_path']}\n")
            f.write(f"Total Files Processed: {report_data['case_information']['total_files_processed']}\n\n")
            
            f.write("SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Successful Hashes: {report_data['summary']['successful_hashes']}\n")
            f.write(f"Failed Hashes: {report_data['summary']['failed_hashes']}\n")
            f.write(f"Successful Verifications: {report_data['summary']['successful_verifications']}\n")
            f.write(f"Failed Verifications: {report_data['summary']['failed_verifications']}\n\n")
            
            if self.verification_log:
                f.write("VERIFICATION RESULTS\n")
                f.write("-" * 40 + "\n")
                for verification in self.verification_log:
                    status = "✓ VERIFIED" if verification.verified else "✗ FAILED"
                    f.write(f"{status} - {verification.algorithm}\n")
                    f.write(f"Original: {verification.original_hash}\n")
                    f.write(f"Current:  {verification.current_hash}\n")
                    f.write(f"Time: {verification.timestamp}\n\n")
        
        logger.info(f"Forensic reports generated:")
        logger.info(f"  JSON Report: {report_path}")
        logger.info(f"  Text Report: {text_report_path}")
        
        return str(report_path)

def main():
    """
    Main function for standalone execution
    """
    if len(sys.argv) < 4:
        print("Usage: python hashdeep.py <case_id> <evidence_path> <output_path> [operation]")
        print("Operations: hash, verify, report")
        sys.exit(1)
    
    case_id = sys.argv[1]
    evidence_path = sys.argv[2]
    output_path = sys.argv[3]
    operation = sys.argv[4] if len(sys.argv) > 4 else "hash"
    
    # Initialize processor
    processor = HashDeepProcessor(case_id, evidence_path, output_path)
    
    try:
        if operation == "hash":
            # Process directory and create hash database
            if os.path.isdir(evidence_path):
                results = processor.process_directory(evidence_path)
                print(f"Processed {len(results)} files")
            else:
                result = processor.calculate_file_hash(evidence_path)
                processor.hash_database.append(result)
                print(f"Hash calculated for: {evidence_path}")
        
        elif operation == "verify":
            # Example verification (would need specific hash values)
            print("Verification mode requires original hash values")
        
        elif operation == "report":
            # Generate forensic report
            report_path = processor.generate_forensic_report()
            print(f"Report generated: {report_path}")
        
        else:
            print(f"Unknown operation: {operation}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error during operation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()