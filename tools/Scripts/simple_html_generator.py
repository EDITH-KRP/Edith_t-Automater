import os
import glob
import re
import time
from datetime import datetime

def read_questions_file():
    """Read the most recent questions.txt file"""
    # Look for questions files in the new Results/CASE_*/Questions directory structure
    pattern = os.path.join('..', '..', 'Results', 'CASE_*', 'Questions', '*.txt')
    question_files = glob.glob(pattern)
    
    if not question_files:
        print("No question files found in Results directory. Looking in old evidence directory...")
        # Fallback to old structure for backward compatibility
        pattern = os.path.join('..', '..', 'evidence', 'Results', 'Questions', '*.txt')
        question_files = glob.glob(pattern)
        
    if not question_files:
        print("No question files found in evidence directory either...")
        pattern = os.path.join('..', '..', 'evidence', '*.txt')
        question_files = glob.glob(pattern)
        
    if not question_files:
        print("No question files found. Please run q_script.py first.")
        return None
    
    # Sort by modification time (newest first)
    question_files.sort(key=os.path.getmtime, reverse=True)
    
    # Read the most recent file
    with open(question_files[0], 'r', errors='ignore') as f:
        content = f.read()
    
    print(f"Using data from: {question_files[0]}")
    return content, question_files[0]

def get_output_directory(questions_file_path, timestamp):
    """Determine the correct output directory based on the questions file path"""
    # Check if the questions file is in the new Results/CASE_* structure
    if 'Results' in questions_file_path and 'CASE_' in questions_file_path:
        # Extract the case folder from the path
        # Path format: Results/CASE_20251007_160412/Questions/filename.txt
        parts = questions_file_path.split(os.sep)
        for i, part in enumerate(parts):
            if part.startswith('CASE_'):
                case_folder = part
                # Create output path in the same case folder
                output_dir = os.path.join('..', '..', 'Results', case_folder, 'Final_Reports')
                break
        else:
            # Fallback if case folder not found
            output_dir = os.path.join('..', '..', 'evidence', 'Final_Reports')
    else:
        # Use old structure for backward compatibility
        output_dir = os.path.join('..', '..', 'evidence', 'Final_Reports')
    
    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def parse_questions_data(content):
    """Parse the questions.txt file content and return a dictionary"""
    data = {}
    lines = content.strip().split('\n')
    
    # Find the start of actual questions data (skip headers and metadata)
    start_idx = 0
    for i, line in enumerate(lines):
        # Skip header lines, separator lines, and metadata
        if ('=' in line and len(line.strip()) > 20) or line.strip() == '' or 'Case ID:' in line or 'Generated:' in line or 'Case Directory:' in line:
            continue
        # Stop at METADATA section
        if 'METADATA' in line:
            break
        # This is actual data
        if ':' in line and not any(x in line for x in ['Case ID:', 'Generated:', 'Case Directory:']):
            start_idx = i
            break
    
    # Parse the actual data lines
    for i in range(start_idx, len(lines)):
        line = lines[i].strip()
        
        # Stop at METADATA section
        if 'METADATA' in line or '============================================================' in line:
            break
            
        if ':' in line and line.strip():
            # Split only on the first colon to handle values that contain colons
            key, value = line.split(':', 1)
            
            # Clean up key by removing example text - handle cases where closing ) might be missing
            clean_key = re.sub(r'\s*\(Example[^)]*\)?', '', key.strip())
            # Also handle cases where the key ends with just "(Example"
            clean_key = re.sub(r'\s*\(Example.*$', '', clean_key)
            
            # Clean up value - strip whitespace and remove any remaining closing parenthesis from example
            clean_value = value.strip()
            # If value starts with closing parenthesis from example, remove it and everything before the actual value
            if '):' in clean_value:
                # Find the actual value after the example closing
                clean_value = clean_value.split('):')[-1].strip()
            
            # Skip empty values and metadata
            if clean_value and not any(x in clean_key for x in ['Case ID', 'Generated', 'Case Directory', 'File created', 'Script version']):
                data[clean_key] = clean_value
    
    return data

def extract_date_time(datetime_str):
    """Extract date and time from a combined string"""
    # Clean up any example text
    datetime_str = re.sub(r'\(Example:.*?\)', '', datetime_str).strip()
    
    # Common patterns like '12-09-2025 2:00PM' or '23/10/2025 2:30'
    match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(\d{1,2}:\d{2}(?:AM|PM)?)', datetime_str)
    if match:
        return match.group(1), match.group(2)
    
    # Try to find separate date and time portions - support both / and - separators
    date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', datetime_str)
    time_match = re.search(r'(\d{1,2}:\d{2}(?:AM|PM)?)', datetime_str)
    
    date = date_match.group(1) if date_match else ""
    time = time_match.group(1) if time_match else ""
    
    if date and time:
        return date, time
    elif date:
        return date, ""
    
    return datetime_str, ""

def extract_device_info(storage_str):
    """Extract device info parts from a string like 'Make/Model/Size/SerialNo'"""
    parts = storage_str.split('/')
    
    make = parts[0] if len(parts) > 0 else ""
    model = parts[1] if len(parts) > 1 else ""
    size = parts[2] if len(parts) > 2 else ""
    serial_no = parts[3] if len(parts) > 3 else ""
    
    return make, model, size, serial_no

