#!/usr/bin/env python3
"""
EDITH-Automater ExifTool Automated Module

Processes files from evidence directory with advanced metadata extraction.
Outputs JSON, CSV, HTML reports with file integrity verification.

Usage:
- python exiftool_auto.py                    # Normal run
- python exiftool_auto.py --prompt           # Custom input directory
- python exiftool_auto.py --config-only      # Show configuration

Author: ADITHYA N T
Version: 3.2 - Enhanced Portable Edition
"""

import sys
import json
import csv
import html
import logging
import subprocess
import hashlib
import platform
import struct
import zlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import argparse


class AutomatedExifTool:
    """Automated ExifTool for batch processing evidence files"""
    
    def __init__(self, case_id: str = None, show_prompt: bool = False, custom_result_dir: str = None):
        self.case_id = case_id or f"AUTO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.tool_dir = Path(__file__).parent
        self.evidence_dir = (self.tool_dir / ".." / ".." / "evidence").resolve()
        
        # Use custom result directory if provided, otherwise use default
        if custom_result_dir:
            self.result_dir = Path(custom_result_dir).resolve()
        else:
            self.result_dir = (self.evidence_dir / ".." / "Results" / "Exiftool_output").resolve()
        
        custom_input = self._prompt_for_input_directory() if show_prompt else None
        if custom_input:
            self.evidence_dir = custom_input
        
        self.setup_directories()
        self.setup_logging()
        self.exiftool_path = self._find_exiftool_executable()
        
        self.config = {
            "advanced_extraction": True,
            "export_json": True,
            "export_csv": True,
            "export_html": True,
            "generate_hashes": True,
            "timeout": 300,
            "max_file_size_mb": 10240,  # 10GB - allow large forensic images
            "quick_mode": False
        }
        
        self.processed_files = []
        self.failed_files = []
        self.total_metadata_entries = 0
        
        self.logger.info(f"Automated ExifTool initialized for case: {self.case_id}")
        self.logger.info(f"Evidence directory: {self.evidence_dir}")
        self.logger.info(f"Result directory: {self.result_dir}")
    
    def setup_directories(self):
        self.case_result_dir = self.result_dir / self.case_id
        self.output_dir = self.case_result_dir / "metadata"
        
        for directory in [self.case_result_dir, self.output_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        if not self.evidence_dir.exists():
            self.evidence_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created evidence directory: {self.evidence_dir}")
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(f"AutoExifTool_{self.case_id}")
    
    def _find_exiftool_executable(self) -> str:
        # Platform-specific executable names
        is_windows = platform.system().lower() == 'windows'
        exe_name = "exiftool.exe" if is_windows else "exiftool"
        
        possible_paths = [
            self.tool_dir / "bin" / exe_name,
            self.tool_dir / exe_name,
            exe_name  # Will search in PATH
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(path)
        
        # Try system PATH - platform specific
        try:
            if is_windows:
                result = subprocess.run(['where', 'exiftool'], capture_output=True, text=True, 
                                      shell=True, encoding='utf-8', errors='ignore', timeout=10)
            else:
                result = subprocess.run(['which', 'exiftool'], capture_output=True, text=True, 
                                      encoding='utf-8', errors='ignore', timeout=10)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception:
            pass
        
        raise FileNotFoundError("ExifTool executable not found")
    
    def _prompt_for_input_directory(self) -> Optional[Path]:
        try:
            print(f"\nCustom Input Directory (default: {self.evidence_dir})")
            user_input = input("Enter path or press Enter for default: ").strip()
            
            if not user_input:
                print("✓ Using default evidence directory")
                return None
            
            custom_path = Path(user_input).resolve()
            if custom_path.exists() and custom_path.is_dir():
                print(f"✓ Custom input directory: {custom_path}")
                return custom_path
            else:
                print(f"⚠️ Invalid path, using default")
                return None
                
        except (KeyboardInterrupt, EOFError, Exception):
            print("\n✓ Using default evidence directory")
            return None
    
    def scan_evidence_directory(self) -> List[Path]:
        supported_extensions = {
            # Media files
            '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp',
            '.pdf', '.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.doc', '.docx', 
            '.xls', '.xlsx', '.ppt', '.pptx', '.txt',
            # Forensic image formats
            '.e01', '.ex01', '.l01', '.dd', '.raw', '.img', '.001', '.000',
            '.aff', '.afd', '.vmdk', '.vhd', '.vhdx', '.dmg'
        }
        
        if not self.evidence_dir.exists():
            self.logger.warning(f"Evidence directory does not exist: {self.evidence_dir}")
            return []
        
        max_size_bytes = self.config["max_file_size_mb"] * 1024 * 1024
        evidence_files = []
        skipped_files = []
        
        for f in self.evidence_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in supported_extensions:
                try:
                    file_size = f.stat().st_size
                    if file_size <= max_size_bytes:
                        evidence_files.append(f)
                    else:
                        skipped_files.append(f)
                        self.logger.warning(f"Skipping large file ({file_size/1024/1024:.1f}MB): {f.name}")
                except OSError:
                    self.logger.warning(f"Cannot access file: {f}")
        
        if skipped_files:
            self.logger.info(f"Skipped {len(skipped_files)} files (too large)")
        
        self.logger.info(f"Found {len(evidence_files)} supported files")
        return evidence_files
    
    # ------------------------------------------------------------------ #
    # EWF / E01 binary header parser                                       #
    # ------------------------------------------------------------------ #
    def _extract_ewf_header_metadata(self, e01_path: Path) -> dict:
        """
        Parse the E01/EWF binary segment file to extract the embedded
        'header' or 'header2' section that contains case-level metadata
        (case number, examiner, acquisition date/time, media type, etc.).

        Returns a flat dict whose keys are prefixed with 'EWF:'.  Returns
        an empty dict if the file is not a recognised EWF container or if
        no header section can be found.
        """
        EWF_SIGNATURES = (
            b'EVF\x09\x0D\x0A\xFF\x00',   # EWF-E01 (Guidance Software / EnCase)
            b'LWF\x09\x0D\x0A\xFF\x00',   # EWF-Lx01 (logical evidence)
            b'EWF\x09\x0D\x0A\xFF\x00',   # generic EWF2
        )
        # Human-readable names for the single-character / short keys used
        # in the EWF 'header' section (FTK Imager / EnCase convention)
        KEY_MAP = {
            'a':  'EWF:Notes',
            'c':  'EWF:CaseNumber',
            'e':  'EWF:Description',
            'md': 'EWF:DriveModel',
            'm':  'EWF:AcquisitionStartDateTime',
            'n':  'EWF:EvidenceNumber',
            'ov': 'EWF:OperatingSystem',
            'av': 'EWF:AcquisitionSoftware',
            'p':  'EWF:MediaType',
            'r':  'EWF:CompressionType',
            'sn': 'EWF:DriveSerial',
            't':  'EWF:ExaminerName',
            # FTK Imager stores acquisition *end* datetime in the 'u' slot
            'u':  'EWF:AcquisitionEndDateTime',
        }
        MEDIA_TYPES  = {'0': 'Removable', '1': 'Fixed/HDD', '2': 'Optical',
                        '3': 'Memory',    '4': 'Network'}
        COMPRESSION  = {'0': 'None', '1': 'Fast', '2': 'Best',
                        'f': 'Fast', 'b': 'Best', 'n': 'None'}

        result: dict = {}
        try:
            with open(e01_path, 'rb') as fh:
                sig = fh.read(8)
                if not any(sig == s for s in EWF_SIGNATURES):
                    return result   # not a standard EWF file

                fh.read(5)          # start-of-fields (1 b) + segment number (2 b) + end-of-fields (2 b)

                file_size = e01_path.stat().st_size
                for _ in range(100):        # max 100 sections
                    sec_start = fh.tell()
                    if sec_start + 76 > file_size:
                        break

                    # Section descriptor: 76 bytes
                    # [0-15]  type string (NUL-padded)
                    # [16-23] next section offset (uint64 LE)
                    # [24-31] section size       (uint64 LE)
                    # [32-47] padding
                    # [48-51] unused
                    # NOTE: EnCase EWF spec says checksum is at bytes 72-75
                    desc = fh.read(76)
                    if len(desc) < 76:
                        break

                    sec_type = desc[0:16].rstrip(b'\x00').decode('ascii', errors='replace').strip()
                    next_off = struct.unpack_from('<Q', desc, 16)[0]
                    sec_size = struct.unpack_from('<Q', desc, 24)[0]

                    data_size = (sec_size - 76) if sec_size > 76 else 0

                    if sec_type in ('header', 'header2') and data_size > 0:
                        raw = fh.read(data_size)
                        try:
                            plain = zlib.decompress(raw)
                            text  = (plain.decode('utf-16-le', errors='replace')
                                     if sec_type == 'header2'
                                     else plain.decode('ascii', errors='replace'))

                            # Format:
                            #   line 0: version ("1")
                            #   line 1: "main"
                            #   line 2: tab-separated key identifiers
                            #   line 3: tab-separated values
                            lines = [l.rstrip('\r') for l in text.split('\n')]
                            for i, line in enumerate(lines):
                                if line.strip() == 'main' and i + 2 < len(lines):
                                    keys   = lines[i + 1].split('\t')
                                    values = lines[i + 2].split('\t') if (i + 2) < len(lines) else []
                                    for k, v in zip(keys, values):
                                        k, v = k.strip(), v.strip()
                                        if k and v and k in KEY_MAP:
                                            friendly = KEY_MAP[k]
                                            if k == 'p':
                                                v = MEDIA_TYPES.get(v, v)
                                            elif k == 'r':
                                                v = COMPRESSION.get(v, v)
                                            elif k in ('m', 'u'):
                                                # EWF datetime: "YYYY M D H MM SS" → ISO
                                                parts = v.split()
                                                if len(parts) >= 6:
                                                    try:
                                                        v = (f"{int(parts[0]):04d}-{int(parts[1]):02d}-"
                                                             f"{int(parts[2]):02d} {int(parts[3]):02d}:"
                                                             f"{int(parts[4]):02d}:{int(parts[5]):02d}")
                                                    except (ValueError, IndexError):
                                                        pass  # keep raw if parse fails
                                            result[friendly] = v
                                    break
                        except Exception:
                            pass
                        if result:
                            break   # header section found and parsed — stop

                    elif sec_type in ('done', 'next'):
                        break

                    if next_off == 0 or next_off <= sec_start:
                        break
                    fh.seek(next_off)

        except Exception as exc:
            self.logger.warning(f"EWF header parse warning for {e01_path.name}: {exc}")

        return result

    def process_e01_file_directly(self, e01_file_path: str) -> Dict[str, Any]:
        """Process a single .E01 file directly and extract metadata"""
        e01_path = Path(e01_file_path).resolve()
        
        if not e01_path.exists():
            return {"status": "ERROR", "error": f"E01 file not found: {e01_file_path}"}
        
        if not e01_path.is_file():
            return {"status": "ERROR", "error": f"Path is not a file: {e01_file_path}"}
        
        print(f"\n{'='*60}")
        print("EDITH-Automater ExifTool E01 Processing")
        print(f"{'='*60}")
        print(f"Case ID: {self.case_id}")
        print(f"E01 File: {e01_path}")
        print(f"ExifTool Path: {self.exiftool_path}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        
        # Step 1: Run ExifTool (extracts File: group attributes even for E01)
        result = self._run_exiftool_single_file(e01_path)

        # Step 2: Parse EWF binary header for embedded case metadata
        print("[+] Parsing EWF binary header for embedded case metadata...")
        ewf_meta = self._extract_ewf_header_metadata(e01_path)
        if ewf_meta:
            print(f"[+] EWF header parsed — {len(ewf_meta)} metadata field(s) extracted")
            for k, v in ewf_meta.items():
                print(f"    {k}: {v}")
        else:
            print("[-] No EWF case metadata found in header (image may be raw/non-E01)")

        # Step 3: Merge EWF metadata into the ExifTool JSON output
        json_file = self.output_dir / f"metadata_{self.case_id}.json"
        if result.get("success") and result.get("output_file") and Path(result["output_file"]).exists():
            try:
                with open(result["output_file"], 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if isinstance(existing, list) and existing:
                    rec = existing[0]
                elif isinstance(existing, dict):
                    rec = existing
                else:
                    rec = {}
                # Replace the uninformative error with a description
                if rec.get('ExifTool:Error') == 'Unknown file type':
                    rec['ExifTool:Error'] = 'EWF/E01 container — basic file attributes extracted'
                    rec['EWF:FormatNote'] = 'Embedded case metadata extracted from EWF header section'
                rec.update(ewf_meta)
                merged = [rec] if not isinstance(existing, list) else (existing[:-1] + [rec])
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(merged, f, indent=2, ensure_ascii=False)
                result["output_file"] = str(json_file)
                result["metadata_entries"] = len(rec)
            except Exception as merge_err:
                self.logger.warning(f"Could not merge EWF metadata: {merge_err}")
        elif ewf_meta:
            # ExifTool failed but we have EWF metadata — build JSON from scratch
            stat = e01_path.stat()
            rec = {
                "SourceFile": str(e01_path),
                "File:FileName": e01_path.name,
                "File:Directory": str(e01_path.parent),
                "File:FileSize": f"{stat.st_size // (1024*1024)} MB",
                "File:FileModifyDate": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "File:FilePermissions": "-rw-rw-rw-",
                "ExifTool:ExifToolVersion": "N/A",
                "EWF:FormatNote": "EWF/E01 container — file attributes from Python stat()",
            }
            rec.update(ewf_meta)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([rec], f, indent=2, ensure_ascii=False)
            result = {"success": True, "output_file": str(json_file),
                      "metadata_entries": len(rec)}

        if result.get("success"):
            if json_file.exists():
                self._create_multiple_outputs(str(json_file))
            self._generate_summary_report([e01_path], result)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        final_result = {
            "status": "SUCCESS" if result.get("success") else "ERROR",
            "case_id": self.case_id,
            "timestamp": start_time.isoformat(),
            "processing_time": processing_time,
            "file_path": str(e01_path),
            "result_directory": str(self.case_result_dir),
            "metadata_entries": result.get("metadata_entries", 0),
            "ewf_fields_extracted": len(ewf_meta),
            "output_files": {
                "json": str(self.output_dir / f"metadata_{self.case_id}.json"),
                "csv": str(self.output_dir / f"metadata_{self.case_id}.csv"),
                "html": str(self.output_dir / f"metadata_{self.case_id}.html"),
                "summary": str(self.output_dir / f"summary_{self.case_id}.txt")
            }
        }
        
        if not result.get("success"):
            final_result["error"] = result.get("error", "Unknown error")
        
        # Display results
        print(f"{'='*60}")
        print("E01 PROCESSING COMPLETE")
        print(f"{'='*60}")
        
        if final_result["status"] == "SUCCESS":
            print("[OK] E01 metadata extraction successful!")
            print(f"     ExifTool fields : {final_result['metadata_entries']}")
            print(f"     EWF header fields: {final_result['ewf_fields_extracted']}")
            print(f"     Processing time : {final_result['processing_time']:.2f} seconds")
            print(f"     Results saved to: {final_result['result_directory']}")
        else:
            print("[FAIL] E01 processing failed!")
            print(f"Error: {final_result.get('error', 'Unknown error')}")
        
        print(f"{'='*60}\n")
        return final_result
    
    def extract_metadata_batch(self, evidence_files: List[Path]) -> Dict[str, Any]:
        if not evidence_files:
            return {"status": "NO_FILES", "files_processed": 0}
        
        self.logger.info(f"Processing {len(evidence_files)} files")
        start_time = datetime.now()
        
        extraction_result = self._run_exiftool_batch(self.evidence_dir)
        
        if extraction_result.get("success"):
            json_file = extraction_result.get("output_file")
            if json_file and Path(json_file).exists():
                self._create_multiple_outputs(json_file)
            self._generate_integrity_report(evidence_files)
            self._generate_summary_report(evidence_files, extraction_result)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "status": "SUCCESS" if extraction_result.get("success") else "ERROR",
            "case_id": self.case_id,
            "timestamp": start_time.isoformat(),
            "processing_time": processing_time,
            "evidence_directory": str(self.evidence_dir),
            "result_directory": str(self.case_result_dir),
            "files_found": len(evidence_files),
            "files_processed": len(evidence_files) - len(self.failed_files),
            "files_failed": len(self.failed_files),
            "metadata_entries": extraction_result.get("metadata_entries", 0),
            "output_files": {
                "json": str(self.output_dir / f"metadata_{self.case_id}.json"),
                "csv": str(self.output_dir / f"metadata_{self.case_id}.csv"),
                "html": str(self.output_dir / f"metadata_{self.case_id}.html"),
                "summary": str(self.output_dir / f"summary_{self.case_id}.txt"),
                "integrity": str(self.output_dir / f"integrity_{self.case_id}.txt")
            }
        }
        
        if not extraction_result.get("success"):
            result["error"] = extraction_result.get("error", "Unknown error")
        
        self.logger.info(f"Batch processing completed in {processing_time:.2f} seconds")
        return result
    
    def _run_exiftool_batch(self, input_dir: Path) -> Dict[str, Any]:
        output_file = self.output_dir / f"metadata_{self.case_id}.json"
        
        cmd = [self.exiftool_path, "-r"]
        if self.config["advanced_extraction"]:
            cmd.extend(["-all:all", "-G", "-a", "-u", "-ee"])
        else:
            cmd.append("-all")
        cmd.extend(["-coordFormat", "%.6f", "-json", str(input_dir)])
        
        # Calculate dynamic timeout based on file count
        file_count = len(list(input_dir.rglob("*")))
        dynamic_timeout = min(max(file_count * 30, 120), 600)  # 30s per file, min 2min, max 10min
        
        try:
            self.logger.info(f"Executing ExifTool on {file_count} items, timeout: {dynamic_timeout}s")
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=dynamic_timeout, encoding='utf-8', errors='ignore')
            
            # ExifTool returns success if stdout contains JSON data, regardless of exit code
            if result.stdout.strip().startswith('[') or result.stdout.strip().startswith('{'):
                self.logger.info("ExifTool produced valid JSON output")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                metadata_count = 0
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        metadata_count = len(metadata) if isinstance(metadata, list) else 1
                    self.total_metadata_entries = metadata_count
                except Exception:
                    pass
                
                return {"success": True, "output_file": str(output_file), "metadata_entries": metadata_count}
            else:
                return {"success": False, "error": result.stderr or "No valid output produced"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"ExifTool execution timed out after {dynamic_timeout} seconds"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_multiple_outputs(self, json_file: str):
        """Create CSV and HTML outputs from JSON data"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Create CSV output
            if self.config["export_csv"]:
                csv_file = self.output_dir / f"metadata_{self.case_id}.csv"
                self._create_csv_output(metadata, csv_file)
                self.logger.info(f"CSV file created: {csv_file}")
            
            # Create HTML output
            if self.config["export_html"]:
                html_file = self.output_dir / f"metadata_{self.case_id}.html"
                self._create_html_output(metadata, html_file)
                self.logger.info(f"HTML file created: {html_file}")
                
        except Exception as e:
            self.logger.error(f"Error creating multiple outputs: {e}")
    
    def _create_csv_output(self, metadata: Union[List, Dict], csv_file: Path):
        """Create CSV output from metadata"""
        try:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if isinstance(metadata, list) and metadata:
                    # Multiple files
                    all_keys = set()
                    for item in metadata:
                        if isinstance(item, dict):
                            all_keys.update(item.keys())
                    
                    fieldnames = ['SourceFile'] + sorted([k for k in all_keys if k != 'SourceFile'])
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for item in metadata:
                        if isinstance(item, dict):
                            writer.writerow(item)
                            
                elif isinstance(metadata, dict):
                    # Single file
                    fieldnames = list(metadata.keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerow(metadata)
                    
        except Exception as e:
            self.logger.error(f"Error creating CSV: {e}")
    
    def _create_html_output(self, metadata: Union[List, Dict], html_file: Path):
        """Create HTML output from metadata"""
        try:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write('<!DOCTYPE html>\n<html>\n<head>\n')
                f.write('<title>EDITH-Automater ExifTool Report</title>\n')
                f.write('<style>\n')
                f.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
                f.write('.header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }\n')
                f.write('table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }\n')
                f.write('th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n')
                f.write('th { background-color: #f2f2f2; font-weight: bold; }\n')
                f.write('tr:nth-child(even) { background-color: #f9f9f9; }\n')
                f.write('.group { font-weight: bold; color: #0066cc; }\n')
                f.write('.file-section { margin-bottom: 40px; border: 1px solid #ccc; padding: 15px; }\n')
                f.write('</style>\n</head>\n<body>\n')
                
                # Header
                f.write('<div class="header">\n')
                f.write('<h1>EDITH-Automater ExifTool Metadata Report</h1>\n')
                f.write(f'<p><strong>Case ID:</strong> {self.case_id}</p>\n')
                f.write(f'<p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n')
                f.write(f'<p><strong>Evidence Directory:</strong> {self.evidence_dir}</p>\n')
                f.write(f'<p><strong>Total Metadata Entries:</strong> {self.total_metadata_entries}</p>\n')
                f.write('</div>\n')
                
                # Content
                if isinstance(metadata, list):
                    for i, item in enumerate(metadata):
                        if isinstance(item, dict):
                            source_file = item.get("SourceFile", f"File {i+1}")
                            f.write(f'<div class="file-section">\n')
                            f.write(f'<h2>File: {html.escape(source_file)}</h2>\n')
                            f.write(self._create_html_table(item))
                            f.write('</div>\n')
                elif isinstance(metadata, dict):
                    f.write('<div class="file-section">\n')
                    f.write('<h2>Metadata</h2>\n')
                    f.write(self._create_html_table(metadata))
                    f.write('</div>\n')
                
                f.write('</body>\n</html>')
                
        except Exception as e:
            self.logger.error(f"Error creating HTML: {e}")
    
    def _create_html_table(self, data: Dict) -> str:
        """Create HTML table from metadata dictionary"""
        html_content = '<table>\n<tr><th>Property</th><th>Value</th></tr>\n'
        
        for key, value in data.items():
            # Handle group prefixes (e.g., "EXIF:Camera" -> highlight "EXIF")
            display_key = html.escape(str(key))
            if ':' in display_key:
                group, field = display_key.split(':', 1)
                display_key = f'<span class="group">{group}:</span>{field}'
            
            display_value = html.escape(str(value))
            html_content += f'<tr><td>{display_key}</td><td>{display_value}</td></tr>\n'
        
        html_content += '</table>\n'
        return html_content
    
    def _generate_integrity_report(self, evidence_files: List[Path]):
        """Generate file integrity report with hashes"""
        if not self.config["generate_hashes"]:
            return
        
        integrity_file = self.output_dir / f"integrity_{self.case_id}.txt"
        
        try:
            with open(integrity_file, 'w', encoding='utf-8') as f:
                f.write("EDITH-Automater File Integrity Report\n")
                f.write("=" * 50 + "\n")
                f.write(f"Case ID: {self.case_id}\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Files: {len(evidence_files)}\n\n")
                
                for file_path in evidence_files:
                    try:
                        f.write(f"File: {file_path.relative_to(self.evidence_dir)}\n")
                        f.write(f"Full Path: {file_path}\n")
                        f.write(f"Size: {file_path.stat().st_size:,} bytes\n")
                        
                        # Generate hashes using chunked reading (M-12 fix: avoid loading entire file into RAM)
                        CHUNK = 8 * 1024 * 1024  # 8 MB
                        md5 = hashlib.md5()
                        sha1 = hashlib.sha1()
                        sha256 = hashlib.sha256()
                        with open(file_path, 'rb') as file_data:
                            while True:
                                chunk = file_data.read(CHUNK)
                                if not chunk:
                                    break
                                md5.update(chunk)
                                sha1.update(chunk)
                                sha256.update(chunk)
                        f.write(f"MD5: {md5.hexdigest()}\n")
                        f.write(f"SHA1: {sha1.hexdigest()}\n")
                        f.write(f"SHA256: {sha256.hexdigest()}\n")
                        
                        f.write("-" * 50 + "\n")
                        
                    except Exception as e:
                        f.write(f"Error processing {file_path}: {e}\n")
                        f.write("-" * 50 + "\n")
                        self.logger.error(f"Error hashing {file_path}: {e}")
            
            self.logger.info(f"Integrity report created: {integrity_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating integrity report: {e}")
    
    def _generate_summary_report(self, evidence_files: List[Path], extraction_result: Dict[str, Any]):
        """Generate summary report"""
        summary_file = self.output_dir / f"summary_{self.case_id}.txt"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("EDITH-Automater ExifTool Processing Summary\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Case ID: {self.case_id}\n")
                f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Evidence Directory: {self.evidence_dir}\n")
                f.write(f"Result Directory: {self.case_result_dir}\n\n")
                
                f.write("PROCESSING STATISTICS\n")
                f.write("-" * 30 + "\n")
                f.write(f"Files Found: {len(evidence_files)}\n")
                f.write(f"Files Successfully Processed: {len(evidence_files) - len(self.failed_files)}\n")
                f.write(f"Files Failed: {len(self.failed_files)}\n")
                f.write(f"Total Metadata Entries: {extraction_result.get('metadata_entries', 0)}\n\n")
                
                if self.failed_files:
                    f.write("FAILED FILES\n")
                    f.write("-" * 15 + "\n")
                    for failed_file in self.failed_files:
                        f.write(f"- {failed_file}\n")
                    f.write("\n")
                
                f.write("OUTPUT FILES GENERATED\n")
                f.write("-" * 25 + "\n")
                f.write(f"- JSON Report: metadata_{self.case_id}.json\n")
                f.write(f"- CSV Report: metadata_{self.case_id}.csv\n")
                f.write(f"- HTML Report: metadata_{self.case_id}.html\n")
                f.write(f"- Integrity Report: integrity_{self.case_id}.txt\n")
                f.write(f"- Summary Report: summary_{self.case_id}.txt\n\n")
                
                f.write("EXIFTOOL COMMAND USED\n")
                f.write("-" * 22 + "\n")
                f.write(f"{extraction_result.get('command', 'Unknown')}\n\n")
                
                f.write("=" * 60 + "\n")
                f.write("End of Summary Report\n")
            
            self.logger.info(f"Summary report created: {summary_file}")
            
        except Exception as e:
            self.logger.error(f"Error creating summary report: {e}")
    
    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file and return results"""
        file_path = Path(file_path).resolve()
        
        if not file_path.exists():
            return {"status": "ERROR", "error": f"File not found: {file_path}"}
        
        if not file_path.is_file():
            return {"status": "ERROR", "error": f"Path is not a file: {file_path}"}
        
        print(f"\n{'='*60}")
        print("EDITH-Automater ExifTool Single File Processing")
        print(f"{'='*60}")
        print(f"Case ID: {self.case_id}")
        print(f"File: {file_path}")
        print(f"ExifTool Path: {self.exiftool_path}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        result = self._run_exiftool_single_file(file_path)
        
        if result.get("success"):
            json_file = result.get("output_file")
            if json_file and Path(json_file).exists():
                self._create_multiple_outputs(json_file)
            self._generate_summary_report([file_path], result)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        final_result = {
            "status": "SUCCESS" if result.get("success") else "ERROR",
            "case_id": self.case_id,
            "timestamp": start_time.isoformat(),
            "processing_time": processing_time,
            "file_path": str(file_path),
            "result_directory": str(self.case_result_dir),
            "metadata_entries": result.get("metadata_entries", 0),
            "output_files": {
                "json": str(self.output_dir / f"metadata_{self.case_id}.json"),
                "csv": str(self.output_dir / f"metadata_{self.case_id}.csv"),
                "html": str(self.output_dir / f"metadata_{self.case_id}.html"),
                "summary": str(self.output_dir / f"summary_{self.case_id}.txt")
            }
        }
        
        if not result.get("success"):
            final_result["error"] = result.get("error", "Unknown error")
        
        # Display results
        print(f"{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        
        if final_result["status"] == "SUCCESS":
            print("✅ Processing completed successfully!")
            print(f"📈 Metadata entries: {final_result['metadata_entries']}")
            print(f"⏱️  Processing time: {final_result['processing_time']:.2f} seconds")
            print(f"📁 Results saved to: {final_result['result_directory']}")
        else:
            print("❌ Processing failed!")
            print(f"Error: {final_result.get('error', 'Unknown error')}")
        
        print(f"{'='*60}\n")
        return final_result
    
    def _run_exiftool_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Run ExifTool on a single file"""
        output_file = self.output_dir / f"metadata_{self.case_id}.json"
        
        cmd = [self.exiftool_path]
        if self.config["advanced_extraction"]:
            cmd.extend(["-all:all", "-G", "-a", "-u", "-ee"])
        else:
            cmd.append("-all")
        cmd.extend(["-coordFormat", "%.6f", "-json", str(file_path)])
        
        try:
            self.logger.info(f"Processing single file: {file_path.name}")
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=60, encoding='utf-8', errors='ignore')
            
            # ExifTool returns success if stdout contains JSON data
            if result.stdout.strip().startswith('[') or result.stdout.strip().startswith('{'):
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                
                metadata_count = 0
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        metadata_count = len(metadata) if isinstance(metadata, list) else 1
                    self.total_metadata_entries = metadata_count
                except Exception:
                    pass
                
                return {"success": True, "output_file": str(output_file), "metadata_entries": metadata_count}
            else:
                return {"success": False, "error": result.stderr or "No valid output produced"}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "ExifTool execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_all_evidence(self) -> Dict[str, Any]:
        """Main method to process all evidence files automatically"""
        print(f"\n{'='*60}")
        print("EDITH-Automater ExifTool Automated Processing")
        print(f"{'='*60}")
        print(f"Case ID: {self.case_id}")
        print(f"Evidence Directory: {self.evidence_dir}")
        print(f"Result Directory: {self.case_result_dir}")
        print(f"ExifTool Path: {self.exiftool_path}")
        print(f"{'='*60}\n")
        
        # Check if ExifTool exists
        if not Path(self.exiftool_path).exists():
            error_msg = f"ExifTool not found at: {self.exiftool_path}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return {"status": "ERROR", "error": error_msg}
        
        # Scan evidence directory
        evidence_files = self.scan_evidence_directory()
        
        if not evidence_files:
            warning_msg = f"No supported files found in evidence directory: {self.evidence_dir}"
            self.logger.warning(warning_msg)
            print(f"⚠️  {warning_msg}")
            return {"status": "NO_FILES", "message": warning_msg}
        
        print(f"📁 Found {len(evidence_files)} files to process")
        
        # Process all evidence files
        result = self.extract_metadata_batch(evidence_files)
        
        # Display results
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        
        if result["status"] == "SUCCESS":
            print("✅ Processing completed successfully!")
            print(f"📊 Files processed: {result['files_processed']}")
            print(f"📈 Metadata entries: {result['metadata_entries']}")
            print(f"⏱️  Processing time: {result['processing_time']:.2f} seconds")
            print(f"📁 Results saved to: {result['result_directory']}")
        else:
            print("❌ Processing failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print(f"{'='*60}\n")
        
        return result


def main():
    parser = argparse.ArgumentParser(description="EDITH-Automater ExifTool Automated Processing")
    parser.add_argument("--case-id", help="Case identifier")
    parser.add_argument("--config-only", action="store_true", help="Show configuration")
    parser.add_argument("--prompt", action="store_true", help="Show input directory prompt")
    parser.add_argument("--quick", action="store_true", help="Quick mode (basic extraction only)")
    parser.add_argument("--file", help="Process single file instead of directory")
    
    args = parser.parse_args()
    
    try:
        auto_tool = AutomatedExifTool(args.case_id, args.prompt)
        
        if args.quick:
            auto_tool.config["advanced_extraction"] = False
            auto_tool.config["generate_hashes"] = False
            auto_tool.logger.info("Quick mode enabled - basic extraction only")
        
        if args.config_only:
            print(f"Evidence Directory: {auto_tool.evidence_dir}")
            print(f"Result Directory: {auto_tool.result_dir}")
            print(f"ExifTool Path: {auto_tool.exiftool_path}")
            print(f"Case ID: {auto_tool.case_id}")
            return
        
        # Handle single file processing
        if args.file:
            result = auto_tool.process_single_file(args.file)
        else:
            result = auto_tool.process_all_evidence()
            
        sys.exit(0 if result["status"] in ["SUCCESS", "NO_FILES"] else 1)
            
    except KeyboardInterrupt:
        print("\n❌ Processing interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()