# EDITH-Automater Digital Forensics Tool

## Overview
EDITH-Automater is a comprehensive digital forensics automation framework designed to streamline the digital investigation process. It orchestrates multiple forensic tools and automates common analysis tasks.

## Features
- **Automated Evidence Processing**: Streamlined workflow from acquisition to analysis
- **Multiple Tool Integration**: Supports FTKImager, Autopsy, Volatility3, Bulk Extractor, and more
- **Report Generation**: Automated creation of professional forensic reports
- **Case Management**: Organized structure for managing multiple investigations
- **Hash Verification**: Automatic integrity checking of evidence

## Quick Start
1. Place your forensic tools in their respective folders under `/tools/`
2. Configure tool paths in `/orchestrator/config.json`
3. Create a new case using the template in `/case_templates/`
4. Run the orchestrator: `python orchestrator/orchestrator.py --case CASE-001 --evidence /path/to/evidence`

## Directory Structure
- **BOOT/**: Boot files for Windows PE or Linux forensic environments
- **tools/**: Forensic analysis tools (each in separate folders)
- **orchestrator/**: Main automation scripts and configuration
- **evidence/**: Storage for forensic images and evidence files
- **reports/**: Generated reports and analysis results
- **logs/**: Detailed logs for each case and analysis run
- **case_templates/**: Templates for starting new investigations
- **docs/**: User guides and documentation
- **utils/**: Additional utilities and helper tools
- **bin/**: Small helper programs and dependencies

## Supported Tools
- **FTKImager**: Forensic disk imaging and acquisition
- **Autopsy**: Comprehensive digital forensics platform
- **Volatility3**: Advanced memory analysis framework
- **Bulk Extractor**: Feature extraction from disk images
- **ExifTool**: Metadata extraction and analysis
- **HashDeep**: File integrity verification

## Requirements
- Windows 10/11 or Linux
- Python 3.7 or later
- PowerShell (for Windows launcher)
- Sufficient storage for evidence and analysis results

## License
This project is intended for legitimate digital forensics and incident response purposes only.

## Support
For documentation and guides, see the `/docs/` directory.