def generate_digital_evidence_form(data, timestamp, output_dir):
    """Generate digital evidence form HTML from the parsed data"""
    template_path = os.path.join('..', '..', 'reports', 'Reports html', 'digital_evidence_form.html')
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Extract all the needed data
    authorized_officer = data.get("Authorized Officer", "")
    case_name = data.get("Case Name / No", "")
    assessee_name = data.get("Name of Assessee / Party", "")
    premise_address = data.get("Premise Address", "")
    examiner_name = data.get("Examiner's Name and Details", "")
    forensic_examiner = data.get("Digital Forensic Examiner", "")
    
    # Handle dates and times
    start_date, start_time = extract_date_time(data.get("Start Date & Time", ""))
    end_date, end_time = extract_date_time(data.get("End Date & Time", ""))
    
    # Device information
    storage_master = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
    make, model, size, serial_no = extract_device_info(storage_master)
    
    # RAM Collection
    ram_collected = data.get("Volatile Memory / RAM Collected (Yes/No)", "")
    shutdown_type = data.get("Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)", "").lower()
    
    # Basic information
    html_content = html_content.replace('<td colspan="4">Name of The Authorized Officer:</td>', 
                                      f'<td colspan="4">Name of The Authorized Officer: {authorized_officer}</td>')
    html_content = html_content.replace('<td colspan="4">Case Name:</td>', 
                                      f'<td colspan="4">Case Name: {case_name}</td>')
    html_content = html_content.replace('<td colspan="4">Name of the Assessee:</td>', 
                                      f'<td colspan="4">Name of the Assessee: {assessee_name}</td>')
    html_content = html_content.replace('<td colspan="2" rowspan="2" style="width: 50%; vertical-align: top;">Premise Address:</td>', 
                                      f'<td colspan="2" rowspan="2" style="width: 50%; vertical-align: top;">Premise Address: {premise_address}</td>')
    html_content = html_content.replace('<td colspan="4">Examiner\'s Name and Details : </td>', 
                                      f'<td colspan="4">Examiner\'s Name and Details : {examiner_name}</td>')

    # Date and time information - use precise tag replacement
    html_content = html_content.replace('<td style="width: 25%;">Start Date:</td>', 
                                      f'<td style="width: 25%;">Start Date: {start_date}</td>')
    html_content = html_content.replace('<td style="width: 25%;">Start Time:</td>', 
                                      f'<td style="width: 25%;">Start Time: {start_time}</td>')
    html_content = html_content.replace('<td style="width: 25%;">End Date:</td>', 
                                      f'<td style="width: 25%;">End Date: {end_date}</td>')
    html_content = html_content.replace('<td style="width: 25%;">End Time:</td>', 
                                      f'<td style="width: 25%;">End Time: {end_time}</td>')
    
    # For templates that already have spaces in the tags
    html_content = html_content.replace('<td style="width: 25%;">Start Date: </td>', 
                                      f'<td style="width: 25%;">Start Date: {start_date}</td>')
    html_content = html_content.replace('<td style="width: 25%;">Start Time: </td>', 
                                      f'<td style="width: 25%;">Start Time: {start_time}</td>')
    html_content = html_content.replace('<td style="width: 25%;">End Date: </td>', 
                                      f'<td style="width: 25%;">End Date: {end_date}</td>')
    html_content = html_content.replace('<td style="width: 25%;">End Time: </td>', 
                                      f'<td style="width: 25%;">End Time: {end_time}</td>')

    # Device Information
    html_content = html_content.replace('<td>Make :</td>', f'<td>Make: {make}</td>')
    html_content = html_content.replace('<td colspan="2">Drive Model:</td>', f'<td colspan="2">Drive Model: {model}</td>')
    html_content = html_content.replace('<td>Drive SN:</td>', f'<td>Drive SN: {serial_no}</td>')
    html_content = html_content.replace('<td colspan="2">Size:</td>', f'<td colspan="2">Size: {size}</td>')
    
    # RAM Collection
    html_content = html_content.replace('<td colspan="4">Whether Volatile Memory / RAM Memory was collected : </td>', 
                                     f'<td colspan="4">Whether Volatile Memory / RAM Memory was collected : {ram_collected}</td>')
    
    # Shutdown Type
    html_content = html_content.replace('<td class="row-header">Shut Down Type</td>', 
                                     f'<td class="row-header">Shut Down Type: {shutdown_type}</td>')
    
    # Device Type - Handle radio buttons
    device_type = data.get("Device Type (Laptop/Desktop/Server/Other)", "").lower()
    if "laptop" in device_type:
        html_content = html_content.replace('id="laptop" name="device" value="laptop">', 
                                         'id="laptop" name="device" value="laptop" checked>')
    elif "desktop" in device_type:
        html_content = html_content.replace('id="desktop" name="device" value="desktop">', 
                                         'id="desktop" name="device" value="desktop" checked>')
    elif "server" in device_type:
        html_content = html_content.replace('id="server" name="device" value="server">', 
                                         'id="server" name="device" value="server" checked>')
    elif "file" in device_type or "folder" in device_type:
        html_content = html_content.replace('id="file-folder" name="device" value="file-folder">', 
                                         'id="file-folder" name="device" value="file-folder" checked>')
    elif "other" in device_type:
        html_content = html_content.replace('id="others" name="device" value="others">', 
                                         'id="others" name="device" value="others" checked>')

    # Device Status - Handle radio buttons
    device_status = data.get("Device Status at Seizure (On/Off/Sleep)", "").lower()
    if "on" in device_status:
        html_content = html_content.replace('id="on" name="power" value="on">', 
                                         'id="on" name="power" value="on" checked>')
    elif "off" in device_status:
        html_content = html_content.replace('id="off" name="power" value="off">', 
                                         'id="off" name="power" value="off" checked>')
    elif "sleep" in device_status or "hibernate" in device_status:
        html_content = html_content.replace('id="hibernate" name="power" value="hibernate">', 
                                         'id="hibernate" name="power" value="hibernate" checked>')
    
    # Screen visible information
    screen_visible = data.get("Screen Visible (if ON) - What was visible on the screen?", "")
    html_content = html_content.replace('<td colspan="3" style="border-top: none;"></td>', 
                                     f'<td colspan="3" style="border-top: none;">{screen_visible}</td>')
    
    # Shutdown Type radio buttons
    if "normal" in shutdown_type:
        html_content = html_content.replace('id="normal" name="shutdown" value="normal">', 
                                         'id="normal" name="shutdown" value="normal" checked>')
    elif "power" in shutdown_type or "pull" in shutdown_type:
        html_content = html_content.replace('id="power-plug" name="shutdown" value="power-plug">', 
                                         'id="power-plug" name="shutdown" value="power-plug" checked>')
    elif "battery" in shutdown_type:
        html_content = html_content.replace('id="battery" name="shutdown" value="battery">', 
                                         'id="battery" name="shutdown" value="battery" checked>')
    elif "n/a" in shutdown_type or "na" in shutdown_type:
        html_content = html_content.replace('id="na" name="shutdown" value="na">', 
                                         'id="na" name="shutdown" value="na" checked>')
    
    # Media Encryption - Handle radio buttons
    media_encrypted = data.get("Is the suspected media encrypted (Yes/No)", "").lower()
    if "yes" in media_encrypted:
        html_content = html_content.replace('id="yes-encrypt" name="encrypted" value="yes">', 
                                         'id="yes-encrypt" name="encrypted" value="yes" checked>')
        encryption_type = data.get("Type of encryption Software used", "")
        html_content = html_content.replace('<td colspan="3">Type of encryption Software used:</td>', 
                                         f'<td colspan="3">Type of encryption Software used: {encryption_type}</td>')
    elif "no" in media_encrypted:
        html_content = html_content.replace('id="no-encrypt" name="encrypted" value="no">', 
                                         'id="no-encrypt" name="encrypted" value="no" checked>')
    
    # Hard Disk Handling - Handle radio buttons
    disk_handling = data.get("Hard Disk Handling (Seizure/Forensic Previewing/Imaging/Backup)", "").lower()
    if "seizure" in disk_handling:
        html_content = html_content.replace('id="seizure" name="handling" value="seizure">', 
                                         'id="seizure" name="handling" value="seizure" checked>')
    elif "preview" in disk_handling:
        html_content = html_content.replace('id="previewing" name="handling" value="previewing">', 
                                         'id="previewing" name="handling" value="previewing" checked>')
    elif "imaging" in disk_handling:
        html_content = html_content.replace('id="imaging" name="handling" value="imaging">', 
                                         'id="imaging" name="handling" value="imaging" checked>')
    elif "backup" in disk_handling:
        html_content = html_content.replace('id="backup" name="handling" value="backup">', 
                                         'id="backup" name="handling" value="backup" checked>')
    
    # Imaging Software Details
    imaging_software = data.get("Detail of imaging software / Version to be given", "")
    html_content = html_content.replace('<td colspan="4">Detail of imaging software / Version to be given:</td>', 
                                     f'<td colspan="4">Detail of imaging software / Version to be given: {imaging_software}</td>')
    
    # Hash Calculation - Handle radio buttons and algorithm
    hash_calc = data.get("Is Hash Value Calculated (Yes/No)", "").lower()
    if "yes" in hash_calc:
        html_content = html_content.replace('id="yes-hash" name="hash" value="yes">', 
                                         'id="yes-hash" name="hash" value="yes" checked>')
        
        # Algorithm selection
        algorithm = data.get("Algorithm Used (MD5/SHA1/Others)", "").lower()
        if "md5" in algorithm:
            html_content = html_content.replace('id="md5" name="algorithm" value="md5">', 
                                             'id="md5" name="algorithm" value="md5" checked>')
        elif "sha1" in algorithm:
            html_content = html_content.replace('id="sha1" name="algorithm" value="sha1">', 
                                             'id="sha1" name="algorithm" value="sha1" checked>')
        elif "other" in algorithm:
            html_content = html_content.replace('id="others-alg" name="algorithm" value="others">', 
                                             'id="others-alg" name="algorithm" value="others" checked>')
    elif "no" in hash_calc:
        html_content = html_content.replace('id="no-hash" name="hash" value="no">', 
                                         'id="no-hash" name="hash" value="no" checked>')
    
    # Hash Values - only populate if available in data
    md5_hash = data.get("MD5 hash value", "")
    sha1_hash = data.get("SHA1 hash value", "")
    if md5_hash:
        html_content = html_content.replace('<td colspan="4">MD5 hash value :</td>', 
                                         f'<td colspan="4">MD5 hash value : {md5_hash}</td>')
    if sha1_hash:
        html_content = html_content.replace('<td colspan="4">SHA1 hash value :</td>', 
                                         f'<td colspan="4">SHA1 hash value : {sha1_hash}</td>')
    
    # Witness Signature - Handle radio buttons
    witness_signature = data.get("Is Witness Signature Taken (Yes/No)", "").lower()
    if "yes" in witness_signature:
        html_content = html_content.replace('id="yes-witness" name="witness" value="yes">', 
                                         'id="yes-witness" name="witness" value="yes" checked>')
    elif "no" in witness_signature:
        html_content = html_content.replace('id="no-witness" name="witness" value="no">', 
                                         'id="no-witness" name="witness" value="no" checked>')
    
    # Witness Information
    witness_name = data.get("Witness Name", "")
    witness_father = data.get("Witness Father's Name", "")
    html_content = html_content.replace('<td colspan="2" style="height: 60px;">Witness 1:</td>', 
                                     f'<td colspan="2" style="height: 60px;">Witness 1: {witness_name}</td>')
    html_content = html_content.replace('<td colspan="2">Witness 2:</td>', 
                                     f'<td colspan="2">Witness 2: {witness_father}</td>')
    
    # Hard disk replacement radio button - only set if we have data about it
    disk_replaced = data.get("Is the hard disk replaced back", "").lower()
    replacement_date = ""
    replacement_time = ""
    
    if "yes" in disk_replaced:
        html_content = html_content.replace('id="yes-replaced" name="replaced" value="yes">', 
                                         'id="yes-replaced" name="replaced" value="yes" checked>')
        # Only populate date/time if we have specific replacement data
        replacement_date = data.get("Hard disk replacement date", "")
        replacement_time = data.get("Hard disk replacement time", "")
    elif "no" in disk_replaced:
        html_content = html_content.replace('id="no-replaced" name="replaced" value="no">', 
                                         'id="no-replaced" name="replaced" value="no" checked>')
    elif "na" in disk_replaced or "n/a" in disk_replaced:
        html_content = html_content.replace('id="na-replaced" name="replaced" value="na">', 
                                         'id="na-replaced" name="replaced" value="na" checked>')
    
    # Hard disk replacement date and time - only populate if we have actual replacement data
    html_content = html_content.replace('<td>Date:</td>', f'<td>Date: {replacement_date}</td>')
    html_content = html_content.replace('<td>Time:</td>', f'<td>Time: {replacement_time}</td>')
    
    # Working Copy Details - Extract the working copy details
    storage_working = data.get("Storage Working Copy Make/Model/Size/Serial No", "")
    working_make, working_model, working_size, working_serial = extract_device_info(storage_working)
    
    # If working copy data is empty but master copy data exists, use master copy data for working copy
    if not working_make and make:
        working_make, working_model, working_size, working_serial = make, model, size, serial_no
    
    # Apply both master copy and working copy details
    # Find the working copy header section
    working_copy_header = html_content.find('Working Copy Details:')
    if working_copy_header != -1:
        # Find the first table (Master Copy) after "Working Copy Details:"
        first_table_start = html_content.find('<table style="width: 100%; border: none;"', working_copy_header)
        if first_table_start != -1:
            first_table_end = html_content.find('</table>', first_table_start) + 8
            master_table_section = html_content[first_table_start:first_table_end]
            
            # Replace the master copy values in the first table
            master_table_section = master_table_section.replace('Make:</td>', f'Make: {make}</td>')
            master_table_section = master_table_section.replace('Model:</td>', f'Model: {model}</td>')
            master_table_section = master_table_section.replace('Serial No:</td>', f'Serial No: {serial_no}</td>')
            master_table_section = master_table_section.replace('Size:</td>', f'Size: {size}</td>')
            
            # Replace the original master table with the updated one
            html_content = html_content[:first_table_start] + master_table_section + html_content[first_table_end:]
            
            # Find the second table (Working Copy) after the first table
            # Need to re-find positions after the first replacement
            working_copy_header = html_content.find('Working Copy Details:')
            first_table_start = html_content.find('<table style="width: 100%; border: none;"', working_copy_header)
            first_table_end = html_content.find('</table>', first_table_start) + 8
            working_table_start = html_content.find('<table style="width: 100%; border: none;"', first_table_end)
            if working_table_start != -1:
                working_table_end = html_content.find('</table>', working_table_start) + 8
                working_table_section = html_content[working_table_start:working_table_end]
                
                # Replace the working copy values in this specific table
                working_table_section = working_table_section.replace('Make:</td>', f'Make: {working_make}</td>')
                working_table_section = working_table_section.replace('Model:</td>', f'Model: {working_model}</td>')
                working_table_section = working_table_section.replace('Serial No:</td>', f'Serial No: {working_serial}</td>')
                working_table_section = working_table_section.replace('Size:</td>', f'Size: {working_size}</td>')
                
                # Replace the original table with the updated one
                html_content = html_content[:working_table_start] + working_table_section + html_content[working_table_end:]
    
    # Digital Forensic Examiner
    html_content = html_content.replace('<td colspan="4" style="height: 60px;">Digital Forensic Examiner:</td>', 
                                     f'<td colspan="4" style="height: 60px;">Digital Forensic Examiner: {forensic_examiner}</td>')
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_digital_evidence_form_{timestamp}.html')
    
    # Save the filled HTML form
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Digital Evidence Form generated successfully: {output_path}")
    return output_path

