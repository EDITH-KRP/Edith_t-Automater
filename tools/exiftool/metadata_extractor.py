#!/usr/bin/env python3
"""
Metadata Extraction and Export Tool
Extracts metadata from various file types and exports to CSV/JSON formats
"""

import os
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import mimetypes

# Import libraries for different file types
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import exifread
    EXIFREAD_AVAILABLE = True
except ImportError:
    EXIFREAD_AVAILABLE = False

try:
    from mutagen import File as MutagenFile
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
    HACHOIR_AVAILABLE = True
except ImportError:
    HACHOIR_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

import pandas as pd


class MetadataExtractor:
    """Main class for extracting metadata from various file types"""
    
    def __init__(self, input_directory: str = "input_files", output_directory: str = "output"):
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_directory / 'extraction.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Supported file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
        self.audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma'}
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        
    def get_file_basic_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file system information"""
        try:
            stat = file_path.stat()
            return {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed_time': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'file_extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0]
            }
        except Exception as e:
            self.logger.error(f"Error getting basic info for {file_path}: {e}")
            return {'filename': file_path.name, 'error': str(e)}
    
    def get_magic_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file type information using python-magic"""
        magic_info = {}
        if MAGIC_AVAILABLE:
            try:
                magic_info['magic_mime'] = magic.from_file(str(file_path), mime=True)
                magic_info['magic_description'] = magic.from_file(str(file_path))
            except Exception as e:
                self.logger.warning(f"Magic detection failed for {file_path}: {e}")
        return magic_info
    
    def extract_image_metadata_pil(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata using PIL"""
        metadata = {}
        if not PIL_AVAILABLE:
            return metadata
        
        try:
            with Image.open(file_path) as img:
                # Basic image info
                metadata.update({
                    'image_width': img.width,
                    'image_height': img.height,
                    'image_mode': img.mode,
                    'image_format': img.format
                })
                
                # EXIF data
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        # Convert bytes to string if needed
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8')
                            except:
                                value = str(value)
                        metadata[f'exif_{tag}'] = value
                        
        except Exception as e:
            self.logger.error(f"PIL extraction failed for {file_path}: {e}")
            metadata['pil_error'] = str(e)
        
        return metadata
    
    def extract_image_metadata_exifread(self, file_path: Path) -> Dict[str, Any]:
        """Extract image metadata using exifread"""
        metadata = {}
        if not EXIFREAD_AVAILABLE:
            return metadata
        
        try:
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                for tag, value in tags.items():
                    metadata[f'exifread_{tag}'] = str(value)
        except Exception as e:
            self.logger.error(f"ExifRead extraction failed for {file_path}: {e}")
            metadata['exifread_error'] = str(e)
        
        return metadata
    
    def extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract audio metadata using mutagen"""
        metadata = {}
        if not MUTAGEN_AVAILABLE:
            return metadata
        
        try:
            audio_file = MutagenFile(file_path)
            if audio_file is not None:
                # Basic audio info
                if hasattr(audio_file, 'info'):
                    info = audio_file.info
                    metadata.update({
                        'audio_length': getattr(info, 'length', None),
                        'audio_bitrate': getattr(info, 'bitrate', None),
                        'audio_sample_rate': getattr(info, 'sample_rate', None),
                        'audio_channels': getattr(info, 'channels', None)
                    })
                
                # Tags
                if audio_file.tags:
                    for key, value in audio_file.tags.items():
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value)
                        metadata[f'audio_{key}'] = str(value)
                        
        except Exception as e:
            self.logger.error(f"Audio extraction failed for {file_path}: {e}")
            metadata['audio_error'] = str(e)
        
        return metadata
    
    def extract_hachoir_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using hachoir"""
        metadata = {}
        if not HACHOIR_AVAILABLE:
            return metadata
        
        try:
            parser = createParser(str(file_path))
            if parser:
                with parser:
                    hachoir_metadata = extractMetadata(parser)
                    if hachoir_metadata:
                        for line in hachoir_metadata.exportPlaintext():
                            if ':' in line:
                                key, value = line.split(':', 1)
                                metadata[f'hachoir_{key.strip()}'] = value.strip()
        except Exception as e:
            self.logger.error(f"Hachoir extraction failed for {file_path}: {e}")
            metadata['hachoir_error'] = str(e)
        
        return metadata
    
    def extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract all available metadata from a file"""
        self.logger.info(f"Processing: {file_path}")
        
        # Start with basic file info
        metadata = self.get_file_basic_info(file_path)
        
        # Add magic file type detection
        metadata.update(self.get_magic_info(file_path))
        
        # Extract type-specific metadata
        file_ext = file_path.suffix.lower()
        
        if file_ext in self.image_extensions:
            metadata.update(self.extract_image_metadata_pil(file_path))
            metadata.update(self.extract_image_metadata_exifread(file_path))
        
        if file_ext in self.audio_extensions:
            metadata.update(self.extract_audio_metadata(file_path))
        
        # Try hachoir for all file types (it supports many formats)
        metadata.update(self.extract_hachoir_metadata(file_path))
        
        # Add extraction timestamp
        metadata['extraction_timestamp'] = datetime.now().isoformat()
        
        return metadata
    
    def process_directory(self) -> List[Dict[str, Any]]:
        """Process all files in the input directory"""
        all_metadata = []
        
        if not self.input_directory.exists():
            self.logger.error(f"Input directory {self.input_directory} does not exist")
            return all_metadata
        
        # Find all files recursively
        file_paths = []
        for root, dirs, files in os.walk(self.input_directory):
            for file in files:
                file_paths.append(Path(root) / file)
        
        if not file_paths:
            self.logger.warning(f"No files found in {self.input_directory}")
            return all_metadata
        
        self.logger.info(f"Found {len(file_paths)} files to process")
        
        for file_path in file_paths:
            try:
                metadata = self.extract_file_metadata(file_path)
                all_metadata.append(metadata)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                all_metadata.append({
                    'filename': file_path.name,
                    'file_path': str(file_path),
                    'error': str(e)
                })
        
        return all_metadata
    
    def export_to_json(self, metadata_list: List[Dict[str, Any]], filename: str = None) -> str:
        """Export metadata to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metadata_export_{timestamp}.json"
        
        output_path = self.output_directory / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON export completed: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            raise
    
    def export_to_csv(self, metadata_list: List[Dict[str, Any]], filename: str = None) -> str:
        """Export metadata to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metadata_export_{timestamp}.csv"
        
        output_path = self.output_directory / filename
        
        try:
            if metadata_list:
                df = pd.DataFrame(metadata_list)
                df.to_csv(output_path, index=False, encoding='utf-8')
                
                self.logger.info(f"CSV export completed: {output_path}")
                return str(output_path)
            else:
                self.logger.warning("No metadata to export to CSV")
                return ""
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise
    
    def generate_summary_report(self, metadata_list: List[Dict[str, Any]]) -> str:
        """Generate a summary report of the extraction process"""
        if not metadata_list:
            return "No files processed."
        
        total_files = len(metadata_list)
        successful_extractions = len([m for m in metadata_list if 'error' not in m])
        failed_extractions = total_files - successful_extractions
        
        # File type distribution
        file_types = {}
        for metadata in metadata_list:
            ext = metadata.get('file_extension', 'unknown')
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Total size
        total_size = sum(metadata.get('file_size', 0) for metadata in metadata_list)
        total_size_mb = round(total_size / (1024 * 1024), 2)
        
        summary = f"""
METADATA EXTRACTION SUMMARY REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

FILES PROCESSED:
- Total files: {total_files}
- Successful extractions: {successful_extractions}
- Failed extractions: {failed_extractions}
- Total size: {total_size_mb} MB

FILE TYPE DISTRIBUTION:
"""
        for ext, count in sorted(file_types.items()):
            summary += f"- {ext}: {count} files\n"
        
        summary += f"\nAVAILABLE LIBRARIES:\n"
        summary += f"- PIL/Pillow: {'✓' if PIL_AVAILABLE else '✗'}\n"
        summary += f"- ExifRead: {'✓' if EXIFREAD_AVAILABLE else '✗'}\n"
        summary += f"- Mutagen: {'✓' if MUTAGEN_AVAILABLE else '✗'}\n"
        summary += f"- Hachoir: {'✓' if HACHOIR_AVAILABLE else '✗'}\n"
        summary += f"- Python-magic: {'✓' if MAGIC_AVAILABLE else '✗'}\n"
        
        return summary
    
    def run_extraction(self, export_json: bool = True, export_csv: bool = True) -> Dict[str, str]:
        """Run the complete metadata extraction process"""
        self.logger.info("Starting metadata extraction process...")
        
        # Process all files
        metadata_list = self.process_directory()
        
        # Generate summary
        summary = self.generate_summary_report(metadata_list)
        self.logger.info(summary)
        
        # Save summary to file
        summary_path = self.output_directory / "extraction_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        results = {'summary': str(summary_path)}
        
        # Export to requested formats
        if export_json and metadata_list:
            results['json'] = self.export_to_json(metadata_list)
        
        if export_csv and metadata_list:
            results['csv'] = self.export_to_csv(metadata_list)
        
        self.logger.info("Metadata extraction process completed!")
        return results


def main():
    """Main function to run the metadata extractor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract metadata from files and export to CSV/JSON")
    parser.add_argument("--input", "-i", default="input_files", 
                       help="Input directory containing files to process")
    parser.add_argument("--output", "-o", default="output", 
                       help="Output directory for results")
    parser.add_argument("--no-json", action="store_true", 
                       help="Skip JSON export")
    parser.add_argument("--no-csv", action="store_true", 
                       help="Skip CSV export")
    
    args = parser.parse_args()
    
    # Create extractor and run
    extractor = MetadataExtractor(args.input, args.output)
    results = extractor.run_extraction(
        export_json=not args.no_json,
        export_csv=not args.no_csv
    )
    
    print("\nExtraction completed! Generated files:")
    for format_type, path in results.items():
        print(f"- {format_type.upper()}: {path}")


if __name__ == "__main__":
    main()
