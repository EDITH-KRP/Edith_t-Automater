#!/usr/bin/env python3
"""
FTK Image Metadata Capture Module
Extract metadata from FTK Imager-created forensic image files
Works with: E01, EWF, DD, SMART, AD1 formats
"""

import os
import sys
import json
import struct
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Try to import libewf for E01 analysis
try:
    import pyewf
    EWF_AVAILABLE = True
except ImportError:
    EWF_AVAILABLE = False

# Try to import pytsk3 for image analysis
try:
    import pytsk3
    TSK_AVAILABLE = True
except ImportError:
    TSK_AVAILABLE = False


class FTKImageAnalyzer:
    """
    Analyze FTK Imager-created forensic images
    Extracts metadata, hashes, and evidence information
    """

    def __init__(self, image_path: str):
        """
        Initialize analyzer with image file path
        
        Args:
            image_path: Path to FTK image file (.E01, .dd, etc.)
        """
        self.image_path = Path(image_path)
        self.logger = logging.getLogger(__name__)
        self.metadata = {}
        
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
    
    def get_image_format(self) -> str:
        """Detect image format from file extension"""
        extension = self.image_path.suffix.upper()
        
        format_map = {
            '.E01': 'EWF (Encase)',
            '.001': 'EWF (Encase)',
            '.DD': 'Raw DD',
            '.IMG': 'Raw Image',
            '.ISO': 'ISO Image',
            '.VHD': 'Virtual Hard Disk',
            '.VMDK': 'Virtual Machine Disk',
            '.AD1': 'AccessData SMART'
        }
        
        return format_map.get(extension, f'Unknown ({extension})')
    
    def extract_e01_metadata(self) -> Dict:
        """
        Extract metadata from EWF (.E01) image files
        Requires: pyewf library
        """
        if not EWF_AVAILABLE:
            self.logger.warning("pyewf not installed. Install with: pip install libewf-python")
            return {}
        
        try:
            ewf_handle = pyewf.glob(str(self.image_path))
            if not ewf_handle:
                self.logger.error("Could not open EWF image")
                return {}
            
            metadata = {
                'format': 'EWF (Encase)',
                'segment_count': len(ewf_handle),
                'sectors': ewf_handle[0].media_size // 512,
                'media_size_bytes': ewf_handle[0].media_size,
                'bytes_per_sector': 512,
                'sector_count': ewf_handle[0].media_size // 512,
                'segments': []
            }
            
            # Extract info from first segment (header)
            first_seg = ewf_handle[0]
            
            # Get acquisition details
            for info_type in range(pyewf.LIBEWF_HANDLE_VALUE_TYPE_UNKNOWN):
                try:
                    value = first_seg.get_header_value(info_type)
                    if value:
                        metadata[f'header_{info_type}'] = value
                except:
                    pass
            
            # Get hash values from image header
            try:
                metadata['md5_hash'] = first_seg.get_header_value('hash')
            except:
                pass
            
            # Get segment file names
            for i, segment in enumerate(ewf_handle):
                try:
                    metadata['segments'].append({
                        'number': i + 1,
                        'size_bytes': segment.media_size,
                        'file': segment.filename if hasattr(segment, 'filename') else 'unknown'
                    })
                except:
                    pass
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting E01 metadata: {e}")
            return {}
    
    def extract_raw_image_metadata(self) -> Dict:
        """
        Extract metadata from raw image files (.dd, .img)
        """
        try:
            file_size = self.image_path.stat().st_size
            
            metadata = {
                'format': self.get_image_format(),
                'file_size_bytes': file_size,
                'sectors': file_size // 512,
                'bytes_per_sector': 512,
                'file_name': self.image_path.name,
                'file_path': str(self.image_path)
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting raw image metadata: {e}")
            return {}
    
    def calculate_image_hash(self, algorithm: str = 'md5', chunk_size: int = 8192) -> str:
        """
        Calculate hash of image file
        
        Args:
            algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
            chunk_size: Bytes to read at a time
        
        Returns:
            Hash string
        """
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(self.image_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        
        except Exception as e:
            self.logger.error(f"Error calculating {algorithm} hash: {e}")
            return ""
    
    def extract_ftk_log_info(self) -> Dict:
        """
        Look for FTK Imager log files and extract metadata
        FTK typically creates .log files next to the image
        """
        metadata = {}
        
        # Check for .log file in same directory
        log_file = self.image_path.parent / f"{self.image_path.stem}.log"
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Extract common FTK log info
                    lines = content.split('\n')
                    for line in lines:
                        if 'Source:' in line:
                            metadata['source_device'] = line.split(':', 1)[1].strip()
                        elif 'MD5:' in line or 'md5:' in line:
                            metadata['md5_hash'] = line.split(':', 1)[1].strip()
                        elif 'SHA1:' in line or 'sha1:' in line:
                            metadata['sha1_hash'] = line.split(':', 1)[1].strip()
                        elif 'SHA256:' in line or 'sha256:' in line:
                            metadata['sha256_hash'] = line.split(':', 1)[1].strip()
                        elif 'Case:' in line or 'Evidence:' in line:
                            metadata['case_info'] = line.split(':', 1)[1].strip()
                        elif 'Created:' in line or 'Date:' in line:
                            metadata['created_date'] = line.split(':', 1)[1].strip()
                
                self.logger.info(f"Extracted FTK log info from: {log_file}")
            
            except Exception as e:
                self.logger.warning(f"Could not parse FTK log file: {e}")
        
        return metadata
    
    def check_verification_file(self) -> Dict:
        """
        Look for FTK verification files (.txt, .ver, .verify)
        FTK often creates verification reports with hashes
        """
        metadata = {}
        verify_extensions = ['.txt', '.ver', '.verify', '.hash', '.md5']
        
        for ext in verify_extensions:
            verify_file = self.image_path.parent / f"{self.image_path.stem}{ext}"
            
            if verify_file.exists():
                try:
                    with open(verify_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Parse hash information
                        if 'md5' in content.lower():
                            for line in content.split('\n'):
                                if 'md5' in line.lower():
                                    parts = line.split(':', 1)
                                    if len(parts) == 2:
                                        metadata['md5_hash'] = parts[1].strip()
                        
                        if 'sha' in content.lower():
                            for line in content.split('\n'):
                                if 'sha' in line.lower():
                                    if '256' in line:
                                        parts = line.split(':', 1)
                                        if len(parts) == 2:
                                            metadata['sha256_hash'] = parts[1].strip()
                                    elif '1' in line and '256' not in line:
                                        parts = line.split(':', 1)
                                        if len(parts) == 2:
                                            metadata['sha1_hash'] = parts[1].strip()
                        
                        metadata['verify_file'] = str(verify_file)
                
                except Exception as e:
                    self.logger.warning(f"Could not parse verify file {verify_file}: {e}")
        
        return metadata
    
    def analyze_with_pytsk3(self) -> Dict:
        """
        Use pytsk3 to analyze image file system
        Extracts partition and file system information
        """
        if not TSK_AVAILABLE:
            return {}
        
        try:
            img = pytsk3.Img_Info(str(self.image_path))
            
            metadata = {
                'image_size': img.get_size(),
                'partitions': []
            }
            
            # Try to get partition information
            try:
                vol = pytsk3.TSK_VS_Info(img)
                
                for addr in vol:
                    part_info = {
                        'address': addr.addr,
                        'flags': addr.flags,
                        'start_sector': addr.start,
                        'sector_count': addr.len,
                        'description': addr.desc.decode('utf-8', errors='ignore') if addr.desc else ''
                    }
                    metadata['partitions'].append(part_info)
            
            except Exception as e:
                self.logger.debug(f"Could not analyze partitions: {e}")
            
            return metadata
        
        except Exception as e:
            self.logger.warning(f"Could not use pytsk3 analyzer: {e}")
            return {}
    
    def extract_all_metadata(self) -> Dict:
        """
        Extract all available metadata from image
        
        Returns:
            Complete metadata dictionary
        """
        self.logger.info(f"Analyzing FTK image: {self.image_path}")
        
        # Start with basic file info
        all_metadata = {
            'image_file': str(self.image_path),
            'file_name': self.image_path.name,
            'file_size_bytes': self.image_path.stat().st_size,
            'file_created': datetime.fromtimestamp(
                self.image_path.stat().st_ctime
            ).isoformat(),
            'file_modified': datetime.fromtimestamp(
                self.image_path.stat().st_mtime
            ).isoformat(),
            'format': self.get_image_format()
        }
        
        # Extract format-specific metadata
        if self.image_path.suffix.upper() in ['.E01', '.001']:
            all_metadata.update(self.extract_e01_metadata())
        else:
            all_metadata.update(self.extract_raw_image_metadata())
        
        # Extract FTK-specific metadata
        all_metadata.update(self.extract_ftk_log_info())
        
        # Check for verification files
        all_metadata.update(self.check_verification_file())
        
        # Calculate image hashes if not already present
        if 'md5_hash' not in all_metadata:
            self.logger.info("Calculating MD5 hash (this may take a while)...")
            all_metadata['md5_hash'] = self.calculate_image_hash('md5')
        
        if 'sha1_hash' not in all_metadata:
            self.logger.info("Calculating SHA1 hash...")
            all_metadata['sha1_hash'] = self.calculate_image_hash('sha1')
        
        if 'sha256_hash' not in all_metadata:
            self.logger.info("Calculating SHA256 hash...")
            all_metadata['sha256_hash'] = self.calculate_image_hash('sha256')
        
        # Extract pytsk3 metadata
        all_metadata.update(self.analyze_with_pytsk3())
        
        self.metadata = all_metadata
        return all_metadata
    
    def save_metadata_json(self, output_path: str) -> bool:
        """
        Save extracted metadata to JSON file
        
        Args:
            output_path: Path to save JSON file
        
        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            self.logger.info(f"Metadata saved to: {output_path}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error saving metadata: {e}")
            return False
    
    def get_report_dict(self) -> Dict:
        """
        Get metadata formatted for report generation
        
        Returns:
            Dictionary suitable for HTML/PDF report templates
        """
        meta = self.metadata
        
        report_dict = {
            'image_file': meta.get('image_file', ''),
            'file_name': meta.get('file_name', ''),
            'format': meta.get('format', ''),
            'file_size_gb': round(meta.get('file_size_bytes', 0) / (1024**3), 2),
            'file_size_bytes': meta.get('file_size_bytes', 0),
            'sectors': meta.get('sectors', 0) or meta.get('media_size_bytes', 0) // 512,
            'bytes_per_sector': meta.get('bytes_per_sector', 512),
            'md5': meta.get('md5_hash', 'Not calculated'),
            'sha1': meta.get('sha1_hash', 'Not calculated'),
            'sha256': meta.get('sha256_hash', 'Not calculated'),
            'file_created': meta.get('file_created', ''),
            'file_modified': meta.get('file_modified', ''),
            'source_device': meta.get('source_device', 'Unknown'),
            'case_info': meta.get('case_info', ''),
            'partition_count': len(meta.get('partitions', [])),
            'segment_count': len(meta.get('segments', []))
        }
        
        return report_dict


def main():
    """Command-line interface for FTK image analysis"""
    import argparse
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(
        description='Extract metadata from FTK Imager forensic images'
    )
    parser.add_argument('image_file', help='Path to FTK image file (.E01, .dd, etc.)')
    parser.add_argument('-o', '--output', help='Output JSON file for metadata')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        analyzer = FTKImageAnalyzer(args.image_file)
        metadata = analyzer.extract_all_metadata()
        
        # Print results
        print("\n" + "="*80)
        print("FTK IMAGE METADATA EXTRACTION")
        print("="*80)
        print(json.dumps(metadata, indent=2))
        
        # Save if output specified
        if args.output:
            analyzer.save_metadata_json(args.output)
            print(f"\n✓ Metadata saved to: {args.output}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
