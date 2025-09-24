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
    from metadata_remover import MetadataRemover
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
        self.config = self._load_config(config_path)
        
        # Setup paths
        self.tool_dir = Path(__file__).parent
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
            "removal": {
                "backup_originals": True,
                "verify_removal": True,
                "generate_reports": True
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
        self.removal_dir = self.case_output_dir / "removal"
        self.logs_dir = self.case_output_dir / "logs"
        self.temp_dir = self.case_output_dir / "temp"
        
        for directory in [self.extraction_dir, self.removal_dir, self.logs_dir, self.temp_dir]:
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
        Extract metadata from files
        
        Args:
            input_path (str): Path to file or directory to analyze
            **kwargs: Additional options to override config
            
        Returns:
            dict: Extraction results
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
            
            # Copy/link input to workspace
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
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare standardized result
            standardized_result = {
                "operation": "metadata_extraction",
                "case_id": self.case_id,
                "status": "SUCCESS" if result.get("success", False) else "FAILED",
                "input_path": str(input_path),
                "output_directory": str(extraction_output),
                "execution_time": execution_time,
                "files_processed": len(input_files),
                "extraction_method": "native_exiftool" if use_native else "python_modules",
                "timestamp": start_time.isoformat(),
                "results": result
            }
            
            # Store result
            self.results["last_extraction"] = standardized_result
            
            self.logger.info(f"Metadata extraction completed in {execution_time:.2f} seconds")
            return standardized_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                "operation": "metadata_extraction",
                "case_id": self.case_id,
                "status": "FAILED",
                "input_path": str(input_path) if 'input_path' in locals() else "unknown",
                "execution_time": execution_time,
                "error_message": str(e),
                "timestamp": start_time.isoformat()
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
    
    def remove_metadata(self, input_path: str, **kwargs) -> Dict[str, Any]:
        """
        Remove metadata from files
        
        Args:
            input_path (str): Path to file or directory to clean
            **kwargs: Additional options
            
        Returns:
            dict: Removal results
        """
        start_time = datetime.now()
        self.logger.info(f"Starting metadata removal for: {input_path}")
        
        try:
            if not METADATA_MODULES_AVAILABLE:
                raise RuntimeError("Python metadata modules not available for removal")
            
            # Prepare paths
            input_path = Path(input_path)
            if not input_path.exists():
                raise FileNotFoundError(f"Input path does not exist: {input_path}")
            
            # Setup removal workspace
            removal_input = self.temp_dir / "removal_input"
            removal_output = self.removal_dir / "cleaned_files"
            removal_reports = self.removal_dir / "reports"
            
            removal_input.mkdir(exist_ok=True)
            removal_output.mkdir(exist_ok=True)
            removal_reports.mkdir(exist_ok=True)
            
            # Copy input to workspace
            if input_path.is_file():
                import shutil
                shutil.copy2(input_path, removal_input / input_path.name)
            elif input_path.is_dir():
                import shutil
                temp_input = removal_input / "input_data"
                shutil.copytree(input_path, temp_input)
            
            # Initialize metadata remover
            remover = MetadataRemover(
                input_directory=str(removal_input),
                output_directory=str(removal_output),
                reports_directory=str(removal_reports)
            )
            
            # Run removal
            results = remover.run_removal_process(
                export_json=True,
                export_csv=True
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare standardized result
            standardized_result = {
                "operation": "metadata_removal",
                "case_id": self.case_id,
                "status": "SUCCESS",
                "input_path": str(input_path),
                "cleaned_files_directory": str(removal_output),
                "reports_directory": str(removal_reports),
                "execution_time": execution_time,
                "removal_stats": remover.removal_stats,
                "timestamp": start_time.isoformat(),
                "results": results
            }
            
            self.results["last_removal"] = standardized_result
            self.logger.info(f"Metadata removal completed in {execution_time:.2f} seconds")
            return standardized_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                "operation": "metadata_removal",
                "case_id": self.case_id,
                "status": "FAILED",
                "input_path": str(input_path) if 'input_path' in locals() else "unknown",
                "execution_time": execution_time,
                "error_message": str(e),
                "timestamp": start_time.isoformat()
            }
            
            self.logger.error(f"Metadata removal failed: {e}")
            self.results["last_removal"] = error_result
            return error_result
    
    def run_analysis(self, input_path: str, operation: str = "extract", **kwargs) -> Dict[str, Any]:
        """
        Run analysis operation (main entry point for orchestrators)
        
        Args:
            input_path (str): Path to analyze
            operation (str): Operation type ("extract", "remove", "both")
            **kwargs: Additional options
            
        Returns:
            dict: Analysis results
        """
        self.logger.info(f"Running analysis operation: {operation} on {input_path}")
        
        results = {
            "case_id": self.case_id,
            "operation": operation,
            "input_path": input_path,
            "start_time": datetime.now().isoformat(),
            "status": "RUNNING"
        }
        
        try:
            if operation in ["extract", "both"]:
                extract_result = self.extract_metadata(input_path, **kwargs)
                results["extraction"] = extract_result
            
            if operation in ["remove", "both"]:
                remove_result = self.remove_metadata(input_path, **kwargs)
                results["removal"] = remove_result
            
            # Determine overall status
            all_operations = []
            if "extraction" in results:
                all_operations.append(results["extraction"]["status"])
            if "removal" in results:
                all_operations.append(results["removal"]["status"])
            
            if all(status == "SUCCESS" for status in all_operations):
                results["status"] = "SUCCESS"
            elif any(status == "SUCCESS" for status in all_operations):
                results["status"] = "PARTIAL_SUCCESS"
            else:
                results["status"] = "FAILED"
            
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
                "extraction_enabled": self.config["extraction"]["export_json"] or self.config["extraction"]["export_csv"],
                "removal_enabled": self.config["removal"]["backup_originals"]
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

def quick_remove(input_path: str, case_id: str = None) -> Dict[str, Any]:
    """
    Quick metadata removal function
    
    Args:
        input_path (str): Path to clean
        case_id (str): Optional case ID
        
    Returns:
        dict: Removal results
    """
    runner = create_runner(case_id)
    return runner.remove_metadata(input_path)

def quick_analysis(input_path: str, operation: str = "extract", case_id: str = None) -> Dict[str, Any]:
    """
    Quick analysis function
    
    Args:
        input_path (str): Path to analyze
        operation (str): Operation type
        case_id (str): Optional case ID
        
    Returns:
        dict: Analysis results
    """
    runner = create_runner(case_id)
    return runner.run_analysis(input_path, operation)

# Command line interface
def main():
    """Command line interface for the integrated runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ExifTool Integrated Runner")
    parser.add_argument("input_path", help="Path to file or directory to analyze")
    parser.add_argument("--case-id", help="Case identifier")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--operation", choices=["extract", "remove", "both"], 
                       default="extract", help="Operation to perform")
    parser.add_argument("--output-dir", help="Override output directory")
    parser.add_argument("--status", action="store_true", help="Show runner status")
    parser.add_argument("--summary", action="store_true", help="Show results summary")
    
    args = parser.parse_args()
    
    try:
        # Create runner
        runner = create_runner(args.case_id, args.config)
        
        if args.status:
            status = runner.get_status()
            print(json.dumps(status, indent=2))
            return
        
        # Override config if needed
        if args.output_dir:
            runner.config["output"]["base_dir"] = args.output_dir
            runner.setup_working_directories()
        
        # Run analysis
        result = runner.run_analysis(args.input_path, args.operation)
        
        # Show results
        if args.summary:
            summary = runner.generate_summary()
            print(json.dumps(summary, indent=2))
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