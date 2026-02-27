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

if getattr(sys, 'frozen', False):
    # Frozen (PyInstaller one-file): exe can be placed anywhere (USB, Desktop …).
    # Put Results/, config.json, etc. right NEXT TO the exe so the user can find them.
    PROJECT_ROOT = Path(sys.executable).resolve().parent
    _tools_dir   = Path(sys._MEIPASS) / "tools"
else:
    PROJECT_ROOT = Path(__file__).parent.parent
    _tools_dir   = PROJECT_ROOT / "tools"

sys.path.insert(0, str(_tools_dir))

# Import FTK module
try:
    from ftk_metadata import integrate_ftk_with_case
    FTK_AVAILABLE = True
except ImportError:
    FTK_AVAILABLE = False

class EDITHOrchestrator:
    """Main orchestrator class for EDITH-Automater"""

    def __init__(self):
        self.setup_logging()
        # ── Frozen-exe detection ─────────────────────────────────────────────
        # When built with PyInstaller (one-file), __file__ resolves to the
        # _MEIPASS temp dir.  Use sys.executable (the actual .exe) instead.
        if getattr(sys, 'frozen', False):
            # Frozen: Results/ lives next to the exe — easy to find on USB / Desktop
            self.project_root = Path(sys.executable).resolve().parent
            self._bundle_dir   = Path(sys._MEIPASS)
        else:
            self.project_root = Path(__file__).parent.parent
            self._bundle_dir   = None
        # ────────────────────────────────────────────────────────────────────
        self.results_dir = self.project_root / "Results"
        self.results_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger("EDITHOrchestrator")
        self.python_executable = self.get_python_executable()
        self.config = self._load_config()

    def _load_config(self):
        """M-1 FIX: Load config.json and expose settings to the rest of the orchestrator."""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            try:
                import json
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.logger.info(f"Configuration loaded from {config_path}")
                return cfg
            except Exception as e:
                self.logger.warning(f"Could not load config.json: {e}. Using built-in defaults.")
        return {}

    def get_python_executable(self):
        """Get the correct Python executable, preferring virtual environment.
        When running as a frozen exe the exe itself is NOT a Python interpreter,
        so we must locate a real python on the system PATH."""
        if getattr(sys, 'frozen', False):
            # Frozen: find a real Python interpreter via PATH
            for candidate in ('python', 'python3', 'py'):
                found = shutil.which(candidate)
                if found and Path(found).resolve() != Path(sys.executable).resolve():
                    self.logger.info(f"Frozen mode — system Python found: {found}")
                    return found
            self.logger.warning(
                "Frozen mode — no system Python found on PATH. "
                "Install Python and ensure it is on the PATH."
            )
            return sys.executable   # last resort (will likely fail)

        # Unfrozen: prefer venv
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            self.logger.info(f"Using virtual environment Python: {venv_python}")
            return str(venv_python)

        self.logger.info(f"Using system Python: {sys.executable}")
        return sys.executable

    def get_subprocess_env(self):
        """Get environment with virtual environment activated.
        When frozen, expose the _MEIPASS bundle dir on PYTHONPATH so
        subprocesses (q_script, script_3, report_gen …) can import
        the bundled packages."""
        env = os.environ.copy()

        # Add virtual environment to PATH if it exists
        venv_scripts = self.project_root / ".venv" / "Scripts"
        if venv_scripts.exists():
            current_path = env.get('PATH', '')
            env['PATH'] = f"{venv_scripts};{current_path}"
            env['VIRTUAL_ENV'] = str(self.project_root / ".venv")
            env.pop('PYTHONHOME', None)

        # When frozen, add bundle dir so scripts can import bundled modules
        if self._bundle_dir and self._bundle_dir.exists():
            existing_pp = env.get('PYTHONPATH', '')
            bundle_str  = str(self._bundle_dir)
            env['PYTHONPATH'] = f"{bundle_str};{existing_pp}" if existing_pp else bundle_str

        # Always tell every subprocess where the real Results folder is.
        # Without this, frozen subprocesses derive the path from __file__ which
        # points to the _MEIPASS temp dir and gets deleted on exit.
        env['EDITH_RESULTS_BASE'] = str(self.results_dir)

        return env

    def get_scripts_dir(self) -> Path:
        """Return the Scripts directory whether running frozen or from source.
        Frozen  → scripts are extracted to _MEIPASS/tools/Scripts
        Unfrozen → scripts live under project_root/tools/Scripts"""
        if self._bundle_dir and self._bundle_dir.exists():
            return self._bundle_dir / "tools" / "Scripts"
        return self.project_root / "tools" / "Scripts"

    def setup_logging(self):
        """Configure logging for the orchestrator"""
        # Mod-8 FIX: use absolute path so log file location is predictable regardless of cwd
        log_path = Path(__file__).parent / "orchestrator.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_path)),
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
        """Find the most recent case directory by parsing the timestamp in the case ID name"""
        try:
            case_dirs = [d for d in self.results_dir.iterdir()
                        if d.is_dir() and d.name.startswith('CASE_')]
            if not case_dirs:
                return None

            # Mod-3 FIX: sort by the timestamp embedded in the name, not st_ctime
            # (st_ctime is NOT creation time on Linux — it is inode change time)
            def _case_key(p):
                try:
                    return p.name  # CASE_YYYYMMDD_HHMMSS sorts lexicographically = chronologically
                except Exception:
                    return p.name

            latest = max(case_dirs, key=_case_key)
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

    async def run_evidence_collection_interactive(self, case_id=None, case_dir=None, evidence_path=None):
        """Run interactive evidence collection using q_script.py"""
        self.logger.info("Starting Interactive Evidence Collection (q_script.py)")

        print(f"\n{'='*80}")
        print("EDITH-Automater: Interactive Evidence Collection")
        print(f"{'='*80}")

        # C-4 FIX: pre-initialize so return dict is always valid even if an exception fires early
        status = "error"
        message = "Unknown error in evidence collection"

        try:
            scripts_dir = self.get_scripts_dir()

            try:
                python_executable = self.python_executable

                print(f"[INFO] Starting interactive evidence collection...")
                print(f"[INFO] Running q_script.py...")
                print(f"[INFO] Scripts dir: {scripts_dir}")

                # Forward evidence path so q_script auto-confirms the image file question
                env = self.get_subprocess_env()
                if evidence_path and Path(evidence_path).is_file():
                    env['EDITH_EVIDENCE_PATH'] = str(evidence_path)
                    print(f"[INFO] Evidence path pre-supplied to questionnaire: {evidence_path}")

                result = subprocess.run([
                    python_executable, str(scripts_dir / 'q_script.py')
                ], timeout=1800, env=env, cwd=str(scripts_dir))  # 30 minute timeout for user interaction

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

            except Exception:
                raise  # re-raise so outer excepts handle it

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

    async def run_evidence_collection_automated(self, case_id, case_dir, evidence_path=None):
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

        # Compute hashes from evidence file if provided
        md5_hash = ""
        sha256_hash = ""
        evidence_size = "TBD"
        evidence_label = "TBD"
        if evidence_path and Path(evidence_path).is_file():
            import hashlib
            ep = Path(evidence_path)
            evidence_label = ep.name
            evidence_size = str(ep.stat().st_size) + " bytes"
            md5_h = hashlib.md5()
            sha256_h = hashlib.sha256()
            try:
                with open(ep, "rb") as _ef:
                    for _chunk in iter(lambda: _ef.read(8 * 1024 * 1024), b""):
                        md5_h.update(_chunk)
                        sha256_h.update(_chunk)
                md5_hash = md5_h.hexdigest()
                sha256_hash = sha256_h.hexdigest()
                print(f"[INFO] Evidence MD5:    {md5_hash}")
                print(f"[INFO] Evidence SHA256: {sha256_hash}")
            except Exception as _e:
                self.logger.warning(f"Could not hash evidence file: {_e}")

        # NOTE: Key names MUST match report_gen.py lookup keys (with parenthetical options).
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
            "Device Type (Laptop/Desktop/Server/Other)": "Other",
            "Device Status at Seizure (On/Off/Sleep)": "Off",
            "Volatile Memory / RAM Collected (Yes/No)": "No",
            "Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)": "N/A",
            "Is the suspected media encrypted (Yes/No)": "No",
            "Hard Disk Handling (Seizure/Forensic Previewing/Imaging/Backup)": "Imaging",
            "Forensic Works Performed": "Data Acquisition, Data Extraction, Data Analysis",
            "Is Hash Value Calculated (Yes/No)": "Yes",
            "Algorithm Used (MD5/SHA1/Others)": "SHA-256",
            "MD5 hash value": md5_hash if md5_hash else "N/A",
            "SHA1 hash value": sha256_hash if sha256_hash else "N/A",
            "Storage Master Copy Make/Model/Size/Serial No": f"{evidence_label}///{evidence_size}",
            "Storage Working Copy Make/Model/Size/Serial No": f"{evidence_label}///{evidence_size}",
            "Victim Device Make/Model/Size/Serial No": f"Unknown///{evidence_size}",
            "Hard Disk Capacity": evidence_size,
            "No. of HDD Used": "1",
            "Is Witness Signature Taken (Yes/No)": "No",
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

        # M-5 FIX: validate evidence file before starting any tool
        if not Path(evidence_path).exists():
            print(f"[ERROR] Evidence file not found: {evidence_path}")
            return {
                "status": "error", "case_id": case_id, "case_dir": str(case_dir),
                "message": f"Evidence file not found: {evidence_path}",
                "evidence_path": evidence_path, "memory_path": memory_path,
                "report_generation": None
            }
        if not Path(evidence_path).is_file():
            print(f"[ERROR] Evidence path is not a file: {evidence_path}")
            return {
                "status": "error", "case_id": case_id, "case_dir": str(case_dir),
                "message": f"Evidence path is not a file: {evidence_path}",
                "evidence_path": evidence_path, "memory_path": memory_path,
                "report_generation": None
            }

        # C-4 FIX: pre-initialize so return dict is always valid
        status = "error"
        message = "Unknown error in forensic analysis"

        try:
            scripts_dir = self.get_scripts_dir()

            print(f"\n[INFO] Starting automated forensic analysis...")
            print(f"[INFO] Evidence file: {evidence_path}")
            if memory_path:
                print(f"[INFO] Memory file: {memory_path}")

            try:
                python_executable = self.python_executable

                # Pass evidence/memory as explicit CLI args — no stdin dependency
                cmd = [python_executable, str(scripts_dir / 'script_3.py'), '--evidence', evidence_path]
                if memory_path:
                    cmd += ['--memory', memory_path]

                # Set environment variable to tell script_3.py to use existing case directory
                env = self.get_subprocess_env()
                env['EDITH_USE_EXISTING_CASE'] = 'true'
                env['EDITH_CASE_DIR'] = case_dir
                env['EDITH_CASE_ID'] = case_id

                print(f"[INFO] Executing forensic analysis workflow...")
                print(f"[INFO] Live output (large evidence files may take several minutes):")
                print("-" * 60)
                sys.stdout.flush()

                # Stream output line-by-line so progress is visible in real-time
                returncode = None
                try:
                    with subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding='utf-8',
                        errors='replace',
                        env=env,
                        cwd=str(scripts_dir)
                    ) as proc:
                        for line in proc.stdout:
                            print(f"  {line}", end='', flush=True)
                        proc.wait(timeout=3600)
                        returncode = proc.returncode
                except subprocess.TimeoutExpired:
                    raise

                print("-" * 60)

                if returncode == 0:
                    print(f"\n[SUCCESS] Forensic analysis completed successfully!")
                    print(f"[INFO] Results saved to: {case_dir}")
                    status = "success"
                    message = "Forensic analysis completed successfully"
                else:
                    print(f"\n[WARNING] Forensic analysis completed with warnings (rc={returncode})")
                    print(f"[INFO] Check output above and logs in: {case_dir}")
                    status = "warning"
                    message = f"Forensic analysis completed with warnings (rc={returncode})"

            except Exception:
                raise

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

        # C-4 FIX: pre-initialize
        status = "error"
        message = "Unknown error in forensic analysis"

        try:
            scripts_dir = self.get_scripts_dir()

            try:
                python_executable = self.python_executable

                print(f"[INFO] Starting interactive forensic analysis...")
                print(f"[INFO] Running script_3.py...")

                # Pass evidence/memory as explicit CLI args — no stdin dependency
                cmd = [python_executable, str(scripts_dir / 'script_3.py'), '--evidence', evidence_path]
                if memory_path:
                    cmd += ['--memory', memory_path]

                result = subprocess.run(
                    cmd, text=True, timeout=3600,
                    env=self.get_subprocess_env(), cwd=str(scripts_dir))

                if result.returncode == 0:
                    print(f"\n[SUCCESS] Forensic analysis completed successfully!")
                    status = "success"
                    message = "Interactive forensic analysis completed successfully"
                else:
                    print(f"\n[WARNING] Forensic analysis completed with warnings")
                    status = "warning"
                    message = "Forensic analysis completed with warnings"

            except Exception:
                raise

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

        # C-4 FIX: pre-initialize
        status = "error"
        message = "Unknown error in report generation"

        try:
            scripts_dir = self.get_scripts_dir()

            print(f"\n[INFO] Starting report generation...")
            print(f"[INFO] Running report_gen.py...")

            try:
                # C-8 FIX: use cwd= instead of os.chdir()
                # Run report_gen.py
                python_executable = self.python_executable

                # Pass the exact case directory so report_gen picks the right case
                rep_env = self.get_subprocess_env()
                rep_env['CASE_DIR'] = str(case_dir)

                print(f"[INFO] Live output:")
                print("-" * 60)
                sys.stdout.flush()

                returncode = None
                try:
                    with subprocess.Popen(
                        [python_executable, str(scripts_dir / 'report_gen.py')],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        encoding='utf-8',
                        errors='replace',
                        env=rep_env,
                        cwd=str(scripts_dir)
                    ) as proc:
                        for line in proc.stdout:
                            print(f"  {line}", end='', flush=True)
                        proc.wait(timeout=600)
                        returncode = proc.returncode
                except subprocess.TimeoutExpired:
                    raise

                print("-" * 60)

                if returncode == 0:
                    print(f"\n[SUCCESS] Report generation completed successfully!")
                    status = "success"
                    message = "Report generation completed successfully"
                else:
                    print(f"\n[WARNING] Report generation completed with warnings (rc={returncode})")
                    status = "warning"
                    message = f"Report generation completed with warnings (rc={returncode})"

            except Exception:
                raise

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

    async def process_ftk_image(self, image_path, case_dir, case_id, case_name="", officer_name=""):
        """
        Process FTK Imager forensic image and extract metadata
        
        Args:
            image_path: Path to FTK image file (.E01, .dd, etc.)
            case_dir: Case directory path
            case_id: Case ID
            case_name: Case name
            officer_name: Officer name
        
        Returns:
            Dictionary with processing results
        """
        
        if not FTK_AVAILABLE:
            self.logger.error("FTK module not available. Install with: pip install libewf-python pytsk3")
            return {
                "status": "error",
                "case_id": case_id,
                "case_dir": case_dir,
                "message": "FTK module not available"
            }
        
        if not Path(image_path).exists():
            self.logger.error(f"Image file not found: {image_path}")
            return {
                "status": "error",
                "case_id": case_id,
                "case_dir": case_dir,
                "message": f"Image file not found: {image_path}"
            }
        
        try:
            self.logger.info(f"Processing FTK image: {image_path}")
            print(f"\n[FTK IMAGE PROCESSING] Analyzing: {Path(image_path).name}")
            
            # Call FTK integration
            result = integrate_ftk_with_case(
                case_dir=case_dir,
                image_path=image_path,
                case_id=case_id,
                case_name=case_name,
                officer_name=officer_name
            )
            
            if result['success']:
                self.logger.info("FTK image processing completed successfully")
                
                # Extract key information
                image_metadata = result.get('image_metadata', {})
                ftk_form_path = result.get('ftk_form_path', '')
                
                print(f"✓ Image processed successfully")
                print(f"  File: {image_metadata.get('file_name', 'N/A')}")
                print(f"  Format: {image_metadata.get('format', 'N/A')}")
                print(f"  Size: {image_metadata.get('file_size_gb', 0)} GB")
                print(f"  MD5: {image_metadata.get('md5', 'N/A')}")
                print(f"  Report: {Path(ftk_form_path).name}")
                
                return {
                    "status": "success",
                    "case_id": case_id,
                    "case_dir": case_dir,
                    "image_path": image_path,
                    "image_metadata": image_metadata,
                    "ftk_form_path": ftk_form_path
                }
            else:
                error_msg = result.get('error', 'Unknown error during FTK processing')
                self.logger.error(f"FTK processing failed: {error_msg}")
                print(f"✗ FTK processing failed: {error_msg}")
                
                return {
                    "status": "error",
                    "case_id": case_id,
                    "case_dir": case_dir,
                    "message": error_msg
                }
        
        except Exception as e:
            self.logger.error(f"Error processing FTK image: {e}")
            print(f"✗ Error processing FTK image: {e}")
            
            return {
                "status": "error",
                "case_id": case_id,
                "case_dir": case_dir,
                "message": str(e)
            }

    async def run_sequential_workflow(self, evidence_path, memory_path=None, interactive=True):
        """Run evidence collection followed by FTK image processing and forensic analysis sequentially"""
        self.logger.info("Starting Sequential Workflow")

        print(f"\n{'='*80}")
        print("EDITH-Automater: SEQUENTIAL WORKFLOW")
        print("Evidence Collection → FTK Image Processing → Forensic Analysis")
        print(f"{'='*80}")

        # Step 1: Evidence Collection
        print(f"\n[STEP 1] Evidence Collection")
        print("-" * 50)

        if interactive:
            evidence_result = await self.run_evidence_collection_interactive()
        else:
            case_dir, case_id = self.create_new_case()
            evidence_result = await self.run_evidence_collection_automated(case_id, case_dir, evidence_path=evidence_path)

        if evidence_result["status"] not in ["success", "warning"]:
            print(f"[ERROR] Evidence collection failed, stopping workflow")
            return evidence_result

        case_id = evidence_result["case_id"]
        case_dir = evidence_result["case_dir"]
        image_path = None
        ftk_result = None
        
        # Step 2: FTK Image Processing (if image file configured)
        # Read image path from case info
        case_info_file = Path(case_dir) / ".case_info"
        if case_info_file.exists():
            try:
                with open(case_info_file, 'r') as f:
                    for line in f:
                        if 'IMAGE_PATH=' in line:
                            image_path = line.split('=', 1)[1].strip()
            except Exception as e:
                self.logger.debug(f"Could not read image path from case info: {e}")
        
        if image_path and Path(image_path).exists():
            print(f"\n[STEP 2] FTK Image Processing")
            print("-" * 50)
            
            # Extract case info for FTK processing
            case_name = ""
            officer_name = ""
            case_info_fields = {}
            
            if case_info_file.exists():
                try:
                    with open(case_info_file, 'r') as f:
                        for line in f:
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                case_info_fields[key] = value
                    case_name = case_info_fields.get('CASE_NAME', 'Investigation')
                    officer_name = case_info_fields.get('OFFICER_NAME', 'Officer')
                except Exception as e:
                    self.logger.debug(f"Could not extract case info: {e}")
            
            ftk_result = await self.process_ftk_image(
                image_path=image_path,
                case_dir=case_dir,
                case_id=case_id,
                case_name=case_name,
                officer_name=officer_name
            )
            
            step_number = 3
        else:
            step_number = 2
            ftk_result = None
        
        # Step N: Forensic Analysis
        print(f"\n[STEP {step_number}] Forensic Analysis")
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
        if ftk_result:
            print(f"[STEP 2] FTK Image Processing: {ftk_result['status']}")
            print(f"[STEP 3] Forensic Analysis: {forensic_result['status']}")
        else:
            print(f"[STEP 2] Forensic Analysis: {forensic_result['status']}")
        
        # Show report generation status if available
        if forensic_result.get('report_generation'):
            print(f"[STEP 3] Report Generation: {forensic_result['report_generation']['status']}")

        # Check success status
        statuses_to_check = [evidence_result["status"], forensic_result["status"]]
        if ftk_result:
            statuses_to_check.insert(1, ftk_result["status"])
        
        if all(s == "success" for s in statuses_to_check):
            overall_status = "success"
            print(f"\n[SUCCESS] Sequential workflow completed successfully!")
        elif any(s == "success" for s in statuses_to_check):
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

        result_dict = {
            "status": overall_status,
            "case_id": case_id,
            "case_dir": case_dir,
            "evidence_collection": evidence_result,
            "forensic_analysis": forensic_result
        }
        
        if ftk_result:
            result_dict["ftk_image_processing"] = ftk_result
        
        return result_dict

    async def run_simultaneous_workflow(self, evidence_path, memory_path=None):
        """Run evidence collection questionnaire first (interactive), then forensic analysis."""
        self.logger.info("Starting Simultaneous Integrated Workflow")

        print(f"\n{'='*80}")
        print("EDITH-Automater: SIMULTANEOUS INTEGRATED WORKFLOW")
        print("Step 1: Interactive Evidence Collection  ->  Step 2: Forensic Analysis")
        print(f"{'='*80}")

        # ------------------------------------------------------------------ #
        # STEP 1 — Ask questions interactively (blocks until user is done)   #
        # ------------------------------------------------------------------ #
        print(f"\n[STEP 1/2] Evidence Collection Questionnaire")
        print(f"{'─'*60}")

        evidence_result = await self.run_evidence_collection_interactive(evidence_path=evidence_path)

        if isinstance(evidence_result, Exception) or evidence_result.get("status") not in ("success", "completed"):
            err = evidence_result if isinstance(evidence_result, Exception) else evidence_result.get("message", "unknown")
            print(f"[ERROR] Evidence collection failed: {err}")
            return {
                "status": "failed",
                "case_id": None,
                "case_dir": None,
                "evidence_collection": str(err),
                "forensic_analysis": None,
                "report_generation": None,
            }

        # q_script.py creates its own case directory — retrieve it
        case_id  = evidence_result.get("case_id")
        case_dir = evidence_result.get("case_dir")

        print(f"\n[INFO] Evidence collection complete — Case: {case_id}")
        print(f"[INFO] Case Directory: {case_dir}")

        # ------------------------------------------------------------------ #
        # STEP 2 — Run forensic analysis (uses the case created in step 1)  #
        # ------------------------------------------------------------------ #
        print(f"\n[STEP 2/2] Forensic Analysis")
        print(f"{'─'*60}")

        forensic_result = None
        forensic_status = "skipped"
        try:
            forensic_result = await self.run_forensic_analysis_automated(case_id, case_dir, evidence_path, memory_path)
            if isinstance(forensic_result, Exception):
                print(f"[ERROR] Forensic analysis failed: {forensic_result}")
                forensic_status = "failed"
            else:
                forensic_status = forensic_result.get("status", "unknown")
                print(f"[SUCCESS] Forensic Analysis: {forensic_status}")
        except Exception as e:
            print(f"[ERROR] Forensic analysis failed: {e}")
            forensic_result = {"status": "error", "message": str(e)}
            forensic_status = "failed"

        # ------------------------------------------------------------------ #
        # Overall status + report generation                                 #
        # ------------------------------------------------------------------ #
        evidence_status = evidence_result.get("status", "unknown")

        if evidence_status in ("success", "completed") and forensic_status == "success":
            overall_status = "success"
            print(f"\n[SUCCESS] Both steps completed successfully!")
        elif evidence_status in ("success", "completed") or forensic_status == "success":
            overall_status = "partial_success"
            print(f"\n[PARTIAL] Workflow completed with some issues")
        else:
            overall_status = "failed"
            print(f"\n[ERROR] Workflow failed")

        report_result = None
        if overall_status in ("success", "partial_success") and case_id and case_dir:
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

        print(f"\n[INFO] All results saved to: {case_dir}")
        if report_result and report_result.get("status") == "success":
            print(f"[INFO] Reports and PDFs generated automatically!")

        self.logger.info(f"Simultaneous workflow completed for case: {case_id} with status: {overall_status}")

        return {
            "status": overall_status,
            "case_id": case_id,
            "case_dir": case_dir,
            "evidence_collection": evidence_result,
            "forensic_analysis": forensic_result if not isinstance(forensic_result, Exception) else str(forensic_result),
            "report_generation": report_result,
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
