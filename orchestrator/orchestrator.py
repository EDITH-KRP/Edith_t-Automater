#!/usr/bin/env python3
"""
EDITH-Automater Main Orchestrator
Central controller for forensic workflow automation
"""

import os
import sys
import argparse
import asyncio
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "tools"))

class EDITHOrchestrator:
    """Main orchestrator class for EDITH-Automater"""

    def __init__(self):
        self.setup_logging()
        self.project_root = Path(__file__).parent.parent
        self.results_dir = self.project_root / "Results"
        self.results_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("EDITHOrchestrator")

    def setup_logging(self):
        """Configure logging for the orchestrator"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('orchestrator.log'),
                logging.StreamHandler()
            ]
        )

    def generate_case_id(self, prefix="CASE"):
        """Generate a new case ID with timestamp"""
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_case_directory(self, case_id=None):
        """Create a new case directory structure"""
        if case_id is None:
            case_id = self.generate_case_id()

        case_dir = self.results_dir / case_id

        # Define tool-specific subdirectories
        subdirs = {
            'questions': case_dir / "Questions",
            'hashdeep': case_dir / "HashDeep_output",
            'autopsy': case_dir / "Autopsy_output",
            'volatility': case_dir / "Volatility_output",
            'exiftool': case_dir / "ExifTool_output",
            'bulk_extractor': case_dir / "BulkExtractor_output",
            'reports': case_dir / "Final_Reports"
        }

        # Create all directories
        for subdir_name, subdir_path in subdirs.items():
            subdir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {subdir_path}")

        return str(case_dir), case_id, {k: str(v) for k, v in subdirs.items()}

    def create_new_case(self, prefix="CASE"):
        """Create a new case directory using local utilities"""
        case_id = self.generate_case_id(prefix)
        case_dir, case_id, subdirs = self.create_case_directory(case_id)
        self.logger.info(f"Created new case: {case_id} at {case_dir}")
        return case_dir, case_id

    def find_latest_case(self):
        """Find the most recent case directory"""
        try:
            case_dirs = [d for d in self.results_dir.iterdir()
                        if d.is_dir() and d.name.startswith('CASE_')]
            if not case_dirs:
                return None

            # Sort by creation time (newest first)
            latest = max(case_dirs, key=lambda x: x.stat().st_ctime)
            return str(latest)
        except Exception as e:
            self.logger.error(f"Error finding latest case: {e}")
            return None

    def list_all_cases(self):
        """List all existing cases"""
        try:
            cases = []
            for case_dir in self.results_dir.iterdir():
                if case_dir.is_dir() and case_dir.name.startswith('CASE_'):
                    case_info_file = case_dir / ".case_info"
                    case_data = {"CASE_ID": case_dir.name, "path": str(case_dir)}

                    if case_info_file.exists():
                        try:
                            with open(case_info_file, 'r') as f:
                                for line in f:
                                    if '=' in line:
                                        key, value = line.strip().split('=', 1)
                                        case_data[key] = value
                        except Exception as e:
                            self.logger.warning(f"Could not read case info for {case_dir.name}: {e}")

                    cases.append(case_data)

            return sorted(cases, key=lambda x: x.get('CREATED', ''), reverse=True)
        except Exception as e:
            self.logger.error(f"Error listing cases: {e}")
            return []

    def ensure_case_structure(self, case_dir):
        """Ensure case directory structure exists"""
        case_path = Path(case_dir)
        if not case_path.exists():
            self.logger.error(f"Case directory does not exist: {case_dir}")
            return False

        # Check and create subdirectories if needed
        subdirs = ["Questions", "HashDeep_output", "Autopsy_output",
                  "Volatility_output", "ExifTool_output", "BulkExtractor_output", "Final_Reports"]

        for subdir in subdirs:
            subdir_path = case_path / subdir
            subdir_path.mkdir(exist_ok=True)

        return True

    async def run_evidence_collection_interactive(self, case_id=None, case_dir=None):
        """Run interactive evidence collection using q_script.py"""
        self.logger.info("Starting Interactive Evidence Collection (q_script.py)")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Interactive Evidence Collection")
        print(f"{'='*80}")

        try:
            scripts_dir = self.project_root / "tools" / "Scripts"
            original_cwd = os.getcwd()

            try:
                os.chdir(scripts_dir)

                # Run q_script.py interactively
                python_executable = sys.executable

                print(f"[INFO] Starting interactive evidence collection...")
                print(f"[INFO] Running q_script.py...")

                result = subprocess.run([
                    python_executable, 'q_script.py'
                ], timeout=1800)  # 30 minute timeout for user interaction

                if result.returncode == 0:
                    print(f"\n[SUCCESS] Evidence collection completed successfully!")

                    # Try to find the latest case directory created
                    latest_case = self.find_latest_case()
                    if latest_case:
                        case_dir = latest_case
                        case_id = Path(latest_case).name
                        print(f"[INFO] Case created: {case_id}")
                        print(f"[INFO] Case directory: {case_dir}")

                    status = "success"
                    message = "Interactive evidence collection completed successfully"
                else:
                    print(f"\n[WARNING] Evidence collection completed with warnings")
                    status = "warning"
                    message = "Evidence collection completed with warnings"

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] Evidence collection timed out after 30 minutes")
            status = "timeout"
            message = "Evidence collection timed out"
        except Exception as e:
            print(f"\n[ERROR] Failed to run evidence collection: {e}")
            self.logger.error(f"Interactive evidence collection failed: {e}")
            status = "error"
            message = f"Evidence collection failed: {e}"

        return {
            "status": status,
            "case_id": case_id,
            "case_dir": case_dir,
            "message": message
        }

    async def run_evidence_collection_automated(self, case_id, case_dir):
        """Run automated evidence collection without user prompts"""
        self.logger.info("Starting Automated Evidence Collection")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Automated Evidence Collection")
        print(f"{'='*80}")
        print(f"Case ID: {case_id}")
        print(f"Case Directory: {case_dir}")
        print(f"{'='*80}")

        # Create a basic evidence collection form with default values
        questions_dir = Path(case_dir) / "Questions"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        form_file = questions_dir / f"evidence_collection_form_{timestamp}.txt"

        # Generate automated form
        automated_answers = {
            "Case Name / No": f"AUTO_{case_id}",
            "Authorized Officer": "Automated System",
            "Name of Assessee / Party": "TBD",
            "Premise Address": "TBD",
            "Start Date & Time": datetime.now().strftime('%d-%m-%Y %H:%M'),
            "End Date & Time": "TBD",
            "Search Date": datetime.now().strftime('%d-%m-%Y'),
            "Examiner's Name and Details": "EDITH-Automater System",
            "Digital Forensic Examiner": "EDITH-Automater",
            "Working Hours": "Automated",
            "Device Type": "Unknown",
            "Device Status at Seizure": "Unknown",
            "Volatile Memory / RAM Collected": "No",
            "Shut Down Type": "N/A",
            "Is the suspected media encrypted": "Unknown",
            "Hard Disk Handling": "Imaging",
            "Forensic Works Performed": "Data Acquisition, Data Extraction, Data Analysis",
            "Is Hash Value Calculated": "Yes",
            "Algorithm Used": "SHA1",
            "Storage Master Copy": "TBD",
            "Storage Working Copy": "TBD",
            "Hard Disk Capacity": "TBD",
            "No. of HDD Used": "1",
            "Is Witness Signature Taken": "No",
            "Witness Name": "N/A"
        }

        # Write automated form
        with open(form_file, "w", encoding='utf-8') as f:
            f.write("Digital Evidence Collection & Chain of Custody Form (AUTOMATED)\n")
            f.write("="*60 + "\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Case Directory: {case_dir}\n")
            f.write("="*60 + "\n\n")

            for question, answer in automated_answers.items():
                f.write(f"{question}: {answer}\n")

            f.write(f"\n{'='*60}\n")
            f.write("METADATA\n")
            f.write(f"{'='*60}\n")
            f.write(f"File created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Script version: orchestrator.py automated\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Case directory: {case_dir}\n")

        print(f"[SUCCESS] Automated evidence collection form created: {form_file}")
        self.logger.info(f"Automated evidence collection completed for case: {case_id}")

        return {
            "status": "success",
            "case_id": case_id,
            "case_dir": str(case_dir),
            "form_file": str(form_file)
        }

    async def run_forensic_analysis_automated(self, case_id, case_dir, evidence_path, memory_path=None):
        """Run automated forensic analysis using script_3.py"""
        self.logger.info("Starting Automated Forensic Analysis")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Automated Forensic Analysis")
        print(f"{'='*80}")
        print(f"Case ID: {case_id}")
        print(f"Case Directory: {case_dir}")
        print(f"Evidence: {evidence_path}")
        if memory_path:
            print(f"Memory: {memory_path}")
        print(f"{'='*80}")

        # Ensure case structure exists
        self.ensure_case_structure(case_dir)

        try:
            scripts_dir = self.project_root / "tools" / "Scripts"
            original_cwd = os.getcwd()

            print(f"\n[INFO] Starting automated forensic analysis...")
            print(f"[INFO] Evidence file: {evidence_path}")
            if memory_path:
                print(f"[INFO] Memory file: {memory_path}")

            try:
                os.chdir(scripts_dir)

                # Use direct script_3.py with input automation
                python_executable = sys.executable

                print(f"[INFO] Executing forensic analysis workflow...")

                # Prepare input for script_3.py to automate the prompts
                input_data = f"{evidence_path}\n"
                if memory_path:
                    input_data += f"{memory_path}\n"
                else:
                    input_data += "\n"

                # Set environment variable to tell script_3.py to use existing case directory
                env = os.environ.copy()
                env['EDITH_USE_EXISTING_CASE'] = 'true'
                env['EDITH_CASE_DIR'] = case_dir
                env['EDITH_CASE_ID'] = case_id

                result = subprocess.run([
                    python_executable, 'script_3.py'
                ], input=input_data, text=True, env=env, capture_output=True, timeout=3600)

                if result.returncode == 0:
                    print(f"\n[SUCCESS] Forensic analysis completed successfully!")
                    print(f"[INFO] Results saved to: {case_dir}")
                    status = "success"
                    message = "Forensic analysis completed successfully"
                else:
                    print(f"\n[WARNING] Forensic analysis completed with warnings")
                    print(f"[INFO] Check logs for details: {case_dir}")
                    status = "warning"
                    message = "Forensic analysis completed with warnings"

                # Show output summary
                if result.stdout:
                    lines = result.stdout.split('\n')
                    print(f"\n[OUTPUT] Analysis Summary (last 15 lines):")
                    for line in lines[-15:]:
                        if line.strip():
                            print(f"  {line}")

                # Show any errors
                if result.stderr:
                    print(f"\n[STDERR] Error details:")
                    error_lines = result.stderr.split('\n')
                    for line in error_lines[-5:]:
                        if line.strip():
                            print(f"  {line}")

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] Forensic analysis timed out after 1 hour")
            status = "timeout"
            message = "Forensic analysis timed out"
        except Exception as e:
            print(f"\n[ERROR] Failed to run automated analysis: {e}")
            self.logger.error(f"Automated forensic analysis failed for case: {case_id}: {e}")
            status = "error"
            message = f"Automated analysis failed: {e}"

        # Run report generation if forensic analysis was successful
        report_result = None
        if status in ["success", "warning"]:
            print(f"\n[INFO] Starting automatic report generation...")
            try:
                report_result = await self.run_report_generation(case_id, case_dir)
                if report_result["status"] == "success":
                    print(f"[SUCCESS] Report generation completed successfully!")
                elif report_result["status"] == "warning":
                    print(f"[WARNING] Report generation completed with warnings")
                else:
                    print(f"[ERROR] Report generation failed: {report_result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"[ERROR] Report generation failed: {e}")
                report_result = {"status": "error", "message": str(e)}

        return {
            "status": status,
            "case_id": case_id,
            "case_dir": str(case_dir),
            "message": message,
            "evidence_path": evidence_path,
            "memory_path": memory_path,
            "report_generation": report_result
        }

    async def run_forensic_analysis_interactive(self, evidence_path, memory_path=None, case_id=None):
        """Run interactive forensic analysis using script_3.py"""
        self.logger.info("Starting Interactive Forensic Analysis")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Interactive Forensic Analysis")
        print(f"{'='*80}")

        try:
            scripts_dir = self.project_root / "tools" / "Scripts"
            original_cwd = os.getcwd()

            try:
                os.chdir(scripts_dir)

                # Run script_3.py interactively
                python_executable = sys.executable

                print(f"[INFO] Starting interactive forensic analysis...")
                print(f"[INFO] Running script_3.py...")

                # Create input for script_3.py
                input_data = f"{evidence_path}\n"
                if memory_path:
                    input_data += f"{memory_path}\n"
                else:
                    input_data += "\n"

                result = subprocess.run([
                    python_executable, 'script_3.py'
                ], input=input_data, text=True, timeout=3600)

                if result.returncode == 0:
                    print(f"\n[SUCCESS] Forensic analysis completed successfully!")
                    status = "success"
                    message = "Interactive forensic analysis completed successfully"
                else:
                    print(f"\n[WARNING] Forensic analysis completed with warnings")
                    status = "warning"
                    message = "Forensic analysis completed with warnings"

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] Forensic analysis timed out after 1 hour")
            status = "timeout"
            message = "Forensic analysis timed out"
        except Exception as e:
            print(f"\n[ERROR] Failed to run forensic analysis: {e}")
            self.logger.error(f"Interactive forensic analysis failed: {e}")
            status = "error"
            message = f"Forensic analysis failed: {e}"

        return {
            "status": status,
            "case_id": case_id,
            "message": message,
            "evidence_path": evidence_path,
            "memory_path": memory_path
        }

    async def run_report_generation(self, case_id, case_dir):
        """Run report generation using report_gen.py"""
        self.logger.info("Starting Report Generation")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Report Generation")
        print(f"{'='*80}")
        print(f"Case ID: {case_id}")
        print(f"Case Directory: {case_dir}")
        print(f"{'='*80}")

        try:
            scripts_dir = self.project_root / "tools" / "Scripts"
            original_cwd = os.getcwd()

            print(f"\n[INFO] Starting report generation...")
            print(f"[INFO] Running report_gen.py...")

            try:
                os.chdir(scripts_dir)

                # Run report_gen.py
                python_executable = sys.executable

                result = subprocess.run([
                    python_executable, 'report_gen.py'
                ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

                if result.returncode == 0:
                    print(f"\n[SUCCESS] Report generation completed successfully!")
                    
                    # Show report generation summary from stdout
                    if result.stdout:
                        lines = result.stdout.split('\n')
                        print(f"\n[REPORT SUMMARY]:")
                        for line in lines:
                            if line.strip() and ("generated" in line.lower() or "pdf" in line.lower() or "success" in line.lower()):
                                print(f"  {line.strip()}")
                    
                    status = "success"
                    message = "Report generation completed successfully"
                else:
                    print(f"\n[WARNING] Report generation completed with warnings")
                    if result.stderr:
                        print(f"[STDERR] {result.stderr}")
                    status = "warning"
                    message = "Report generation completed with warnings"

            finally:
                os.chdir(original_cwd)

        except subprocess.TimeoutExpired:
            print(f"\n[ERROR] Report generation timed out after 10 minutes")
            status = "timeout"
            message = "Report generation timed out"
        except Exception as e:
            print(f"\n[ERROR] Failed to run report generation: {e}")
            self.logger.error(f"Report generation failed for case: {case_id}: {e}")
            status = "error"
            message = f"Report generation failed: {e}"

        return {
            "status": status,
            "case_id": case_id,
            "case_dir": str(case_dir),
            "message": message
        }

    async def run_sequential_workflow(self, evidence_path, memory_path=None, interactive=True):
        """Run evidence collection followed by forensic analysis sequentially"""
        self.logger.info("Starting Sequential Workflow")

        print(f"\n{'='*80}")
        print("EDITH-Automater: SEQUENTIAL WORKFLOW")
        print("Evidence Collection → Forensic Analysis")
        print(f"{'='*80}")

        # Step 1: Evidence Collection
        print(f"\n[STEP 1] Evidence Collection")
        print("-" * 50)

        if interactive:
            evidence_result = await self.run_evidence_collection_interactive()
        else:
            case_dir, case_id = self.create_new_case()
            evidence_result = await self.run_evidence_collection_automated(case_id, case_dir)

        if evidence_result["status"] not in ["success", "warning"]:
            print(f"[ERROR] Evidence collection failed, stopping workflow")
            return evidence_result

        case_id = evidence_result["case_id"]
        case_dir = evidence_result["case_dir"]

        # Step 2: Forensic Analysis
        print(f"\n[STEP 2] Forensic Analysis")
        print("-" * 50)

        if case_id and case_dir:
            forensic_result = await self.run_forensic_analysis_automated(
                case_id, case_dir, evidence_path, memory_path
            )
        else:
            # Fallback if case info not available
            forensic_result = await self.run_forensic_analysis_interactive(
                evidence_path, memory_path, case_id
            )

        # Overall result
        print(f"\n{'='*80}")
        print("SEQUENTIAL WORKFLOW RESULTS")
        print(f"{'='*80}")
        print(f"[STEP 1] Evidence Collection: {evidence_result['status']}")
        print(f"[STEP 2] Forensic Analysis: {forensic_result['status']}")
        
        # Show report generation status if available
        if forensic_result.get('report_generation'):
            print(f"[STEP 3] Report Generation: {forensic_result['report_generation']['status']}")

        if evidence_result["status"] == "success" and forensic_result["status"] == "success":
            overall_status = "success"
            print(f"\n[SUCCESS] Sequential workflow completed successfully!")
        elif "success" in [evidence_result["status"], forensic_result["status"]]:
            overall_status = "partial_success"
            print(f"\n[PARTIAL] Sequential workflow completed with some issues")
        else:
            overall_status = "failed"
            print(f"\n[ERROR] Sequential workflow failed")

        if case_dir:
            print(f"[INFO] All results saved to: {case_dir}")
            # Show report generation summary if available
            if forensic_result.get('report_generation') and forensic_result['report_generation']['status'] == "success":
                print(f"[INFO] Reports and PDFs generated automatically!")

        return {
            "status": overall_status,
            "case_id": case_id,
            "case_dir": case_dir,
            "evidence_collection": evidence_result,
            "forensic_analysis": forensic_result
        }

    async def run_simultaneous_workflow(self, evidence_path, memory_path=None):
        """Run evidence collection and forensic analysis simultaneously"""
        self.logger.info("Starting Simultaneous Integrated Workflow")

        print(f"\n{'='*80}")
        print("EDITH-Automater: SIMULTANEOUS INTEGRATED WORKFLOW")
        print("Evidence Collection + Forensic Analysis Running in Parallel")
        print(f"{'='*80}")

        # Create case for simultaneous execution
        case_dir, case_id = self.create_new_case()

        print(f"\n[INFO] Case Created: {case_id}")
        print(f"[INFO] Case Directory: {case_dir}")

        # Run both workflows simultaneously
        print(f"\n[INFO] Starting parallel execution...")
        print(f"[INFO] - Evidence Collection (automated)")
        print(f"[INFO] - Forensic Analysis (automated)")

        # Create tasks for parallel execution
        evidence_task = asyncio.create_task(
            self.run_evidence_collection_automated(case_id, case_dir),
            name="evidence_collection"
        )

        forensic_task = asyncio.create_task(
            self.run_forensic_analysis_automated(case_id, case_dir, evidence_path, memory_path),
            name="forensic_analysis"
        )

        # Wait for both tasks to complete
        try:
            evidence_result, forensic_result = await asyncio.gather(
                evidence_task,
                forensic_task,
                return_exceptions=True
            )

            print(f"\n{'='*80}")
            print("PARALLEL EXECUTION RESULTS")
            print(f"{'='*80}")

            # Check evidence collection result
            if isinstance(evidence_result, Exception):
                print(f"[ERROR] Evidence Collection failed: {evidence_result}")
                evidence_status = "failed"
            else:
                print(f"[SUCCESS] Evidence Collection: {evidence_result['status']}")
                evidence_status = evidence_result['status']

            # Check forensic analysis result
            if isinstance(forensic_result, Exception):
                print(f"[ERROR] Forensic Analysis failed: {forensic_result}")
                forensic_status = "failed"
            else:
                print(f"[SUCCESS] Forensic Analysis: {forensic_result['status']}")
                forensic_status = forensic_result['status']

            # Overall status
            if evidence_status == "success" and forensic_status == "success":
                overall_status = "success"
                print(f"\n[SUCCESS] Both workflows completed successfully!")
            elif "success" in [evidence_status, forensic_status]:
                overall_status = "partial_success"
                print(f"\n[PARTIAL] One or both workflows completed with issues")
            else:
                overall_status = "failed"
                print(f"\n[ERROR] Both workflows failed")

            # Run report generation if any workflow was successful
            report_result = None
            if overall_status in ["success", "partial_success"]:
                print(f"\n[INFO] Starting automatic report generation...")
                try:
                    report_result = await self.run_report_generation(case_id, case_dir)
                    if report_result["status"] == "success":
                        print(f"[SUCCESS] Report generation completed successfully!")
                    elif report_result["status"] == "warning":
                        print(f"[WARNING] Report generation completed with warnings")
                    else:
                        print(f"[ERROR] Report generation failed: {report_result.get('message', 'Unknown error')}")
                except Exception as e:
                    print(f"[ERROR] Report generation failed: {e}")
                    report_result = {"status": "error", "message": str(e)}

            print(f"[INFO] All results saved to: {case_dir}")
            if report_result and report_result["status"] == "success":
                print(f"[INFO] Reports and PDFs generated automatically!")

            self.logger.info(f"Simultaneous workflow completed for case: {case_id} with status: {overall_status}")

            return {
                "status": overall_status,
                "case_id": case_id,
                "case_dir": case_dir,
                "evidence_collection": evidence_result if not isinstance(evidence_result, Exception) else str(evidence_result),
                "forensic_analysis": forensic_result if not isinstance(forensic_result, Exception) else str(forensic_result),
                "report_generation": report_result
            }

        except Exception as e:
            print(f"\n[ERROR] Parallel execution failed: {e}")
            self.logger.error(f"Simultaneous workflow failed for case: {case_id}: {e}")
            return {
                "status": "failed",
                "case_id": case_id,
                "case_dir": case_dir,
                "error": str(e)
            }

    def print_help(self):
        """Print help information"""
        help_text = """
