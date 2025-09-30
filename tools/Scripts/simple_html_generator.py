#!/usr/bin/env python3
"""
EDITH-Automater Simple Report Generator
HTML Report Generation from Digital Evidence Collection Forms

This script automatically:
1. Reads form data from questions.txt
2. Populates HTML templates with the data
3. Saves filled HTML reports (ready for manual PDF conversion)

Author: EDITH-Automater Team
Date: September 30, 2025
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

class SimpleReportGenerator:
    """
    Simple class for generating HTML reports from digital evidence collection forms
    """
    
    def __init__(self):
        """Initialize the Report Generator"""
        # Set up paths
        self.base_path = Path("e:/Github-adhi982/Edith_t-Automater")
        self.questions_file = self.base_path / "evidence" / "Results" / "Questions" / "questions.txt"
        self.html_templates_dir = self.base_path / "reports" / "Reports html"
        self.output_dir = self.base_path / "evidence" / "Final_Reports"
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.setup_logging()
        
        # Initialize data storage
        self.form_data = {}
        
        # Template mapping
        self.html_templates = [
            "chain_of_custody.html",
            "digital_evidence_form.html", 
            "email_digital_evidence_form.html",
            "form_65B.html",
            "job_form.html",
            "master_copy.html"
        ]
        
    def setup_logging(self):
        """Set up logging for the report generator"""
        log_file = self.base_path / "logs" / f"simple_report_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [SimpleReportGen] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def read_questions_file(self) -> Dict[str, str]:
        """
        Read and parse the questions.txt file
        
        Returns:
            dict: Parsed form data
        """
        if not self.questions_file.exists():
            self.logger.error(f"Questions file not found: {self.questions_file}")
            return {}
            
        self.logger.info(f"Reading questions file: {self.questions_file}")
        
        # Try different encodings to handle the file
        encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1252', 'latin1', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                with open(self.questions_file, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            # If all encodings fail, try reading as binary and replace errors
            try:
                with open(self.questions_file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception as e:
                self.logger.error(f"Error reading questions file with any encoding: {str(e)}")
                return {}
        
        try:
            # Parse the content
            data = {}
            lines = content.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line and not line.startswith('=') and line:
                    # Split only on the first colon to handle values with colons
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        # Clean up any encoding artifacts
                        key = key.replace('�', "'")
                        value = value.replace('�', "'")
                        data[key] = value
            
            self.form_data = data
            self.logger.info(f"Successfully parsed {len(data)} fields from questions file")
            
            # Print parsed data for debugging
            print("\nParsed Form Data:")
            print("-" * 50)
            for key, value in data.items():
                print(f"{key}: {value}")
            print("-" * 50)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error parsing questions file: {str(e)}")
            return {}
    
    def populate_html_template(self, template_name: str, template_content: str) -> str:
        """
        Populate HTML template with form data
        
        Args:
            template_name (str): Name of the template file
            template_content (str): Original HTML content
            
        Returns:
            str: Populated HTML content
        """
        self.logger.info(f"Populating template: {template_name}")
        
        populated_content = template_content
        
        # Get the exact examiner key from the data
        examiner_key = "Examiner's Name and Details"
        examiner_value = self.form_data.get(examiner_key, 'N/A')
        
        # Direct field replacements for common fields
        replacements = {
            # Case information
            "Case Name:": f"Case Name: {self.form_data.get('Case Name / No', 'N/A')}",
            "Name of The Authorized Officer:": f"Name of The Authorized Officer: {self.form_data.get('Authorized Officer', 'N/A')}",
            "Name of the Assessee:": f"Name of the Assessee: {self.form_data.get('Name of Assessee / Party', 'N/A')}",
            
            # Examiner information - use exact key from parsed data
            "Examiner's Name and Details : ": f"Examiner's Name and Details : {examiner_value}",
            "Digital Forensic Examiner:": f"Digital Forensic Examiner: {self.form_data.get('Digital Forensic Examiner', 'N/A')}",
            
            # Device information
            "Device Owner / In Possession of:": f"Device Owner / In Possession of: {self.form_data.get('Device Owner / In Possession of', 'N/A')}",
            "Whether Volatile Memory / RAM Memory was collected?": f"Whether Volatile Memory / RAM Memory was collected? {self.form_data.get('Volatile Memory / RAM Collected (Yes/No)', 'N/A')}",
            
            # Drive and device details
            "Make :": f"Make: {self.form_data.get('Device Make', 'N/A')}",
            "Drive Model:": f"Drive Model: {self.form_data.get('Drive Model', 'N/A')}",
            "Drive SN:": f"Drive SN: {self.form_data.get('Drive Serial Number', 'N/A')}",
            "Size:": f"Size: {self.form_data.get('Hard Disk Capacity', 'N/A')}",
            
            # Storage information
            "Storage Master Copy Make/Model/Size/Serial No:": f"Storage Master Copy: {self.form_data.get('Storage Master Copy Make/Model/Size/Serial No', 'N/A')}",
            "Storage Working Copy Make/Model/Size/Serial No:": f"Storage Working Copy: {self.form_data.get('Storage Working Copy Make/Model/Size/Serial No', 'N/A')}",
            
            # Hash information
            "Is Hash Value Calculated (Yes/No):": f"Hash Value Calculated: {self.form_data.get('Is Hash Value Calculated (Yes/No)', 'N/A')}",
            "Algorithm Used (MD5/SHA1/Others):": f"Algorithm Used: {self.form_data.get('Algorithm Used (MD5/SHA1/Others)', 'N/A')}",
            "MD5 Hash Value:": f"MD5 Hash Value: {self.form_data.get('MD5 Hash Value', 'N/A')}",
            "SHA1 Hash Value:": f"SHA1 Hash Value: {self.form_data.get('SHA1 Hash Value', 'N/A')}",
            
            # Email information
            "Email Service Provider:": f"Email Service Provider: {self.form_data.get('Email Service Provider', 'N/A')}",
            "Email ID:": f"Email ID: {self.form_data.get('Email ID', 'N/A')}",
            "Software Used to Backup Email:": f"Software Used to Backup Email: {self.form_data.get('Software Used to Backup Email', 'N/A')}",
            "Is Email Data Encrypted (Yes/No):": f"Email Data Encrypted: {self.form_data.get('Is Email Data Encrypted (Yes/No)', 'N/A')}",
            "Email Data Handling (Previewing/Imaging/Backup):": f"Email Data Handling: {self.form_data.get('Email Data Handling (Previewing/Imaging/Backup)', 'N/A')}",
            
            # Witness information
            "Witness Name:": f"Witness Name: {self.form_data.get('Witness Name', 'N/A')}",
            "Witness Father's Name:": f"Witness Father's Name: {self.form_data.get('Witness Father\'s Name', 'N/A')}",
            
            # Working hours and dates
            "Working Hours:": f"Working Hours: {self.form_data.get('Working Hours', 'N/A')}",
            "Search Date:": f"Search Date: {self.form_data.get('Search Date', 'N/A')}",
            "Hard Disk Capacity:": f"Hard Disk Capacity: {self.form_data.get('Hard Disk Capacity', 'N/A')}",
            "No. of HDD Used:": f"No. of HDD Used: {self.form_data.get('No. of HDD Used', 'N/A')}",
            "No. of HDD provided by Lab Systems (I) Pvt. Ltd.:": f"No. of HDD provided by Lab Systems: {self.form_data.get('No. of HDD provided by Lab Systems (I) Pvt. Ltd.', 'N/A')}",
            "No. of HDD provided by Income Tax Department:": f"No. of HDD provided by Income Tax Department: {self.form_data.get('No. of HDD provided by Income Tax Department', 'N/A')}",
            
            # Imaging software
            "Imaging Software / Version:": f"Imaging Software / Version: {self.form_data.get('Imaging Software / Version', 'N/A')}",
            
            # Shutdown type
            "Shut Down Type": f"Shut Down Type: {self.form_data.get('Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)', 'N/A')}",
        }
        
        # Apply all text replacements
        for search_text, replacement in replacements.items():
            if search_text in populated_content:
                populated_content = populated_content.replace(search_text, replacement)
        
        # Handle specific table cell replacements that need full cell content replacement
        if 'Examiner\'s Name and Details :' in populated_content:
            populated_content = populated_content.replace(
                'Examiner\'s Name and Details : </td>',
                f'Examiner\'s Name and Details : {examiner_value}</td>'
            )
        
        # Handle Digital Forensic Examiner field
        populated_content = populated_content.replace(
            '<td colspan="4" style="height: 60px;">Digital Forensic Examiner:</td>',
            f'<td colspan="4" style="height: 60px;">Digital Forensic Examiner: {self.form_data.get("Digital Forensic Examiner", "N/A")}</td>'
        )
        
        # Handle empty table cells that need specific data
        # Fill empty cells after specific labels
        
        # Handle "Make :" field
        populated_content = populated_content.replace(
            "<td>Make :</td>",
            f"<td>Make: {self.form_data.get('Device Make', 'N/A')}</td>"
        )
        
        # Handle "Drive Model:" field  
        populated_content = populated_content.replace(
            "<td colspan=\"2\">Drive Model:</td>",
            f"<td colspan=\"2\">Drive Model: {self.form_data.get('Drive Model', 'N/A')}</td>"
        )
        
        # Handle "Drive SN:" field
        populated_content = populated_content.replace(
            "<td>Drive SN:</td>",
            f"<td>Drive SN: {self.form_data.get('Drive Serial Number', 'N/A')}</td>"
        )
        
        # Handle "Size:" field using Hard Disk Capacity
        populated_content = populated_content.replace(
            "<td colspan=\"2\">Size:</td>",
            f"<td colspan=\"2\">Size: {self.form_data.get('Hard Disk Capacity', 'N/A')}</td>"
        )
        
        # Handle "If switched On, What is visible on screen?" field
        if "Device Status at Seizure (On/Off/Sleep)" in self.form_data:
            status = self.form_data["Device Status at Seizure (On/Off/Sleep)"]
            if "on" in status.lower():
                screen_info = self.form_data.get("Screen Visible (if ON)", "Screen information not provided")
                populated_content = populated_content.replace(
                    '<td colspan="3" style="border-top: none;"></td>',
                    f'<td colspan="3" style="border-top: none;">{screen_info}</td>'
                )
        
        # Handle shutdown type radio buttons
        if "Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)" in self.form_data:
            shutdown_type = self.form_data["Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)"].lower()
            if "normal" in shutdown_type:
                populated_content = populated_content.replace(
                    'id="normal" name="shutdown" value="normal"',
                    'id="normal" name="shutdown" value="normal" checked'
                )
            elif "power" in shutdown_type or "pulled" in shutdown_type:
                populated_content = populated_content.replace(
                    'id="power-pulled" name="shutdown" value="power-pulled"',
                    'id="power-pulled" name="shutdown" value="power-pulled" checked'
                )
            elif "battery" in shutdown_type:
                populated_content = populated_content.replace(
                    'id="battery-removed" name="shutdown" value="battery-removed"',
                    'id="battery-removed" name="shutdown" value="battery-removed" checked'
                )
        
        # Handle date/time splitting for start and end dates
        if "Start Date & Time" in self.form_data:
            datetime_str = self.form_data["Start Date & Time"]
            try:
                # Try to parse and split the datetime
                parts = datetime_str.split()
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = " ".join(parts[1:])
                    
                    populated_content = populated_content.replace("Start Date:", f"Start Date: {date_part}")
                    populated_content = populated_content.replace("Start Time:", f"Start Time: {time_part}")
                else:
                    populated_content = populated_content.replace("Start Date:", f"Start Date: {datetime_str}")
            except:
                populated_content = populated_content.replace("Start Date:", f"Start Date: {datetime_str}")
                
        if "End Date & Time" in self.form_data:
            datetime_str = self.form_data["End Date & Time"]
            try:
                parts = datetime_str.split()
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = " ".join(parts[1:])
                    
                    populated_content = populated_content.replace("End Date:", f"End Date: {date_part}")
                    populated_content = populated_content.replace("End Time:", f"End Time: {time_part}")
                else:
                    populated_content = populated_content.replace("End Date:", f"End Date: {datetime_str}")
            except:
                populated_content = populated_content.replace("End Date:", f"End Date: {datetime_str}")
        
        # Handle premise address
        if "Premise Address" in self.form_data:
            premise_addr = self.form_data["Premise Address"]
            populated_content = populated_content.replace("Premise Address:", f"Premise Address: {premise_addr}")
        
        # Handle radio button selections for device type
        if template_name == "digital_evidence_form.html" and "Device Type (Laptop/Desktop/Server/Other)" in self.form_data:
            device_type = self.form_data["Device Type (Laptop/Desktop/Server/Other)"].lower()
            if "laptop" in device_type:
                populated_content = populated_content.replace(
                    'id="laptop" name="device" value="laptop"',
                    'id="laptop" name="device" value="laptop" checked'
                )
            elif "desktop" in device_type:
                populated_content = populated_content.replace(
                    'id="desktop" name="device" value="desktop"',
                    'id="desktop" name="device" value="desktop" checked'
                )
            elif "server" in device_type:
                populated_content = populated_content.replace(
                    'id="server" name="device" value="server"',
                    'id="server" name="device" value="server" checked'
                )
        
        # Handle power state radio buttons
        if template_name == "digital_evidence_form.html" and "Device Status at Seizure (On/Off/Sleep)" in self.form_data:
            status = self.form_data["Device Status at Seizure (On/Off/Sleep)"].lower()
            if "on" in status:
                populated_content = populated_content.replace(
                    'id="on" name="power" value="on"',
                    'id="on" name="power" value="on" checked'
                )
            elif "off" in status:
                populated_content = populated_content.replace(
                    'id="off" name="power" value="off"',
                    'id="off" name="power" value="off" checked'
                )
            elif "sleep" in status:
                populated_content = populated_content.replace(
                    'id="hibernate" name="power" value="hibernate"',
                    'id="hibernate" name="power" value="hibernate" checked'
                )
        
        # Special handling for Chain of Custody form
        if template_name == "chain_of_custody.html":
            # Replace case name field
            populated_content = populated_content.replace(
                'Name of the Case:</td>',
                f'Name of the Case: {self.form_data.get("Case Name / No", "N/A")}</td>'
            )
            
            # Replace authorized officer field
            populated_content = populated_content.replace(
                'Authorized Officer:</td>',
                f'Authorized Officer: {self.form_data.get("Authorized Officer", "N/A")}</td>'
            )
            
            # Replace start date and time
            populated_content = populated_content.replace(
                'Start Date and Time of Search:</td>',
                f'Start Date and Time of Search: {self.form_data.get("Start Date & Time", "N/A")}</td>'
            )
            
            # Fill in the case description
            case_name = self.form_data.get("Case Name / No", "_________________")
            search_date = self.form_data.get("Search Date", "________________")
            populated_content = populated_content.replace(
                'During the search in the case of _________________ on <!-- real date for report --> the',
                f'During the search in the case of {case_name} on {search_date} the'
            )
            
            # Parse storage details for master and working copies
            master_copy = self.form_data.get("Storage Master Copy Make/Model/Size/Serial No", "N/A")
            working_copy = self.form_data.get("Storage Working Copy Make/Model/Size/Serial No", "N/A")
            
            # Split master copy details (assuming format: Make/Model/Size/Serial)
            if master_copy != "N/A" and "/" in master_copy:
                master_parts = master_copy.split("/")
                if len(master_parts) >= 4:
                    master_make = master_parts[0] if len(master_parts) > 0 else "N/A"
                    master_model = master_parts[1] if len(master_parts) > 1 else "N/A"
                    master_size = master_parts[2] if len(master_parts) > 2 else "N/A"
                    master_serial = master_parts[3] if len(master_parts) > 3 else "N/A"
                else:
                    master_make = master_model = master_size = master_serial = "N/A"
            else:
                master_make = master_model = master_size = master_serial = "N/A"
            
            # Split working copy details
            if working_copy != "N/A" and "/" in working_copy:
                working_parts = working_copy.split("/")
                if len(working_parts) >= 4:
                    working_make = working_parts[0] if len(working_parts) > 0 else "N/A"
                    working_model = working_parts[1] if len(working_parts) > 1 else "N/A"
                    working_size = working_parts[2] if len(working_parts) > 2 else "N/A"
                    working_serial = working_parts[3] if len(working_parts) > 3 else "N/A"
                else:
                    working_make = working_model = working_size = working_serial = "N/A"
            else:
                working_make = working_model = working_size = working_serial = "N/A"
                
            # Replace storage details using simpler approach
            populated_content = populated_content.replace("Make:<br>", f"Make: {master_make}<br>")
            populated_content = populated_content.replace("Model:<br>", f"Model: {master_model}<br>")
            populated_content = populated_content.replace("Size:<br>", f"Size: {master_size}<br>")
            populated_content = populated_content.replace("Serial NO:", f"Serial NO: {master_serial}")
            
            # Also replace for working copy (appears twice in the document)
            # We need to be more specific for working copy
            working_section = f'''<td colspan="2" style="font-weight: bold; line-height: 1.8;">
                    Make: {working_make}<br>
                    Model: {working_model}<br>
                    Size: {working_size}<br>
                    Serial NO: {working_serial}
                </td>'''
            
            # Find and replace the working copy section specifically
            original_working = '''<td colspan="2" style="font-weight: bold; line-height: 1.8;">
                    Make:<br>
                    Model:<br>
                    Size:<br>
                    Serial NO:
                </td>'''
            
            # Replace second occurrence (working copy)
            if original_working in populated_content:
                # Split by the pattern and rejoin with replacement for second occurrence
                parts = populated_content.split(original_working)
                if len(parts) >= 3:  # First occurrence (master) + middle + second occurrence (working)
                    populated_content = parts[0] + original_working + parts[1] + working_section + "".join(parts[2:])
        
        # Special handling for Digital Evidence Form
        if template_name == "digital_evidence_form.html":
            # Parse storage data for device info section
            master_copy = self.form_data.get("Storage Master Copy Make/Model/Size/Serial No", "N/A")
            
            if master_copy != "N/A" and "/" in master_copy:
                master_parts = master_copy.split("/")
                device_make = master_parts[0] if len(master_parts) > 0 else "N/A"
                device_model = master_parts[1] if len(master_parts) > 1 else "N/A"
                device_size = master_parts[2] if len(master_parts) > 2 else "N/A"
                device_serial = master_parts[3] if len(master_parts) > 3 else "N/A"
            else:
                device_make = device_model = device_size = device_serial = "N/A"
            
            # Fix Device Info section
            populated_content = populated_content.replace("Make: N/A", f"Make: {device_make}")
            populated_content = populated_content.replace("Drive Model: N/A", f"Drive Model: {device_model}")
            populated_content = populated_content.replace("Drive SN: N/A", f"Drive SN: {device_serial}")
            
            # Fix storage details in nested tables on page 2
            # Master Copy section
            populated_content = populated_content.replace(
                '<td style="border: none; width: 25%; text-align: left;">Make:</td>',
                f'<td style="border: none; width: 25%; text-align: left;">Make: {device_make}</td>',
                1  # Replace only first occurrence
            )
            populated_content = populated_content.replace(
                '<td style="border: none; width: 25%; text-align: left;">Model:</td>',
                f'<td style="border: none; width: 25%; text-align: left;">Model: {device_model}</td>',
                1  # Replace only first occurrence
            )
            populated_content = populated_content.replace(
                '<td style="border: none; padding-top: 15px; text-align: left;">Serial No:</td>',
                f'<td style="border: none; padding-top: 15px; text-align: left;">Serial No: {device_serial}</td>',
                1  # Replace only first occurrence
            )
            
            # Working Copy section (second occurrences)
            populated_content = populated_content.replace(
                '<td style="border: none; width: 25%; text-align: left;">Make:</td>',
                f'<td style="border: none; width: 25%; text-align: left;">Make: {device_make}</td>'
            )
            populated_content = populated_content.replace(
                '<td style="border: none; width: 25%; text-align: left;">Model:</td>',
                f'<td style="border: none; width: 25%; text-align: left;">Model: {device_model}</td>'
            )
            populated_content = populated_content.replace(
                '<td style="border: none; padding-top: 15px; text-align: left;">Serial No:</td>',
                f'<td style="border: none; padding-top: 15px; text-align: left;">Serial No: {device_serial}</td>'
            )
            
            # Handle hash value radio buttons
            hash_calculated = self.form_data.get("Is Hash Value Calculated (Yes/No)", "").lower()
            if "yes" in hash_calculated or "y" in hash_calculated:
                populated_content = populated_content.replace(
                    'id="yes-hash" name="hash" value="yes"',
                    'id="yes-hash" name="hash" value="yes" checked'
                )
            
            # Handle algorithm selection (if we have algorithm data)
            algorithm = self.form_data.get("Algorithm Used (MD5/SHA1/Others)", "").lower()
            if "md5" in algorithm:
                populated_content = populated_content.replace(
                    'id="md5" name="algorithm" value="md5"',
                    'id="md5" name="algorithm" value="md5" checked'
                )
            if "sha1" in algorithm:
                populated_content = populated_content.replace(
                    'id="sha1" name="algorithm" value="sha1"',
                    'id="sha1" name="algorithm" value="sha1" checked'
                )
        
        # Special handling for Form 65B
        if template_name == "form_65B.html":
            # Fill blank-line spans with actual data
            assessee_name = self.form_data.get("Name of Assessee / Party", "___________")
            witness_father = self.form_data.get("Witness Father's Name", "___________")
            premise_address = self.form_data.get("Premise Address", "___________")
            case_name = self.form_data.get("Case Name / No", "___________")
            
            # Replace blank lines in order they appear
            populated_content = populated_content.replace('<span class="blank-line"></span>', assessee_name, 1)
            populated_content = populated_content.replace('<span class="blank-line"></span>', witness_father, 1)  
            populated_content = populated_content.replace('<span class="blank-line"></span>', premise_address, 1)
            populated_content = populated_content.replace('<span class="blank-line"></span>', case_name, 1)
        
        # Special handling for Job Form
        if template_name == "job_form.html":
            # Fill working hours in the table
            working_hours = self.form_data.get("Working Hours", "N/A")
            populated_content = populated_content.replace("Working Hours</td>", f"Working Hours: {working_hours}</td>")
            
            # Fill examiner information
            examiner_info = self.form_data.get("Digital Forensic Examiner", "N/A")
            populated_content = populated_content.replace("Digital Forensic Examiner:", f"Digital Forensic Examiner: {examiner_info}")
        
        # Special handling for Master Copy
        if template_name == "master_copy.html":
            # Fill HDD Serial Number
            master_copy = self.form_data.get("Storage Master Copy Make/Model/Size/Serial No", "N/A")
            if master_copy != "N/A" and "/" in master_copy:
                parts = master_copy.split("/")
                hdd_serial = parts[3] if len(parts) > 3 else "N/A"
            else:
                hdd_serial = "N/A"
            
            populated_content = populated_content.replace("HDD Serial No.", hdd_serial)
            
            # Fill other missing fields
            authorized_officer = self.form_data.get("Authorized Officer", "N/A")
            populated_content = populated_content.replace("Authorized Officer:", f"Authorized Officer: {authorized_officer}")
        
        return populated_content
    
    def generate_all_reports(self) -> List[str]:
        """
        Generate all HTML reports from templates
        
        Returns:
            list: List of generated HTML file paths
        """
        self.logger.info("Starting HTML report generation process...")
        
        # Read form data
        if not self.read_questions_file():
            self.logger.error("Failed to read questions file. Cannot proceed.")
            return []
        
        generated_htmls = []
        
        # Process each HTML template
        for template_name in self.html_templates:
            template_path = self.html_templates_dir / template_name
            
            if not template_path.exists():
                self.logger.warning(f"Template not found: {template_path}")
                continue
                
            try:
                # Read HTML template
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Populate template with data
                populated_html = self.populate_html_template(template_name, html_content)
                
                # Generate HTML filename
                html_filename = f"FILLED_{template_name.replace('.html', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                html_path = self.output_dir / html_filename
                
                # Save populated HTML
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(populated_html)
                
                generated_htmls.append(str(html_path))
                self.logger.info(f"Generated: {html_filename}")
                    
            except Exception as e:
                self.logger.error(f"Error processing template {template_name}: {str(e)}")
                continue
        
        return generated_htmls
    
    def print_summary(self, generated_htmls: List[str]):
        """
        Print generation summary
        
        Args:
            generated_htmls (list): List of generated HTML paths
        """
        print("\n" + "="*80)
        print("EDITH-Automater HTML Report Generation Summary")
        print("="*80)
        print(f"Output Directory: {self.output_dir}")
        print(f"Templates Processed: {len(self.html_templates)}")
        print(f"HTML Files Generated: {len(generated_htmls)}")
        print()
        
        if generated_htmls:
            print("Generated HTML Reports:")
            for html_path in generated_htmls:
                filename = Path(html_path).name
                print(f"  Generated: {filename}")
            print()
            print("📌 To convert to PDF:")
            print("   1. Open each HTML file in a web browser")
            print("   2. Use 'Print' → 'Save as PDF' option")
            print("   3. Or use online HTML-to-PDF converters")
        else:
            print("No HTML reports were generated.")
            
        print("\n" + "="*80)


def main():
    """Main function to run the report generator"""
    print("\nEDITH-Automater HTML Report Generator")
    print("="*50)
    
    # Initialize report generator
    generator = SimpleReportGenerator()
    
    # Generate reports
    generated_htmls = generator.generate_all_reports()
    
    # Print summary
    generator.print_summary(generated_htmls)
    
    if generated_htmls:
        print("🎉 HTML report generation completed successfully!")
    else:
        print("⚠️ HTML report generation completed with errors.")


if __name__ == "__main__":
    main()