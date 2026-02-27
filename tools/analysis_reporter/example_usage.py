"""
Analysis Reporter - Usage Examples
Demonstrates how to use the Analysis Reporter module
"""

import sys
from pathlib import Path

# Example 1: Simple Report Generation
def example_1_simple_report():
    """Generate a basic analysis report from a case directory"""
    from analysis_reporter import generate_analysis_report
    
    case_directory = "/path/to/case/Case_2026_001"
    
    status, summary, report_path = generate_analysis_report(
        case_dir=case_directory,
        case_id="CASE_2026_001",
        case_name="Financial Fraud Investigation",
        officer_name="Detective Smith"
    )
    
    if status == "SUCCESS":
        print(f"✓ Report generated successfully")
        print(f"  Location: {report_path}")
        print(f"  Risk Score: {summary.get('risk_score', 'N/A')}/100")
        print(f"  Suspicious Files: {summary.get('suspicious_files', 0)}")
        print(f"  Credit Cards Detected: {summary.get('credit_cards_detected', 0)}")
    else:
        print(f"✗ Error: {status}")


# Example 2: Using AnalysisReporter Class
def example_2_reporter_class():
    """Use the AnalysisReporter class for more control"""
    from analysis_reporter import AnalysisReporter
    
    case_directory = "/path/to/case/Case_2026_001"
    
    # Initialize reporter
    reporter = AnalysisReporter(case_directory)
    
    # Parse all forensic tool outputs
    if reporter.parse_all_outputs():
        print("✓ Tool outputs parsed successfully")
        
        # Generate HTML report
        report_path = reporter.generate_report(
            case_id="CASE_2026_001",
            case_name="Financial Fraud Investigation",
            officer_name="Detective Smith"
        )
        
        if report_path:
            print(f"✓ Report generated: {report_path}")
            
            # Get summary statistics
            summary = reporter.get_summary()
            print(f"\nFindings Summary:")
            print(f"  Suspicious Files: {summary['suspicious_files']}")
            print(f"  Deleted Files Recovered: {summary['deleted_files']}")
            print(f"  Malware Indicators: {summary['malware_indicators']}")
            print(f"  Total Emails: {summary['emails']}")
            print(f"  Total URLs: {summary['urls']}")
            print(f"  Credit Cards: {summary['credit_cards']}")
            print(f"  Risk Score: {summary['risk_score']}/100")
    else:
        print("✗ Failed to parse tool outputs")


# Example 3: Custom Analysis
def example_3_custom_analysis():
    """Custom analysis of specific findings"""
    from analysis_reporter import AnalysisToolsParser
    
    case_directory = "/path/to/case/Case_2026_001"
    
    # Parse outputs
    parser = AnalysisToolsParser(case_directory)
    findings = parser.parse_all_outputs()
    
    # Get critical findings
    critical = parser.get_critical_findings()
    
    print("CRITICAL FINDINGS:")
    for finding in critical:
        print(f"  [{finding['level']}] {finding['description']}")
    
    # Analyze specific categories
    print(f"\nEMAILS FOUND: {findings['bulk_extractor']['total_emails']}")
    if findings['bulk_extractor']['emails']:
        print("  Sample emails:")
        for email in findings['bulk_extractor']['emails'][:5]:
            print(f"    - {email}")
    
    print(f"\nCREDIT CARDS DETECTED: {findings['bulk_extractor']['total_cards']}")
    if findings['bulk_extractor']['credit_cards']:
        print("  Last 4 digits (privacy protected):")
        for card in findings['bulk_extractor']['credit_cards'][:5]:
            print(f"    - {card['masked']}")
    
    # Risk assessment
    risk_score = parser.get_risk_score()
    if risk_score >= 75:
        risk_level = "CRITICAL"
    elif risk_score >= 50:
        risk_level = "HIGH"
    elif risk_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    
    print(f"\nOVERALL RISK: {risk_level} ({risk_score}/100)")


