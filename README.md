# EDITH-Automater
## **E**vidence **D**igital **I**nvestigation **T**echnical **H**arness

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)]()

> One command runs five forensic tools, verifies evidence integrity, correlates findings into a single interactive timeline, and generates court-ready PDF reports.

---

## Quick Start (2 commands)

```powershell
# 1. Install dependencies (once)
pip install -r tools\requirements.txt

# 2. Run the full pipeline on an E01 disk image
.\run_pipeline.bat "C:\path\to\evidence.E01"
```

When the pipeline finishes, your browser opens automatically to the **Case Dashboard**.

---

## What it does

```
evidence.E01
    │
    ├─► HashDeep    — MD5 + SHA1 + SHA256 hash of the entire image (baseline)
    ├─► ExifTool    — Reads EWF container headers (case no., examiner, acq. date)
    ├─► Autopsy     — File system analysis via SleuthKit (fls, fsstat, mmls)
    ├─► BulkExtractor — Carves emails, URLs, IPs, phones from raw sectors
    ├─► HashDeep    — Re-hashes image, compares to baseline (PASS / FAIL)
    │
    └─► Timeline Correlator
            ↓
        case_dashboard.html   ← opens automatically
        Timeline/investigation_timeline.html
        Reports pdf/*.pdf     ← Chain of Custody, Evidence Form, Job Form
```

### Key differentiator — Cross-Tool Timeline

Events from all five tools are merged, de-duplicated, and sorted chronologically into a single HTML timeline with:

- **Filter by tool** (Autopsy / BulkExtractor / ExifTool / HashDeep / Volatility)
- **Filter by severity** (CRITICAL / HIGH / MEDIUM / LOW / INFO)
- **Date range picker** — zoom to a specific window
- **Keyword search** — instant full-text filter across all events
- **Expand All / Collapse All / Export CSV / Print to PDF**

---

## Integrity & accuracy proof

Every pipeline run produces:

```
HashDeep_output/verification/integrity_verification.txt
────────────────────────────────────────────────────────
MD5    match: PASS
SHA1   match: PASS
SHA256 match: PASS

OVERALL: INTEGRITY MAINTAINED
```

The same three hashes appear in the auto-generated Chain of Custody PDF — no manual transcription, no opportunity for error.

---

## Case Dashboard

`Results/CASE_YYYYMMDD_HHMMSS/case_dashboard.html`

- Large green ✓ **INTEGRITY MAINTAINED** banner (or red ✗ if hashes differ)
- Per-tool event counts with ACTIVE / SKIPPED / NO DATA badges
- EWF container metadata (case number, examiner, subject, acquisition date)
- BulkExtractor artifact breakdown (emails, URLs, phones, base16 hashes)
- Top findings table (MEDIUM / HIGH / CRITICAL events)
- One-click links to the timeline and all PDFs

---

## Memory analysis (optional)

```powershell
.\run_pipeline.bat "evidence\disk.E01" "evidence\memory.vmem"
```

Pass any `.mem / .vmem / .dmp / .raw` file as the second argument. Without one, Volatility records a clear **SKIPPED** status in the dashboard and timeline rather than silently producing an empty folder.

---

## Project structure

```
EDITH-Automater/
├── run_pipeline.bat            ← start here
├── orchestrator/
│   └── orchestrator.py         ← main engine
├── tools/
│   ├── autopsy/                ← SleuthKit (mmls, fls, fsstat, tsk_recover)
│   ├── bulk-extractor/         ← email, URL, IP, phone carving
│   ├── exiftool/bin/           ← ExifTool binary
│   ├── hashdeep/               ← hash + verify
│   ├── volatility/             ← memory analysis (optional)
│   ├── timeline/
│   │   └── timeline_correlator.py  ← cross-tool event merge
│   ├── Scripts/
│   │   ├── script_3.py         ← forensic workflow
│   │   └── report_gen.py       ← PDF generation
│   └── requirements.txt
├── evidence/                   ← place .E01 / .vmem files here
├── Results/                    ← all case output lands here
│   └── CASE_YYYYMMDD_HHMMSS/
│       ├── case_dashboard.html         ← START HERE after pipeline
│       ├── Timeline/
│       │   └── investigation_timeline.html
│       ├── Reports pdf/                ← Chain of Custody, Evidence Form…
│       ├── HashDeep_output/
│       │   └── verification/integrity_verification.txt
│       ├── Autopsy_output/
│       ├── BulkExtractor_output/
│       └── ExifTool_output/
└── reports/Reports html/       ← PDF/HTML templates
```

---

## System requirements

| | Minimum | Recommended |
|---|---|---|
| OS | Windows 10 64-bit | Windows 11 |
| Python | 3.8+ | 3.11+ |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB free | 100 GB SSD |

---

## Legal

For legitimate digital forensics, incident response, and educational use only. Ensure proper authorisation before analysing any evidence. Follow chain-of-custody procedures and local regulations.


