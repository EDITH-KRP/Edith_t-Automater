#!/usr/bin/env python3
"""
Metadata Remover and Export Tool
Removes metadata from various file types and exports removal information to CSV/JSON formats
"""

import os
import json
import csv
import logging
import shutil
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
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

import pandas as pd


class MetadataRemover:
    """Main class for removing metadata from various file types"""
    
    def __init__(self, input_directory: str = "input_files", 
                 output_directory: str = "cleaned_files",
                 reports_directory: str = "removal_reports"):
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.reports_directory = Path(reports_directory)
        
        # Create directories
        self.output_directory.mkdir(exist_ok=True)
        self.reports_directory.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.reports_directory / 'metadata_removal.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Supported file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
        self.audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma'}
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}
        
        # Removal statistics
        self.removal_stats = {
            'total_files': 0,
            'successfully_cleaned': 0,
            'failed_cleaning': 0,
            'no_metadata_found': 0,
            'unsupported_format': 0
        }
        
        # Detailed removal log
        self.removal_log = []
    
    def get_file_basic_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic file system information"""
        try:
            stat = file_path.stat()
            return {
                'filename': file_path.name,
                'original_path': str(file_path),
                'file_size': stat.st_size,
                'file_size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'file_extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0]
            }
        except Exception as e:
            self.logger.error(f"Error getting basic info for {file_path}: {e}")
            return {'filename': file_path.name, 'error': str(e)}
    
    def extract_metadata_before_removal(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata before removal for logging purposes"""
        metadata = {}
        file_ext = file_path.suffix.lower()
        
        try:
            if file_ext in self.image_extensions and PIL_AVAILABLE:
                with Image.open(file_path) as img:
                    exif_data = img._getexif()
                    if exif_data:
                        metadata['original_exif_tags'] = len(exif_data)
                        # Store some key metadata for the log
                        for tag_id, value in list(exif_data.items())[:5]:  # First 5 tags
                            tag = TAGS.get(tag_id, tag_id)
                            if isinstance(value, bytes):
                                try:
                                    value = value.decode('utf-8')
                                except:
                                    value = str(value)
                            metadata[f'removed_{tag}'] = str(value)[:100]  # Truncate long values
            
            elif file_ext in self.audio_extensions and MUTAGEN_AVAILABLE:
                audio_file = MutagenFile(file_path)
                if audio_file and audio_file.tags:
                    metadata['original_audio_tags'] = len(audio_file.tags)
                    # Store some key tags
                    for i, (key, value) in enumerate(list(audio_file.tags.items())[:5]):
                        if isinstance(value, list):
                            value = ', '.join(str(v) for v in value)
                        metadata[f'removed_{key}'] = str(value)[:100]
                        
        except Exception as e:
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def remove_image_metadata(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Remove metadata from image files"""
        result = {
            'success': False,
            'method': 'PIL',
            'metadata_found': False,
            'metadata_removed': False,
            'error': None
        }
        
        if not PIL_AVAILABLE:
            result['error'] = 'PIL not available'
            return result
        
        try:
            with Image.open(input_path) as img:
                # Check if metadata exists
                exif_data = img._getexif()
                if exif_data:
                    result['metadata_found'] = True
                    result['original_exif_count'] = len(exif_data)
                
                # Create a new image without EXIF data
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Convert to RGB for JPEG compatibility
                    if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                        img = img.convert('RGB')
                
                # Save without metadata
                img.save(output_path, quality=95, optimize=True)
                
                # Verify metadata removal
                with Image.open(output_path) as cleaned_img:
                    new_exif = cleaned_img._getexif()
                    if not new_exif or len(new_exif) == 0:
                        result['metadata_removed'] = True
                    else:
                        result['remaining_exif_count'] = len(new_exif)
                
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error removing image metadata from {input_path}: {e}")
        
        return result
    
    def remove_audio_metadata(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Remove metadata from audio files"""
        result = {
            'success': False,
            'method': 'Mutagen',
            'metadata_found': False,
            'metadata_removed': False,
            'error': None
        }
        
        if not MUTAGEN_AVAILABLE:
            result['error'] = 'Mutagen not available'
            return result
        
        try:
            # First, copy the file
            shutil.copy2(input_path, output_path)
            
            # Load the copied file and remove tags
            audio_file = MutagenFile(output_path)
            
            if audio_file is not None:
                if audio_file.tags:
                    result['metadata_found'] = True
                    result['original_tags_count'] = len(audio_file.tags)
                    
                    # Remove all tags
                    audio_file.delete()
                    audio_file.save()
                    
                    # Verify removal
                    verification_file = MutagenFile(output_path)
                    if verification_file and verification_file.tags:
                        result['remaining_tags_count'] = len(verification_file.tags)
                    else:
                        result['metadata_removed'] = True
                else:
                    result['metadata_found'] = False
                
                result['success'] = True
            else:
                result['error'] = 'Could not load audio file'
                
        except ID3NoHeaderError:
            # No ID3 header means no metadata to remove
            shutil.copy2(input_path, output_path)
            result['success'] = True
            result['metadata_found'] = False
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error removing audio metadata from {input_path}: {e}")
        
        return result
    
    def remove_pdf_metadata(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        """Remove metadata from PDF files"""
        result = {
            'success': False,
            'method': 'PyPDF2',
            'metadata_found': False,
            'metadata_removed': False,
            'error': None
        }
        
        if not PYPDF2_AVAILABLE:
            result['error'] = 'PyPDF2 not available'
            return result
        
        try:
            with open(input_path, 'rb') as input_file:
                reader = PyPDF2.PdfReader(input_file)
                
                # Check for metadata
                if reader.metadata:
                    result['metadata_found'] = True
                    result['original_metadata'] = dict(reader.metadata)
                
                # Create writer and copy pages without metadata
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    writer.add_page(page)
                
                # Write to output file
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                
                # Verify metadata removal
                with open(output_path, 'rb') as verify_file:
                    verify_reader = PyPDF2.PdfReader(verify_file)
                    if not verify_reader.metadata or len(verify_reader.metadata) == 0:
                        result['metadata_removed'] = True
                
                result['success'] = True
                
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error removing PDF metadata from {input_path}: {e}")
        
        return result
    
    def remove_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Remove metadata from a single file"""
        self.logger.info(f"Processing: {file_path}")
        
        # Get basic file info
        file_info = self.get_file_basic_info(file_path)
        
        # Extract metadata before removal for logging
        original_metadata = self.extract_metadata_before_removal(file_path)
        
        # Determine output path
        relative_path = file_path.relative_to(self.input_directory)
        output_path = self.output_directory / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize result
        result = {
            **file_info,
            'output_path': str(output_path),
            'processing_time': datetime.now().isoformat(),
            'original_metadata': original_metadata,
            'removal_result': {},
            'status': 'failed'
        }
        
        file_ext = file_path.suffix.lower()
        
        try:
            # Choose appropriate removal method
            if file_ext in self.image_extensions:
                removal_result = self.remove_image_metadata(file_path, output_path)
            elif file_ext in self.audio_extensions:
                removal_result = self.remove_audio_metadata(file_path, output_path)
            elif file_ext == '.pdf':
                removal_result = self.remove_pdf_metadata(file_path, output_path)
            else:
                # For unsupported formats, just copy the file
                shutil.copy2(file_path, output_path)
                removal_result = {
                    'success': True,
                    'method': 'copy',
                    'metadata_found': False,
                    'metadata_removed': False,
                    'note': 'Unsupported format - file copied without modification'
                }
                self.removal_stats['unsupported_format'] += 1
            
            result['removal_result'] = removal_result
            
            # Update statistics
            if removal_result['success']:
                if removal_result.get('metadata_found'):
                    if removal_result.get('metadata_removed'):
                        result['status'] = 'cleaned'
                        self.removal_stats['successfully_cleaned'] += 1
                    else:
                        result['status'] = 'partial_clean'
                        self.removal_stats['failed_cleaning'] += 1
                else:
                    result['status'] = 'no_metadata'
                    self.removal_stats['no_metadata_found'] += 1
            else:
                result['status'] = 'failed'
                self.removal_stats['failed_cleaning'] += 1
            
            # Verify output file exists
            if output_path.exists():
                output_stat = output_path.stat()
                result['output_size'] = output_stat.st_size
                result['output_size_mb'] = round(output_stat.st_size / (1024 * 1024), 2)
                result['size_difference'] = result['file_size'] - output_stat.st_size
            
        except Exception as e:
            result['removal_result'] = {'error': str(e), 'success': False}
            result['status'] = 'error'
            self.removal_stats['failed_cleaning'] += 1
            self.logger.error(f"Error processing {file_path}: {e}")
        
        return result
    
    def process_directory(self) -> List[Dict[str, Any]]:
        """Process all files in the input directory"""
        all_results = []
        
        if not self.input_directory.exists():
            self.logger.error(f"Input directory {self.input_directory} does not exist")
            return all_results
        
        # Find all files recursively
        file_paths = []
        for root, dirs, files in os.walk(self.input_directory):
            for file in files:
                file_paths.append(Path(root) / file)
        
        if not file_paths:
            self.logger.warning(f"No files found in {self.input_directory}")
            return all_results
        
        self.logger.info(f"Found {len(file_paths)} files to process")
        self.removal_stats['total_files'] = len(file_paths)
        
        for file_path in file_paths:
            try:
                result = self.remove_file_metadata(file_path)
                all_results.append(result)
                self.removal_log.append(result)
            except Exception as e:
                self.logger.error(f"Failed to process {file_path}: {e}")
                error_result = {
                    'filename': file_path.name,
                    'original_path': str(file_path),
                    'status': 'error',
                    'error': str(e),
                    'processing_time': datetime.now().isoformat()
                }
                all_results.append(error_result)
                self.removal_log.append(error_result)
        
        return all_results
    
    def export_to_json(self, results_list: List[Dict[str, Any]], filename: str = None) -> str:
        """Export removal results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metadata_removal_report_{timestamp}.json"
        
        output_path = self.reports_directory / filename
        
        try:
            report_data = {
                'removal_summary': self.removal_stats,
                'processing_timestamp': datetime.now().isoformat(),
                'input_directory': str(self.input_directory),
                'output_directory': str(self.output_directory),
                'detailed_results': results_list
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"JSON report exported: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            raise
    
    def export_to_csv(self, results_list: List[Dict[str, Any]], filename: str = None) -> str:
        """Export removal results to CSV file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metadata_removal_report_{timestamp}.csv"
        
        output_path = self.reports_directory / filename
        
        try:
            if results_list:
                # Flatten nested dictionaries for CSV
                flattened_results = []
                for result in results_list:
                    flat_result = {}
                    for key, value in result.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                flat_result[f"{key}_{sub_key}"] = sub_value
                        else:
                            flat_result[key] = value
                    flattened_results.append(flat_result)
                
                df = pd.DataFrame(flattened_results)
                df.to_csv(output_path, index=False, encoding='utf-8')
                
                self.logger.info(f"CSV report exported: {output_path}")
                return str(output_path)
            else:
                self.logger.warning("No results to export to CSV")
                return ""
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            raise
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of the removal process"""
        total = self.removal_stats['total_files']
        if total == 0:
            return "No files processed."
        
        success_rate = round((self.removal_stats['successfully_cleaned'] / total) * 100, 2)
        
        summary = f"""
METADATA REMOVAL SUMMARY REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

PROCESSING STATISTICS:
- Total files processed: {total}
- Successfully cleaned: {self.removal_stats['successfully_cleaned']}
- Failed cleaning: {self.removal_stats['failed_cleaning']}
- No metadata found: {self.removal_stats['no_metadata_found']}
- Unsupported formats: {self.removal_stats['unsupported_format']}
- Success rate: {success_rate}%

DIRECTORIES:
- Input: {self.input_directory}
- Output: {self.output_directory}
- Reports: {self.reports_directory}

AVAILABLE LIBRARIES:
- PIL/Pillow: {'✓' if PIL_AVAILABLE else '✗'} (Image metadata removal)
- Mutagen: {'✓' if MUTAGEN_AVAILABLE else '✗'} (Audio metadata removal)
- PyPDF2: {'✓' if PYPDF2_AVAILABLE else '✗'} (PDF metadata removal)

SUPPORTED FORMATS:
- Images: {', '.join(sorted(self.image_extensions))}
- Audio: {', '.join(sorted(self.audio_extensions))}
- Documents: .pdf (with PyPDF2)

PRIVACY NOTES:
- Original files are preserved in the input directory
- Cleaned files are saved in the output directory
- All metadata removal operations are logged
- Verify cleaned files before deleting originals
"""
        
        return summary
    
    def run_removal_process(self, export_json: bool = True, export_csv: bool = True) -> Dict[str, str]:
        """Run the complete metadata removal process"""
        self.logger.info("Starting metadata removal process...")
        
        # Process all files
        results = self.process_directory()
        
        # Generate summary
        summary = self.generate_summary_report()
        self.logger.info(summary)
        
        # Save summary to file
        summary_path = self.reports_directory / "removal_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        output_files = {'summary': str(summary_path)}
        
        # Export to requested formats
        if export_json and results:
            output_files['json'] = self.export_to_json(results)
        
        if export_csv and results:
            output_files['csv'] = self.export_to_csv(results)
        
        self.logger.info("Metadata removal process completed!")
        return output_files


def main():
    """Main function to run the metadata remover"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove metadata from files and export removal reports")
    parser.add_argument("--input", "-i", default="input_files", 
                       help="Input directory containing files to clean")
    parser.add_argument("--output", "-o", default="cleaned_files", 
                       help="Output directory for cleaned files")
    parser.add_argument("--reports", "-r", default="removal_reports", 
                       help="Directory for removal reports")
    parser.add_argument("--no-json", action="store_true", 
                       help="Skip JSON report export")
    parser.add_argument("--no-csv", action="store_true", 
                       help="Skip CSV report export")
    
    args = parser.parse_args()
    
    # Create remover and run
    remover = MetadataRemover(args.input, args.output, args.reports)
    results = remover.run_removal_process(
        export_json=not args.no_json,
        export_csv=not args.no_csv
    )
    
    print("\nMetadata removal completed! Generated files:")
    for format_type, path in results.items():
        print(f"- {format_type.upper()}: {path}")
    
    print(f"\nCleaned files saved to: {args.output}")
    print(f"Reports saved to: {args.reports}")


if __name__ == "__main__":
    main()
