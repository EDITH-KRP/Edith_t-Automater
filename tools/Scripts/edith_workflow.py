#!/usr/bin/env python3
"""
EDITH-Automater Master Workflow
Complete Digital Evidence Report Generation System

This script orchestrates the complete workflow:
1. Data Collection (q_script.py)
2. HTML Report Generation (simple_html_generator.py)
3. Instructions for PDF conversion

Author: EDITH-Automater Team
Date: September 30, 2025
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

class EDITHWorkflow:
    """Master workflow controller for EDITH-Automater"""
    
    def __init__(self):
        self.base_path = Path("e:/Github-adhi982/Edith_t-Automater")
        self.scripts_path = self.base_path / "tools" / "Scripts"
        self.questions_file = self.base_path / "evidence" / "Results" / "Questions" / "questions.txt"
        self.output_dir = self.base_path / "evidence" / "Final_Reports"
        
    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "="*80)
        print("🚀 EDITH-Automater - Digital Evidence Report Generation System")
        print("="*80)
        print("Complete Forensic Documentation Workflow")
        print(f"📁 Project: {self.base_path}")
        print(f"⏰ Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
    def check_environment(self):
        """Check if environment is ready"""
        print("\n🔍 Environment Check:")
        
        # Check Python environment
        print(f"✅ Python: {sys.version.split()[0]}")
        
        # Check required directories
        required_dirs = [
            self.base_path / "tools" / "Scripts",
            self.base_path / "reports" / "Reports html",
            self.base_path / "evidence" / "Results" / "Questions"
        ]
        
        for dir_path in required_dirs:
            if dir_path.exists():
                print(f"✅ Directory: {dir_path.name}")
            else:
                print(f"❌ Missing: {dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {dir_path}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def step1_data_collection(self):
        """Step 1: Run data collection script"""
        print("\n" + "="*50)
        print("📝 STEP 1: Digital Evidence Data Collection")
        print("="*50)
        
        choice = input("\nDo you want to collect new evidence data? (y/n): ").lower().strip()
        
        if choice == 'y':
            print("\n🚀 Starting data collection...")
            print("📋 Please answer all questions completely")
            print("💾 Data will be saved to evidence/Results/Questions/questions.txt")
            print("-" * 50)
            
            # Run q_script.py
            try:
                result = subprocess.run([
                    sys.executable, 
                    str(self.scripts_path / "q_script.py")
                ], capture_output=False, text=True)
                
                if result.returncode == 0:
                    print("\n✅ Data collection completed successfully!")
                else:
                    print(f"\n❌ Data collection failed with code: {result.returncode}")
                    return False
                    
            except Exception as e:
                print(f"\n❌ Error running data collection: {str(e)}")
                return False
        else:
            # Check if questions.txt exists
            if self.questions_file.exists():
                print(f"\n✅ Using existing data: {self.questions_file}")
                print(f"📊 File size: {self.questions_file.stat().st_size} bytes")
                print(f"📅 Modified: {datetime.fromtimestamp(self.questions_file.stat().st_mtime)}")
            else:
                print(f"\n❌ No existing data found at: {self.questions_file}")
                print("Please run data collection first.")
                return False
                
        return True
    
    def step2_report_generation(self):
        """Step 2: Generate HTML reports"""
        print("\n" + "="*50)
        print("📄 STEP 2: HTML Report Generation")
        print("="*50)
        
        if not self.questions_file.exists():
            print("❌ No questions.txt file found. Please complete Step 1 first.")
            return False
            
        print(f"📖 Reading data from: {self.questions_file.name}")
        print(f"📁 Output directory: {self.output_dir}")
        print("\n🚀 Generating professional forensic reports...")
        
        try:
            # Run simple_html_generator.py
            result = subprocess.run([
                sys.executable,
                str(self.scripts_path / "simple_html_generator.py")
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ HTML report generation completed!")
                
                # List generated files
                html_files = list(self.output_dir.glob("FILLED_*.html"))
                if html_files:
                    print(f"\n📄 Generated {len(html_files)} HTML reports:")
                    for file in sorted(html_files):
                        size_kb = file.stat().st_size / 1024
                        print(f"  ✅ {file.name} ({size_kb:.1f} KB)")
                else:
                    print("\n⚠️ No HTML files found in output directory")
                    
            else:
                print(f"❌ Report generation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error generating reports: {str(e)}")
            return False
            
        return True
    
    def step3_pdf_instructions(self):
        """Step 3: Provide PDF conversion instructions"""
        print("\n" + "="*50)
        print("📄 STEP 3: PDF Conversion Instructions")
        print("="*50)
        
        html_files = list(self.output_dir.glob("FILLED_*.html"))
        
        if not html_files:
            print("❌ No HTML files found to convert")
            return False
            
        print("📋 Convert HTML reports to PDF using one of these methods:")
        print("\n🌐 METHOD 1: Browser Conversion (Recommended)")
        print("  1. Open each HTML file in Chrome/Edge/Firefox")
        print("  2. Press Ctrl+P (Print)")
        print("  3. Select 'Save as PDF'")
        print("  4. Choose destination and save")
        
        print("\n🔧 METHOD 2: Automated Conversion")
        print("  1. Install wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
        print("  2. Run batch conversion script (coming soon)")
        
        print("\n🌍 METHOD 3: Online Converters")
        print("  • https://html-pdf-converter.com/")
        print("  • https://www.ilovepdf.com/html-to-pdf")
        print("  • https://smallpdf.com/html-to-pdf")
        
        print(f"\n📁 HTML files location: {self.output_dir}")
        print("📄 File names:")
        for file in sorted(html_files):
            print(f"  • {file.name}")
            
        return True
    
    def cleanup_old_files(self):
        """Clean up old test files"""
        print("\n🧹 Cleaning up old test files...")
        
        old_files = list(self.output_dir.glob("FILLED_*.html"))
        if old_files:
            choice = input(f"\nFound {len(old_files)} old files. Delete them? (y/n): ").lower().strip()
            if choice == 'y':
                for file in old_files:
                    file.unlink()
                    print(f"🗑️ Deleted: {file.name}")
                print("✅ Cleanup completed")
            else:
                print("⏸️ Keeping existing files")
        else:
            print("✅ No old files to clean up")
    
    def run_complete_workflow(self):
        """Run the complete workflow"""
        self.print_banner()
        self.check_environment()
        
        # Optional cleanup
        self.cleanup_old_files()
        
        # Step 1: Data Collection
        if not self.step1_data_collection():
            print("\n❌ Workflow stopped at Step 1")
            return False
            
        # Step 2: Report Generation
        if not self.step2_report_generation():
            print("\n❌ Workflow stopped at Step 2")
            return False
            
        # Step 3: PDF Instructions
        if not self.step3_pdf_instructions():
            print("\n❌ Workflow stopped at Step 3")
            return False
            
        # Success summary
        print("\n" + "="*80)
        print("🎉 EDITH-Automater Workflow Completed Successfully!")
        print("="*80)
        print("✅ Data collected and validated")
        print("✅ Professional HTML reports generated")
        print("✅ PDF conversion instructions provided")
        print("\n📋 Next Steps:")
        print("1. Review the generated HTML reports")
        print("2. Convert to PDF using your preferred method")
        print("3. Store PDFs in secure evidence repository")
        print("\n📞 Support: Contact forensic team for assistance")
        print("="*80)
        
        return True


def main():
    """Main entry point"""
    try:
        workflow = EDITHWorkflow()
        success = workflow.run_complete_workflow()
        
        if success:
            input("\nPress Enter to exit...")
        else:
            input("\nWorkflow incomplete. Press Enter to exit...")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()