# Analysis Reporter Module

Professional forensic analysis report generator for EDITH-Automater

## Overview

The Analysis Reporter module aggregates outputs from all forensic analysis tools (Autopsy, Volatility, Bulk Extractor, ExifTool, HashDeep) and generates comprehensive HTML analysis reports with professional formatting.

## Features

✅ **Multi-Tool Integration**
- Parses Autopsy suspicious files and deleted file recovery
- Extracts Volatility memory analysis (processes, malware, connections)
- Aggregates Bulk Extractor patterns (emails, URLs, credit cards, phone numbers, SSN)
- Collects ExifTool metadata (GPS coordinates, document authors)
- Verifies HashDeep file integrity checks

✅ **Intelligent Analysis**
- Risk scoring system (0-100)
- Critical findings highlighting
- Automatic threat detection
- Evidence categorization by severity

✅ **Professional Reports**
- Clean, modern HTML design
- Auto-populated case information
- Executive summary with key metrics
- Detailed findings by tool
- Print-friendly layout
- Mobile-responsive design

✅ **Data Organization**
- Structured JSON outputs
- Machine-readable findings
- Timestamped reports
- Case metadata preservation

## Module Structure

```
analysis_reporter/
├── analyze_tool_outputs.py          # Parse forensic tool outputs
├── generate_analysis_report.py      # Create HTML reports
├── analysis_reporter_integration.py # Orchestrator integration
├── test_analysis_reporter.py        # Test suite
├── __init__.py                      # Package initialization
└── README.md                        # This file
```

## Classes & Functions

### AnalysisToolsParser

Parses outputs from forensic analysis tools.

```python
from analysis_reporter import AnalysisToolsParser

parser = AnalysisToolsParser("/path/to/case")
findings = parser.parse_all_outputs()

# Get critical findings
critical = parser.get_critical_findings()

# Get risk score (0-100)
risk_score = parser.get_risk_score()
```

**Methods:**
- `parse_autopsy_logs()` - Parse Autopsy analysis results
- `parse_volatility_output()` - Parse Volatility3 memory analysis
- `parse_bulk_extractor_output()` - Parse pattern extraction (emails, URLs, etc)
- `parse_exiftool_metadata()` - Parse metadata extraction results
- `parse_hashdeep_verification()` - Parse file integrity verification
- `parse_all_outputs()` - Parse all available outputs
- `get_critical_findings()` - Extract critical findings
- `get_risk_score()` - Calculate overall risk score

### AnalysisReportGenerator

Generates professional HTML analysis reports.

```python
from analysis_reporter import AnalysisReportGenerator

generator = AnalysisReportGenerator(
    case_name="Financial Investigation",
    case_id="CASE_2026_001",
    officer_name="Detective Smith"
)

html_report = generator.generate_report(findings)
```

**Methods:**
- `generate_report(findings)` - Generate complete HTML report

### AnalysisReporter

High-level class for orchestrator integration.

```python
from analysis_reporter import AnalysisReporter

reporter = AnalysisReporter("/path/to/case")

# Parse all outputs
reporter.parse_all_outputs()

# Generate report
report_path = reporter.generate_report(
    case_id="CASE_2026_001",
    case_name="Investigation Name",
    officer_name="Officer Name"
)

# Get summary
summary = reporter.get_summary()
```

### generate_analysis_report()

Standalone function for report generation.

```python
from analysis_reporter import generate_analysis_report

status, summary, report_path = generate_analysis_report(
    case_dir="/path/to/case",
    case_id="CASE_2026_001",
    case_name="Investigation Name",
    officer_name="Officer Name"
)

if status == "SUCCESS":
    print(f"Report generated: {report_path}")
    print(f"Risk score: {summary['risk_score']}")
```

## Generated Outputs

The module creates the following files in `Analysis_Results/` directory:

### 1. Analysis_Findings_Report.html
Professional HTML report with:
- Executive summary with metrics
- Risk scoring visualization
- Autopsy findings (suspicious/deleted files)
- Volatility analysis (processes, malware, connections)
- Pattern extraction (emails, URLs, cards, SSN)
- Metadata analysis (GPS, authors, dates)
- File integrity verification status

