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

try:
    import subprocess
    SUBPROCESS_AVAILABLE = True
except ImportError:
    SUBPROCESS_AVAILABLE = False

try:
    import hashlib
    HASHLIB_AVAILABLE = True
except ImportError:
    HASHLIB_AVAILABLE = False

try:
    import struct
    STRUCT_AVAILABLE = True
except ImportError:
    STRUCT_AVAILABLE = False

import pandas as pd


class MetadataExtractor:
    """Main class for extracting metadata from various file types"""
    
    def __init__(self, input_directory: str = "input_files", output_directory: str = "output", 
                 config: Dict[str, Any] = None, case_id: str = None):
        self.input_directory = Path(input_directory)
        self.output_directory = Path(output_directory)
        self.case_id = case_id or "METADATA_EXTRACT"
        
        # Load configuration
        self.config = self._load_config(config)
        
        # Create output directory
        self.output_directory.mkdir(exist_ok=True)
        
        # Setup logging with case-specific information
        self._setup_logging()
        
        # Configure extraction based on loaded config
        self._configure_extraction()
        
        # Supported file extensions (can be overridden by config)
        self.image_extensions = self.config.get('image_extensions', 
            {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.raw', '.cr2', '.nef', '.arw', '.dng'})
        self.audio_extensions = self.config.get('audio_extensions',
            {'.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.ape', '.opus'})
        self.video_extensions = self.config.get('video_extensions',
            {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mts', '.mxf'})
        self.document_extensions = self.config.get('document_extensions',
            {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.rtf', '.txt'})
        self.forensic_extensions = self.config.get('forensic_extensions',
            {'.e01', '.ex01', '.l01', '.dd', '.img', '.raw', '.dmg', '.ad1', '.aff', '.afd'})
        
        # Check for native ExifTool availability
        self.exiftool_available = self._check_exiftool_availability()
        
        # Check for ewfinfo (Expert Witness Format tools) availability
        self.ewfinfo_available = self._check_ewfinfo_availability()
    
    def _load_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load configuration from various sources"""
        default_config = {
            'extraction_options': {
                'include_thumbnails': False,
                'extract_gps': True,
                'extract_timestamps': True,
                'include_technical_metadata': True
            },
            'output_options': {
                'export_json': True,
                'export_csv': True,
                'timestamp_files': True,
                'create_summary': True
            },
            'logging': {
                'level': 'INFO',
                'file_logging': True,
                'detailed_logging': False
            },
            'performance': {
                'batch_size': 100,
                'use_multiprocessing': False,
                'timeout_per_file': 30
            }
        }
        
        # Merge with provided config
        if config:
            for key, value in config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value
        
        # Try to load from local config file
        config_file = Path(__file__).parent / "extractor_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
                    for key, value in file_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Warning: Could not load extractor config: {e}")
        
        return default_config
    
    def _check_exiftool_availability(self) -> bool:
        """Check if native ExifTool is available"""
        try:
            result = subprocess.run(['exiftool', '-ver'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.exiftool_version = result.stdout.strip()
                return True
        except Exception:
            pass
        return False
    
    def _check_ewfinfo_availability(self) -> bool:
        """Check if ewfinfo (libewf tools) is available"""
        try:
            # Try ewfinfo first
            result = subprocess.run(['ewfinfo', '-V'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.ewfinfo_version = result.stdout.strip().split('\n')[0] if result.stdout else "unknown"
                return True
        except Exception:
            pass
        
        # Try alternative names/locations
        alternative_paths = ['ewfinfo.exe', 'libewf-tools\\ewfinfo.exe', 'tools\\ewfinfo.exe']
        for path in alternative_paths:
            try:
                result = subprocess.run([path, '-V'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.ewfinfo_version = result.stdout.strip().split('\n')[0] if result.stdout else "unknown"
                    self.ewfinfo_path = path
                    return True
            except Exception:
                continue
        
        return False
    
    def get_ewfinfo_installation_guide(self) -> str:
        """Provide installation guidance for ewfinfo"""
        return """
EWFINFO INSTALLATION GUIDE
==========================

ewfinfo is part of libewf-tools and provides comprehensive analysis of Expert Witness Format (EWF/E01) files.

WINDOWS INSTALLATION OPTIONS:

1. CHOCOLATEY (Recommended):
   - Install Chocolatey: https://chocolatey.org/install
   - Run: choco install libewf-tools
   - ewfinfo will be available in PATH

2. MANUAL DOWNLOAD:
   - Visit: https://github.com/libyal/libewf/releases
   - Download Windows binaries
   - Extract to a folder (e.g., C:\\tools\\libewf)
   - Add to PATH or place in project directory

3. MSYS2/MINGW:
   - Install MSYS2: https://www.msys2.org/
   - Run: pacman -S mingw-w64-x86_64-libewf
   - Add MSYS2 bin to Windows PATH

4. FORENSIC SUITES:
   - Many forensic suites include libewf tools
   - Check if ewfinfo is available in existing installations

VERIFICATION:
- Run 'ewfinfo -V' to verify installation
- Should show libewf version information

BENEFITS FOR E01 ANALYSIS:
- Complete case/evidence metadata
- Acquisition details (examiner, date, tools)
- Drive information (model, serial, capacity)
- Integrity hashes (MD5, SHA1)
- Compression and error information
- Digital signatures and timestamps
"""
    
    def _setup_logging(self):
        """Setup logging with case-specific configuration"""
        log_level = getattr(logging, self.config['logging']['level'].upper(), logging.INFO)
        
        handlers = []
        
        # File logging
        if self.config['logging']['file_logging']:
            log_file = self.output_directory / f'extraction_{self.case_id}.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            handlers.append(file_handler)
        
        # Console logging (always enabled but can be controlled by level)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        handlers.append(console_handler)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
            handlers=handlers,
            force=True
        )
        self.logger = logging.getLogger(f'MetadataExtractor_{self.case_id}')
    
    def _configure_extraction(self):
        """Configure extraction parameters based on config"""
        self.extraction_options = self.config.get('extraction_options', {})
        self.output_options = self.config.get('output_options', {})
        self.performance_options = self.config.get('performance', {})
        
        # Set extraction flags
        self.include_thumbnails = self.extraction_options.get('include_thumbnails', False)
        self.extract_gps = self.extraction_options.get('extract_gps', True)
        self.extract_timestamps = self.extraction_options.get('extract_timestamps', True)
        self.include_technical = self.extraction_options.get('include_technical_metadata', True)
        
        # Set output flags  
        self.export_json = self.output_options.get('export_json', True)
        self.export_csv = self.output_options.get('export_csv', True)
        self.timestamp_files = self.output_options.get('timestamp_files', True)
        self.create_summary = self.output_options.get('create_summary', True)
        
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
    
    def get_file_hashes(self, file_path: Path) -> Dict[str, Any]:
        """Calculate file hashes for integrity verification"""
        hashes = {}
        if not HASHLIB_AVAILABLE:
            return hashes
        
        try:
            # Only calculate hashes for files smaller than 100MB to avoid performance issues
            file_size = file_path.stat().st_size
            if file_size > 100 * 1024 * 1024:  # 100MB
                hashes['hash_skipped'] = f"File too large ({file_size} bytes)"
                return hashes
            
            with open(file_path, 'rb') as f:
                content = f.read()
                hashes['md5'] = hashlib.md5(content).hexdigest()
                hashes['sha1'] = hashlib.sha1(content).hexdigest()
                hashes['sha256'] = hashlib.sha256(content).hexdigest()
        except Exception as e:
            self.logger.warning(f"Hash calculation failed for {file_path}: {e}")
            hashes['hash_error'] = str(e)
        
        return hashes
    
    def extract_native_exiftool_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata using native ExifTool executable"""
        metadata = {}
        if not self.exiftool_available:
            return metadata
        
        try:
            # Run ExifTool with comprehensive options
            cmd = ['exiftool', '-j', '-a', '-u', '-g', '-args', str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout:
                try:
                    exiftool_data = json.loads(result.stdout)
                    if exiftool_data and len(exiftool_data) > 0:
                        # Flatten the ExifTool output
                        exif_metadata = exiftool_data[0]
                        for key, value in exif_metadata.items():
                            # Clean up key names
                            clean_key = f"exiftool_{key.replace(' ', '_').replace(':', '_').replace('/', '_')}"
                            metadata[clean_key] = value
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to parse plain text output
                    cmd_text = ['exiftool', '-a', '-u', '-g', str(file_path)]
                    result_text = subprocess.run(cmd_text, capture_output=True, text=True, timeout=30)
                    if result_text.returncode == 0:
                        for line in result_text.stdout.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                clean_key = f"exiftool_{key.strip().replace(' ', '_').replace(':', '_').replace('/', '_')}"
                                metadata[clean_key] = value.strip()
            else:
                metadata['exiftool_error'] = result.stderr or "No output from ExifTool"
                
        except subprocess.TimeoutExpired:
            metadata['exiftool_error'] = "ExifTool timeout"
        except Exception as e:
            metadata['exiftool_error'] = str(e)
        
        return metadata
    
    def extract_windows_properties(self, file_path: Path) -> Dict[str, Any]:
        """Extract Windows file properties using PowerShell"""
        metadata = {}
        if not SUBPROCESS_AVAILABLE:
            return metadata
        
        try:
            # PowerShell command to get extended file properties
            ps_cmd = f"""
            $file = Get-Item '{file_path}'
            $shell = New-Object -ComObject Shell.Application
            $folder = $shell.Namespace($file.DirectoryName)
            $item = $folder.ParseName($file.Name)
            
            $properties = @{{}}
            for ($i = 0; $i -le 400; $i++) {{
                $name = $folder.GetDetailsOf($null, $i)
                $value = $folder.GetDetailsOf($item, $i)
                if ($name -and $value) {{
                    $properties[$name] = $value
                }}
            }}
            $properties | ConvertTo-Json -Depth 3
            """
            
            result = subprocess.run(['powershell', '-Command', ps_cmd], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                try:
                    props = json.loads(result.stdout)
                    for key, value in props.items():
                        clean_key = f"windows_{key.replace(' ', '_').replace(':', '_').replace('/', '_')}"
                        metadata[clean_key] = value
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Windows properties extraction failed for {file_path}: {e}")
        
        return metadata
    
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
        """Extract all available metadata from a file using every available method"""
        self.logger.info(f"Processing: {file_path}")
        
        # Start with basic file info
        metadata = self.get_file_basic_info(file_path)
        
        # Add magic file type detection
        metadata.update(self.get_magic_info(file_path))
        
        # ALWAYS try native ExifTool first (most comprehensive)
        exiftool_metadata = self.extract_native_exiftool_metadata(file_path)
        metadata.update(exiftool_metadata)
        
        # Add file hashes for integrity
        metadata.update(self.get_file_hashes(file_path))
        
        # Add Windows properties (on Windows systems)
        try:
            metadata.update(self.extract_windows_properties(file_path))
        except Exception as e:
            self.logger.debug(f"Windows properties extraction skipped: {e}")
        
        # Extract type-specific metadata using Python libraries
        file_ext = file_path.suffix.lower()
        
        if file_ext in self.image_extensions:
            metadata.update(self.extract_image_metadata_pil(file_path))
            metadata.update(self.extract_image_metadata_exifread(file_path))
        
        if file_ext in self.audio_extensions:
            metadata.update(self.extract_audio_metadata(file_path))
        
        # Try hachoir for all file types (supports many formats including forensic ones)
        metadata.update(self.extract_hachoir_metadata(file_path))
        
        # For forensic files, add additional analysis
        if file_ext in self.forensic_extensions:
            metadata.update(self.extract_forensic_metadata(file_path))
        
        # Add comprehensive file analysis
        metadata.update(self.extract_comprehensive_analysis(file_path))
        
        # Add extraction timestamp and tool versions
        metadata['extraction_timestamp'] = datetime.now().isoformat()
        metadata['extractor_version'] = "2.1_ewf_integrated"
        metadata['exiftool_available'] = self.exiftool_available
        if self.exiftool_available:
            metadata['exiftool_version'] = getattr(self, 'exiftool_version', 'unknown')
        metadata['ewfinfo_available'] = self.ewfinfo_available
        if self.ewfinfo_available:
            metadata['ewfinfo_version'] = getattr(self, 'ewfinfo_version', 'unknown')
        
        return metadata
    
    def extract_ewf_metadata_with_ewfinfo(self, file_path: Path) -> Dict[str, Any]:
        """Extract comprehensive EWF metadata using ewfinfo tool"""
        metadata = {}
        if not self.ewfinfo_available:
            metadata['ewfinfo_status'] = 'ewfinfo not available'
            return metadata
        
        try:
            # Get ewfinfo command (use stored path if available)
            ewfinfo_cmd = getattr(self, 'ewfinfo_path', 'ewfinfo')
            
            # Run ewfinfo with various options for comprehensive data
            commands = {
                'general': [ewfinfo_cmd, '-v', str(file_path)],
                'header': [ewfinfo_cmd, '-H', str(file_path)], 
                'media': [ewfinfo_cmd, '-m', str(file_path)],
                'hash': [ewfinfo_cmd, '-h', str(file_path)]
            }
            
            for info_type, cmd in commands.items():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0 and result.stdout:
                        # Parse ewfinfo output
                        parsed_data = self._parse_ewfinfo_output(result.stdout, info_type)
                        for key, value in parsed_data.items():
                            metadata[f'ewf_{info_type}_{key}'] = value
                    else:
                        metadata[f'ewf_{info_type}_error'] = result.stderr or "No output"
                except subprocess.TimeoutExpired:
                    metadata[f'ewf_{info_type}_error'] = "Timeout"
                except Exception as e:
                    metadata[f'ewf_{info_type}_error'] = str(e)
            
            metadata['ewfinfo_version'] = getattr(self, 'ewfinfo_version', 'unknown')
            
        except Exception as e:
            metadata['ewfinfo_error'] = str(e)
        
        return metadata
    
    def _parse_ewfinfo_output(self, output: str, info_type: str) -> Dict[str, Any]:
        """Parse ewfinfo output into structured metadata"""
        parsed = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_').replace('-', '_')
                    value = value.strip()
                    
                    # Clean up common ewfinfo field names
                    key_mappings = {
                        'case_number': 'case_number',
                        'evidence_number': 'evidence_number', 
                        'examiner_name': 'examiner_name',
                        'notes': 'notes',
                        'description': 'description',
                        'acquiry_date': 'acquisition_date',
                        'system_date': 'system_date',
                        'acquiry_operating_system': 'acquisition_os',
                        'acquiry_software_version': 'acquisition_software',
                        'md5_hash': 'md5_hash',
                        'sha1_hash': 'sha1_hash',
                        'number_of_sectors': 'total_sectors',
                        'bytes_per_sector': 'bytes_per_sector',
                        'media_size': 'media_size',
                        'compression_method': 'compression_method',
                        'compression_level': 'compression_level',
                        'error_granularity': 'error_granularity',
                        'guid': 'guid',
                        'model': 'drive_model',
                        'serial_number': 'drive_serial'
                    }
                    
                    final_key = key_mappings.get(key, key)
                    parsed[final_key] = value
                    
                except ValueError:
                    continue
        
        return parsed
    
    def extract_ewf_header_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Detailed EWF header analysis using manual parsing"""
        metadata = {}
        
        try:
            with open(file_path, 'rb') as f:
                # Read EWF header (first 13 bytes contain signature and format info)
                header = f.read(1024)
                
                if len(header) >= 13:
                    # EWF signature analysis
                    signature = header[:8]
                    metadata['ewf_signature_hex'] = signature.hex()
                    
                    if signature.startswith(b'EVF'):
                        metadata['ewf_format_type'] = 'Expert Witness Format (EVF)'
                        metadata['ewf_version'] = 'EVF'
                    elif signature.startswith(b'EWF'):
                        metadata['ewf_format_type'] = 'Expert Witness Format (EWF)'  
                        metadata['ewf_version'] = 'EWF'
                    elif signature.startswith(b'LVF'):
                        metadata['ewf_format_type'] = 'Logical Volume Format (LVF)'
                        metadata['ewf_version'] = 'LVF'
                    else:
                        metadata['ewf_format_type'] = 'Unknown EWF variant'
                    
                    # Try to parse format version and fields
                    if STRUCT_AVAILABLE and len(header) >= 16:
                        try:
                            # Parse basic header structure (varies by EWF version)
                            format_byte = header[8] if len(header) > 8 else 0
                            metadata['ewf_format_version_byte'] = format_byte
                            
                            # Look for section headers in first 1KB
                            section_types = []
                            for i in range(0, min(len(header) - 16, 1000), 4):
                                chunk = header[i:i+4]
                                if chunk in [b'head', b'volu', b'disk', b'data', b'hash', b'done']:
                                    section_types.append(chunk.decode('ascii', errors='ignore'))
                            
                            if section_types:
                                metadata['ewf_sections_found'] = list(set(section_types))
                                
                        except Exception as e:
                            metadata['ewf_header_parse_error'] = str(e)
                
                # Additional header analysis
                metadata['ewf_header_size_analyzed'] = len(header)
                metadata['ewf_full_header_hex'] = header[:128].hex()  # First 128 bytes
                
        except Exception as e:
            metadata['ewf_header_error'] = str(e)
        
        return metadata
    
    def extract_forensic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract forensic-specific metadata for disk images and evidence files"""
        metadata = {}
        file_ext = file_path.suffix.lower()
        
        try:
            # For E01/EWF files - comprehensive analysis
            if file_ext in ['.e01', '.ex01', '.l01', '.s01']:
                
                # Basic header analysis (always done)
                with open(file_path, 'rb') as f:
                    header = f.read(1024)
                    metadata['forensic_header_hex'] = header[:64].hex()
                    
                    # Look for EWF signatures
                    if b'EVF' in header[:16]:
                        metadata['forensic_format'] = 'Expert Witness Format (EVF)'
                    elif b'EWF' in header[:16]:
                        metadata['forensic_format'] = 'Expert Witness Format (EWF)'
                    elif b'LVF' in header[:16]:
                        metadata['forensic_format'] = 'Logical Volume Format (LVF)'
                    else:
                        metadata['forensic_format'] = 'Unknown EWF variant'
                
                # Try ewfinfo for comprehensive metadata (if available)
                if self.ewfinfo_available:
                    self.logger.info(f"Using ewfinfo for comprehensive EWF analysis of {file_path}")
                    ewf_metadata = self.extract_ewf_metadata_with_ewfinfo(file_path)
                    metadata.update(ewf_metadata)
                else:
                    self.logger.warning(f"ewfinfo not available, using manual EWF analysis for {file_path}")
                    # Manual header analysis as fallback
                    ewf_header_metadata = self.extract_ewf_header_analysis(file_path)
                    metadata.update(ewf_header_metadata)
                
                metadata['ewf_analysis_method'] = 'ewfinfo' if self.ewfinfo_available else 'manual_header_analysis'
            
            # For DD images and other raw formats
            elif file_ext in ['.dd', '.img', '.raw', '.bin']:
                metadata['forensic_format'] = 'Raw disk image'
                
                # Basic raw image analysis
                try:
                    with open(file_path, 'rb') as f:
                        # Check for filesystem signatures
                        f.seek(0x1FE)  # Boot sector signature location
                        boot_sig = f.read(2)
                        if boot_sig == b'\x55\xAA':
                            metadata['raw_boot_signature'] = 'Valid (0x55AA)'
                        else:
                            metadata['raw_boot_signature'] = f'Invalid ({boot_sig.hex()})'
                        
                        # Check for common filesystem signatures
                        f.seek(0x36)  # FAT filesystem signature
                        fat_sig = f.read(8)
                        if b'FAT' in fat_sig:
                            metadata['raw_filesystem_hint'] = 'FAT detected'
                        
                        f.seek(0x52)  # NTFS signature location
                        ntfs_sig = f.read(4)
                        if ntfs_sig == b'NTFS':
                            metadata['raw_filesystem_hint'] = 'NTFS detected'
                            
                except Exception as e:
                    metadata['raw_analysis_error'] = str(e)
            
            # For other forensic formats
            elif file_ext in ['.aff', '.afd', '.ad1', '.dmg']:
                metadata['forensic_format'] = f'Forensic image ({file_ext.upper()})'
                
            metadata['forensic_analysis_attempted'] = True
            metadata['forensic_tools_available'] = {
                'ewfinfo': self.ewfinfo_available,
                'manual_analysis': True
            }
            
        except Exception as e:
            metadata['forensic_error'] = str(e)
        
        return metadata
    
    def extract_comprehensive_analysis(self, file_path: Path) -> Dict[str, Any]:
        """Perform comprehensive file analysis"""
        metadata = {}
        
        try:
            # File entropy analysis (simplified)
            file_size = file_path.stat().st_size
            metadata['analysis_file_complexity'] = 'large' if file_size > 100*1024*1024 else 'standard'
            
            # Check for embedded files or structures
            if file_size > 0:
                with open(file_path, 'rb') as f:
                    # Read first and last chunks
                    first_chunk = f.read(min(4096, file_size))
                    metadata['analysis_first_bytes_hex'] = first_chunk[:32].hex()
                    
                    if file_size > 4096:
                        f.seek(-min(4096, file_size), 2)
                        last_chunk = f.read()
                        metadata['analysis_last_bytes_hex'] = last_chunk[-32:].hex()
                    
                    # Look for common signatures
                    signatures = {
                        'PDF': b'%PDF',
                        'JPEG': b'\xff\xd8\xff',
                        'PNG': b'\x89PNG',
                        'ZIP': b'PK\x03\x04',
                        'GIF': b'GIF8',
                        'BMP': b'BM',
                        'TIFF': b'II*\x00',
                        'EXE': b'MZ',
                        'ELF': b'\x7fELF'
                    }
                    
                    detected_formats = []
                    for format_name, signature in signatures.items():
                        if signature in first_chunk:
                            detected_formats.append(format_name)
                    
                    if detected_formats:
                        metadata['analysis_detected_formats'] = detected_formats
            
            # Add file characteristics
            metadata['analysis_timestamp'] = datetime.now().isoformat()
            
        except Exception as e:
            metadata['analysis_error'] = str(e)
        
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
        
        summary += f"\nAVAILABLE EXTRACTION TOOLS:\n"
        summary += f"- Native ExifTool: {'✓' if self.exiftool_available else '✗'}"
        if self.exiftool_available:
            summary += f" (v{getattr(self, 'exiftool_version', 'unknown')})"
        summary += "\n"
        summary += f"- ewfinfo (EWF Analysis): {'✓' if self.ewfinfo_available else '✗'}"
        if self.ewfinfo_available:
            summary += f" ({getattr(self, 'ewfinfo_version', 'unknown')})"
        summary += "\n"
        summary += f"- PIL/Pillow: {'✓' if PIL_AVAILABLE else '✗'}\n"
        summary += f"- ExifRead: {'✓' if EXIFREAD_AVAILABLE else '✗'}\n"
        summary += f"- Mutagen: {'✓' if MUTAGEN_AVAILABLE else '✗'}\n"
        summary += f"- Hachoir: {'✓' if HACHOIR_AVAILABLE else '✗'}\n"
        summary += f"- Python-magic: {'✓' if MAGIC_AVAILABLE else '✗'}\n"
        summary += f"- File Hashing: {'✓' if HASHLIB_AVAILABLE else '✗'}\n"
        summary += f"- Windows Properties: {'✓' if SUBPROCESS_AVAILABLE else '✗'}\n"
        
        summary += f"\nEXTRACTION METHODS USED:\n"
        summary += f"- Comprehensive metadata extraction\n"
        summary += f"- Expert Witness Format (EWF/E01) analysis\n"
        summary += f"- File integrity hashing\n"
        summary += f"- Forensic file analysis\n"
        summary += f"- Multi-library approach\n"
        summary += f"- Native tool integration\n"
        if self.ewfinfo_available:
            summary += f"- Professional EWF metadata extraction\n"
        else:
            summary += f"- Manual EWF header analysis (ewfinfo not available)\n"
        
        return summary
    
    def run_extraction(self, export_json: bool = None, export_csv: bool = None) -> Dict[str, str]:
        """Run the complete metadata extraction process"""
        self.logger.info("Starting metadata extraction process...")
        
        # Use config defaults if not specified
        if export_json is None:
            export_json = self.export_json
        if export_csv is None:
            export_csv = self.export_csv
        
        # Process all files
        metadata_list = self.process_directory()
        
        # Generate summary
        summary = self.generate_summary_report(metadata_list)
        self.logger.info(summary)
        
        # Save summary to file if configured
        if self.create_summary:
            summary_filename = f"extraction_summary_{self.case_id}.txt" if self.timestamp_files else "extraction_summary.txt"
            summary_path = self.output_directory / summary_filename
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)
        
        results = {'summary': str(summary_path) if self.create_summary else ''}
        
        # Export to requested formats
        if export_json and metadata_list:
            json_filename = f"metadata_export_{self.case_id}.json" if self.timestamp_files else "metadata_export.json"
            results['json'] = self.export_to_json(metadata_list, json_filename)
        
        if export_csv and metadata_list:
            csv_filename = f"metadata_export_{self.case_id}.csv" if self.timestamp_files else "metadata_export.csv"
            results['csv'] = self.export_to_csv(metadata_list, csv_filename)
        
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