def generate_chain_of_custody_form(data, timestamp, output_dir):
    """Generate chain of custody form HTML from the parsed data"""
    template_path = os.path.join('..', '..', 'reports', 'Reports html', 'chain_of_custody.html')
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Extract all the needed data
    authorized_officer = data.get("Authorized Officer", "")
    case_name = data.get("Case Name / No", "")
    premise_address = data.get("Premise Address", "")
    
    # Handle start date and time - combine them for this form
    start_date, start_time = extract_date_time(data.get("Start Date & Time", ""))
    start_datetime = f"{start_date} {start_time}" if start_date and start_time else start_date or start_time
    
    # Device information for master copy
    storage_master = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
    master_make, master_model, master_size, master_serial = extract_device_info(storage_master)
    
    # Device information for working copy
    storage_working = data.get("Storage Working Copy Make/Model/Size/Serial No", "")
    working_make, working_model, working_size, working_serial = extract_device_info(storage_working)
    
    # Basic case information
    html_content = html_content.replace('<td colspan="4" style="font-weight: bold;">Name of the Case:</td>', 
                                      f'<td colspan="4" style="font-weight: bold;">Name of the Case: {case_name}</td>')
    html_content = html_content.replace('<td colspan="4" style="font-weight: bold;">Authorized Officer:</td>', 
                                      f'<td colspan="4" style="font-weight: bold;">Authorized Officer: {authorized_officer}</td>')
    
    # Handle search date and time - use regex to find and replace more reliably
    pattern = r'<td style="width: 50%;">Start Date and Time of Search:\s*</td>'
    replacement = f'<td style="width: 50%;">Start Date and Time of Search: {start_datetime}</td>'
    html_content = re.sub(pattern, replacement, html_content)
    
    # Handle premise address
    html_content = html_content.replace('<td style="width: 50%;" colspan="3">Premise Address:</td>', 
                                      f'<td style="width: 50%;" colspan="3">Premise Address: {premise_address}</td>')
    
    # Description - insert case name and date into the description
    html_content = html_content.replace('the case of _________________', 
                                      f'the case of {case_name}')
    html_content = html_content.replace('<!-- real date for report -->', 
                                      f'{start_date}')
    
    # Master Copy Details and Working Copy Details - Use more precise replacement
    # Find the table row that contains both Master Copy and Working Copy sections
    master_working_pattern = r'(<td colspan="2" style="font-weight: bold; line-height: 1\.8;">\s*)(Make:<br>\s*Model:<br>\s*Size:<br>\s*Serial NO:)(\s*</td>\s*<td colspan="2" style="font-weight: bold; line-height: 1\.8;">\s*)(Make:<br>\s*Model:<br>\s*Size:<br>\s*Serial NO:)(\s*</td>)'
    
    master_details = f"Make: {master_make}<br>\n                    Model: {master_model}<br>\n                    Size: {master_size}<br>\n                    Serial NO: {master_serial}"
    working_details = f"Make: {working_make}<br>\n                    Model: {working_model}<br>\n                    Size: {working_size}<br>\n                    Serial NO: {working_serial}"
    
    replacement = f"\\1{master_details}\\3{working_details}\\5"
    html_content = re.sub(master_working_pattern, replacement, html_content)
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_chain_of_custody_{timestamp}.html')
    
    # Save the filled HTML form
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Chain of Custody Form generated successfully: {output_path}")
    return output_path