### 2. findings.json
Complete structured findings data:
```json
{
  "autopsy": {
    "suspicious_files": [...],
    "deleted_files": [...]
  },
  "volatility": {
    "processes": [...],
    "malware_detected": [...]
  },
  "bulk_extractor": {
    "emails": [...],
    "urls": [...]
  },
  ...
}
```

### 3. critical_findings.json
High-priority findings:
```json
{
  "critical_findings": [
    {
      "level": "CRITICAL",
      "category": "Payment Cards",
      "count": 3,
      "description": "Found 3 credit card numbers"
    }
  ],
  "risk_score": 85,
  "generated_time": "2026-02-06T15:45:22..."
}
```

### 4. analysis_summary.json
Quick reference summary:
```json
{
  "case_id": "CASE_2026_001",
  "case_name": "Financial Investigation",
  "officer_name": "Detective Smith",
  "risk_score": 85,
  "findings_summary": {
    "suspicious_files": 12,
    "malware_indicators": 2,
    "credit_cards_detected": 3,
    ...
  }
}
```

## Case Directory Structure

Expected directory structure for case:

```
Case_2026_001/
├── .case_info                      # Case metadata
├── Autopsy_Results/                # Autopsy output files
│   └── *.log, *.txt
├── Volatility_Results/             # Volatility3 output files
│   └── *.log, *.txt
├── BulkExtractor_Results/          # Bulk Extractor results
│   ├── email.txt
│   ├── url.txt
│   ├── ccn.txt
│   ├── phone.txt
│   └── ssn.txt
├── ExifTool_Results/               # ExifTool metadata
│   └── *.log, *.json, *.txt
├── HashDeep_Results/               # HashDeep verification
│   └── *.log, *.txt
└── Analysis_Results/               # Generated by this module ← NEW
    ├── Analysis_Findings_Report.html
    ├── findings.json
    ├── critical_findings.json
    └── analysis_summary.json
```

## Usage Examples

### Basic Usage

```python
from analysis_reporter import generate_analysis_report

# Generate report from case directory
status, summary, report_path = generate_analysis_report(
    case_dir="/cases/Case_2026_001",
    case_id="CASE_2026_001",
    case_name="Financial Fraud Investigation",
    officer_name="Detective John Smith"
)

if status == "SUCCESS":
    print(f"✓ Report generated: {report_path}")
    print(f"✓ Risk score: {summary['risk_score']}/100")
    print(f"✓ Critical findings: {summary['credit_cards_detected']} credit cards")
```

### Using AnalysisReporter Class

```python
from analysis_reporter import AnalysisReporter

# Initialize reporter
reporter = AnalysisReporter("/cases/Case_2026_001")

# Parse all tool outputs
if reporter.parse_all_outputs():
    # Generate HTML report
    report_path = reporter.generate_report(
        case_id="CASE_2026_001",
        case_name="Investigation",
        officer_name="Officer"
    )
    
    # Get summary statistics
    summary = reporter.get_summary()
    
    print(f"Suspicious files: {summary['suspicious_files']}")
    print(f"Malware indicators: {summary['malware_indicators']}")
    print(f"Risk score: {summary['risk_score']}")
```

### Custom Analysis

```python
from analysis_reporter import AnalysisToolsParser, AnalysisReportGenerator

# Parse outputs
parser = AnalysisToolsParser("/cases/Case_2026_001")
findings = parser.parse_all_outputs()

# Analyze specific category
credit_cards = parser.findings['bulk_extractor']['credit_cards']
emails = parser.findings['bulk_extractor']['emails']

# Get critical findings
critical = parser.get_critical_findings()
for finding in critical:
    if finding['level'] == 'CRITICAL':
        print(f"CRITICAL: {finding['description']}")

# Generate custom report
generator = AnalysisReportGenerator("My Case", "CASE_001", "Officer")
html = generator.generate_report(findings)
```

## Risk Scoring System

Risk scores are calculated based on:

