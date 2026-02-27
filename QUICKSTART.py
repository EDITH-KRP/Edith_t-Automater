#!/usr/bin/env python3
"""
EDITH-Automater with FTK Integration - Quick Start Guide
"""

print("""
================================================================================
                    EDITH-AUTOMATER FTK INTEGRATION
                         QUICK START GUIDE
================================================================================

✅ INTEGRATION STATUS: COMPLETE & VERIFIED

Your digital forensics tool now includes integrated FTK image analysis!

================================================================================
GETTING STARTED
================================================================================

1. RUN THE STANDARD WORKFLOW:

   python orchestrator/orchestrator.py sequential

   This will:
   ✓ Launch evidence collection questionnaire
   ✓ Ask for FTK image file path (optional)
   ✓ Process the forensic image automatically
   ✓ Run forensic analysis (Autopsy, Volatility, etc)
   ✓ Generate professional reports

================================================================================
NEW FEATURES
================================================================================

During evidence collection, you'll now be asked:

  "Path to FTK Imager image file (.E01, .dd, .img, etc.)"

Simply provide the full path to your forensic image:
  C:\\Evidence\\suspect_laptop.E01
  
Or leave blank to skip FTK processing (still works normally).

================================================================================
AUTOMATIC FTK PROCESSING
================================================================================

When you provide an image file, the system automatically:

✓ Extracts image metadata
✓ Detects image format (E01, DD, SMART, IMG, etc)
✓ Calculates MD5, SHA1, SHA256 hashes
✓ Analyzes partitions and file systems
✓ Generates professional FTK Acquisition Report (HTML)
✓ Saves all data to case directory

Generated files saved to: CASE_*/FTK_Acquisition/

  ├─ image_metadata.json        [Machine-readable metadata]
  ├─ acquisition_summary.json   [Quick reference data]
  └─ FTK_Acquisition_Report.html [Professional report - printable/PDF]

================================================================================
WORKFLOW WITH FTK
================================================================================

Evidence Collection
        ↓
[NEW] FTK Image Processing
        ↓
Forensic Analysis (Autopsy, Volatility, etc)
        ↓
Report Generation
        ↓
Case Complete

================================================================================
EXAMPLE SESSION
================================================================================

$ python orchestrator/orchestrator.py sequential

================================================================================
EDITH-Automater: SEQUENTIAL WORKFLOW
Evidence Collection → FTK Image Processing → Forensic Analysis
================================================================================

[STEP 1] Evidence Collection
--------------------------------------------------
[Questionnaire...]
Authorized Officer: Detective Smith
Case Name / No: CASE_2026_FIN_001
[...more questions...]

Path to FTK Imager image file: C:\\Evidence\\laptop.E01
✓ Image file confirmed

✓ Evidence Collection - Completed

[STEP 2] FTK Image Processing    <-- NEW!
--------------------------------------------------
[FTK IMAGE PROCESSING] Analyzing: laptop.E01

✓ Image processed successfully
  File: laptop.E01
  Format: EWF (Encase)
  Size: 256.5 GB
  MD5: d6c29ffb7f5dc74a054f1c4477e9c641
  Report: FTK_Acquisition_Report.html

[STEP 3] Forensic Analysis
--------------------------------------------------
[Analysis tools running...]
✓ HashDeep: Hashes calculated
✓ Autopsy: File system analyzed
✓ Volatility: Memory analyzed
✓ Bulk Extractor: Patterns extracted
✓ ExifTool: Metadata extracted

✓ Forensic Analysis - Completed

[Report Generation]
--------------------------------------------------
✓ Generating professional case reports
✓ Creating PDF versions
✓ Finalizing documentation

================================================================================
SEQUENTIAL WORKFLOW RESULTS
================================================================================
[STEP 1] Evidence Collection: success
[STEP 2] FTK Image Processing: success    <-- NEW!
[STEP 3] Forensic Analysis: success

[SUCCESS] Sequential workflow completed successfully!
[INFO] All results saved to: C:\\Results\\CASE_20260206_120000
[INFO] Reports and PDFs generated automatically!

================================================================================
RESULTS LOCATION
================================================================================

All case data saved to: Results/CASE_20260206_120000/

FTK-specific files:
  FTK_Acquisition/
  ├─ image_metadata.json
  ├─ acquisition_summary.json
  └─ FTK_Acquisition_Report.html

Other analysis results:
  ├─ HashDeep_output/
  ├─ Autopsy_output/
  ├─ Volatility_output/
  ├─ ExifTool_output/
  ├─ BulkExtractor_output/
  └─ Final_Reports/

================================================================================
VERIFICATION
================================================================================

Before running, verify the integration is working:

  python verify_ftk_integration.py

This will check:
✓ FTK module loaded
✓ Orchestrator integration
✓ All methods available
✓ Functionality working

================================================================================
COMMAND REFERENCE
================================================================================

Standard workflow:
  python orchestrator/orchestrator.py sequential

Verify integration:
  python verify_ftk_integration.py

Run FTK tests:
  python tools\\ftk_metadata\\test_ftk_module.py

Test FTK directly on an image:
  python tools\\ftk_metadata\\ftk_image_analyzer.py "image.E01" -o output.json

View test results:
  type tools\\ftk_metadata\\TEST_RESULTS.md

================================================================================
SUPPORTED IMAGE FORMATS
================================================================================

The FTK module supports all FTK Imager output formats:

✓ E01 / EWF        (Encase format)
✓ DD               (Raw disk dump)
✓ IMG              (Raw image)
✓ ISO              (CD/DVD images)
✓ VHD              (Virtual Hard Disk)
✓ VMDK             (Virtual Machine Disk)
✓ SMART / AD1      (AccessData format)

Simply provide the file path during evidence collection!

================================================================================
FEATURES
================================================================================

✓ Automatic image analysis
✓ Metadata extraction (size, sectors, partitions)
✓ Hash verification (MD5, SHA1, SHA256)
✓ Professional HTML reports
✓ Case integration
✓ Optional processing (can skip if no image)
✓ Error handling and logging
✓ Works with existing workflow

================================================================================
SUPPORT
================================================================================

If you encounter issues:

1. Run verification:
   python verify_ftk_integration.py

2. Check logs:
   type orchestrator.log

3. Verify dependencies:
   pip install libewf-python pytsk3 -U

4. Read documentation:
   - FTK_INTEGRATION_COMPLETE.md
   - tools/ftk_metadata/README.md
   - INTEGRATION_SUMMARY.md

================================================================================
TROUBLESHOOTING
================================================================================

Issue: "FTK module not available"
  → Install: pip install libewf-python pytsk3

Issue: "Image file not found"
  → Use absolute path: C:\\Full\\Path\\To\\image.E01
  → Confirm file exists before running

Issue: "FTK processing failed"
  → Check image file integrity
  → Ensure sufficient disk space
  → Verify image format supported

================================================================================
YOU'RE ALL SET!
================================================================================

Your EDITH-Automater now has integrated FTK image analysis!

To start your first case:

  python orchestrator/orchestrator.py sequential

Then:
  1. Answer the evidence collection questions
  2. Provide your FTK image file path when asked
  3. Let the system process everything automatically
  4. Get professional reports in the case directory

Happy investigating! 🔍

================================================================================
Version: 1.0 (February 6, 2026)
Status: ✅ PRODUCTION READY
================================================================================
""")
