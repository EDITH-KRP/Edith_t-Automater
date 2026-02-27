#!/usr/bin/env python3
"""
FTK Integration Module for EDITH-Automater
Handles image acquisition reporting and case integration
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from .ftk_image_analyzer import FTKImageAnalyzer


class FTKIntegration:
    """
    Integration layer between FTK Imager and EDITH-Automater
    Handles metadata extraction and case documentation
    """

    def __init__(self, case_dir: str):
        """
        Initialize FTK integration for a case
        
        Args:
            case_dir: Path to case directory
        """
        self.case_dir = Path(case_dir)
        self.logger = logging.getLogger(__name__)
        self.ftk_output_dir = self.case_dir / "FTK_Acquisition"
        self.ftk_output_dir.mkdir(exist_ok=True)

    def process_image_file(self, image_path: str) -> Dict:
        """
        Process an FTK Imager image file and extract metadata
        
        Args:
            image_path: Path to FTK image file
        
        Returns:
            Dictionary with extracted metadata
        """
        try:
            analyzer = FTKImageAnalyzer(image_path)
            metadata = analyzer.extract_all_metadata()
            
            # Save metadata JSON
            metadata_file = self.ftk_output_dir / "image_metadata.json"
            analyzer.save_metadata_json(str(metadata_file))
            
            self.logger.info(f"Image metadata extracted and saved")
            
            return analyzer.get_report_dict()
        
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return {}

    def generate_ftk_acquisition_form(self, image_metadata: Dict, 
                                      officer_name: str = "",
                                      case_name: str = "",
                                      case_id: str = "") -> str:
        """
        Generate FTK Acquisition Report HTML form
        
        Args:
            image_metadata: Metadata from FTK image analysis
            officer_name: Name of officer who acquired image
            case_name: Name of the case
            case_id: Case ID
        
        Returns:
            HTML content for the form
        """
        
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FTK Image Acquisition Report</title>
    <style>
        @page {{
            size: A4;
            margin: 0;
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .page {{
            width: 210mm;
            min-height: 297mm;
            margin: 20px auto;
            background-color: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            position: relative;
            box-sizing: border-box;
            border: 1px solid #000;
            padding: 15mm;
        }}
        .title {{
            text-align: center;
            font-weight: bold;
            font-size: 18pt;
            margin-bottom: 20px;
            text-decoration: underline;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        table, th, td {{
            border: 1px solid black;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            vertical-align: top;
            font-size: 10pt;
        }}
        th {{
            background-color: #000;
            color: white;
            font-weight: bold;
        }}
        .label {{
            font-weight: bold;
            width: 35%;
            background-color: #f0f0f0;
        }}
        .hash-table {{
            margin-top: 20px;
        }}
        .hash-table th {{
            width: 25%;
        }}
        .section-title {{
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 10px;
            font-size: 12pt;
            text-decoration: underline;
        }}
        .signature-line {{
            border-top: 1px solid black;
            margin-top: 50px;
            padding-top: 5px;
            text-align: center;
            font-weight: bold;
        }}
        @media print {{
            body {{
                background: none;
            }}
            .page {{
                box-shadow: none;
                border: none;
                margin: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <div class="title">FTK IMAGE ACQUISITION REPORT</div>
        
        <!-- Case Information -->
        <div class="section-title">Case Information</div>
        <table>
            <tr>
                <td class="label">Case ID:</td>
                <td>{case_id if case_id else '____________________'}</td>
            </tr>
            <tr>
                <td class="label">Case Name:</td>
                <td>{case_name if case_name else '____________________'}</td>
            </tr>
            <tr>
                <td class="label">Acquiring Officer:</td>
                <td>{officer_name if officer_name else '____________________'}</td>
            </tr>
            <tr>
                <td class="label">Acquisition Date/Time:</td>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        </table>
        
        <!-- Image Information -->
        <div class="section-title">Source Device Information</div>
        <table>
            <tr>
                <td class="label">Source Device:</td>
                <td>{image_metadata.get('source_device', '____________________')}</td>
            </tr>
            <tr>
                <td class="label">Device Serial Number:</td>
                <td>____________________</td>
            </tr>
            <tr>
                <td class="label">Device Make/Model:</td>
                <td>____________________</td>
            </tr>
            <tr>
                <td class="label">Storage Capacity:</td>
                <td>{image_metadata.get('file_size_gb', 0)} GB</td>
            </tr>
        </table>
        
        <!-- Image File Information -->
        <div class="section-title">Image File Details</div>
        <table>
            <tr>
                <td class="label">Image File Name:</td>
                <td>{image_metadata.get('file_name', 'N/A')}</td>
            </tr>
            <tr>
                <td class="label">Image Format:</td>
                <td>{image_metadata.get('format', 'N/A')}</td>
            </tr>
            <tr>
                <td class="label">File Size (Bytes):</td>
                <td>{image_metadata.get('file_size_bytes', 0):,}</td>
            </tr>
            <tr>
                <td class="label">File Size (GB):</td>
                <td>{image_metadata.get('file_size_gb', 0)}</td>
            </tr>
            <tr>
                <td class="label">Total Sectors:</td>
                <td>{image_metadata.get('sectors', 0):,}</td>
            </tr>
            <tr>
                <td class="label">Bytes Per Sector:</td>
                <td>{image_metadata.get('bytes_per_sector', 512)}</td>
            </tr>
            <tr>
                <td class="label">Number of Segments:</td>
                <td>{image_metadata.get('segment_count', 1)}</td>
            </tr>
            <tr>
                <td class="label">Number of Partitions:</td>
                <td>{image_metadata.get('partition_count', 0)}</td>
            </tr>
        </table>
        
        <!-- Hash Verification -->
        <div class="section-title">Hash Verification</div>
        <table class="hash-table">
            <tr>
                <th>Algorithm</th>
                <th>Hash Value</th>
            </tr>
            <tr>
                <td style="font-weight: bold;">MD5</td>
                <td style="font-family: monospace; word-break: break-all;">{image_metadata.get('md5', 'Not calculated')}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">SHA-1</td>
                <td style="font-family: monospace; word-break: break-all;">{image_metadata.get('sha1', 'Not calculated')}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">SHA-256</td>
                <td style="font-family: monospace; word-break: break-all;">{image_metadata.get('sha256', 'Not calculated')}</td>
            </tr>
        </table>
        
        <!-- Acquisition Method -->
        <div class="section-title">Acquisition Method</div>
        <table>
            <tr>
                <td class="label">Tool Used:</td>
                <td>FTK Imager</td>
            </tr>
            <tr>
                <td class="label">Tool Version:</td>
                <td>____________________</td>
            </tr>
            <tr>
                <td class="label">Acquisition Method:</td>
                <td>
                    <label><input type="radio" name="method"> Physical</label>&nbsp;&nbsp;
                    <label><input type="radio" name="method"> Logical</label>&nbsp;&nbsp;
                    <label><input type="radio" name="method"> Volatile Memory</label>
                </td>
            </tr>
            <tr>
                <td class="label">Write-Blocker Used:</td>
                <td>
                    <label><input type="radio" name="blocker"> Yes</label>&nbsp;&nbsp;
                    <label><input type="radio" name="blocker"> No</label>
                </td>
            </tr>
            <tr>
                <td class="label">Compression:</td>
                <td>____________________</td>
            </tr>
        </table>
        
        <!-- Verification -->
        <div class="section-title">Verification & Quality Assurance</div>
        <table>
            <tr>
                <td class="label">Hashes Verified:</td>
                <td>
                    <label><input type="radio" name="verified"> Yes</label>&nbsp;&nbsp;
                    <label><input type="radio" name="verified"> No</label>
                </td>
            </tr>
            <tr>
                <td class="label">Verification Date/Time:</td>
                <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td class="label">Verified By:</td>
                <td>____________________</td>
            </tr>
            <tr>
                <td class="label">Issues/Notes:</td>
                <td style="height: 60px;"></td>
            </tr>
        </table>
        
        <!-- Signatures -->
        <div class="section-title">Signatures</div>
        <div style="display: flex; justify-content: space-between; margin-top: 50px;">
            <div style="width: 45%;">
                <div class="signature-line">Acquiring Officer</div>
            </div>
            <div style="width: 45%;">
                <div class="signature-line">Verifying Officer</div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        return html_template

    def save_ftk_acquisition_form(self, image_metadata: Dict, 
                                  officer_name: str = "",
                                  case_name: str = "",
                                  case_id: str = "") -> str:
        """
        Generate and save FTK Acquisition Report form
        
        Args:
            image_metadata: Extracted image metadata
            officer_name: Officer name
            case_name: Case name
            case_id: Case ID
        
        Returns:
            Path to saved HTML file
        """
        html_content = self.generate_ftk_acquisition_form(
            image_metadata, officer_name, case_name, case_id
        )
        
        output_file = self.ftk_output_dir / "FTK_Acquisition_Report.html"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"FTK Acquisition Report saved to: {output_file}")
        
        return str(output_file)

    def create_acquisition_summary(self, image_metadata: Dict) -> Dict:
        """
        Create a summary dictionary of acquisition for quick reference
        
        Args:
            image_metadata: Extracted metadata
        
        Returns:
            Summary dictionary
        """
        summary = {
            'file_name': image_metadata.get('file_name'),
            'file_size_gb': image_metadata.get('file_size_gb'),
            'format': image_metadata.get('format'),
            'sector_count': image_metadata.get('sectors'),
            'md5_hash': image_metadata.get('md5'),
            'sha1_hash': image_metadata.get('sha1'),
            'sha256_hash': image_metadata.get('sha256'),
            'partition_count': image_metadata.get('partition_count'),
            'extraction_date': datetime.now().isoformat()
        }
        
        # Save summary
        summary_file = self.ftk_output_dir / "acquisition_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Acquisition summary saved to: {summary_file}")
        
        return summary


def integrate_ftk_with_case(case_dir: str, image_path: str, 
                           case_id: str = "", case_name: str = "",
                           officer_name: str = "") -> Dict:
    """
    Complete FTK integration workflow for a case
    
    Args:
        case_dir: Path to case directory
        image_path: Path to FTK image file
        case_id: Case ID
        case_name: Case name
        officer_name: Acquiring officer name
    
    Returns:
        Dictionary with results
    """
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize FTK integration
        ftk = FTKIntegration(case_dir)
        
        # Process image
        logger.info(f"Processing FTK image: {image_path}")
        image_metadata = ftk.process_image_file(image_path)
        
        if not image_metadata:
            return {'success': False, 'error': 'Failed to extract image metadata'}
        
        # Generate FTK Acquisition Report
        ftk_form_path = ftk.save_ftk_acquisition_form(
            image_metadata, officer_name, case_name, case_id
        )
        
        # Create acquisition summary
        summary = ftk.create_acquisition_summary(image_metadata)
        
        logger.info("FTK integration completed successfully")
        
        return {
            'success': True,
            'image_metadata': image_metadata,
            'ftk_form_path': ftk_form_path,
            'summary': summary
        }
    
    except Exception as e:
        logger.error(f"Error during FTK integration: {e}")
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python ftk_integration.py <case_dir> <image_path> [case_id] [case_name] [officer_name]")
        sys.exit(1)
    
    case_dir = sys.argv[1]
    image_path = sys.argv[2]
    case_id = sys.argv[3] if len(sys.argv) > 3 else ""
    case_name = sys.argv[4] if len(sys.argv) > 4 else ""
    officer_name = sys.argv[5] if len(sys.argv) > 5 else ""
    
    result = integrate_ftk_with_case(case_dir, image_path, case_id, case_name, officer_name)
    print(json.dumps(result, indent=2))