def generate_form_65B(data, timestamp, output_dir):
    """Generate Form 65B HTML from the parsed data"""
    template_path = os.path.join('..', '..', 'reports', 'Reports html', 'form_65B.html')
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Extract all the needed data
    assessee_name = data.get("Name of Assessee / Party", "")
    case_name = data.get("Case Name / No", "")
    premise_address = data.get("Premise Address", "")
    device_owner = data.get("Device Owner / In Possession of", "")
    device_type = data.get("Device Type (Laptop/Desktop/Server/Other)", "")
    
    # Device information
    storage_master = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
    master_make, master_model, master_size, master_serial = extract_device_info(storage_master)
    
    storage_working = data.get("Storage Working Copy Make/Model/Size/Serial No", "")
    working_make, working_model, working_size, working_serial = extract_device_info(storage_working)
    
    # If working copy data is empty but master copy data exists, use master copy data for working copy
    if not working_make and master_make:
        working_make, working_model, working_size, working_serial = master_make, master_model, master_size, master_serial
    
    # Fill the personal information blanks
    html_content = html_content.replace('<span class="blank-line"></span> S/O <span class="blank-line"></span> residing/ working/ director at <span class="blank-line"></span>', 
                                     f'<span class="blank-line">{assessee_name}</span> S/O <span class="blank-line"></span> residing/ working/ director at <span class="blank-line">{premise_address}</span>')
    
    # Fill the case name in the search proceedings section
    html_content = html_content.replace('in the case of M/s. <span class="blank-line"></span>', 
                                     f'in the case of M/s. <span class="blank-line">{case_name}</span>')
    
    # Fill the device evidence table - first row
    if device_type or master_make or device_owner:
        # Find the first empty table row and populate it
        empty_row_pattern = r'<tr>\s*<td style="height: 50px;"></td>\s*<td></td>\s*<td></td>\s*</tr>'
        device_details = f"{master_make} {master_model} ({master_size})" if master_make else ""
        replacement_row = f'<tr><td style="height: 50px;">{device_type}</td><td>{device_details}</td><td>{device_owner}</td></tr>'
        html_content = re.sub(empty_row_pattern, replacement_row, html_content, count=1)
    
    # Fill Master Copy Details and Working Copy Details using simple string replacement
    # Since the template has consistent structure, we can use direct replacement
    
    # For Master Copy section - replace empty values
    master_section_start = html_content.find('<div class="copy-header">Master Copy Details</div>')
    working_section_start = html_content.find('<div class="copy-header">Working Copy Details</div>')
    
    if master_section_start != -1 and working_section_start != -1:
        # Extract master copy section
        master_section = html_content[master_section_start:working_section_start]
        
        # Replace values in master section (order: Make, Size, Model, Serial No.)
        master_section = master_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{master_make}</div>', 1)
        master_section = master_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{master_size}</div>', 1)
        master_section = master_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{master_model}</div>', 1) 
        master_section = master_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{master_serial}</div>', 1)
        
        # Extract working copy section (from working header to end of the copy-details div)
        # Find the closing </div> of the copy-details section
        copy_details_end = html_content.find('</div>', html_content.find('<div class="content"', working_section_start))
        working_section = html_content[working_section_start:copy_details_end]
        
        # Replace values in working section (order: Make, Size, Model, Serial No.)
        working_section = working_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{working_make}</div>', 1)
        working_section = working_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{working_size}</div>', 1)
        working_section = working_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{working_model}</div>', 1)
        working_section = working_section.replace('<div class="copy-value"></div>', f'<div class="copy-value">{working_serial}</div>', 1)
        
        # Reconstruct the HTML
        html_content = html_content[:master_section_start] + master_section + working_section + html_content[copy_details_end:]
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_form_65B_{timestamp}.html')
    
    # Save the filled HTML form
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Form 65B generated successfully: {output_path}")
    return output_path