# Example 4: Report for Multiple Cases
def example_4_batch_reporting():
    """Generate reports for multiple cases"""
    from analysis_reporter import AnalysisReporter
    from datetime import datetime
    
    cases = [
        {
            "path": "/path/to/cases/Case_2026_001",
            "id": "CASE_2026_001",
            "name": "Financial Fraud - Company A",
            "officer": "Detective Smith"
        },
        {
            "path": "/path/to/cases/Case_2026_002",
            "id": "CASE_2026_002",
            "name": "Tax Evasion - Individual",
            "officer": "Detective Jones"
        },
        {
            "path": "/path/to/cases/Case_2026_003",
            "id": "CASE_2026_003",
            "name": "Money Laundering - Business",
            "officer": "Detective Lee"
        }
    ]
    
    print("Processing Multiple Cases...")
    print("=" * 60)
    
    results = []
    
    for case in cases:
        try:
            reporter = AnalysisReporter(case['path'])
            
            if reporter.parse_all_outputs():
                report_path = reporter.generate_report(
                    case_id=case['id'],
                    case_name=case['name'],
                    officer_name=case['officer']
                )
                
                summary = reporter.get_summary()
                
                results.append({
                    "case_id": case['id'],
                    "case_name": case['name'],
                    "status": "SUCCESS",
                    "report_path": report_path,
                    "risk_score": summary['risk_score'],
                    "critical_findings": summary['critical_findings']
                })
                
                print(f"\n✓ {case['id']}")
                print(f"  Risk Score: {summary['risk_score']}/100")
                print(f"  Critical Findings: {summary['critical_findings']}")
            else:
                results.append({
                    "case_id": case['id'],
                    "status": "PARSE_ERROR"
                })
                print(f"\n✗ {case['id']} - Failed to parse outputs")
                
        except Exception as e:
            results.append({
                "case_id": case['id'],
                "status": f"ERROR: {str(e)}"
            })
            print(f"\n✗ {case['id']} - {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    
    successful = len([r for r in results if r.get('status') == 'SUCCESS'])
    failed = len([r for r in results if r.get('status') != 'SUCCESS'])
    
    print(f"Total Cases: {len(cases)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if successful > 0:
        print("\nHigh Risk Cases:")
        for result in results:
            if result.get('status') == 'SUCCESS' and result.get('risk_score', 0) >= 75:
                print(f"  {result['case_id']}: Risk Score {result['risk_score']}/100")


# Example 5: Exporting to JSON
def example_5_json_export():
    """Export findings to JSON for external processing"""
    import json
    from analysis_reporter import AnalysisToolsParser
    
    case_directory = "/path/to/case/Case_2026_001"
    
    # Parse outputs
    parser = AnalysisToolsParser(case_directory)
    findings = parser.parse_all_outputs()
    
    # Export to JSON file
    output_file = Path(case_directory) / "findings_export.json"
    
    with open(output_file, 'w') as f:
        json.dump(findings, f, indent=2, default=str)
    
    print(f"✓ Findings exported to: {output_file}")
    
    # Also export summary
    summary_data = {
        "case_id": "CASE_2026_001",
        "generated_at": str(datetime.now()),
        "risk_score": parser.get_risk_score(),
        "critical_findings": parser.get_critical_findings(),
        "statistics": {
            "suspicious_files": len(findings['autopsy']['suspicious_files']),
            "deleted_files": len(findings['autopsy']['deleted_files']),
            "malware_indicators": len(findings['volatility']['malware_detected']),
            "emails": findings['bulk_extractor']['total_emails'],
            "urls": findings['bulk_extractor']['total_urls'],
            "credit_cards": findings['bulk_extractor']['total_cards'],
        }
    }
    
    summary_file = Path(case_directory) / "findings_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"✓ Summary exported to: {summary_file}")


# Example 6: Integration with Case Processing Pipeline
def example_6_pipeline_integration():
    """Show how to integrate with orchestrator workflow"""
    from analysis_reporter import generate_analysis_report
    
    def process_forensic_case(case_info):
        """Process complete forensic case"""
        case_dir = case_info['directory']
        case_id = case_info['case_id']
        case_name = case_info['case_name']
        officer = case_info['officer_name']
        
        print(f"\n[STEP 1] Processing Evidence Collection... ✓")
        print(f"[STEP 2] FTK Image Analysis... ✓")
        print(f"[STEP 3] Autopsy Disk Analysis... ✓")
        print(f"[STEP 4] Volatility Memory Analysis... ✓")
        print(f"[STEP 5] Pattern Extraction (Bulk Extractor)... ✓")
        
        # NEW: Generate analysis report
        print(f"[STEP 6] Generating Analysis Report...")
        
        status, summary, report_path = generate_analysis_report(
            case_dir=case_dir,
            case_id=case_id,
            case_name=case_name,
            officer_name=officer
        )
        
        if status == "SUCCESS":
            print(f"  ✓ Analysis report generated")
            print(f"  ✓ Location: {report_path}")
            print(f"  ✓ Risk Level: ", end="")
            
            risk = summary.get('risk_score', 0)
            if risk >= 75:
                print("CRITICAL 🔴")
            elif risk >= 50:
                print("HIGH 🟠")
            elif risk >= 25:
                print("MEDIUM 🟡")
            else:
                print("LOW 🟢")
        else:
            print(f"  ✗ Error: {status}")
        
        print(f"[STEP 7] Final Report Assembly... ✓")
        print(f"\n📋 CASE PROCESSING COMPLETE")
        print(f"   Case ID: {case_id}")
        print(f"   Status: Ready for Review")
        print(f"   Report: {report_path}")
        
        return report_path
    
    # Sample case information
    case_info = {
        "directory": "/cases/Case_2026_001",
        "case_id": "CASE_2026_001",
        "case_name": "Financial Fraud Investigation",
        "officer_name": "Detective Smith"
    }
    
    # Process case
    report_path = process_forensic_case(case_info)


# Example 7: Filtering Critical Findings
def example_7_critical_findings():
    """Focus on critical findings only"""
    from analysis_reporter import AnalysisToolsParser
    
    case_directory = "/path/to/case/Case_2026_001"
    
    parser = AnalysisToolsParser(case_directory)
    findings = parser.parse_all_outputs()
    
    # Get critical findings
    critical = parser.get_critical_findings()
    
    if not critical:
        print("No critical findings detected")
        return
    
    print("CRITICAL FINDINGS REQUIRING IMMEDIATE ATTENTION:")
    print("=" * 60)
    
    for i, finding in enumerate(critical, 1):
        print(f"\n{i}. {finding['category']}")
        print(f"   Level: {finding['level']}")
        print(f"   Count: {finding['count']}")
        print(f"   Details: {finding['description']}")
        
        # Provide recommendations
        if finding['category'] == 'Payment Cards':
            print(f"   Action: Monitor for unauthorized transactions")
            print(f"           Notify financial institutions")
            print(f"           Report to fraud department")
        
        elif finding['category'] == 'Malware Detection':
            print(f"   Action: Quarantine affected systems")
            print(f"           Check for data exfiltration")
            print(f"           Scan all connected devices")
        
        elif finding['category'] == 'PII Exposure':
            print(f"   Action: Notify affected individuals")
            print(f"           Monitor for identity theft")
            print(f"           Document exposure extent")
        
        elif finding['category'] == 'File Integrity':
            print(f"   Action: Review chain of custody")
            print(f"           Verify evidence authenticity")
            print(f"           Flag potential tampering")


if __name__ == "__main__":
    print("=" * 70)
    print("ANALYSIS REPORTER - USAGE EXAMPLES")
    print("=" * 70)
    print("\nThis file demonstrates how to use the Analysis Reporter module")
    print("in different scenarios.\n")
    print("Available examples:")
    print("  1. example_1_simple_report() - Basic report generation")
    print("  2. example_2_reporter_class() - Using AnalysisReporter class")
    print("  3. example_3_custom_analysis() - Custom analysis of findings")
    print("  4. example_4_batch_reporting() - Multiple cases processing")
    print("  5. example_5_json_export() - Export findings to JSON")
    print("  6. example_6_pipeline_integration() - Integration with workflow")
    print("  7. example_7_critical_findings() - Filter critical findings")
    print("\nNote: Update paths before running examples\n")