EDITH-Automater Orchestrator - Digital Forensics Automation

USAGE:
    python orchestrator.py [COMMAND] [OPTIONS]

COMMANDS:
    simultaneous           Run evidence collection and forensic analysis simultaneously (automated)
    sequential             Run evidence collection then forensic analysis sequentially (interactive)
    sequential-auto        Run evidence collection then forensic analysis sequentially (automated)
    evidence-only          Run evidence collection only (interactive)
    evidence-auto          Run evidence collection only (automated)
    forensic-only          Run forensic analysis only (interactive)
    forensic-auto          Run forensic analysis only (automated)
    report-only            Run report generation only (for existing case)
    list-cases             List all available cases
    help                   Show this help message

OPTIONS:
    --evidence PATH        Path to evidence file (.E01/.dd/.raw) [REQUIRED for forensic workflows]
    --memory PATH          Path to memory dump file [OPTIONAL]
    --case CASE_ID         Use specific case ID [OPTIONAL]

EXAMPLES:
    # Run simultaneous workflow (automated - fastest)
    python orchestrator.py simultaneous --evidence /path/to/charlie.E01 --memory /path/to/memory.mem

    # Run sequential workflow (interactive evidence collection)
    python orchestrator.py sequential --evidence /path/to/charlie.E01

    # Run sequential workflow (fully automated)
    python orchestrator.py sequential-auto --evidence /path/to/charlie.E01

    # Run evidence collection only (interactive)
    python orchestrator.py evidence-only

    # Run forensic analysis only (automated)
    python orchestrator.py forensic-auto --evidence /path/to/charlie.E01 --case CASE_20251007_123456

    # Run report generation only (for existing case)
    python orchestrator.py report-only --case CASE_20251007_123456

    # List all cases
    python orchestrator.py list-cases