def generate_job_form(data, timestamp, output_dir):
    """Generate Job Form HTML from the parsed data"""
    template_path = os.path.join('..', '..', 'reports', 'Reports html', 'job_form.html')
    with open(template_path, 'r') as f:
        html_content = f.read()
    
    # Extract all the needed data
    case_name = data.get("Case Name / No", "")
    authorized_officer = data.get("Authorized Officer", "")
    assessee_name = data.get("Name of Assessee / Party", "")
    premise_address = data.get("Premise Address", "")
    forensic_examiner = data.get("Digital Forensic Examiner", "")
    working_hours = data.get("Working Hours", "")
    
    # Handle dates and times
    start_date, start_time = extract_date_time(data.get("Start Date & Time", ""))
    end_date, end_time = extract_date_time(data.get("End Date & Time", ""))
    
    # Device information
    device_type = data.get("Device Type (Laptop/Desktop/Server/Other)", "")
    device_owner = data.get("Device Owner / In Possession of", "")
    storage_master = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
    make, model, size, serial_no = extract_device_info(storage_master)
    
    # Hard disk handling type
    disk_handling = data.get("Hard Disk Handling (Seizure/Forensic Previewing/Imaging/Backup)", "")
    
    # Hard disk capacity and counts
    hdd_capacity = data.get("Hard Disk Capacity", "")
    hdd_used = data.get("No. of HDD Used", "")
    hdd_lab_systems = data.get("No. of HDD provided by Lab Systems (I) Pvt. Ltd.", "")
    hdd_income_tax = data.get("No. of HDD provided by Income Tax Department", "")
    
    # Basic Information
    html_content = html_content.replace('<td style="width: 25%; font-weight: bold;">Case Name/No</td>\n                <td colspan="3"></td>', 
                                     f'<td style="width: 25%; font-weight: bold;">Case Name/No</td>\n                <td colspan="3">{case_name}</td>')
    
    # Date & Time In/Out
    html_content = html_content.replace('<td style="width: 25%; font-weight: bold;">Date & Time in</td>\n                <td style="width: 25%;"></td>', 
                                     f'<td style="width: 25%; font-weight: bold;">Date & Time in</td>\n                <td style="width: 25%;">{start_date} {start_time}</td>')
    html_content = html_content.replace('<td style="width: 25%; font-weight: bold;">Date & Time Out</td>\n                <td style="width: 25%;"></td>', 
                                     f'<td style="width: 25%; font-weight: bold;">Date & Time Out</td>\n                <td style="width: 25%;">{end_date} {end_time}</td>')
    
    # Authorized Officer
    html_content = html_content.replace('<td style="font-weight: bold;">Authorised Officer</td>\n                <td colspan="3"></td>', 
                                     f'<td style="font-weight: bold;">Authorised Officer</td>\n                <td colspan="3">{authorized_officer}</td>')
    
    # Name of the Party
    html_content = html_content.replace('<td style="font-weight: bold;">Name of the Party</td>\n                <td colspan="3"></td>', 
                                     f'<td style="font-weight: bold;">Name of the Party</td>\n                <td colspan="3">{assessee_name}</td>')
    
    # Premises Address
    html_content = html_content.replace('<td style="font-weight: bold;">Premises Address</td>\n                <td colspan="3"></td>', 
                                     f'<td style="font-weight: bold;">Premises Address</td>\n                <td colspan="3">{premise_address}</td>')
    
    # Forensic Works Performed - Check radio buttons based on selected works
    forensic_works = data.get("Forensic Works Performed", "")
    if forensic_works:
        forensic_works_lower = forensic_works.lower()
        
        # Map the forensic works to radio buttons
        if "data acquisition" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="data_acquisition">', 
                                             '<input type="radio" name="data_acquisition" checked>')
        if "data extraction" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="data_extraction">', 
                                             '<input type="radio" name="data_extraction" checked>')
        if "data analysis" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="data_analysis">', 
                                             '<input type="radio" name="data_analysis" checked>')
        if "data duplication" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="data_duplication">', 
                                             '<input type="radio" name="data_duplication" checked>')
        if "data raw backup" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="data_raw_backup">', 
                                             '<input type="radio" name="data_raw_backup" checked>')
        if "email backup" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="email_backup">', 
                                             '<input type="radio" name="email_backup" checked>')
        if "cloud acquisition" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="cloud_acquisition">', 
                                             '<input type="radio" name="cloud_acquisition" checked>')
        if "other works" in forensic_works_lower:
            html_content = html_content.replace('<input type="radio" name="other_works">', 
                                             '<input type="radio" name="other_works" checked>')
    else:
        # Fallback to disk handling if forensic works not specified
        if disk_handling:
            disk_handling_lower = disk_handling.lower()
            if "imaging" in disk_handling_lower or "acquisition" in disk_handling_lower:
                html_content = html_content.replace('<input type="radio" name="data_acquisition">', 
                                                 '<input type="radio" name="data_acquisition" checked>')
            if "backup" in disk_handling_lower:
                html_content = html_content.replace('<input type="radio" name="data_raw_backup">', 
                                                 '<input type="radio" name="data_raw_backup" checked>')
            if "preview" in disk_handling_lower or "analysis" in disk_handling_lower:
                html_content = html_content.replace('<input type="radio" name="data_analysis">', 
                                                 '<input type="radio" name="data_analysis" checked>')
    
    # Item Details Table - Fill first row with device information
    if device_type or make or device_owner:
        device_details = f"{make} {model} ({size})" if make else ""
        action_taken = disk_handling if disk_handling else ""
        
        # Replace first empty row in Item Details table
        empty_row_pattern = r'<tr>\s*<td style="height: 35px;"></td>\s*<td></td>\s*<td></td>\s*<td></td>\s*</tr>'
        replacement_row = f'<tr><td style="height: 35px;">1</td><td>{device_type}</td><td>{device_details}</td><td>{action_taken}</td></tr>'
        html_content = re.sub(empty_row_pattern, replacement_row, html_content, count=1)
    
    # Hard Disk Capacity Table - Fill based on capacity data
    if hdd_capacity:
        # Extract capacity value and fill the appropriate row
        if "2" in hdd_capacity and "tb" in hdd_capacity.lower():
            # Fill 2TB row with all values
            html_content = html_content.replace(
                '<td style="text-align: center;">2 TB</td>\n                <td></td>\n                <td></td>\n                <td></td>',
                f'<td style="text-align: center;">2 TB</td>\n                <td>{hdd_used}</td>\n                <td>{hdd_lab_systems}</td>\n                <td>{hdd_income_tax}</td>'
            )
        elif "1" in hdd_capacity and "tb" in hdd_capacity.lower():
            # Fill 1TB row with all values
            html_content = html_content.replace(
                '<td style="text-align: center;">1 TB</td>\n                <td></td>\n                <td></td>\n                <td></td>',
                f'<td style="text-align: center;">1 TB</td>\n                <td>{hdd_used}</td>\n                <td>{hdd_lab_systems}</td>\n                <td>{hdd_income_tax}</td>'
            )
        elif "4" in hdd_capacity and "tb" in hdd_capacity.lower():
            # Fill 4TB row with all values
            html_content = html_content.replace(
                '<td style="text-align: center;">4 TB</td>\n                <td></td>\n                <td></td>\n                <td></td>',
                f'<td style="text-align: center;">4 TB</td>\n                <td>{hdd_used}</td>\n                <td>{hdd_lab_systems}</td>\n                <td>{hdd_income_tax}</td>'
            )
    
    # Fill Total No. of Hard Disk Used
    if hdd_used:
        html_content = html_content.replace(
            '<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\n                <td></td>',
            f'<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\n                <td>{hdd_used}</td>'
        )
    
    # Total Hard Disk Used
    if hdd_used:
        html_content = html_content.replace('<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\n                <td></td>', 
                                         f'<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\n                <td>{hdd_used}</td>')
    
    # Working Hours Table - Fill forensic examiner info
    examiner1_name = data.get("Digital Forensic Examiner 1 Name", "") or forensic_examiner
    examiner1_hours = data.get("Digital Forensic Examiner 1 Working Hours", "")
    examiner2_name = data.get("Digital Forensic Examiner 2 Name", "")
    examiner2_hours = data.get("Digital Forensic Examiner 2 Working Hours", "")
    overall_hours = data.get("Overall Working Hours", "") or working_hours
    
    # Fill first examiner
    if examiner1_name:
        html_content = html_content.replace('<td style="text-align: center;">1.</td>\n                <td style="height: 35px;"></td>\n                <td></td>', 
                                         f'<td style="text-align: center;">1.</td>\n                <td style="height: 35px;">{examiner1_name}</td>\n                <td>{examiner1_hours}</td>')
    
    # Fill second examiner if exists
    if examiner2_name:
        html_content = html_content.replace('<td style="text-align: center;">2.</td>\n                <td style="height: 35px;"></td>\n                <td></td>', 
                                         f'<td style="text-align: center;">2.</td>\n                <td style="height: 35px;">{examiner2_name}</td>\n                <td>{examiner2_hours}</td>')
    
    # Fill overall working hours
    if overall_hours:
        html_content = html_content.replace('<td style="text-align: center; font-weight: bold;">Overall Working Hours</td>\n                <td></td>', 
                                         f'<td style="text-align: center; font-weight: bold;">Overall Working Hours</td>\n                <td>{overall_hours}</td>')
    
    # Signature Section - Leave empty for manual completion
    # Lead Forensic Examiner and Authorised Officer signatures will remain blank
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_job_form_{timestamp}.html')
    
    # Save the filled HTML form
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"Job Form generated successfully: {output_path}")
    return output_path