| Finding Type | Points | Notes |
|---|---|---|
| Credit card number | 30 | Per card (capped at 3) |
| Malware indicator | 30 | Per indicator (capped at 3) |
| SSN | 30 | Per SSN (capped at 3) |
| Suspicious file | 15 | Up to 3 files |
| Modified file | 15 | Clear evidence tampering |
| Email extraction | 5 | Per 10 emails |
| URL extraction | 5 | Per URL category |

**Score Interpretation:**
- 75-100: **CRITICAL** - Serious potential fraud/crime
- 50-74: **HIGH** - Significant suspicious activity
- 25-49: **MEDIUM** - Notable findings present
- 0-24: **LOW** - Minimal suspicious activity

## Testing

Run the test suite:

```bash
python test_analysis_reporter.py
```

Expected output:
```
══════════════════════════════════════════════════════════════════════════════════════╗
█  ANALYSIS REPORTER TEST SUITE                                                        █
╚══════════════════════════════════════════════════════════════════════════════════════╝

TEST 1: Analysis Tools Parser
✓ Suspicious files detected: 2
✓ Deleted files recovered: 2
✓ Malware indicators: 2
✓ Emails extracted: 5
✓ URLs found: 5
✓ Credit cards detected: 3
✓ Critical findings: 1
✓ Risk score: 95/100

✅ TEST 1 PASSED

... (additional tests)

✅ ALL TESTS PASSED
```

## Integration with Orchestrator

To integrate with the orchestrator as a new workflow step:

```python
# In orchestrator.py, add to run_sequential_workflow():

from analysis_reporter import generate_analysis_report

# ... after all forensic tools complete ...

print("\n[STEP 7] Generating Analysis Report...")
status, summary, report_path = generate_analysis_report(
    case_dir=case_directory,
    case_id=case_id,
    case_name=case_name,
    officer_name=officer_name
)

if status == "SUCCESS":
    print(f"✓ Analysis report generated: {report_path}")
    print(f"✓ Risk score: {summary['risk_score']}/100")
else:
    print(f"⚠ Analysis report generation failed: {status}")
```

## Output Examples

### Executive Summary
Shows overall statistics and risk score:
- Total suspicious files: 12
- Malware indicators: 2
- Credit cards detected: 3
- Emails extracted: 234
- Risk Score: 85/100 (CRITICAL)

### Autopsy Analysis
Lists suspicious and recovered files with:
- File paths
- File types
- Detection source
- When accessible as table

### Volatility Section
Shows processes, malware, and network activity:
- Running processes with PIDs
- Detected malware/trojans
- Network connections to suspicious IPs

### Bulk Extractor Results
Presents extracted patterns:
- Email addresses (clickable)
- URLs visited
- Credit cards (masked for safety)
- Phone numbers
- SSNs (fully masked)

### Metadata Analysis
Shows ExifTool findings:
- GPS coordinates from images
- Document authors and dates
- File type distribution

### File Integrity Verification
Chain of custody status:
- Total files verified
- Valid files (hashes match)
- Modified files (potential tampering)
- Overall integrity status

## Dependencies

- Python 3.8+
- No external dependencies (uses standard library)
- Works with case directories from existing forensic tools

## Performance

- Parses tool outputs: < 2 seconds for typical case (50K files)
- Generates HTML report: < 1 second
- Total report generation: < 5 seconds

## Limitations

1. **Output Format Dependency**: Requires tool output in standard text/JSON format
2. **Incomplete Outputs**: Works with partial tool results (some tools may not have run)
3. **Large Datasets**: Email/URL lists limited to 100 samples per category for readability
4. **No Real-time Updates**: Generates static reports (re-run for updated results)

## Future Enhancements

- [ ] PDF export functionality
- [ ] Interactive timeline visualization
- [ ] Search functionality across findings
- [ ] Custom report templates
- [ ] Database backend for large cases
- [ ] Real-time tool output monitoring
- [ ] Machine learning-based anomaly detection
- [ ] Integration with SIEM systems

## Author

EDITH-Automater Development Team

## License

Proprietary - For Income Tax Investigation use only

---

**Generated**: Analysis Findings Report v1.0.0  
**Last Updated**: 2026-02-06