WORKFLOW MODES:
    - simultaneous: Runs evidence collection and forensic analysis in parallel (fastest, automated)
    - sequential: Runs evidence collection first, then forensic analysis (interactive or automated)
    - evidence-only: Only creates evidence collection forms (interactive or automated)
    - forensic-only: Only runs forensic analysis (interactive or automated)
    - report-only: Only runs report generation for existing case data

INTEGRATION:
    - Uses q_script.py for interactive evidence collection
    - Uses script_3.py for forensic analysis workflow
    - Uses report_gen.py for automatic report and PDF generation
    - Manages case directories and results automatically
    - Supports both interactive and automated modes
        """
        print(help_text)


async def main():
    """Main entry point for the orchestrator"""
    parser = argparse.ArgumentParser(description='EDITH-Automater Orchestrator')
    parser.add_argument('command', nargs='?', help='Command to execute')
    parser.add_argument('--evidence', help='Path to evidence file')
    parser.add_argument('--memory', help='Path to memory dump file')
    parser.add_argument('--case', help='Case ID')

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = EDITHOrchestrator()

    # Execute command
    try:
        if not args.command or args.command == 'help':
            orchestrator.print_help()

        elif args.command == 'simultaneous':
            if not args.evidence:
                print("[ERROR] --evidence parameter required for simultaneous workflow")
                print("Usage: python orchestrator.py simultaneous --evidence /path/to/image.E01")
                return
            result = await orchestrator.run_simultaneous_workflow(
                evidence_path=args.evidence,
                memory_path=args.memory
            )
            print(f"\n[FINAL] Simultaneous workflow completed: {result['case_id']}")

        elif args.command == 'sequential':
            if not args.evidence:
                print("[ERROR] --evidence parameter required for sequential workflow")
                print("Usage: python orchestrator.py sequential --evidence /path/to/image.E01")
                return
            result = await orchestrator.run_sequential_workflow(
                evidence_path=args.evidence,
                memory_path=args.memory,
                interactive=True
            )
            print(f"\n[FINAL] Sequential workflow completed: {result.get('case_id', 'Unknown')}")

        elif args.command == 'sequential-auto':
            if not args.evidence:
                print("[ERROR] --evidence parameter required for sequential-auto workflow")
                print("Usage: python orchestrator.py sequential-auto --evidence /path/to/image.E01")
                return
            result = await orchestrator.run_sequential_workflow(
                evidence_path=args.evidence,
                memory_path=args.memory,
                interactive=False
            )
            print(f"\n[FINAL] Sequential automated workflow completed: {result.get('case_id', 'Unknown')}")

        elif args.command == 'evidence-only':
            result = await orchestrator.run_evidence_collection_interactive()
            print(f"\n[FINAL] Evidence collection completed: {result.get('case_id', 'Unknown')}")

        elif args.command == 'evidence-auto':
            case_dir, case_id = orchestrator.create_new_case()
            result = await orchestrator.run_evidence_collection_automated(case_id, case_dir)
            print(f"\n[FINAL] Automated evidence collection completed: {result.get('case_id', 'Unknown')}")

        elif args.command == 'forensic-only':
            if not args.evidence:
                print("[ERROR] --evidence parameter required for forensic-only workflow")
                print("Usage: python orchestrator.py forensic-only --evidence /path/to/image.E01")
                return
            result = await orchestrator.run_forensic_analysis_interactive(
                evidence_path=args.evidence,
                memory_path=args.memory,
                case_id=args.case
            )
            print(f"\n[FINAL] Interactive forensic analysis completed")

        elif args.command == 'forensic-auto':
            if not args.evidence:
                print("[ERROR] --evidence parameter required for forensic-auto workflow")
                print("Usage: python orchestrator.py forensic-auto --evidence /path/to/image.E01")
                return

            if args.case:
                # Use existing case
                case_id = args.case
                case_dir = str(orchestrator.results_dir / case_id)
                if not Path(case_dir).exists():
                    print(f"[ERROR] Case directory not found: {case_dir}")
                    return
            else:
                # Create new case
                case_dir, case_id = orchestrator.create_new_case()

            result = await orchestrator.run_forensic_analysis_automated(
                case_id=case_id,
                case_dir=case_dir,
                evidence_path=args.evidence,
                memory_path=args.memory
            )
            print(f"\n[FINAL] Automated forensic analysis completed: {case_id}")

        elif args.command == 'report-only':
            if not args.case:
                print("[ERROR] --case parameter required for report-only workflow")
                print("Usage: python orchestrator.py report-only --case CASE_20251007_123456")
                return
            
            case_id = args.case
            case_dir = str(orchestrator.results_dir / case_id)
            if not Path(case_dir).exists():
                print(f"[ERROR] Case directory not found: {case_dir}")
                return
                
            result = await orchestrator.run_report_generation(case_id, case_dir)
            print(f"\n[FINAL] Report generation completed: {case_id}")

        elif args.command == 'list-cases':
            cases = orchestrator.list_all_cases()
            if cases:
                print("\n[INFO] Available Cases:")
                print("-" * 80)
                for case in cases:
                    print(f"Case ID: {case['CASE_ID']}")
                    print(f"Created: {case.get('CREATED', 'Unknown')}")
                    print(f"Path: {case['path']}")
                    print("-" * 80)
            else:
                print("No cases found.")

        else:
            print(f"[ERROR] Unknown command: {args.command}")
            orchestrator.print_help()

    except KeyboardInterrupt:
        print("\n[INTERRUPT] Workflow interrupted by user")
    except Exception as e:
        print(f"[ERROR] {e}")
        orchestrator.logger.error(f"Orchestrator error: {e}")


if __name__ == "__main__":
    print("EDITH-Automater Orchestrator Starting...")
    print("=" * 60)
    asyncio.run(main())
