"""
Analysis Report HTML Generator
Creates professional HTML reports from aggregated forensic findings
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class AnalysisReportGenerator:
    """Generate professional HTML analysis reports"""
    
    def __init__(self, case_name: str = "", case_id: str = "", officer_name: str = ""):
        """
        Initialize report generator
        
        Args:
            case_name: Name of the case
            case_id: Case identifier
            officer_name: Examining officer name
        """
        self.case_name = case_name
        self.case_id = case_id
        self.officer_name = officer_name
        self.generated_time = datetime.now()
    
    def generate_report(self, findings: Dict[str, Any]) -> str:
        """
        Generate complete HTML analysis report
        
        Args:
            findings: Dictionary of findings from AnalysisToolsParser
            
        Returns:
            HTML string of complete report
        """
        html = self._create_header()
        html += self._create_executive_summary(findings)
        html += self._create_autopsy_section(findings["autopsy"])
        html += self._create_volatility_section(findings["volatility"])
        html += self._create_bulk_extractor_section(findings["bulk_extractor"])
        html += self._create_exiftool_section(findings["exiftool"])
        html += self._create_hashdeep_section(findings["hashdeep"])
        html += self._create_footer()
        
        return html
    
    def _create_header(self) -> str:
        """Create HTML header with case information"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Findings Report - {self.case_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        h2 {{
            color: #34495e;
            font-size: 22px;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 4px solid #e74c3c;
            padding-left: 10px;
        }}
        
        h3 {{
            color: #5d6d7b;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        .case-info {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        
        .info-item {{
            background: #ecf0f1;
            padding: 10px;
            border-radius: 4px;
        }}
        
        .info-label {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .info-value {{
            color: #555;
        }}
        
        .executive-summary {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 30px;
            border-radius: 4px;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .summary-card {{
            background: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .summary-number {{
            font-size: 28px;
            font-weight: bold;
            color: #e74c3c;
        }}
        
        .summary-label {{
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }}
        
        .critical-findings {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .critical-item {{
            background: white;
            padding: 10px;
            margin: 5px 0;
            border-left: 3px solid #dc3545;
            border-radius: 2px;
        }}
        
        .risk-high {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .risk-medium {{
            color: #ff9800;
            font-weight: bold;
        }}
        
        .risk-low {{
            color: #28a745;
            font-weight: bold;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 20px;
        }}
        
        th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        tr:hover {{
            background: #f0f0f0;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .alert {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 12px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        
        .alert.warning {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        
        .alert.success {{
            background: #d4edda;
            border-left-color: #28a745;
        }}
        
        .evidence-count {{
            font-weight: bold;
            color: #e74c3c;
        }}
        
        .no-findings {{
            color: #666;
            font-style: italic;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 4px;
        }}
        
        .footer {{
            border-top: 1px solid #ddd;
            margin-top: 40px;
            padding-top: 20px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
        
        .sample-list {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
            max-height: 300px;
            overflow-y: auto;
        }}
        
        .sample-item {{
            padding: 5px;
            border-bottom: 1px solid #eee;
            font-size: 13px;
            font-family: 'Courier New', monospace;
            word-break: break-all;
        }}
        
        .sample-item:last-child {{
            border-bottom: none;
        }}
        
        .risk-score {{
            font-size: 36px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            border-radius: 50%;
            width: 150px;
            height: 150px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px auto;
        }}
        
        .risk-score.critical {{
            background: #dc3545;
            color: white;
        }}
        
        .risk-score.high {{
            background: #ff9800;
            color: white;
        }}
        
        .risk-score.medium {{
            background: #ffc107;
            color: #333;
        }}
        
        .risk-score.low {{
            background: #28a745;
            color: white;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚓ ANALYSIS FINDINGS REPORT</h1>
            <div class="case-info">
                <div class="info-item">
                    <span class="info-label">Case ID:</span>
                    <span class="info-value">{self.case_id}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Case Name:</span>
                    <span class="info-value">{self.case_name}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Examining Officer:</span>
                    <span class="info-value">{self.officer_name if self.officer_name else 'Not Specified'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Report Generated:</span>
                    <span class="info-value">{self.generated_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                </div>
            </div>
        </div>
"""
    
    def _create_executive_summary(self, findings: Dict[str, Any]) -> str:
        """Create executive summary section"""
        
        # Calculate key metrics
        total_suspicious = len(findings["autopsy"]["suspicious_files"])
        total_deleted = len(findings["autopsy"]["deleted_files"])
        malware_count = len(findings["volatility"]["malware_detected"])
        total_emails = findings["bulk_extractor"]["total_emails"]
        total_urls = findings["bulk_extractor"]["total_urls"]
        credit_cards = findings["bulk_extractor"]["total_cards"]
        ssn_count = len(findings["bulk_extractor"]["ssn"])
        
        # Calculate risk level
        risk_score = 0
        risk_score += credit_cards * 30
        risk_score += malware_count * 30
        risk_score += ssn_count * 30
        risk_score += min(total_suspicious, 3) * 15
        risk_score = min(risk_score, 100)
        
        if risk_score >= 75:
            risk_level = "CRITICAL"
            risk_class = "critical"
        elif risk_score >= 50:
            risk_level = "HIGH"
            risk_class = "high"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
            risk_class = "medium"
        else:
            risk_level = "LOW"
            risk_class = "low"
        
        html = f"""        <div class="section">
            <div class="executive-summary">
                <h2 style="border: none; padding: 0; margin: 0;">📋 EXECUTIVE SUMMARY</h2>
                <p style="margin-top: 15px;">
                    This Analysis Findings Report aggregates results from multiple forensic analysis tools
                    including Autopsy, Volatility3, Bulk Extractor, ExifTool, and HashDeep.
                </p>
                
                <div class="risk-score {risk_class}">
                    {risk_score}
                </div>
                <p style="text-align: center; margin-top: 10px;">Overall Risk Score: <span class="risk-{risk_class}">{risk_level}</span></p>
                
                <div class="summary-grid">
                    <div class="summary-card">
                        <div class="summary-number">{total_suspicious}</div>
                        <div class="summary-label">Suspicious Files</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{total_deleted}</div>
                        <div class="summary-label">Deleted Files Recovered</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{malware_count}</div>
                        <div class="summary-label">Malware Indicators</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{credit_cards}</div>
                        <div class="summary-label">Credit Cards Detected</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{total_emails}</div>
                        <div class="summary-label">Emails Extracted</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{total_urls}</div>
                        <div class="summary-label">URLs Found</div>
                    </div>
                </div>
            </div>
"""
        
        # Add critical findings if any
        if credit_cards > 0 or malware_count > 0 or ssn_count > 0:
            html += """            <div class="critical-findings">
                <h3 style="margin-top: 0; color: #dc3545;">⚠️ CRITICAL FINDINGS</h3>
"""
            if credit_cards > 0:
                html += f"""                <div class="critical-item">
                    <span class="risk-high">CRITICAL:</span> Found <span class="evidence-count">{credit_cards}</span> credit card numbers
                </div>
"""
            if malware_count > 0:
                html += f"""                <div class="critical-item">
                    <span class="risk-high">CRITICAL:</span> Detected <span class="evidence-count">{malware_count}</span> potential malware indicators
                </div>
"""
            if ssn_count > 0:
                html += f"""                <div class="critical-item">
                    <span class="risk-high">CRITICAL:</span> Found <span class="evidence-count">{ssn_count}</span> social security numbers
                </div>
"""
            html += """            </div>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_autopsy_section(self, autopsy_findings: Dict[str, Any]) -> str:
        """Create Autopsy analysis section"""
        html = f"""        <div class="section">
            <h2>🔍 AUTOPSY ANALYSIS</h2>
            
            <h3>Suspicious Files ({len(autopsy_findings['suspicious_files'])} found)</h3>
"""
        if autopsy_findings["suspicious_files"]:
            html += """            <table>
                <thead>
                    <tr>
                        <th>File/Path</th>
                        <th>Type</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in autopsy_findings["suspicious_files"][:50]:
                html += f"""                    <tr>
                        <td><code>{item.get('file', 'unknown')}</code></td>
                        <td>{item.get('type', 'unknown')}</td>
                        <td>{item.get('source', 'unknown')}</td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No suspicious files detected</div>
"""
        
        html += f"""            
            <h3>Deleted Files Recovered ({len(autopsy_findings['deleted_files'])} found)</h3>
"""
        if autopsy_findings["deleted_files"]:
            html += """            <table>
                <thead>
                    <tr>
                        <th>File/Path</th>
                        <th>Type</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in autopsy_findings["deleted_files"][:50]:
                html += f"""                    <tr>
                        <td><code>{item.get('file', 'unknown')}</code></td>
                        <td>{item.get('type', 'unknown')}</td>
                        <td>{item.get('source', 'unknown')}</td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No deleted files recovered</div>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_volatility_section(self, volatility_findings: Dict[str, Any]) -> str:
        """Create Volatility memory analysis section"""
        html = f"""        <div class="section">
            <h2>💾 VOLATILITY MEMORY ANALYSIS</h2>
            
            <h3>Malware Detection ({len(volatility_findings['malware_detected'])} indicators found)</h3>
"""
        if volatility_findings["malware_detected"]:
            html += """            <div class="alert">
                ⚠️ <strong>Potential malware or suspicious processes detected</strong>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Indicator</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in volatility_findings["malware_detected"][:50]:
                html += f"""                    <tr>
                        <td><span class="risk-high">MALWARE</span></td>
                        <td>{item.get('indicator', 'unknown')}</td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No malware indicators detected</div>
"""
        
        html += f"""            
            <h3>Processes Analyzed ({len(volatility_findings['processes'])} total)</h3>
"""
        if volatility_findings["processes"]:
            html += """            <table>
                <thead>
                    <tr>
                        <th>Process ID (PID)</th>
                        <th>Process Name</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in volatility_findings["processes"][:50]:
                html += f"""                    <tr>
                        <td>{item.get('pid', 'unknown')}</td>
                        <td><code>{item.get('name', 'unknown')}</code></td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No process data extracted</div>
"""
        
        html += f"""            
            <h3>Network Connections ({len(volatility_findings['network_connections'])} found)</h3>
"""
        if volatility_findings["network_connections"]:
            html += """            <table>
                <thead>
                    <tr>
                        <th>IP Address</th>
                        <th>Port</th>
                        <th>Domain</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in volatility_findings["network_connections"][:50]:
                html += f"""                    <tr>
                        <td><code>{item.get('address', 'unknown')}</code></td>
                        <td>{item.get('port', 'unknown')}</td>
                        <td>{item.get('domain', 'unknown')}</td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No network connections detected</div>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_bulk_extractor_section(self, bulk_findings: Dict[str, Any]) -> str:
        """Create Bulk Extractor patterns section"""
        html = f"""        <div class="section">
            <h2>🔎 PATTERN EXTRACTION (Bulk Extractor)</h2>
"""
        
        # Credit cards
        if bulk_findings["credit_cards"]:
            html += """            <h3>💳 Credit Card Numbers Detected (CRITICAL)</h3>
            <div class="alert">
                <strong>⚠️ CRITICAL:</strong> Credit card numbers detected in evidence. These may indicate financial fraud.
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Last 4 Digits</th>
                        <th>Masked Number</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in bulk_findings["credit_cards"][:20]:
                html += f"""                    <tr>
                        <td>{item.get('number', 'unknown')}</td>
                        <td><code>{item.get('masked', 'unknown')}</code></td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <h3>💳 Credit Card Numbers</h3>
            <div class="no-findings">No credit card numbers detected</div>
"""
        
        # SSN
        if bulk_findings["ssn"]:
            html += """            <h3>🆔 Social Security Numbers (CRITICAL)</h3>
            <div class="alert">
                <strong>⚠️ CRITICAL:</strong> Social Security Numbers detected. Indicates PII exposure.
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Masked Number</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in bulk_findings["ssn"][:20]:
                html += f"""                    <tr>
                        <td><code>{item.get('number', 'unknown')}</code></td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        
        # Emails
        html += f"""            <h3>📧 Emails Extracted ({bulk_findings['total_emails']} total)</h3>
"""
        if bulk_findings["emails"]:
            html += """            <div class="sample-list">
"""
            for email in bulk_findings["emails"][:50]:
                html += f"""                <div class="sample-item">{email}</div>
"""
            html += """            </div>
"""
        else:
            html += """            <div class="no-findings">No emails extracted</div>
"""
        
        # URLs
        html += f"""            <h3>🔗 URLs Found ({bulk_findings['total_urls']} total)</h3>
"""
        if bulk_findings["urls"]:
            html += """            <div class="sample-list">
"""
            for url in bulk_findings["urls"][:50]:
                html += f"""                <div class="sample-item">{url}</div>
"""
            html += """            </div>
"""
        else:
            html += """            <div class="no-findings">No URLs found</div>
"""
        
        # Phone numbers
        html += f"""            <h3>📞 Phone Numbers ({bulk_findings['total_phones']} total)</h3>
"""
        if bulk_findings["phone_numbers"]:
            html += """            <div class="sample-list">
"""
            for phone in bulk_findings["phone_numbers"][:50]:
                html += f"""                <div class="sample-item">{phone}</div>
"""
            html += """            </div>
"""
        else:
            html += """            <div class="no-findings">No phone numbers found</div>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_exiftool_section(self, exif_findings: Dict[str, Any]) -> str:
        """Create ExifTool metadata section"""
        html = f"""        <div class="section">
            <h2>📸 METADATA ANALYSIS (ExifTool)</h2>
            
            <h3>Images ({exif_findings['images']['count']} found)</h3>
"""
        
        if exif_findings["images"]["locations"]:
            html += f"""            <p><strong>GPS Coordinates Found: {len(exif_findings['images']['locations'])}</strong></p>
            <table>
                <thead>
                    <tr>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>File</th>
                    </tr>
                </thead>
                <tbody>
"""
            for location in exif_findings["images"]["locations"][:50]:
                html += f"""                    <tr>
                        <td>{location.get('lat', 'unknown')}</td>
                        <td>{location.get('lon', 'unknown')}</td>
                        <td><code>{location.get('file', 'unknown')}</code></td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        else:
            html += """            <div class="no-findings">No GPS coordinates found in images</div>
"""
        
        html += f"""            
            <h3>Documents ({exif_findings['documents']['count']} found)</h3>
"""
        
        if exif_findings["documents"]["authors"]:
            html += """            <p><strong>Document Authors/Creators:</strong></p>
            <div class="sample-list">
"""
            for author in exif_findings["documents"]["authors"][:50]:
                html += f"""                <div class="sample-item">{author}</div>
"""
            html += """            </div>
"""
        else:
            html += """            <div class="no-findings">No document authors identified</div>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_hashdeep_section(self, hash_findings: Dict[str, Any]) -> str:
        """Create HashDeep integrity verification section"""
        html = f"""        <div class="section">
            <h2>✅ FILE INTEGRITY VERIFICATION (HashDeep)</h2>
            
            <h3>Summary</h3>
            <table>
                <tbody>
                    <tr>
                        <td><strong>Total Files Verified</strong></td>
                        <td>{hash_findings['total_files_verified']}</td>
                    </tr>
                    <tr>
                        <td><strong>Files Valid (Hashes Match)</strong></td>
                        <td>{hash_findings['files_valid']}</td>
                    </tr>
                    <tr>
                        <td><strong>Modified Files</strong></td>
                        <td>{len(hash_findings['files_modified'])} <span class="risk-{('high' if hash_findings['files_modified'] else 'low')}">({hash_findings['integrity_status']})</span></td>
                    </tr>
                    <tr>
                        <td><strong>Chain of Custody Status</strong></td>
                        <td>
"""
        
        if hash_findings["integrity_status"] == "VERIFIED":
            html += """                            <span class="risk-low">✓ VERIFIED AND INTACT</span>
"""
        else:
            html += f"""                            <span class="risk-high">✗ {hash_findings['integrity_status']}</span>
"""
        
        html += """                        </td>
                    </tr>
                </tbody>
            </table>
"""
        
        if hash_findings["files_modified"]:
            html += """            <h3>Modified Files (Potential Evidence Tampering)</h3>
            <div class="alert">
                <strong>⚠️ WARNING:</strong> The following files have been modified since initial acquisition. This may indicate evidence tampering.
            </div>
            <table>
                <thead>
                    <tr>
                        <th>File/Path</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
            for item in hash_findings["files_modified"][:50]:
                html += f"""                    <tr>
                        <td><code>{item.get('file', 'unknown')}</code></td>
                        <td><span class="risk-high">{item.get('status', 'unknown').upper()}</span></td>
                    </tr>
"""
            html += """                </tbody>
            </table>
"""
        
        html += """        </div>
"""
        return html
    
    def _create_footer(self) -> str:
        """Create HTML footer"""
        return f"""        <div class="footer">
            <p><strong>EDITH-Automater Forensic Analysis System</strong></p>
            <p>Analysis Findings Report Generated: {self.generated_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p>This report contains sensitive forensic evidence. Handle with appropriate confidentiality.</p>
            <p style="margin-top: 20px; font-size: 11px;">
                Report includes findings from: Autopsy | Volatility3 | Bulk Extractor | ExifTool | HashDeep
            </p>
        </div>
    </div>
</body>
</html>
"""