def generate_master_copy(data, timestamp, output_dir):
    """Generate Master Copy HTML from the parsed data"""
    template_path = os.path.join('..', '..', 'reports', 'Reports html', 'master_copy.html')
    
    # Read the template file
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract data from questions
    case_name = data.get("Case Name / No", "")
    premise_address = data.get("Premise Address", "")
    search_date = data.get("Search Date", "") or data.get("Search Date (Example: 12-09-2025)", "")
    # Clean up search date - remove example text
    if "Example:" in search_date:
        search_date = search_date.split(")")[-1].strip()
    elif search_date == "":
        search_date = ""
    
    assessee_name = data.get("Name of Assessee / Party", "")
    device_type = data.get("Device Type (Laptop/Desktop/Server/Other)", "")
    authorized_officer = data.get("Authorized Officer", "")
    witness_name = data.get("Witness Name", "")
    
    # Extract HDD serial number from storage info
    storage_master = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
    make, model, size, serial_no = extract_device_info(storage_master)
    
    # Fill the header with HDD Serial No
    if serial_no:
        html_content = html_content.replace('<div>S/N: HDD Serial No.</div>', 
                                         f'<div>S/N: {serial_no}</div>')
    
    # Fill case information
    if case_name:
        html_content = html_content.replace('<p><strong>Case Name:</strong> <!-- IF Company – Company Name, If House – Main Person Name --></p>', 
                                         f'<p><strong>Case Name:</strong> {case_name}</p>')
    
    if premise_address:
        html_content = html_content.replace('<p><strong>Address:</strong> <!--Complete address of the company or house where the search is taking place.--></p>', 
                                         f'<p><strong>Address:</strong> {premise_address}</p>')
    
    if search_date:
        html_content = html_content.replace('<p><strong>Search Date:</strong> <!--06.10.2021 --></p>', 
                                         f'<p><strong>Search Date:</strong> {search_date}</p>')
    
    # Create device description
    device_description = ""
    if make and model and size:
        device_description = f"This {make} {model} {size} External HDD Contains Below mentioned data."
    elif size:
        device_description = f"This {size} External HDD Contains Below mentioned data."
    else:
        device_description = "This External HDD Contains Below mentioned data."
    
    html_content = html_content.replace('<p><!--This Seagate One Touch 1TB External HDD Contains Below mentioned data. --></p>', 
                                     f'<p>{device_description}</p>')
    
    # Fill items list - Keep empty for manual completion
    # Items will be filled manually during the investigation process
    
    # Clean up all item placeholders to leave them empty
    item_placeholders = [
        '<!-- Assessee_Name_Laptop_01 -->',
        '<!--Assessee_Name_Laptop_02 -->',
        '<!--Assessee_Name_Apple_Mobile -->',
        '<!--Assessee_Name_Samsung_Mobile -->',
        '<!--assessee@gmail.com -->'
    ]
    
    for placeholder in item_placeholders:
        # Replace placeholders with empty content but keep the list structure
        html_content = html_content.replace(f'<li>{placeholder}</li>', '<li></li>')
    
    # Clean up any extra newlines that might be left
    html_content = html_content.replace('\n                \n                \n            </ol>', '\n            </ol>')
    
    # Signature sections remain empty for manual completion as per requirement
    # Assessee, AO, Witness 1, Witness 2 signatures will be filled manually
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_master_copy_{timestamp}.html')
    
    # Save the filled HTML form
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Master Copy generated successfully: {output_path}")
    return output_path

