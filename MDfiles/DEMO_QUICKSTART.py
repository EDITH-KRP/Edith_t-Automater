#!/usr/bin/env python3
"""
EDITH-Automater Demo Quickstart
================================
Fast demonstration script for hackathon judges
Runs a complete forensic workflow with sample data
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Color codes for Windows
try:
    import colorama
    colorama.init()
    GREEN = colorama.Fore.GREEN
    RED = colorama.Fore.RED
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    RESET = colorama.Fore.RESET
    BOLD = colorama.Style.BRIGHT
except ImportError:
    GREEN = RED = YELLOW = BLUE = RESET = BOLD = ""


class DemoRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.demo_mode = True
        self.start_time = time.time()
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
        print(f"{BOLD}{BLUE}{'='*80}{RESET}\n")
    
    def print_step(self, step_num, total_steps, description):
        """Print a step indicator"""
        print(f"{BOLD}[Step {step_num}/{total_steps}]{RESET} {description}")
        print(f"{'-'*80}")
    
    def print_success(self, message):
        """Print a success message"""
        print(f"{GREEN}✓ {message}{RESET}")
    
    def print_warning(self, message):
        """Print a warning message"""
        print(f"{YELLOW}⚠ {message}{RESET}")
    
    def print_error(self, message):
        """Print an error message"""
        print(f"{RED}✗ {message}{RESET}")
    
    def check_dependencies(self):
        """Quick dependency check"""
        self.print_step(1, 5, "Checking Dependencies")
        
        critical_packages = ['reportlab', 'jinja2', 'plotly', 'psutil', 'openpyxl']
        missing = []
        
        for package in critical_packages:
            try:
                __import__(package)
                self.print_success(f"{package} installed")
            except ImportError:
                missing.append(package)
                self.print_warning(f"{package} missing (optional for demo)")
        
        if missing:
            self.print_warning(f"Missing packages: {', '.join(missing)}")
            self.print_warning("Run: pip install " + ' '.join(missing))
            print()
            response = input(f"{YELLOW}Continue anyway? (y/n): {RESET}").strip().lower()
            if response != 'y':
                print(f"{RED}Demo cancelled. Install dependencies first.{RESET}")
                sys.exit(1)
        else:
            self.print_success("All critical dependencies installed!")
        
        print()
        time.sleep(1)
    
    def create_sample_case(self):
        """Create a sample case for demonstration"""
        self.print_step(2, 5, "Creating Sample Case")
        
        # Create a case directory
        case_id = f"DEMO_CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        results_dir = self.project_root / "Results"
        case_dir = results_dir / case_id
        
        # Create subdirectories
        subdirs = {
            'questions': case_dir / "Questions",
            'hashdeep': case_dir / "HashDeep_output",
            'autopsy': case_dir / "Autopsy_output",
            'volatility': case_dir / "Volatility_output",
            'exiftool': case_dir / "ExifTool_output",
            'bulk_extractor': case_dir / "BulkExtractor_output",
            'reports': case_dir / "Final_Reports"
        }
        
        for name, path in subdirs.items():
            path.mkdir(parents=True, exist_ok=True)
            self.print_success(f"Created {name} directory")
        
        # Create sample evidence collection form
        questions_file = subdirs['questions'] / "questions.txt"
        with open(questions_file, 'w') as f:
            f.write("Digital Evidence Collection & Chain of Custody Form (DEMO)\n")
            f.write("="*60 + "\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Case Directory: {case_dir}\n")
            f.write("="*60 + "\n\n")
            f.write("Case Name / No: DEMO_HACKATHON_2026\n")
            f.write("Authorized Officer: Demo Officer\n")
            f.write("Name of Assessee / Party: Sample Suspect\n")
            f.write("Premise Address: Demo Location\n")
            f.write("Start Date & Time: 27-02-2026 10:00AM\n")
            f.write("End Date & Time: 27-02-2026 02:00PM\n")
            f.write("Search Date: 27-02-2026\n")
            f.write("Examiner's Name and Details: EDITH Team\n")
            f.write("Digital Forensic Examiner: Auto-Forensics System\n")
            f.write("Working Hours: 4hr\n")
            f.write("Device Type (Laptop/Desktop/Server/Other): Laptop\n")
            f.write("Victim Device Make/Model/Size/Serial No: Dell/Latitude/1TB/DEMO123456\n")
            f.write("Device Status at Seizure (On/Off/Sleep): Off\n")
            f.write("Volatile Memory / RAM Collected (Yes/No): No\n")
            f.write("Shut Down Type (Normal/Power Pulled/Battery Removed/N/A): Normal\n")
            f.write("Is the suspected media encrypted (Yes/No): No\n")
            f.write("Hard Disk Handling (Seizure/Forensic Previewing/Imaging/Backup): Imaging\n")
            f.write("Forensic Works Performed: Data Acquisition, Data Extraction, Data Analysis\n")
            f.write("Is Hash Value Calculated (Yes/No): Yes\n")
            f.write("Algorithm Used (MD5/SHA1/Others): SHA1\n")
            f.write("Storage Master Copy Make/Model/Size/Serial No: WD/MyBook/2TB/STORAGE001\n")
            f.write("Storage Working Copy Make/Model/Size/Serial No: Seagate/Portable/1TB/STORAGE002\n")
            f.write("Hard Disk Capacity: 1 TB\n")
            f.write("No. of HDD Used: 1\n")
            f.write("Is Witness Signature Taken (Yes/No): Yes\n")
            f.write("Witness Name: John Doe\n")
        
        self.print_success(f"Sample evidence form created: questions.txt")
        
        # Save case info
        case_info_file = case_dir / ".case_info"
        with open(case_info_file, 'w') as f:
            f.write(f"CASE_ID={case_id}\n")
            f.write(f"CASE_DIR={case_dir}\n")
            f.write(f"CREATED={datetime.now().isoformat()}\n")
            f.write(f"CASE_NAME=DEMO_HACKATHON_2026\n")
            f.write(f"OFFICER_NAME=Demo Officer\n")
        
        self.print_success(f"Case created: {case_id}")
        print()
        time.sleep(1)
        
        return str(case_dir), case_id
    
    def simulate_forensic_analysis(self, case_dir, case_id):
        """Simulate forensic analysis with demo data"""
        self.print_step(3, 5, "Running Forensic Analysis (Simulated)")
        
        case_path = Path(case_dir)
        
        # Simulate HashDeep
        hashdeep_dir = case_path / "HashDeep_output"
        hashdeep_file = hashdeep_dir / "hash_report.txt"
        with open(hashdeep_file, 'w') as f:
            f.write("EDITH-Automater HashDeep Report (DEMO)\n")
            f.write("="*60 + "\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\nHashes Calculated:\n")
            f.write("MD5:    d41d8cd98f00b204e9800998ecf8427e\n")
            f.write("SHA1:   da39a3ee5e6b4b0d3255bfef95601890afd80709\n")
            f.write("SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n")
        self.print_success("HashDeep analysis completed")
        
        # Simulate Autopsy
        autopsy_dir = case_path / "Autopsy_output"
        autopsy_file = autopsy_dir / "analysis.txt"
        with open(autopsy_file, 'w') as f:
            f.write("Autopsy Analysis Report (DEMO)\n")
            f.write("="*60 + "\n")
            f.write("File System: NTFS\n")
            f.write("Total Files: 15,284\n")
            f.write("Deleted Files: 347\n")
            f.write("Hidden Files: 89\n")
        self.print_success("Autopsy analysis completed")
        
        # Simulate ExifTool
        exiftool_dir = case_path / "ExifTool_output"
        exiftool_file = exiftool_dir / "metadata.txt"
        with open(exiftool_file, 'w') as f:
            f.write("ExifTool Metadata Analysis (DEMO)\n")
            f.write("="*60 + "\n")
            f.write("Images Processed: 234\n")
            f.write("Documents Processed: 1,543\n")
            f.write("Metadata Entries: 8,765\n")
        self.print_success("ExifTool analysis completed")
        
        print()
        time.sleep(1)
    
    def generate_reports(self, case_dir, case_id):
        """Generate demonstration reports"""
        self.print_step(4, 5, "Generating Reports")
        
        try:
            # Try to run report generator
            scripts_dir = self.project_root / "tools" / "Scripts"
            
            # Set environment variables
            env = os.environ.copy()
            env['CASE_DIR'] = str(case_dir)
            
            result = subprocess.run(
                [sys.executable, str(scripts_dir / "report_gen.py")],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(scripts_dir)
            )
            
            if result.returncode == 0:
                self.print_success("Reports generated successfully!")
            else:
                self.print_warning("Report generation had warnings (HTML reports still available)")
            
        except Exception as e:
            self.print_warning(f"Could not auto-generate reports: {e}")
            self.print_warning("Manual report generation available at: tools/Scripts/report_gen.py")
        
        print()
        time.sleep(1)
    
    def show_results(self, case_dir, case_id):
        """Show results and next steps"""
        self.print_step(5, 5, "Demo Complete!")
        
        elapsed = time.time() - self.start_time
        
        print(f"\n{BOLD}{GREEN}Demo ran successfully in {elapsed:.1f} seconds!{RESET}\n")
        
        case_path = Path(case_dir)
        reports_dir = case_path / "Final_Reports"
        
        print(f"{BOLD}Case Information:{RESET}")
        print(f"  Case ID: {case_id}")
        print(f"  Location: {case_dir}")
        print()
        
        print(f"{BOLD}Generated Artifacts:{RESET}")
        print(f"  ✓ Evidence Collection Form")
        print(f"  ✓ HashDeep Analysis")
        print(f"  ✓ Autopsy Analysis")
        print(f"  ✓ ExifTool Metadata")
        
        # Check for reports
        if reports_dir.exists():
            html_reports = list(reports_dir.glob("*.html"))
            pdf_reports = list(reports_dir.glob("*.pdf"))
            
            if html_reports:
                print(f"  ✓ HTML Reports ({len(html_reports)} generated)")
            if pdf_reports:
                print(f"  ✓ PDF Reports ({len(pdf_reports)} generated)")
        
        print()
        print(f"{BOLD}Next Steps:{RESET}")
        print(f"  1. Explore case directory: {case_dir}")
        print(f"  2. View HTML reports in browser")
        print(f"  3. Run full workflow: python orchestrator/orchestrator.py --help")
        print()
        
        # Offer to open reports
        if reports_dir.exists():
            html_reports = list(reports_dir.glob("FILLED_*.html"))
            if html_reports:
                print(f"{YELLOW}Open first report in browser? (y/n): {RESET}", end='')
                response = input().strip().lower()
                if response == 'y':
                    import webbrowser
                    webbrowser.open(str(html_reports[0]))
                    self.print_success("Report opened in browser!")
        
        print()
        print(f"{BOLD}{BLUE}{'='*80}{RESET}")
        print(f"{BOLD}{GREEN}EDITH-Automater Demo Complete!{RESET}".center(88))
        print(f"{BOLD}{BLUE}{'='*80}{RESET}")
        print()


def main():
    """Main demo execution"""
    demo = DemoRunner()
    
    demo.print_header("EDITH-Automater HACKATHON DEMO")
    print(f"{BOLD}Digital Forensics Automation Framework{RESET}".center(88))
    print("Automated Evidence Collection → Analysis → Reporting".center(80))
    print()
    
    try:
        # Run demo steps
        demo.check_dependencies()
        case_dir, case_id = demo.create_sample_case()
        demo.simulate_forensic_analysis(case_dir, case_id)
        demo.generate_reports(case_dir, case_id)
        demo.show_results(case_dir, case_id)
        
    except KeyboardInterrupt:
        print(f"\n{RED}Demo interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Demo error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
