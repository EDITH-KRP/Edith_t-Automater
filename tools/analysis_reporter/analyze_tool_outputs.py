"""
Analysis Tool Outputs Parser
Parses outputs from Autopsy, Volatility, Bulk Extractor, ExifTool, and HashDeep
Aggregates findings into structured format for reporting
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


class AnalysisToolsParser:
    """Parse and aggregate outputs from forensic analysis tools"""
    
    def __init__(self, case_dir: str):
        """
        Initialize parser with case directory
        
        Args:
            case_dir: Path to case directory containing forensic results
        """
        self.case_dir = Path(case_dir)
        self.findings = {
            "autopsy": {
                "suspicious_files": [],
                "deleted_files": [],
                "user_activity": [],
                "file_count": 0,
                "total_size": 0
            },
            "volatility": {
                "processes": [],
                "malware_detected": [],
                "network_connections": [],
                "process_count": 0
            },
            "bulk_extractor": {
                "emails": [],
                "urls": [],
                "credit_cards": [],
                "phone_numbers": [],
                "ssn": [],
                "total_emails": 0,
                "total_urls": 0,
                "total_cards": 0,
                "total_phones": 0
            },
            "exiftool": {
                "images": {
                    "count": 0,
                    "locations": [],
                    "dates": [],
                    "cameras": []
                },
                "documents": {
                    "count": 0,
                    "authors": [],
                    "dates": [],
                    "file_types": {}
                }
            },
            "hashdeep": {
                "total_files_verified": 0,
                "files_valid": 0,
                "files_modified": [],
                "files_missing": [],
                "integrity_status": "UNKNOWN"
            }
        }
    
    def parse_autopsy_logs(self) -> bool:
        """
        Parse Autopsy analysis results
        Looks for autopsy results in case directory
        
        Returns:
            True if logs found and parsed, False otherwise
        """
        try:
            autopsy_dir = self.case_dir / "Autopsy_Results"
            if not autopsy_dir.exists():
                return False
            
            # Look for Autopsy log files
            log_files = list(autopsy_dir.glob("**/*.txt")) + list(autopsy_dir.glob("**/*.log"))
            
            suspicious_count = 0
            deleted_count = 0
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read()
                        
                        # Parse suspicious files - look for lines with [ALERT] and SUSPICIOUS
                        suspicious_lines = re.finditer(
                            r'\[ALERT\].*SUSPICIOUS.*\n.*?Path:\s*([^\n]+)',
                            content, re.IGNORECASE | re.DOTALL
                        )
                        for match in suspicious_lines:
                            file_path = match.group(1).strip()
                            if file_path:
                                self.findings["autopsy"]["suspicious_files"].append({
                                    "file": file_path[:100],
                                    "type": "suspicious",
                                    "source": log_file.name
                                })
                        
                        # Also look for MALWARE, HIDDEN, UNUSUAL patterns
                        other_patterns = re.finditer(
                            r'(?:MALWARE|HIDDEN|UNUSUAL|VIRUS|TROJAN|ROOTKIT).*?(?:Path|File|Name)[:\s]+([^\n]+)',
                            content, re.IGNORECASE
                        )
                        for match in other_patterns:
                            file_path = match.group(1).strip()
                            if file_path and not any(s["file"] == file_path for s in self.findings["autopsy"]["suspicious_files"]):
                                self.findings["autopsy"]["suspicious_files"].append({
                                    "file": file_path[:100],
                                    "type": "suspicious",
                                    "source": log_file.name
                                })
                        
                        # Parse deleted files - look for [RECOVERED] DELETED blocks
                        deleted_lines = re.finditer(
                            r'\[RECOVERED\].*DELETED.*\n.*?Path:\s*([^\n]+)',
                            content, re.IGNORECASE | re.DOTALL
                        )
                        for match in deleted_lines:
                            file_path = match.group(1).strip()
                            if file_path:
                                self.findings["autopsy"]["deleted_files"].append({
                                    "file": file_path[:100],
                                    "type": "recovered",
                                    "source": log_file.name
                                })
                        
                        # Also look for UNALLOCATED, CARVING patterns
                        other_deleted = re.finditer(
                            r'(?:UNALLOCATED|CARVING|ORPHANED).*?(?:Path|File|Name)[:\s]+([^\n]+)',
                            content, re.IGNORECASE
                        )
                        for match in other_deleted:
                            file_path = match.group(1).strip()
                            if file_path and not any(d["file"] == file_path for d in self.findings["autopsy"]["deleted_files"]):
                                self.findings["autopsy"]["deleted_files"].append({
                                    "file": file_path[:100],
                                    "type": "recovered",
                                    "source": log_file.name
                                })
                except Exception as e:
                    pass
            
            self.findings["autopsy"]["suspicious_files"] = self.findings["autopsy"]["suspicious_files"][:50]
            self.findings["autopsy"]["deleted_files"] = self.findings["autopsy"]["deleted_files"][:50]
            
            return len(log_files) > 0
            
        except Exception as e:
            return False
    
    def parse_volatility_output(self) -> bool:
        """
        Parse Volatility3 memory analysis results
        
        Returns:
            True if logs found and parsed
        """
        try:
            vol_dir = self.case_dir / "Volatility_Results"
            if not vol_dir.exists():
                return False
            
            log_files = list(vol_dir.glob("**/*.txt")) + list(vol_dir.glob("**/*.log"))
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read()
                        
                        # Parse processes
                        process_matches = re.finditer(
                            r'(?:PID|Process).*?(\d+).*?([a-zA-Z0-9_\.]+\.exe)',
                            content, re.IGNORECASE
                        )
                        for match in process_matches:
                            if len(self.findings["volatility"]["processes"]) < 100:
                                self.findings["volatility"]["processes"].append({
                                    "pid": match.group(1),
                                    "name": match.group(2)
                                })
                        
                        # Detect malware indicators
                        malware_patterns = [
                            r'trojan|ransomware|backdoor|worm|virus|malware|cryptominer',
                            r'suspicious.*process|hidden.*process|rootkit',
                            r'network.*anomaly|unusual.*connection'
                        ]
                        
                        for pattern in malware_patterns:
                            matches = re.finditer(pattern + r'.*?([^\n]+)', content, re.IGNORECASE)
                            for match in matches:
                                if len(self.findings["volatility"]["malware_detected"]) < 50:
                                    self.findings["volatility"]["malware_detected"].append({
                                        "type": "potential_malware",
                                        "indicator": match.group(1).strip()[:100]
                                    })
                        
                        # Parse network connections
                        conn_matches = re.finditer(
                            r'(?:connection|socket).*?([\d\.]+).*?(\d+).*?([a-z0-9\-\.]+)',
                            content, re.IGNORECASE
                        )
                        for match in conn_matches:
                            if len(self.findings["volatility"]["network_connections"]) < 50:
                                self.findings["volatility"]["network_connections"].append({
                                    "address": match.group(1),
                                    "port": match.group(2),
                                    "domain": match.group(3)
                                })
                
                except Exception as e:
                    pass
            
            return len(log_files) > 0
            
        except Exception as e:
            return False
    
    def parse_bulk_extractor_output(self) -> bool:
        """
        Parse Bulk Extractor pattern extraction results
        
        Returns:
            True if results found
        """
        try:
            bulk_dir = self.case_dir / "BulkExtractor_Results"
            if not bulk_dir.exists():
                return False
            
            # Parse email.txt
            email_file = bulk_dir / "email.txt"
            if email_file.exists():
                try:
                    with open(email_file, 'r', errors='ignore') as f:
                        emails = []
                        for line in f:
                            email = line.strip()
                            if '@' in email and email not in emails:
                                emails.append(email)
                        self.findings["bulk_extractor"]["emails"] = emails[:100]
                        self.findings["bulk_extractor"]["total_emails"] = len(emails)
                except Exception as e:
                    pass
            
            # Parse url.txt
            url_file = bulk_dir / "url.txt"
            if url_file.exists():
                try:
                    with open(url_file, 'r', errors='ignore') as f:
                        urls = []
                        for line in f:
                            url = line.strip()
                            if url.startswith('http') and url not in urls:
                                urls.append(url)
                        self.findings["bulk_extractor"]["urls"] = urls[:100]
                        self.findings["bulk_extractor"]["total_urls"] = len(urls)
                except Exception as e:
                    pass
            
            # Parse ccn.txt (credit card numbers)
            ccn_file = bulk_dir / "ccn.txt"
            if ccn_file.exists():
                try:
                    with open(ccn_file, 'r', errors='ignore') as f:
                        cards = []
                        for line in f:
                            card = line.strip()
                            if card and len(card) >= 13:
                                cards.append({
                                    "number": card[-4:],  # Last 4 digits only
                                    "masked": "*" * (len(card) - 4) + card[-4:]
                                })
                        self.findings["bulk_extractor"]["credit_cards"] = cards[:50]
                        self.findings["bulk_extractor"]["total_cards"] = len(cards)
                except Exception as e:
                    pass
            
            # Parse phone.txt
            phone_file = bulk_dir / "phone.txt"
            if phone_file.exists():
                try:
                    with open(phone_file, 'r', errors='ignore') as f:
                        phones = []
                        for line in f:
                            phone = line.strip()
                            if phone and phone not in phones:
                                phones.append(phone)
                        self.findings["bulk_extractor"]["phone_numbers"] = phones[:100]
                        self.findings["bulk_extractor"]["total_phones"] = len(phones)
                except Exception as e:
                    pass
            
            # Parse ssn.txt (social security numbers)
            ssn_file = bulk_dir / "ssn.txt"
            if ssn_file.exists():
                try:
                    with open(ssn_file, 'r', errors='ignore') as f:
                        ssns = []
                        for line in f:
                            ssn = line.strip()
                            if ssn and ssn not in ssns:
                                ssns.append({
                                    "number": "***-**-" + ssn[-4:],  # Last 4 digits only
                                    "source": "bulk_extractor"
                                })
                        self.findings["bulk_extractor"]["ssn"] = ssns[:50]
                except Exception as e:
                    pass
            
            return email_file.exists() or url_file.exists() or ccn_file.exists()
            
        except Exception as e:
            return False
    
    def parse_exiftool_metadata(self) -> bool:
        """
        Parse ExifTool metadata extraction results
        
        Returns:
            True if metadata found
        """
        try:
            exif_dir = self.case_dir / "ExifTool_Results"
            if not exif_dir.exists():
                return False
            
            log_files = list(exif_dir.glob("**/*.txt")) + list(exif_dir.glob("**/*.json"))
            
            image_count = 0
            document_count = 0
            
            for log_file in log_files:
                try:
                    if log_file.suffix == '.json':
                        with open(log_file, 'r', errors='ignore') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                for item in data:
                                    if isinstance(item, dict):
                                        file_type = item.get('FileType', '')
                                        if file_type in ['JPEG', 'PNG', 'TIFF', 'GIF']:
                                            image_count += 1
                                            if item.get('GPSLatitude'):
                                                self.findings["exiftool"]["images"]["locations"].append({
                                                    "lat": item.get('GPSLatitude'),
                                                    "lon": item.get('GPSLongitude'),
                                                    "file": item.get('SourceFile', 'unknown')[:50]
                                                })
                                        elif file_type in ['PDF', 'DOCX', 'XLSX', 'XLS', 'DOC']:
                                            document_count += 1
                    else:
                        with open(log_file, 'r', errors='ignore') as f:
                            content = f.read()
                            
                            # Count image mentions
                            image_count += len(re.findall(
                                r'(?:image|jpeg|png|tiff|gif)',
                                content, re.IGNORECASE
                            ))
                            
                            # Extract locations from GPS data
                            gps_matches = re.finditer(
                                r'GPS.*?Latitude[:\s]+([0-9\.\-]+).*?Longitude[:\s]+([0-9\.\-]+)',
                                content, re.IGNORECASE
                            )
                            for match in gps_matches:
                                if len(self.findings["exiftool"]["images"]["locations"]) < 100:
                                    self.findings["exiftool"]["images"]["locations"].append({
                                        "lat": match.group(1),
                                        "lon": match.group(2)
                                    })
                            
                            # Extract authors
                            author_matches = re.finditer(
                                r'Author[:\s]+([^\n]+)',
                                content, re.IGNORECASE
                            )
                            for match in author_matches:
                                author = match.group(1).strip()
                                if author and author not in self.findings["exiftool"]["documents"]["authors"]:
                                    self.findings["exiftool"]["documents"]["authors"].append(author)
                
                except Exception as e:
                    pass
            
            self.findings["exiftool"]["images"]["count"] = image_count
            self.findings["exiftool"]["documents"]["count"] = document_count
            
            return image_count > 0 or document_count > 0
            
        except Exception as e:
            return False
    
    def parse_hashdeep_verification(self) -> bool:
        """
        Parse HashDeep file integrity verification results
        
        Returns:
            True if verification results found
        """
        try:
            hash_dir = self.case_dir / "HashDeep_Results"
            if not hash_dir.exists():
                return False
            
            log_files = list(hash_dir.glob("**/*.txt")) + list(hash_dir.glob("**/*.log"))
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', errors='ignore') as f:
                        content = f.read()
                        
                        # Parse file counts
                        verified_match = re.search(r'(?:verified|processed|total).*?(\d+)', content, re.IGNORECASE)
                        if verified_match:
                            self.findings["hashdeep"]["total_files_verified"] = int(verified_match.group(1))
                        
                        # Parse valid files
                        valid_match = re.search(r'(?:valid|match|ok).*?(\d+)', content, re.IGNORECASE)
                        if valid_match:
                            self.findings["hashdeep"]["files_valid"] = int(valid_match.group(1))
                        
                        # Parse modified files
                        modified_matches = re.finditer(
                            r'MODIFIED|CHANGED|HASH.*?MISMATCH.*?([^\n]+)',
                            content, re.IGNORECASE
                        )
                        for match in modified_matches:
                            if len(self.findings["hashdeep"]["files_modified"]) < 50:
                                self.findings["hashdeep"]["files_modified"].append({
                                    "file": match.group(1).strip()[:100],
                                    "status": "modified"
                                })
                        
                        # Determine integrity status
                        if self.findings["hashdeep"]["files_modified"]:
                            self.findings["hashdeep"]["integrity_status"] = "COMPROMISED"
                        else:
                            self.findings["hashdeep"]["integrity_status"] = "VERIFIED"
                
                except Exception as e:
                    pass
            
            return len(log_files) > 0
            
        except Exception as e:
            return False
    
    def parse_all_outputs(self) -> Dict[str, Any]:
        """
        Parse all available forensic tool outputs
        
        Returns:
            Dictionary containing aggregated findings
        """
        self.parse_autopsy_logs()
        self.parse_volatility_output()
        self.parse_bulk_extractor_output()
        self.parse_exiftool_metadata()
        self.parse_hashdeep_verification()
        
        return self.findings
    
    def get_findings(self) -> Dict[str, Any]:
        """Get current findings dictionary"""
        return self.findings
    
    def get_critical_findings(self) -> List[Dict[str, Any]]:
        """
        Extract critical findings that need immediate attention
        
        Returns:
            List of critical findings
        """
        critical = []
        
        # Credit cards are always critical
        if self.findings["bulk_extractor"]["total_cards"] > 0:
            critical.append({
                "level": "CRITICAL",
                "category": "Payment Cards",
                "count": self.findings["bulk_extractor"]["total_cards"],
                "description": f"Found {self.findings['bulk_extractor']['total_cards']} credit card numbers"
            })
        
        # Malware is critical
        if self.findings["volatility"]["malware_detected"]:
            critical.append({
                "level": "CRITICAL",
                "category": "Malware Detection",
                "count": len(self.findings["volatility"]["malware_detected"]),
                "description": f"Detected {len(self.findings['volatility']['malware_detected'])} potential malware indicators"
            })
        
        # High number of suspicious files
        if len(self.findings["autopsy"]["suspicious_files"]) > 10:
            critical.append({
                "level": "HIGH",
                "category": "Suspicious Files",
                "count": len(self.findings["autopsy"]["suspicious_files"]),
                "description": f"Found {len(self.findings['autopsy']['suspicious_files'])} suspicious files"
            })
        
        # Modified files indicate tampering
        if self.findings["hashdeep"]["files_modified"]:
            critical.append({
                "level": "HIGH",
                "category": "File Integrity",
                "count": len(self.findings["hashdeep"]["files_modified"]),
                "description": f"Detected {len(self.findings['hashdeep']['files_modified'])} modified files - potential evidence tampering"
            })
        
        # SSN or comprehensive data exposure
        if self.findings["bulk_extractor"]["ssn"]:
            critical.append({
                "level": "CRITICAL",
                "category": "PII Exposure",
                "count": len(self.findings["bulk_extractor"]["ssn"]),
                "description": f"Found {len(self.findings['bulk_extractor']['ssn'])} social security numbers"
            })
        
        return critical
    
    def get_risk_score(self) -> int:
        """
        Calculate overall risk score (0-100)
        Based on types and quantities of findings
        
        Returns:
            Risk score from 0-100
        """
        score = 0
        
        # Critical findings (30 points each)
        score += len(self.findings["bulk_extractor"]["credit_cards"]) * 30
        score += len(self.findings["volatility"]["malware_detected"]) * 30
        score += len(self.findings["bulk_extractor"]["ssn"]) * 30
        
        # High findings (15 points each)
        score += min(len(self.findings["autopsy"]["suspicious_files"]), 3) * 15
        score += len(self.findings["hashdeep"]["files_modified"]) * 15
        
        # Medium findings (5 points each)
        score += min(self.findings["bulk_extractor"]["total_cards"], 3) * 5
        score += min(self.findings["bulk_extractor"]["total_emails"], 10) * 5
        
        # Cap at 100
        return min(score, 100)
