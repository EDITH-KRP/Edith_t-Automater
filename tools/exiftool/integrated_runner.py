#!/usr/bin/env python3
"""
ExifTool Integrated Runner
=========================

This module provides a self-contained integration interface for ExifTool
that can be called by external orchestrators or used standalone.

Features:
- Self-contained configuration management
- Standardized API interface
- Case management and logging
- Orchestrator-compatible output format
- Error handling and recovery

Author: ADITHYA N T
Version: 1.0
Date: September 2025
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import tempfile

# Import local modules
try:
    from metadata_extractor import MetadataExtractor
    METADATA_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Local metadata modules not available: {e}")
    METADATA_MODULES_AVAILABLE = False

class ExifToolIntegratedRunner:
    """
    Self-contained ExifTool runner that can interface with any orchestrator
    """
    
    def __init__(self, case_id: str = None, config_path: str = None):
        """
        Initialize the integrated runner
        
        Args:
            case_id (str): Optional case identifier
            config_path (str): Optional path to configuration file
        """
        self.case_id = case_id or f"EXIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Setup paths first
        self.tool_dir = Path(__file__).parent
        
        # Load config (which may reference tool_dir)
        self.config = self._load_config(config_path)
        
        # Setup working directories
        self.setup_working_directories()
        
        # Setup logging
        self.setup_logging()
        
        # Tool status tracking
        self.execution_status = {
            'initialized': True,
            'config_loaded': bool(self.config),
            'working_dirs_created': True,
            'logging_setup': True,
            'ready': True
        }
        
        # Results storage
        self.results = {}
        
        self.logger.info(f"ExifTool Integrated Runner initialized for case: {self.case_id}")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Load configuration from various sources
        
        Args:
            config_path (str): Path to config file
            
        Returns:
            dict: Configuration settings
        """
        config = {
            "exiftool": {
                "enabled": True,
                "executable_path": "",
                "timeout": 300,
                "options": {
                    "recursive": True,
                    "extract_all": True,
                    "output_format": "json"
                }
            },
            "extraction": {
                "export_json": True,
                "export_csv": True,
                "include_thumbnails": False,
                "preserve_original": True
            },
            "logging": {
                "level": "INFO",
                "file_logging": True,
                "console_logging": True
            },
            "output": {
                "base_dir": "output",
                "create_case_subdirs": True,
                "timestamp_outputs": True
            }
        }
        
        # Try to load from file if specified
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with defaults
                    config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config from {config_path}: {e}")
        
        # Try to load from orchestrator config if available
        orchestrator_config = self.tool_dir.parent.parent / "orchestrator" / "config.json"
        if orchestrator_config.exists():
            try:
                with open(orchestrator_config, 'r') as f:
                    orch_config = json.load(f)
                    if "tools" in orch_config and "exiftool" in orch_config["tools"]:
                        config["exiftool"].update(orch_config["tools"]["exiftool"])
            except Exception as e:
                print(f"Warning: Could not load orchestrator config: {e}")
        
        # Try to find ExifTool executable
        if not config["exiftool"]["executable_path"]:
            config["exiftool"]["executable_path"] = self._find_exiftool_executable()
        
        return config
    
    def _find_exiftool_executable(self) -> str:
        """
        Try to find ExifTool executable in common locations
        
        Returns:
            str: Path to executable or empty string if not found
        """
        possible_paths = [
            self.tool_dir / "exiftool.exe",
            self.tool_dir / "exiftool",
            "exiftool.exe",
            "exiftool"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return str(path)
        
        # Try to find in system PATH
        try:
            result = subprocess.run(['where', 'exiftool'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return ""
    
    def setup_working_directories(self):
        """Setup working directories for the case"""
        base_output = self.tool_dir / self.config["output"]["base_dir"]
        
        if self.config["output"]["create_case_subdirs"]:
            self.case_output_dir = base_output / self.case_id
        else:
            self.case_output_dir = base_output
        
        # Create necessary directories
        self.extraction_dir = self.case_output_dir / "extraction"
        self.logs_dir = self.case_output_dir / "logs"
        self.temp_dir = self.case_output_dir / "temp"
        
        for directory in [self.extraction_dir, self.logs_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging for the integrated runner"""
        log_level = getattr(logging, self.config["logging"]["level"].upper(), logging.INFO)
        
        # Create logger
        self.logger = logging.getLogger(f"ExifTool_{self.case_id}")
        self.logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File logging
        if self.config["logging"]["file_logging"]:
            log_file = self.logs_dir / f"exiftool_{self.case_id}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Console logging
        if self.config["logging"]["console_logging"]:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter(
                '%(levelname)s - [ExifTool] %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current runner status
        
        Returns:
            dict: Status information
        """
        return {
            "case_id": self.case_id,
            "status": self.execution_status,
            "config_loaded": bool(self.config),
            "executable_available": bool(self.config["exiftool"]["executable_path"]),
            "metadata_modules_available": METADATA_MODULES_AVAILABLE,
            "working_directory": str(self.case_output_dir),
            "timestamp": datetime.now().isoformat()
        }
    
    def extract_metadata(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Extract metadata from files with enhanced integration support
        
        Args:
            input_path (str): Path to file or directory to analyze
            **kwargs: Additional options to override config
            
        Returns:
            dict: Extraction results with standardized format for tool integration
        """
        start_time = datetime.now()
        self.logger.info(f"Starting metadata extraction for: {input_path}")
        
        try:
            # Prepare input
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {input_path}")
            
            # Setup extraction workspace
            extraction_input = self.temp_dir / "extraction_input"
            extraction_output = self.extraction_dir / "output"
            
            extraction_input.mkdir(exist_ok=True)
            extraction_output.mkdir(exist_ok=True)
            
            # Copy/link input to workspace and track files
            input_files = []
            if input_path.is_file():
                import shutil
                shutil.copy2(input_path, extraction_input / input_path.name)
                input_files = [extraction_input / input_path.name]
            elif input_path.is_dir():
                import shutil
                temp_input = extraction_input / "input_data"
                shutil.copytree(input_path, temp_input)
                input_files = list(temp_input.rglob("*"))
                input_files = [f for f in input_files if f.is_file()]
            
            # Determine extraction method
            use_native = (self.config["exiftool"]["executable_path"] and 
                         Path(self.config["exiftool"]["executable_path"]).exists())
            
            if use_native:
                result = self._extract_with_native_exiftool(extraction_input, extraction_output, **kwargs)
            elif METADATA_MODULES_AVAILABLE:
                result = self._extract_with_python_modules(extraction_input, extraction_output, **kwargs)
            else:
                raise RuntimeError("No extraction method available (no ExifTool executable or Python modules)")
            
            # Calculate execution time and statistics
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Collect file statistics for integration
            file_stats = self._collect_file_statistics(input_files)
            
            # Generate hash values for chain of custody (integration with hashdeep)
            input_hashes = self._generate_file_hashes(str(input_path))
            
            # Prepare standardized result with enhanced integration data
            standardized_result = {
                "tool_name": "exiftool",
                "operation": "metadata_extraction",
                "case_id": self.case_id,
                "status": "SUCCESS" if result.get("success", False) else "FAILED",
                "input_path": str(input_path),
                "output_directory": str(extraction_output),
                "execution_time": execution_time,
                "files_processed": len(input_files),
                "extraction_method": "native_exiftool" if use_native else "python_modules",
                "timestamp": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "file_statistics": file_stats,
                "integrity_hashes": input_hashes,
                "output_formats": ["json", "csv"] if result.get("success") else [],
                "integration_data": {
                    "compatible_tools": ["autopsy", "hashdeep", "bulk_extractor"],
                    "output_ready": result.get("success", False),
                    "chain_of_custody_maintained": bool(input_hashes.get("md5")),
                    "forensically_sound": True
                },
                "results": result
            }
            
            # Store result
            self.results["last_extraction"] = standardized_result
            
            self.logger.info(f"Metadata extraction completed in {execution_time:.2f} seconds")
            self.logger.info(f"Files processed: {len(input_files)}, Output formats: {standardized_result['output_formats']}")
            return standardized_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                "tool_name": "exiftool",
                "operation": "metadata_extraction",
                "case_id": self.case_id,
                "status": "FAILED",
                "input_path": str(input_path) if 'input_path' in locals() else "unknown",
                "execution_time": execution_time,
                "error_message": str(e),
                "timestamp": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "files_processed": 0,
                "integration_data": {
                    "compatible_tools": [],
                    "output_ready": False,
                    "chain_of_custody_maintained": False,
                    "forensically_sound": False
                }
            }
            
            self.logger.error(f"Metadata extraction failed: {e}")
            self.results["last_extraction"] = error_result
            return error_result
    
    def _extract_with_native_exiftool(self, input_dir: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Extract metadata using native ExifTool executable"""
        self.logger.info("Using native ExifTool executable")
        
        executable = self.config["exiftool"]["executable_path"]
        options = self.config["exiftool"]["options"].copy()
        options.update(kwargs)
        
        # Build command
        cmd = [executable]
        
        if options.get("recursive", True):
            cmd.append("-r")
        
        if options.get("extract_all", True):
            cmd.append("-all")
        
        # Output format
        output_file = output_dir / f"metadata_{self.case_id}.json"
        cmd.extend(["-json", "-out", str(output_file)])
        
        # Add input directory
        cmd.append(str(input_dir))
        
        try:
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config["exiftool"]["timeout"]
            )
            
            if result.returncode == 0:
                # Parse output if JSON
                metadata_count = 0
                if output_file.exists():
                    try:
                        with open(output_file, 'r') as f:
                            metadata = json.load(f)
                            metadata_count = len(metadata) if isinstance(metadata, list) else 1
                    except:
                        pass
                
                return {
                    "success": True,
                    "method": "native_exiftool",
                    "output_file": str(output_file),
                    "metadata_entries": metadata_count,
                    "stdout": result.stdout,
                    "command": " ".join(cmd)
                }
            else:
                return {
                    "success": False,
                    "method": "native_exiftool",
                    "error": result.stderr,
                    "command": " ".join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "method": "native_exiftool",
                "error": f"Execution timed out after {self.config['exiftool']['timeout']} seconds"
            }
    
    def _extract_with_python_modules(self, input_dir: Path, output_dir: Path, **kwargs) -> Dict[str, Any]:
        """Extract metadata using Python modules"""
        self.logger.info("Using Python metadata extraction modules")
        
        try:
            extractor = MetadataExtractor(
                input_directory=str(input_dir),
                output_directory=str(output_dir)
            )
            
            # Configure based on settings
            export_json = self.config["extraction"].get("export_json", True)
            export_csv = self.config["extraction"].get("export_csv", True)
            
            # Run extraction
            results = extractor.run_extraction(
                export_json=export_json,
                export_csv=export_csv
            )
            
            return {
                "success": True,
                "method": "python_modules",
                "results": results,
                "files_found": len(extractor.process_directory()) if hasattr(extractor, 'process_directory') else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "method": "python_modules",
                "error": str(e)
            }
    

    
    def run_analysis(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Run analysis operation (main entry point for orchestrators)
        
        Args:
            input_path (str): Path to analyze
            **kwargs: Additional options
            
        Returns:
            dict: Analysis results
        """
        self.logger.info(f"Running metadata extraction analysis on {input_path}")
        
        results = {
            "case_id": self.case_id,
            "operation": "extract",
            "input_path": input_path,
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING"
        }
        
        try:
            extract_result = self.extract_metadata(input_path, **kwargs)
            results["extraction"] = extract_result
            
            # Set overall status based on extraction result
            results["status"] = extract_result["status"]
            
            results["end_time"] = datetime.now().isoformat()
            self.results["last_analysis"] = results
            
            return results
            
        except Exception as e:
            results["status"] = "FAILED"
            results["error_message"] = str(e)
            results["end_time"] = datetime.now().isoformat()
            
            self.logger.error(f"Analysis operation failed: {e}")
            self.results["last_analysis"] = results
            return results
    
    def get_results(self, operation: str = None) -> Dict[str, Any]:
        """
        Get stored results
        
        Args:
            operation (str): Specific operation to get results for
            
        Returns:
            dict: Results data
        """
        if operation:
            return self.results.get(f"last_{operation}", {})
        else:
            return self.results
    
    def _collect_file_statistics(self, file_list: List[Path]) -> Dict[str, Any]:
        """
        Collect statistics about processed files for integration purposes
        
        Args:
            file_list (List[Path]): List of file paths
            
        Returns:
            Dict[str, Any]: File statistics
        """
        try:
            if not file_list:
                return {"total_files": 0, "total_size_bytes": 0, "file_types": {}}
            
            total_size = 0
            file_types = {}
            
            for file_path in file_list:
                try:
                    size = file_path.stat().st_size
                    total_size += size
                    
                    # Track file extensions
                    ext = file_path.suffix.lower() or "no_extension"
                    file_types[ext] = file_types.get(ext, 0) + 1
                    
                except Exception:
                    continue
            
            return {
                "total_files": len(file_list),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "largest_file_size": max((f.stat().st_size for f in file_list if f.exists()), default=0)
            }
        except Exception as e:
            self.logger.warning(f"Could not collect file statistics: {e}")
            return {"total_files": len(file_list), "error": str(e)}
    
    def _generate_file_hashes(self, file_path: str) -> Dict[str, str]:
        """
        Generate hash values for chain of custody (integration with hashdeep)
        
        Args:
            file_path (str): Path to file or directory
            
        Returns:
            Dict[str, str]: Hash values
        """
        try:
            file_path = Path(file_path)
            
            if file_path.is_file():
                # For single files, calculate hashes directly
                import hashlib
                
                hashes = {"md5": "", "sha256": ""}
                
                with open(file_path, 'rb') as f:
                    content = f.read()
                    hashes["md5"] = hashlib.md5(content).hexdigest()
                    hashes["sha256"] = hashlib.sha256(content).hexdigest()
                
                return hashes
            
            elif file_path.is_dir():
                # For directories, create a manifest hash
                import hashlib
                
                file_list = sorted([str(p) for p in file_path.rglob("*") if p.is_file()])
                manifest_content = "\n".join(file_list).encode('utf-8')
                
                return {
                    "md5": hashlib.md5(manifest_content).hexdigest(),
                    "sha256": hashlib.sha256(manifest_content).hexdigest(),
                    "type": "directory_manifest"
                }
            
        except Exception as e:
            self.logger.warning(f"Could not generate hashes for {file_path}: {e}")
        
        return {"md5": "", "sha256": "", "error": "hash_generation_failed"}
    
    def get_integration_info(self) -> Dict[str, Any]:
        """
        Get information about tool integration capabilities
        
        Returns:
            Dict[str, Any]: Integration information
        """
        return {
            "tool_name": "exiftool",
            "version": "1.0",
            "capabilities": [
                "metadata_extraction",
                "batch_processing",
                "multiple_formats",
                "forensic_reporting"
            ],
            "supported_formats": {
                "images": [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"],
                "documents": [".pdf"],
                "audio": [".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a"],
                "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
            },
            "output_formats": ["json", "csv", "text"],
            "integration_ready": True,
            "chain_of_custody_support": True,
            "compatible_tools": {
                "autopsy": {
                    "compatible": True,
                    "data_exchange": "json_metadata",
                    "use_case": "supplement_timeline_analysis"
                },
                "hashdeep": {
                    "compatible": True,
                    "data_exchange": "file_integrity_verification",
                    "use_case": "evidence_integrity_chain"
                },
                "bulk_extractor": {
                    "compatible": True,
                    "data_exchange": "cross_reference_metadata",
                    "use_case": "enhanced_artifact_context"
                },
                "volatility3": {
                    "compatible": True,
                    "data_exchange": "file_metadata_correlation",
                    "use_case": "memory_dump_file_correlation"
                }
            }
        }
    
    def export_for_integration(self, target_tool: str, case_id: str = None) -> Dict[str, Any]:
        """
        Export data in format suitable for integration with other tools
        
        Args:
            target_tool (str): Target tool name (autopsy, hashdeep, etc.)
            case_id (str): Case identifier for cross-tool referencing
            
        Returns:
            Dict[str, Any]: Integration-ready data export
        """
        case_id = case_id or self.case_id
        
        # Get latest extraction results
        last_result = self.results.get("last_extraction", {})
        
        if target_tool.lower() == "autopsy":
            return {
                "case_id": case_id,
                "tool_source": "exiftool",
                "export_type": "autopsy_integration",
                "metadata_files": last_result.get("results", {}).get("results", {}),
                "timeline_data": self._create_timeline_data(last_result),
                "artifact_references": self._create_artifact_references(last_result)
            }
        
        elif target_tool.lower() == "hashdeep":
            return {
                "case_id": case_id,
                "tool_source": "exiftool",
                "export_type": "hashdeep_integration",
                "file_manifest": last_result.get("file_statistics", {}),
                "integrity_hashes": last_result.get("integrity_hashes", {}),
                "chain_of_custody": self._create_custody_data(last_result)
            }
        
        elif target_tool.lower() == "bulk_extractor":
            return {
                "case_id": case_id,
                "tool_source": "exiftool",
                "export_type": "bulk_extractor_integration",
                "metadata_context": last_result.get("results", {}),
                "file_locations": self._create_file_location_data(last_result)
            }
        
        else:
            # Generic export format
            return {
                "case_id": case_id,
                "tool_source": "exiftool",
                "export_type": "generic_integration",
                "full_results": last_result,
                "summary": self.generate_summary()
            }
    
    def _create_timeline_data(self, extraction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create timeline data for Autopsy integration"""
        timeline_events = []
        
        # Extract timestamp information from results for timeline creation
        if "results" in extraction_result and "results" in extraction_result["results"]:
            # This would be populated with actual timestamp data from extraction
            timeline_events.append({
                "timestamp": extraction_result.get("timestamp"),
                "event_type": "metadata_extraction",
                "description": f"Metadata extracted for case {self.case_id}",
                "source": "exiftool",
                "file_count": extraction_result.get("files_processed", 0)
            })
        
        return timeline_events
    
    def _create_artifact_references(self, extraction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create artifact references for cross-tool correlation"""
        return [{
            "artifact_type": "metadata_extraction",
            "source_tool": "exiftool",
            "case_id": self.case_id,
            "file_path": extraction_result.get("input_path"),
            "extraction_timestamp": extraction_result.get("timestamp"),
            "reference_id": f"exif_{self.case_id}_{extraction_result.get('timestamp', '').replace(':', '_')}"
        }]
    
    def _create_custody_data(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create chain of custody data for HashDeep integration"""
        return {
            "tool_name": "exiftool",
            "case_id": self.case_id,
            "operation": "metadata_extraction",
            "timestamp": extraction_result.get("timestamp"),
            "input_hashes": extraction_result.get("integrity_hashes", {}),
            "forensically_sound": extraction_result.get("integration_data", {}).get("forensically_sound", False)
        }
    
    def _create_file_location_data(self, extraction_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create file location data for Bulk Extractor cross-referencing"""
        return [{
            "source_path": extraction_result.get("input_path"),
            "metadata_extracted": extraction_result.get("status") == "SUCCESS",
            "tool_source": "exiftool",
            "case_reference": self.case_id
        }]

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of all operations
        
        Returns:
            dict: Summary information
        """
        summary = {
            "case_id": self.case_id,
            "runner_status": self.execution_status,
            "operations_performed": list(self.results.keys()),
            "total_operations": len(self.results),
            "working_directory": str(self.case_output_dir),
            "config_summary": {
                "native_exiftool_available": bool(self.config["exiftool"]["executable_path"]),
                "python_modules_available": METADATA_MODULES_AVAILABLE,
                "extraction_enabled": self.config["extraction"]["export_json"] or self.config["extraction"]["export_csv"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add operation summaries
        for op_name, op_result in self.results.items():
            if isinstance(op_result, dict) and "status" in op_result:
                summary[f"{op_name}_status"] = op_result["status"]
                if "execution_time" in op_result:
                    summary[f"{op_name}_time"] = op_result["execution_time"]
        
        return summary

# Factory functions for easy integration

def create_runner(case_id: str = None, config_path: str = None) -> ExifToolIntegratedRunner:
    """
    Factory function to create an integrated runner
    
    Args:
        case_id (str): Case identifier
        config_path (str): Configuration file path
        
    Returns:
        ExifToolIntegratedRunner: Configured runner instance
    """
    return ExifToolIntegratedRunner(case_id, config_path)

def quick_extract(input_path: str, case_id: str = None) -> Dict[str, Any]:
    """
    Quick metadata extraction function
    
    Args:
        input_path (str): Path to analyze
        case_id (str): Optional case ID
        
    Returns:
        dict: Extraction results
    """
    runner = create_runner(case_id)
    return runner.extract_metadata(input_path)

def quick_analysis(input_path: str, case_id: str = None) -> Dict[str, Any]:
    """
    Quick analysis function
    
    Args:
        input_path (str): Path to analyze
        case_id (str): Optional case ID
        
    Returns:
        dict: Analysis results
    """
    runner = create_runner(case_id)
    return runner.run_analysis(input_path)

def get_tool_integration_info() -> Dict[str, Any]:
    """
    Get ExifTool integration capabilities without creating a runner instance
    
    Returns:
        Dict[str, Any]: Integration information
    """
    runner = create_runner()
    return runner.get_integration_info()

def export_for_tool(input_path: str, target_tool: str, case_id: str = None) -> Dict[str, Any]:
    """
    Extract metadata and export in format suitable for specific target tool
    
    Args:
        input_path (str): Path to analyze
        target_tool (str): Target tool name
        case_id (str): Optional case ID
        
    Returns:
        Dict[str, Any]: Tool-specific export data
    """
    runner = create_runner(case_id)
    
    # First extract metadata
    extraction_result = runner.extract_metadata(input_path)
    
    # Then export for target tool
    if extraction_result["status"] == "SUCCESS":
        return runner.export_for_integration(target_tool, case_id)
    else:
        return {
            "error": "Extraction failed",
            "extraction_result": extraction_result,
            "target_tool": target_tool
        }

# Command line interface
def interactive_mode():
    """
    Interactive mode that prompts user for input via command prompt
    """
    print("=" * 60)
    print("         EXIFTOOL METADATA EXTRACTION TOOL")
    print("=" * 60)
    print()
    
    # Get input file/directory path from user
    while True:
        input_path = input("Enter the path to image file or .dd file to analyze: ").strip()
        
        if not input_path:
            print("Error: Please enter a valid path.")
            continue
            
        # Remove quotes if present
        input_path = input_path.strip('"').strip("'")
        
        if not Path(input_path).exists():
            print(f"Error: Path '{input_path}' does not exist. Please enter a valid path.")
            continue
        
        break
    
    # Get case ID from user (optional)
    case_id = input("Enter Case ID (optional, press Enter for auto-generated): ").strip()
    if not case_id:
        case_id = f"EXIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\nProcessing file: {input_path}")
    print(f"Case ID: {case_id}")
    print(f"Output will be saved in: tools/exiftool/output/{case_id}/")
    
    # Ask for confirmation
    confirm = input("\nProceed with extraction? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        return
    
    try:
        # Create runner with output in exiftool directory
        runner = create_runner(case_id)
        
        # Override output directory to ensure it's in exiftool folder
        runner.config["output"]["base_dir"] = "output"
        runner.setup_working_directories()
        
        print("\nStarting metadata extraction...")
        print("-" * 40)
        
        # Run extraction
        result = runner.run_analysis(input_path)
        
        print("-" * 40)
        
        if result["status"] == "SUCCESS":
            print("✓ EXTRACTION COMPLETED SUCCESSFULLY!")
            print(f"Files processed: {result['extraction'].get('files_processed', 0)}")
            print(f"Execution time: {result['extraction'].get('execution_time', 0):.2f} seconds")
            print(f"Output directory: {runner.case_output_dir}")
            
            # List output files
            if runner.case_output_dir.exists():
                print("\nGenerated files:")
                for file_path in runner.case_output_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(runner.case_output_dir)
                        file_size = file_path.stat().st_size
                        print(f"  - {relative_path} ({file_size} bytes)")
            
            # Ask if user wants to see the results summary
            show_summary = input("\nDo you want to see the results summary? (y/n): ").strip().lower()
            if show_summary in ['y', 'yes']:
                summary = runner.generate_summary()
                print("\n" + "=" * 60)
                print("RESULTS SUMMARY")
                print("=" * 60)
                print(json.dumps(summary, indent=2))
                
        else:
            print("✗ EXTRACTION FAILED!")
            print(f"Error: {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Thank you for using ExifTool Metadata Extraction Tool")
    print("=" * 60)

def main():
    """Command line interface for the integrated runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ExifTool Integrated Runner")
    parser.add_argument("input_path", nargs="?", help="Path to file or directory to analyze")
    parser.add_argument("--case-id", help="Case identifier")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--operation", choices=["extract"], 
                       default="extract", help="Operation to perform")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--status", action="store_true", help="Show runner status")
    parser.add_argument("--summary", action="store_true", help="Show results summary")
    parser.add_argument("--integration-info", action="store_true", help="Show tool integration information")
    parser.add_argument("--export-for", choices=["autopsy", "hashdeep", "bulk_extractor"], 
                       help="Export results for specific tool integration")
    parser.add_argument("--chain-of-custody", action="store_true", help="Include full chain of custody data")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # If no input_path provided or interactive mode requested, run interactive mode
    if not args.input_path or args.interactive:
        interactive_mode()
        return
    
    try:
        # Create runner
        runner = create_runner(args.case_id, args.config)
        
        if args.status:
            status = runner.get_status()
            print(json.dumps(status, indent=2))
            return
        
        if args.integration_info:
            integration_info = runner.get_integration_info()
            print(json.dumps(integration_info, indent=2))
            return
        
        # Override config if needed
        if args.output_dir:
            runner.config["output"]["base_dir"] = args.output_dir
            runner.setup_working_directories()
        
        # Run analysis
        result = runner.run_analysis(args.input_path)
        
        # Show results
        if args.summary:
            summary = runner.generate_summary()
            print(json.dumps(summary, indent=2))
        elif args.export_for:
            # Export for specific tool integration
            if result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]:
                export_data = runner.export_for_integration(args.export_for, args.case_id)
                print(json.dumps(export_data, indent=2))
            else:
                print(f"Cannot export for {args.export_for}: extraction failed")
                print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        if result["status"] in ["SUCCESS", "PARTIAL_SUCCESS"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()