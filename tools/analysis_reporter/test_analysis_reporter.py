"""
Analysis Reporter Test Suite
Tests for analysis report generation
"""

import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis_reporter.analyze_tool_outputs import AnalysisToolsParser
from analysis_reporter.generate_analysis_report import AnalysisReportGenerator
from analysis_reporter.analysis_reporter_integration import AnalysisReporter, generate_analysis_report


class SampleCaseGenerator:
    """Generate sample case with mock forensic tool outputs"""
    
    @staticmethod
    def create_sample_case(case_dir: str) -> None:
        """Create sample case directory structure with mock outputs"""
        case_path = Path(case_dir)
        case_path.mkdir(parents=True, exist_ok=True)
        
        # Create Autopsy results
        autopsy_dir = case_path / "Autopsy_Results"
        autopsy_dir.mkdir(exist_ok=True)
        
        autopsy_log = """
[ALERT] SUSPICIOUS FILE DETECTED
Path: C:\\Users\\Suspect\\Documents\\Financial_Records_Hidden.xlsx
Type: Spreadsheet (Hidden)
Modified: 2026-02-01 10:32:15

[ALERT] SUSPICIOUS FILE DETECTED
Path: C:\\Users\\Suspect\\AppData\\Roaming\\suspicious_executable.exe
Type: Executable
Modified: 2026-01-15 14:22:30

[RECOVERED] DELETED FILE
Path: C:\\Users\\Suspect\\Desktop\\Invoice_Fakes.docx
Size: 1.2 MB
Recovered from: Unallocated clusters

[RECOVERED] DELETED FILE
Path: C:\\Users\\Suspect\\Downloads\\Bank_Transfer_Log.xlsx
Size: 512 KB
Recovered from: Unallocated clusters
"""
        
        with open(autopsy_dir / "autopsy_analysis.log", 'w') as f:
            f.write(autopsy_log)
        
        # Create Volatility results
        volatility_dir = case_path / "Volatility_Results"
        volatility_dir.mkdir(exist_ok=True)
        
        volatility_log = """
PROCESS LISTING
===============
PID 2345 - svchost.exe
PID 3456 - cryptominer.bin [MALWARE DETECTED] Unusual network activity detected
PID 4567 - ransomware.exe [TROJAN] Known ransomware signature matched
PID 5678 - explorer.exe

NETWORK CONNECTIONS
===================
Connection: 192.168.1.100:8080 - malicious_server.ru
Connection: 10.0.0.50:443 - command_and_control.onion
"""
        
        with open(volatility_dir / "volatility_analysis.log", 'w') as f:
            f.write(volatility_log)
        
        # Create Bulk Extractor results
        bulk_dir = case_path / "BulkExtractor_Results"
        bulk_dir.mkdir(exist_ok=True)
        
        # Email file
        emails = """john.doe@gmail.com
suspect@company.com
admin@bank.com
fraudulent@shell_corp.com
contact@darkweb.ru
"""
        with open(bulk_dir / "email.txt", 'w') as f:
            f.write(emails)
        
        # URL file
        urls = """http://www.google.com
http://www.facebook.com
https://www.bankofamerica.com
http://malicious_site.ru/banking
https://dark_web.onion/marketplace
"""
        with open(bulk_dir / "url.txt", 'w') as f:
            f.write(urls)
        
        # Credit card file (masked)
        ccn = """4532123456789123
5412987654321098
3714234567890123
"""
        with open(bulk_dir / "ccn.txt", 'w') as f:
            f.write(ccn)
        
        # Phone file
        phones = """+1-234-567-8901
+1-555-123-4567
+44-20-7946-0958
"""
        with open(bulk_dir / "phone.txt", 'w') as f:
            f.write(phones)
        
        # SSN file
        ssn = """123-45-6789
987-65-4321
"""
        with open(bulk_dir / "ssn.txt", 'w') as f:
            f.write(ssn)
        
        # Create ExifTool results
        exif_dir = case_path / "ExifTool_Results"
        exif_dir.mkdir(exist_ok=True)
        
        exif_log = """
FILE: photo_1.jpg
FileType: JPEG
GPSLatitude: 40.7128
GPSLongitude: -74.0060
CreateDate: 2026-01-15 10:30:45

FILE: document_1.docx
FileType: DOCX
Author: John Smith
ModifyDate: 2026-02-01 14:22:10

FILE: finance_2025.xlsx
FileType: XLSX
Author: Suspect Individual
ModifyDate: 2026-02-05 16:45:30
"""
        
        with open(exif_dir / "exif_metadata.log", 'w') as f:
            f.write(exif_log)
        
        # Create HashDeep results
        hash_dir = case_path / "HashDeep_Results"
        hash_dir.mkdir(exist_ok=True)
        
        hash_log = """
FILES VERIFIED: 50000
VALID (Hashes Match): 49977
MODIFIED FILES:
  C:\\Users\\Suspect\\Documents\\Report_Final.xlsx - HASH MISMATCH
  C:\\Users\\Suspect\\Downloads\\data.txt - HASH MISMATCH
  
CHAIN OF CUSTODY: VERIFIED
"""
        
        with open(hash_dir / "hashdeep_verification.log", 'w') as f:
            f.write(hash_log)


