ExifTool Automation Script - README
=====================================

OVERVIEW
--------
The ExifTool automation script (exiftool_auto.py) provides automated metadata extraction 
from digital evidence files with support for batch processing, single file analysis, 
and flexible output formats. The script is cross-platform compatible (Windows/Linux).

REQUIREMENTS
------------
- Python 3.6 or higher
- ExifTool executable (included in bin/ directory for Windows)
- For Linux: Install ExifTool using package manager
  - Ubuntu/Debian: sudo apt install exiftool
  - CentOS/RHEL/Fedora: sudo yum install perl-Image-ExifTool

USAGE
-----
Basic Usage:
    python exiftool_auto.py [OPTIONS]

COMMAND LINE OPTIONS
-------------------

Required Arguments:
  --case-id CASE_ID         Case identifier for evidence processing
                           Example: --case-id "CASE-2025-001"

Optional Arguments:
  -h, --help               Show help message and exit
  
  --config-only            Generate configuration file only, don't process files
                          Useful for setting up processing parameters
                          
  --prompt                 Enable interactive prompts for custom input directory
                          By default, script runs without prompts using relative paths
                          Use this flag to specify custom evidence directory
                          
  --quick                  Enable quick mode - skip large files (>100MB by default)
                          Reduces processing time for large evidence collections
                          
  --file FILE_PATH         Process single file instead of entire evidence directory
                          Provide absolute or relative path to specific file
                          Example: --file "document.pdf" or --file "C:\evidence\photo.jpg"

PROCESSING MODES
---------------

1. Batch Processing (Default):
   - Processes all supported files in evidence directory
   - Creates comprehensive metadata reports
   - Generates JSON, CSV, and HTML output formats

2. Single File Processing:
   - Use --file flag to process individual files
   - Faster for testing or specific file analysis
   - Same output formats as batch processing

3. Quick Mode:
   - Use --quick flag to skip large files
   - Configurable file size limit (default: 100MB)
   - Useful for initial surveys of large evidence collections

4. Interactive Mode:
   - Use --prompt flag to specify custom directories
   - Allows processing evidence from any location
   - Prompts for input directory path

SUPPORTED FILE TYPES
--------------------
- Images: JPG, JPEG, PNG, GIF, BMP, TIFF, RAW formats
- Documents: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- Audio: MP3, WAV, FLAC, AAC, M4A
- Video: MP4, AVI, MOV, WMV, MKV, FLV
- Archives: ZIP, RAR, 7Z, TAR, GZ
- Executables: EXE, DLL, MSI
- And many more formats supported by ExifTool

OUTPUT FORMATS
--------------
The script generates three output formats:

1. JSON Format (exiftool_metadata.json):
   - Machine-readable structured data
   - Complete metadata for all processed files
   - Suitable for further automated processing

2. CSV Format (exiftool_metadata.csv):
   - Spreadsheet-compatible format
   - Key metadata fields in tabular format
   - Easy to import into analysis tools

3. HTML Format (exiftool_metadata.html):
   - Human-readable formatted report
   - Professional presentation with styling
   - Suitable for court presentations or reports

DIRECTORY STRUCTURE
------------------
Default paths (relative to script location):
- Evidence Input: ../../evidence/
- Output Directory: ../../evidence/Results/Exiftool_output/

Custom paths can be specified using --prompt flag.

CONFIGURATION OPTIONS
---------------------
Configuration file (config.json) contains:
- timeout: Maximum processing time per file (seconds)
- max_file_size_mb: File size limit for quick mode
- advanced_extraction: Enable detailed metadata extraction

EXAMPLES
--------

1. Basic evidence processing:
   python exiftool_auto.py --case-id "CASE-2025-001"

2. Process with custom directory (interactive):
   python exiftool_auto.py --case-id "CASE-2025-001" --prompt

3. Quick processing (skip large files):
   python exiftool_auto.py --case-id "CASE-2025-001" --quick

4. Process single file:
   python exiftool_auto.py --case-id "CASE-2025-001" --file "suspicious_document.pdf"

5. Generate configuration only:
   python exiftool_auto.py --case-id "CASE-2025-001" --config-only

6. Interactive mode with quick processing:
   python exiftool_auto.py --case-id "CASE-2025-001" --prompt --quick

ERROR HANDLING
--------------
- Unicode encoding issues are handled automatically
- Timeout protection prevents hanging on problematic files
- Detailed error logging for troubleshooting
- Graceful handling of unsupported file types

CROSS-PLATFORM COMPATIBILITY
----------------------------
- Windows: Uses included ExifTool executable (bin/exiftool.exe)
- Linux: Automatically detects system-installed ExifTool
- Path handling works on both Windows and Unix systems
- Unicode support for international file names

PERFORMANCE NOTES
-----------------
- Processing time depends on file count and sizes
- Quick mode recommended for large evidence collections
- Single file processing for testing specific files
- Batch processing generates comprehensive reports

TROUBLESHOOTING
---------------
1. "ExifTool executable not found":
   - Windows: Ensure bin/exiftool.exe exists
   - Linux: Install ExifTool using package manager

2. "No supported files found":
   - Check evidence directory contains supported file types
   - Verify directory path is correct

3. Processing timeout:
   - Use --quick flag to skip large files
   - Adjust timeout in configuration file

4. Unicode errors:
   - Script handles this automatically
   - If persistent, check file name encoding

LEGAL CONSIDERATIONS
-------------------
- Maintain chain of custody for digital evidence
- Document all processing steps and parameters used
- Preserve original evidence integrity
- Follow organizational forensic procedures

For additional support or questions, refer to the ExifTool documentation
or contact the development team.

Last Updated: October 2025
Version: 2.0 (Cross-platform compatible)