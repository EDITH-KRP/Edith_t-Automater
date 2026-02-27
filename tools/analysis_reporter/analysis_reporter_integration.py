"""
Analysis Reporter Integration
Orchestrator integration for analysis report generation
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Any

from .analyze_tool_outputs import AnalysisToolsParser
from .generate_analysis_report import AnalysisReportGenerator


def generate_analysis_report(
    case_dir: str,
    case_id: str = "",
    case_name: str = "",
    officer_name: str = ""
) -> Tuple[str, Dict[str, Any], str]:
    """
    Generate analysis report from forensic tool outputs
    
    Args:
        case_dir: Path to case directory
        case_id: Case identifier
        case_name: Name of case
        officer_name: Examining officer name
        
    Returns:
        Tuple of (status, findings_dict, report_path)
    """
    try:
        case_path = Path(case_dir)
        
        # Parse all tool outputs
        parser = AnalysisToolsParser(str(case_path))
        findings = parser.parse_all_outputs()
        
        # Get critical findings and risk score
        critical_findings = parser.get_critical_findings()
        risk_score = parser.get_risk_score()
        
        # Generate HTML report
        generator = AnalysisReportGenerator(case_name, case_id, officer_name)
        html_report = generator.generate_report(findings)
        
        # Create Analysis_Results directory
        analysis_dir = case_path / "Analysis_Results"
        analysis_dir.mkdir(exist_ok=True)
        
        # Save HTML report
        report_path = analysis_dir / "Analysis_Findings_Report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Save findings as JSON
        findings_json_path = analysis_dir / "findings.json"
        with open(findings_json_path, 'w', encoding='utf-8') as f:
            json.dump(findings, f, indent=2, default=str)
        
        # Save critical findings
        critical_path = analysis_dir / "critical_findings.json"
        with open(critical_path, 'w', encoding='utf-8') as f:
            json.dump({
                "critical_findings": critical_findings,
                "risk_score": risk_score,
                "generated_time": datetime.now().isoformat()
            }, f, indent=2)
        
        # Save summary
        summary_path = analysis_dir / "analysis_summary.json"
        summary = {
            "case_id": case_id,
            "case_name": case_name,
            "officer_name": officer_name,
            "generated_time": datetime.now().isoformat(),
            "risk_score": risk_score,
            "findings_summary": {
                "suspicious_files": len(findings["autopsy"]["suspicious_files"]),
                "deleted_files_recovered": len(findings["autopsy"]["deleted_files"]),
                "malware_indicators": len(findings["volatility"]["malware_detected"]),
                "emails_extracted": findings["bulk_extractor"]["total_emails"],
                "urls_found": findings["bulk_extractor"]["total_urls"],
                "credit_cards_detected": findings["bulk_extractor"]["total_cards"],
                "ssn_detected": len(findings["bulk_extractor"]["ssn"]),
                "images_found": findings["exiftool"]["images"]["count"],
                "documents_found": findings["exiftool"]["documents"]["count"],
                "total_files_verified": findings["hashdeep"]["total_files_verified"],
                "files_modified": len(findings["hashdeep"]["files_modified"]),
                "integrity_status": findings["hashdeep"]["integrity_status"]
            }
        }
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        return (
            "SUCCESS",
            summary["findings_summary"],
            str(report_path)
        )
        
    except Exception as e:
        return (
            f"ERROR: {str(e)}",
            {},
            ""
        )


class AnalysisReporter:
    """Analysis reporter for orchestrator integration"""
    
    def __init__(self, case_dir: str):
        """
        Initialize analysis reporter
        
        Args:
            case_dir: Path to case directory
        """
        self.case_dir = Path(case_dir)
        self.parser = AnalysisToolsParser(str(self.case_dir))
        self.generator = None
        self.findings = {}
        self.critical_findings = []
        self.risk_score = 0
    
    def parse_all_outputs(self) -> bool:
        """
        Parse all forensic tool outputs
        
        Returns:
            True if successful
        """
        try:
            self.findings = self.parser.parse_all_outputs()
            self.critical_findings = self.parser.get_critical_findings()
            self.risk_score = self.parser.get_risk_score()
            return True
        except Exception as e:
            return False
    
    def generate_report(self, case_id: str = "", case_name: str = "", officer_name: str = "") -> str:
        """
        Generate analysis report
        
        Args:
            case_id: Case identifier
            case_name: Case name
            officer_name: Officer name
            
        Returns:
            Path to generated report
        """
        try:
            self.generator = AnalysisReportGenerator(case_name, case_id, officer_name)
            html = self.generator.generate_report(self.findings)
            
            # Save report
            analysis_dir = self.case_dir / "Analysis_Results"
            analysis_dir.mkdir(exist_ok=True)
            
            report_path = analysis_dir / "Analysis_Findings_Report.html"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return str(report_path)
        except Exception as e:
            return ""
    
    def get_summary(self) -> Dict[str, Any]:
        """Get findings summary"""
        return {
            "suspicious_files": len(self.findings.get("autopsy", {}).get("suspicious_files", [])),
            "deleted_files": len(self.findings.get("autopsy", {}).get("deleted_files", [])),
            "malware_indicators": len(self.findings.get("volatility", {}).get("malware_detected", [])),
            "emails": self.findings.get("bulk_extractor", {}).get("total_emails", 0),
            "urls": self.findings.get("bulk_extractor", {}).get("total_urls", 0),
            "credit_cards": self.findings.get("bulk_extractor", {}).get("total_cards", 0),
            "ssn": len(self.findings.get("bulk_extractor", {}).get("ssn", [])),
            "risk_score": self.risk_score,
            "critical_findings": len(self.critical_findings)
        }