def test_parser():
    """TEST 1: Parser Module"""
    print("\n" + "="*60)
    print("TEST 1: Analysis Tools Parser")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample case
        SampleCaseGenerator.create_sample_case(tmpdir)
        
        # Parse outputs
        parser = AnalysisToolsParser(tmpdir)
        findings = parser.parse_all_outputs()
        
        # Verify results
        assert findings["autopsy"]["suspicious_files"], "Should find suspicious files"
        assert findings["autopsy"]["deleted_files"], "Should find deleted files"
        assert findings["volatility"]["malware_detected"], "Should detect malware"
        assert findings["bulk_extractor"]["total_emails"] > 0, "Should extract emails"
        assert findings["bulk_extractor"]["total_urls"] > 0, "Should extract URLs"
        assert findings["bulk_extractor"]["total_cards"] > 0, "Should detect credit cards"
        # Note: ExifTool results are optional as images may not always be present
        
        # Get critical findings
        critical = parser.get_critical_findings()
        risk_score = parser.get_risk_score()
        
        print(f"✓ Suspicious files detected: {len(findings['autopsy']['suspicious_files'])}")
        print(f"✓ Deleted files recovered: {len(findings['autopsy']['deleted_files'])}")
        print(f"✓ Malware indicators: {len(findings['volatility']['malware_detected'])}")
        print(f"✓ Emails extracted: {findings['bulk_extractor']['total_emails']}")
        print(f"✓ URLs found: {findings['bulk_extractor']['total_urls']}")
        print(f"✓ Credit cards detected: {findings['bulk_extractor']['total_cards']}")
        print(f"✓ Critical findings: {len(critical)}")
        print(f"✓ Risk score: {risk_score}/100")
        print("\n✅ TEST 1 PASSED")


def test_report_generator():
    """TEST 2: Report Generator"""
    print("\n" + "="*60)
    print("TEST 2: Report Generator")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample case
        SampleCaseGenerator.create_sample_case(tmpdir)
        
        # Parse and generate report
        parser = AnalysisToolsParser(tmpdir)
        findings = parser.parse_all_outputs()
        
        generator = AnalysisReportGenerator(
            case_name="Test Case - Financial Fraud",
            case_id="CASE_2026_001",
            officer_name="Detective Smith"
        )
        
        html = generator.generate_report(findings)
        
        # Verify HTML content
        assert "<!DOCTYPE html>" in html, "Should contain HTML structure"
        assert "ANALYSIS FINDINGS REPORT" in html, "Should contain title"
        assert "Test Case - Financial Fraud" in html, "Should contain case name"
        assert "CASE_2026_001" in html, "Should contain case ID"
        assert "Detective Smith" in html, "Should contain officer name"
        assert "Autopsy" in html, "Should contain Autopsy section"
        assert "Volatility" in html, "Should contain Volatility section"
        assert "Bulk Extractor" in html, "Should contain Bulk Extractor section"
        assert "ExifTool" in html, "Should contain ExifTool section"
        assert "HashDeep" in html, "Should contain HashDeep section"
        
        # Save report for inspection
        report_path = Path(tmpdir) / "test_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✓ HTML report generated: {len(html)} characters")
        print(f"✓ Report contains case information")
        print(f"✓ Report contains all analysis sections")
        print(f"✓ Report saved to: {report_path}")
        print("\n✅ TEST 2 PASSED")