[![Version](https://img.shields.io/badge/Version-2.0-blue.svg)](https://github.com/adhi982/Edith_t-Automater)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)]()
[![License](https://img.shields.io/badge/License-Educational%20Use-orange.svg)]()

![Workflow](Old-workflow.png)

> **A comprehensive digital forensics automation framework that streamlines the entire digital investigation process from evidence acquisition to professional report generation.**

---

## **Key Features**

### **Multiple Deployment Options**
- **USB Portable**: Complete forensic workstation on a USB drive
- **Single EXE**: Portable executable with bundled Python runtime
- **Source Code**: Full development environment
- **Interactive CLI**: User-friendly command-line interface

### **Integrated Forensic Tools**
- **HashDeep**: File integrity verification and hash analysis
- **Autopsy**: Comprehensive disk analysis and timeline generation
- **Volatility**: Advanced memory forensics and analysis
- **ExifTool**: Metadata extraction from files and images
- **Bulk Extractor**: Pattern extraction (emails, URLs, credit cards, etc.)
- **Report Generator**: Professional PDF and HTML report creation

### **Advanced Case Management**
- **Interactive Q&A**: Guided evidence collection with forensic questionnaires
- **Automated Workflows**: Sequential tool execution with progress tracking
- **Case Organization**: Structured directory layout for multi-case management
- **Chain of Custody**: Built-in evidence documentation and tracking

### **Professional Reporting**
- **HTML Reports**: Interactive web-based analysis results
- **PDF Generation**: Professional forensic documentation
- **Evidence Forms**: Digital evidence collection forms
- **Timeline Analysis**: Chronological event reconstruction

---

## **Quick Start Guide**

### **Option 1: USB Portable (Recommended)**
```powershell
# Create complete USB forensic workstation
python create_usb_portable.py

# Launch from USB (works on any Windows PC)
F:\EDITH-USB-Portable\EDITH-USB.exe
```

### **Option 2: Single EXE Build**
```powershell
# Install dependencies
pip install -r tools\requirements.txt

# Build portable EXE
.\build_exe.bat

# Run the EXE
.\dist\EDITH-Automater\EDITH-Automater.exe
```

### **Option 3: Source Code**
```powershell
# Windows PowerShell launcher
.\orchestrator\launcher.ps1

# Or use Python directly
python orchestrator\orchestrator.py sequential --evidence "path\to\evidence.E01"
```

### **Option 4: Cross-Platform**
```bash
# Linux/macOS launcher
./edith-automater.sh
```

---

## **Project Structure**

```
EDITH-Automater/
├── LAUNCHERS & BUILD
│   ├── EDITH-USB.exe                    # USB portable launcher (auto-generated)
│   ├── build_exe.bat                    # Build single EXE
│   ├── create_usb_portable.py           # Create USB portable version
│   ├── edith-automater.sh               # Linux/macOS launcher
│   └── BUILD_INSTRUCTIONS.md            # EXE build guide
│
├── ORCHESTRATOR (Core Engine)
│   ├── orchestrator.py                  # Main automation engine
│   ├── launcher.ps1                     # Windows PowerShell interface
│   ├── run_orchestrator.bat             # Windows batch launcher
│   ├── setup.py                         # Installation utilities
│   └── setup.sh                         # Linux setup script
│
├── FORENSIC TOOLS
│   ├── Scripts/
│   │   ├── q_script.py                  # Interactive evidence collection
│   │   ├── script_3.py                  # Main forensic workflow
│   │   └── report_gen.py                # Professional report generation
│   ├── autopsy/                         # Autopsy integration
│   ├── bulk-extractor/                  # Pattern extraction tools
│   │   ├── bulk_extractor.py            # Python implementation
│   │   └── run_bulk_extractor.py        # Bulk extractor runner
│   ├── exiftool/                        # Metadata extraction
│   │   └── bin/exiftool.exe             # ExifTool binary
│   ├── hashdeep/                        # File integrity verification
│   ├── volatility/                      # Memory analysis tools
│   └── requirements.txt                 # Python dependencies
│
├── EVIDENCE & RESULTS
│   ├── evidence/                        # Sample evidence files
│   │   ├── charlie.E01                  # Sample disk image
│   │   └── memory.mem                   # Sample memory dump
│   ├── Results/                         # Case analysis results
│   │   └── CASE_YYYYMMDD_HHMMSS/       # Individual case folders
│   │       ├── Questions/               # Evidence collection forms
│   │       ├── HashDeep_output/         # Hash verification results
│   │       ├── Autopsy_output/          # Disk analysis results
│   │       ├── Volatility_output/       # Memory analysis results
│   │       ├── ExifTool_output/         # Metadata extraction
│   │       ├── BulkExtractor_output/    # Pattern extraction
│   │       └── Final_Reports/           # Generated reports
│   └── reports/                         # Report templates
│       └── Reports html/                # HTML report templates
│
├── TEMPLATES & CONFIG
│   ├── case_templates/                  # Case creation templates
│   │   └── NEW_CASE_PROMPT.json        # Evidence collection prompts
│   ├── config.json                     # Tool configuration
│   └── build_exe.spec                  # PyInstaller build specification
│
└── DOCUMENTATION
    ├── README.md                        # This file
    ├── BUILD_INSTRUCTIONS.md            # Detailed build guide
    ├── QUICK_START_EXE_BUILD.md        # Quick EXE build guide
    └── docs/                            # Additional documentation
```

---

## **Forensic Workflow**

### **1. Evidence Collection Phase**
- Interactive questionnaire for case details
- Evidence validation and integrity checking
- Automatic case directory structure creation
- Chain of custody documentation

### **2. Analysis Phase**
- **HashDeep**: Generate and verify file hashes
- **Autopsy**: File system analysis and timeline creation
- **Volatility**: Memory dump analysis and artifact extraction
- **ExifTool**: Metadata extraction from files and images
- **Bulk Extractor**: Pattern extraction (emails, URLs, credit cards, phone numbers)

### **3. Reporting Phase**
- Automated HTML report generation
- Professional PDF documentation
- Evidence summary and findings
- Technical analysis results compilation

---

## **System Requirements**

### **Minimum Requirements**
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB (16GB recommended for large evidence files)
- **Storage**: 50GB free space for analysis results
- **Python**: 3.8+ (bundled in portable versions)

### **Recommended Configuration**
- **OS**: Windows 11 Professional
- **RAM**: 32GB for memory analysis
- **Storage**: 500GB+ SSD for evidence processing
- **CPU**: Multi-core processor for parallel analysis

---

## **Advanced Usage**

### **Command Line Interface**
```powershell
# Sequential workflow with evidence file
python orchestrator.py sequential --evidence "C:\evidence\disk.E01" --memory "C:\evidence\memory.mem"

# Create new case
python orchestrator.py new-case --case-id "INVESTIGATION_001"

# List all cases
python orchestrator.py list-cases

# Generate reports only
python orchestrator.py generate-reports --case "CASE_20241020_143022"
```

### **USB Portable Customization**
```powershell
# Customize USB target location
$env:USB_TARGET = "G:\EDITH-Portable"
python create_usb_portable.py
```

---

## **Security & Legal Considerations**

### **Intended Use**
- ** Legitimate digital forensics investigations**
- ** Incident response and cybersecurity analysis**
- ** Educational and research purposes**
- ** Law enforcement digital evidence analysis**

### **Legal Compliance**
- Ensure proper authorization before analyzing any digital evidence
- Follow chain of custody procedures
- Comply with local laws and regulations regarding digital investigations
- Maintain evidence integrity throughout the analysis process

---

## **Output Examples**

### **Case Structure**
```
Results/CASE_20241020_143022/
├── Questions/
│   ├── evidence_collection_form.html
│   ├── case_details.json
│   └── chain_of_custody.pdf
├── HashDeep_output/
│   ├── file_hashes.txt
│   └── hash_verification.log
├── Autopsy_output/
│   ├── timeline.csv
│   ├── extracted_files/
│   └── analysis_report.html
├── Volatility_output/
│   ├── process_list.txt
│   ├── network_connections.txt
│   └── memory_artifacts/
├── ExifTool_output/
│   ├── metadata_summary.json
│   └── file_metadata/
├── BulkExtractor_output/
│   ├── email_addresses.txt
│   ├── urls.txt
│   ├── credit_cards.txt
│   └── extracted_patterns/
└── Final_Reports/
    ├── CASE_20241020_143022_Report.pdf
    ├── CASE_20241020_143022_Report.html
    └── evidence_summary.pdf
```

---

## **Development & Customization**

### **Adding New Tools**
1. Create tool directory in `/tools/`
2. Add Python integration script
3. Update `orchestrator.py` workflow
4. Test with sample evidence

### **Custom Report Templates**
1. Modify templates in `/reports/Reports html/`
2. Update `report_gen.py` for new formats
3. Test report generation

### **Building from Source**
```powershell
# Development setup
git clone https://github.com/adhi982/Edith_t-Automater.git
cd Edith_t-Automater
pip install -r tools\requirements.txt

# Run tests
python test_exe_build.py

# Build portable version
python create_usb_portable.py
```

---

## **Support & Documentation**

### **Getting Help**
- **Issues**: Check the `Results/` directory for analysis logs
- **Tips**: Use the interactive launcher for guided workflows

### **Common Issues**
- **Python Dependencies**: Run `pip install -r tools\requirements.txt`
- **Tool Paths**: Verify forensic tools are in correct directories
- **Memory Issues**: Increase virtual memory for large evidence files
- **Permissions**: Run as Administrator for complete functionality

---

## **License & Disclaimer**

This project is developed for **educational and legitimate forensic investigation purposes only**. Users are responsible for ensuring compliance with applicable laws and regulations. The authors are not responsible for any misuse of this software.

---

## **Acknowledgments**

Built with integration of industry-standard forensic tools:
- **Sleuth Kit & Autopsy** - Digital forensics platform
- **Volatility Foundation** - Memory analysis framework  
- **Phil Harvey** - ExifTool metadata extraction
- **Simson Garfinkel** - Bulk Extractor inspiration
- **NIST** - HashDeep implementation reference

---

**EDITH-Automater - Empowering Digital Forensics Investigations**