def generate_all_templates(data, timestamp, output_dir):
    """Generate all available templates"""
    templates = [
        ('digital_evidence_form.html', generate_digital_evidence_form),
        ('chain_of_custody.html', generate_chain_of_custody_form),
        ('form_65B.html', generate_form_65B),
        ('job_form.html', generate_job_form),
        ('master_copy.html', generate_master_copy),
        # Add more templates as needed
    ]
    
    generated_files = []
    
    for template_name, generator_func in templates:
        template_path = os.path.join('..', '..', 'reports', 'Reports html', template_name)
        if os.path.exists(template_path):
            try:
                output_path = generator_func(data, timestamp, output_dir)
                generated_files.append(output_path)
            except Exception as e:
                print(f"Error generating {template_name}: {str(e)}")
        else:
            print(f"Template not found: {template_name}")
    
    return generated_files

def main():
    """Main function to generate all forms"""
    # Read the questions file
    result = read_questions_file()
    if not result:
        return
    
    content, questions_file_path = result
    
    # Parse the data
    data = parse_questions_data(content)
    if not data:
        print("Failed to parse data from questions file.")
        return
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get the correct output directory based on the questions file path
    output_dir = get_output_directory(questions_file_path, timestamp)
    
    # Generate all templates
    generated_files = generate_all_templates(data, timestamp, output_dir)
    
    print(f"Form generation complete. Generated {len(generated_files)} files:")
    for file_path in generated_files:
        print(f"  - {os.path.basename(file_path)}")

if __name__ == "__main__":
    main()