def test_integration():
    """TEST 3: Integration Function"""
    print("\n" + "="*60)
    print("TEST 3: Integration Function")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample case
        SampleCaseGenerator.create_sample_case(tmpdir)
        
        # Generate analysis report
        status, summary, report_path = generate_analysis_report(
            case_dir=tmpdir,
            case_id="CASE_2026_001",
            case_name="Financial Fraud Investigation",
            officer_name="Detective Smith"
        )
        
        # Verify results
        assert status == "SUCCESS", f"Should return SUCCESS, got {status}"
        assert report_path, "Should return report path"
        assert Path(report_path).exists(), "Report file should exist"
        
        # Check generated files
        analysis_dir = Path(tmpdir) / "Analysis_Results"
        assert analysis_dir.exists(), "Analysis_Results directory should exist"
        assert (analysis_dir / "Analysis_Findings_Report.html").exists()
        assert (analysis_dir / "findings.json").exists()
        assert (analysis_dir / "critical_findings.json").exists()
        assert (analysis_dir / "analysis_summary.json").exists()
        
        # Check summary content
        assert summary["suspicious_files"] > 0
        assert summary["malware_indicators"] > 0
        assert summary["credit_cards_detected"] > 0
        
        print(f"✓ Report status: {status}")
        print(f"✓ Report generated at: {report_path}")
        print(f"✓ Suspicious files: {summary['suspicious_files']}")
        print(f"✓ Malware indicators: {summary['malware_indicators']}")
        print(f"✓ Credit cards detected: {summary['credit_cards_detected']}")
        print(f"✓ Risk score: {summary.get('risk_score', 'N/A')}")
        print("\n✅ TEST 3 PASSED")


def test_analysis_reporter_class():
    """TEST 4: AnalysisReporter Class"""
    print("\n" + "="*60)
    print("TEST 4: AnalysisReporter Class")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample case
        SampleCaseGenerator.create_sample_case(tmpdir)
        
        # Use AnalysisReporter class
        reporter = AnalysisReporter(tmpdir)
        
        # Parse outputs
        assert reporter.parse_all_outputs(), "Should parse successfully"
        
        # Generate report
        report_path = reporter.generate_report(
            case_id="CASE_2026_001",
            case_name="Test Case",
            officer_name="Officer Name"
        )
        
        assert report_path, "Should return report path"
        assert Path(report_path).exists(), "Report should exist"
        
        # Get summary
        summary = reporter.get_summary()
        
        assert summary["suspicious_files"] > 0
        assert summary["risk_score"] > 0
        assert summary["critical_findings"] >= 0
        
        print(f"✓ Reporter initialized: {tmpdir}")
        print(f"✓ Outputs parsed successfully")
        print(f"✓ Report generated: {report_path}")
        print(f"✓ Summary - Suspicious files: {summary['suspicious_files']}")
        print(f"✓ Summary - Risk score: {summary['risk_score']}")
        print(f"✓ Summary - Critical findings: {summary['critical_findings']}")
        print("\n✅ TEST 4 PASSED")


def run_all_tests():
    """Run all tests"""
    print("\n" + "█"*60)
    print("█  ANALYSIS REPORTER TEST SUITE")
    print("█"*60)
    
    try:
        test_parser()
        test_report_generator()
        test_integration()
        test_analysis_reporter_class()
        
        print("\n" + "█"*60)
        print("█  ALL TESTS PASSED ✅")
        print("█"*60 + "\n")
        
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
