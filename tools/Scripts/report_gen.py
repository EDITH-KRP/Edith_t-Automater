import os
import glob
import re
import time
from datetime import datetime

# PDF generation imports
PDF_AVAILABLE = False
PDF_METHOD = None

try:
    from playwright.sync_api import sync_playwright
    PDF_AVAILABLE = True
    PDF_METHOD = "playwright"
    print("[OK] Playwright available for PDF generation")
except ImportError:
    try:
        import weasyprint
        PDF_AVAILABLE = True
        PDF_METHOD = "weasyprint"
        print("[OK] WeasyPrint available for PDF generation")
    except ImportError:
        # Fallback to Windows built-in method
        import subprocess
        import tempfile
        PDF_AVAILABLE = True
        PDF_METHOD = "windows_builtin"
        print("[OK] Using Windows built-in PDF generation")

def convert_html_to_pdf_weasyprint(html_file_path, pdf_file_path):
    """Convert HTML file to PDF using WeasyPrint respecting existing template CSS"""
    try:
        # Read HTML content without modification to preserve template CSS
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Special handling for job_form to ensure it fills the page properly
        is_job_form = "job_form" in os.path.basename(html_file_path).lower()
        
        # For job_form, ensure proper CSS is applied
        if is_job_form and "@page" not in html_content:
            # Add proper @page CSS if not already present
            css_addition = "<style>@page {size: A4; margin: 0;}</style>"
            html_content = html_content.replace("<head>", "<head>" + css_addition)
        
        # Convert to PDF using original HTML content
        html_doc = weasyprint.HTML(string=html_content, base_url=os.path.dirname(html_file_path))
        html_doc.write_pdf(pdf_file_path)
        print(f"[OK] PDF generated: {os.path.basename(pdf_file_path)}")
        return True
    except Exception as e:
        print(f"[ERROR] PDF conversion failed for {os.path.basename(html_file_path)}: {e}")
        return False

def convert_html_to_pdf_playwright(html_file_path, pdf_file_path):
    """Convert HTML to PDF using Playwright respecting existing HTML template CSS"""
    try:
        # Special handling for job_form to ensure it fills the page properly
        is_job_form = "job_form" in os.path.basename(html_file_path).lower()
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            
            # Use device scale factor of 1.5 for better quality and sizing
            # A4 size in points (595.28 x 841.89)
            # For job_form specifically, use larger viewport height to ensure proper vertical fill
            if is_job_form:
                context = browser.new_context(
                    viewport={"width": 1240, "height": 2000},  # Increased height for job form
                    device_scale_factor=1.5
                )
            else:
                context = browser.new_context(
                    viewport={"width": 1240, "height": 1754},
                    device_scale_factor=1.5
                )
            page = context.new_page()
            
            # Load HTML file without modification to preserve template CSS
            page.goto(f"file://{os.path.abspath(html_file_path)}")
            
            # Wait for content to load properly
            page.wait_for_load_state('networkidle')
            
            # PDF settings differ slightly based on the document type
            pdf_settings = {
                "path": pdf_file_path,
                "format": 'A4',
                "print_background": True,
                "prefer_css_page_size": True,  # Use CSS @page settings from HTML
                "display_header_footer": False,
                "width": '210mm',
                "height": '297mm'
            }
            
            # Different scale settings based on document type
            if is_job_form:
                pdf_settings["scale"] = 1.05  # Slightly larger scale for job form to fill page better
            else:
                pdf_settings["scale"] = 1.0  # Normal scale for standard documents
            
            # Different margin settings based on document type
            if is_job_form:
                # For job form, use smaller margins to maximize page usage
                pdf_settings["margin"] = {
                    'top': '0mm',
                    'right': '0mm', 
                    'bottom': '0mm',
                    'left': '0mm'
                }
            else:
                # Standard margins for other documents
                pdf_settings["margin"] = {
                    'top': '0mm',
                    'right': '0mm', 
                    'bottom': '0mm',
                    'left': '0mm'
                }
            
            # Generate PDF with the configured settings
            page.pdf(**pdf_settings)
            
            browser.close()
                
            print(f"[OK] PDF generated: {os.path.basename(pdf_file_path)}")
            return True
    except Exception as e:
        print(f"[ERROR] PDF conversion failed for {os.path.basename(html_file_path)}: {e}")
        return False

def convert_html_to_pdf_windows_builtin(html_file_path, pdf_file_path):
    """Convert HTML to PDF using Windows built-in print to PDF feature via PowerShell"""
    try:
        # PowerShell script to convert HTML to PDF using Internet Explorer and Print to PDF
        ps_script = f'''
$ie = New-Object -ComObject InternetExplorer.Application
$ie.Visible = $false
$ie.Navigate2("{html_file_path}")
while ($ie.Busy -eq $true) {{
    Start-Sleep -Seconds 1
}}
Start-Sleep -Seconds 3
$ie.ExecWB(6, 2, "{pdf_file_path}")
$ie.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ie)
        '''
        
        # Save PowerShell script to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(ps_script)
            ps_file = f.name
        
        try:
            # Execute PowerShell script
            result = subprocess.run([
                'powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', ps_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(pdf_file_path):
                print(f"[OK] PDF generated: {{os.path.basename(pdf_file_path)}}")
                return True
            else:
                print(f"[WARN] Windows PDF generation had issues, trying simple copy as fallback")
                # Simple fallback - copy HTML as text-based PDF substitute
                with open(html_file_path, 'r', encoding='utf-8') as html_f:
                    html_content = html_f.read()
                
                # Create a simple text version
                import re
                # Remove HTML tags for basic text version
                text_content = re.sub(r'<[^>]+>', '', html_content)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                
                pdf_substitute_path = pdf_file_path.replace('.pdf', '_text.txt')
                with open(pdf_substitute_path, 'w', encoding='utf-8') as txt_f:
                    txt_f.write(f"FORENSIC REPORT (Text Format)\n")
                    txt_f.write(f"Generated: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}\n")
                    txt_f.write(f"Original HTML: {{os.path.basename(html_file_path)}}\n")
                    txt_f.write("="*80 + "\n\n")
                    txt_f.write(text_content)
                
                print(f"[INFO] Created text version: {{os.path.basename(pdf_substitute_path)}}")
                return True
                
        finally:
            # Clean up temp file
            try:
                os.unlink(ps_file)
            except:
                pass
                
    except Exception as e:
        print(f"[ERROR] Windows built-in PDF conversion failed for {{os.path.basename(html_file_path)}}: {{e}}")
        return False

def convert_html_to_pdf(html_file_path, pdf_file_path):
    """Convert HTML to PDF using available method"""
    if not PDF_AVAILABLE:
        print(f"[WARN] Skipping PDF generation for {os.path.basename(html_file_path)} - No PDF library available")
        return False
    
    # Use the available method
    if PDF_METHOD == "playwright":
        return convert_html_to_pdf_playwright(html_file_path, pdf_file_path)
    elif PDF_METHOD == "weasyprint":
        return convert_html_to_pdf_weasyprint(html_file_path, pdf_file_path)
    else:
        return convert_html_to_pdf_windows_builtin(html_file_path, pdf_file_path)

def create_pdf_directory(case_folder_path):
    """Create Reports pdf directory in the case folder"""
    pdf_dir = os.path.join(case_folder_path, 'Reports pdf')
    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        print(f"[DIR] Created PDF directory: {pdf_dir}")
    return pdf_dir

def convert_all_html_to_pdf(final_reports_dir, case_folder_path):
    """Convert all HTML files in Final_Reports to PDFs in Reports pdf folder"""
    if not PDF_AVAILABLE:
        print("[WARN] Skipping PDF generation - No PDF library available")
        return []
    
    # Create PDF directory
    pdf_dir = create_pdf_directory(case_folder_path)
    
    # Find all HTML files in Final_Reports
    html_pattern = os.path.join(final_reports_dir, "FILLED_*.html")
    html_files = glob.glob(html_pattern)
    
    if not html_files:
        print("⚠️ No HTML files found to convert to PDF")
        return []
    
    print(f"\n[PDF] Converting {len(html_files)} HTML files to PDF...")
    successful_pdfs = []
    
    for html_file in html_files:
        # Generate PDF filename
        html_filename = os.path.basename(html_file)
        pdf_filename = html_filename.replace('.html', '.pdf')
        pdf_file_path = os.path.join(pdf_dir, pdf_filename)
        
        # Convert to PDF
        if convert_html_to_pdf(html_file, pdf_file_path):
            successful_pdfs.append(pdf_file_path)
    
    print(f"[OK] Successfully generated {len(successful_pdfs)} PDF files in: {pdf_dir}")
    return successful_pdfs

def read_questions_file():
    """Read the questions.txt file"""
    # Look for questions.txt files in the new Results/CASE_*/Questions directory structure
    pattern = os.path.join('..', '..', 'Results', 'CASE_*', 'Questions', 'questions.txt')
    question_files = glob.glob(pattern)
    
    if not question_files:
        print("No questions.txt files found in Results directory. Looking in old evidence directory...")
        # Fallback to old structure for backward compatibility
        pattern = os.path.join('..', '..', 'evidence', 'Results', 'Questions', 'questions.txt')
        question_files = glob.glob(pattern)
        
    if not question_files:
        print("No questions.txt files found in evidence directory either...")
        pattern = os.path.join('..', '..', 'evidence', 'questions.txt')
        question_files = glob.glob(pattern)
        
    if not question_files:
        print("No questions.txt files found. Please run q_script.py first.")
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
    
    # Device information - use victim device info instead of storage media
    victim_device = data.get("Victim Device Make/Model/Size/Serial No", "")
    
    # Fallback to storage master copy if victim device info is not available (for backward compatibility)
    if not victim_device:
        victim_device = data.get("Storage Master Copy Make/Model/Size/Serial No", "")
        print("[WARN] Victim device information not found, using storage master copy info as fallback")
    
    make, model, size, serial_no = extract_device_info(victim_device)
    
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
        
    # Make a backup of the original template content
    original_content = html_content
    
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
    
    # Print debug info to check data
    print(f"[DEBUG] Job Form Data:")
    print(f"  - Case Name: {case_name}")
    print(f"  - Authorized Officer: {authorized_officer}")
    print(f"  - Party Name: {assessee_name}")
    print(f"  - Address: {premise_address}")
    print(f"  - Date/Time In: {start_date} {start_time}")
    print(f"  - Date/Time Out: {end_date} {end_time}")
    
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
    
    # Use direct HTML string replacements for the basic information table
    # This is more reliable than regex when dealing with the exact structure
    
    # Case Name/No
    html_content = html_content.replace(
        '<td style="width: 25%; font-weight: bold;">Case Name/No</td>\n                <td colspan="3"></td>',
        f'<td style="width: 25%; font-weight: bold;">Case Name/No</td>\n                <td colspan="3">{case_name}</td>'
    )
    
    # Date & Time In/Out
    html_content = html_content.replace(
        '<td style="width: 25%; font-weight: bold;">Date & Time in</td>\n                <td style="width: 25%;"></td>',
        f'<td style="width: 25%; font-weight: bold;">Date & Time in</td>\n                <td style="width: 25%;">{start_date} {start_time}</td>'
    )
    html_content = html_content.replace(
        '<td style="width: 25%; font-weight: bold;">Date & Time Out</td>\n                <td style="width: 25%;"></td>',
        f'<td style="width: 25%; font-weight: bold;">Date & Time Out</td>\n                <td style="width: 25%;">{end_date} {end_time}</td>'
    )
    
    # Authorized Officer
    html_content = html_content.replace(
        '<td style="font-weight: bold;">Authorised Officer</td>\n                <td colspan="3"></td>',
        f'<td style="font-weight: bold;">Authorised Officer</td>\n                <td colspan="3">{authorized_officer}</td>'
    )
    
    # Name of the Party
    html_content = html_content.replace(
        '<td style="font-weight: bold;">Name of the Party</td>\n                <td colspan="3"></td>',
        f'<td style="font-weight: bold;">Name of the Party</td>\n                <td colspan="3">{assessee_name}</td>'
    )
    
    # Premises Address
    html_content = html_content.replace(
        '<td style="font-weight: bold;">Premises Address</td>\n                <td colspan="3"></td>',
        f'<td style="font-weight: bold;">Premises Address</td>\n                <td colspan="3">{premise_address}</td>'
    )
    
    # In case the exact string replacement doesn't work, also try regex as a fallback
    # Case Name
    if case_name and '<td colspan="3">' + case_name + '</td>' not in html_content:
        html_content = re.sub(
            r'(<td[^>]*>Case Name\/No<\/td>\s*<td[^>]*>)([^<]*)(</td>)', 
            f'\\1{case_name}\\3', 
            html_content
        )
    
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
        action_taken = disk_handling if disk_handling else "Imaging"
        
        # First try direct string replacement for the first empty row
        try:
            first_row = '<tr>\n                <td style="height: 45px;"></td>\n                <td></td>\n                <td></td>\n                <td></td>\n            </tr>'
            new_row = f'<tr>\n                <td style="height: 45px; text-align: center;">1</td>\n                <td>{device_type}</td>\n                <td>{device_details}</td>\n                <td>{action_taken}</td>\n            </tr>'
            
            if first_row in html_content:
                html_content = html_content.replace(first_row, new_row, 1)
            else:
                # If direct replacement fails, use the regex approach
                pattern = r'(<tr>\s*<td style="width: 8%; font-weight: bold; text-align: center;">S\. No\.</td>.*?</tr>\s*)<tr>\s*<td style="height: \d+px;"></td>\s*<td></td>\s*<td></td>\s*<td></td>\s*</tr>'
                replacement = f'\\1<tr><td style="height: 45px; text-align: center;">1</td><td>{device_type}</td><td>{device_details}</td><td>{action_taken}</td></tr>'
                html_content = re.sub(pattern, replacement, html_content, count=1, flags=re.DOTALL)
        except Exception as e:
            print(f"Warning: Failed to replace item details row: {e}")
            # Final fallback for item details table
            pattern = r'(<table>.*?<td[^>]*>Item Type</td>.*?<td[^>]*>Details of the Item</td>.*?<td[^>]*>Action Taken</td>.*?</tr>\s*)<tr>'
            replacement = f'\\1<tr><td style="text-align: center;">1</td><td>{device_type}</td><td>{device_details}</td><td>{action_taken}</td></tr>\n            <tr>'
            html_content = re.sub(pattern, replacement, html_content, count=1, flags=re.DOTALL)
    
    # Hard Disk Capacity Table - Fill based on capacity data
    if hdd_capacity or hdd_used:
        # If we have hard disk capacity specified, fill the appropriate row
        if hdd_capacity and "2" in hdd_capacity.lower() and "tb" in hdd_capacity.lower():
            # Try both patterns to be more flexible with different HTML structures
            pattern1 = r'(<td style="text-align: center; height: 35px;">2 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            pattern2 = r'(<td style="text-align: center;">2 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            replacement = f'\\1<td>{hdd_used}</td><td>{hdd_lab_systems}</td><td>{hdd_income_tax}</td>'
            
            # Try both patterns
            if re.search(pattern1, html_content):
                html_content = re.sub(pattern1, replacement, html_content)
            else:
                html_content = re.sub(pattern2, replacement, html_content)
            
        elif hdd_capacity and "1" in hdd_capacity.lower() and "tb" in hdd_capacity.lower():
            # Try both patterns for 1TB
            pattern1 = r'(<td style="text-align: center; height: 35px;">1 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            pattern2 = r'(<td style="text-align: center;">1 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            replacement = f'\\1<td>{hdd_used}</td><td>{hdd_lab_systems}</td><td>{hdd_income_tax}</td>'
            
            if re.search(pattern1, html_content):
                html_content = re.sub(pattern1, replacement, html_content)
            else:
                html_content = re.sub(pattern2, replacement, html_content)
            
        elif hdd_capacity and "4" in hdd_capacity.lower() and "tb" in hdd_capacity.lower():
            # Try both patterns for 4TB
            pattern1 = r'(<td style="text-align: center; height: 35px;">4 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            pattern2 = r'(<td style="text-align: center;">4 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            replacement = f'\\1<td>{hdd_used}</td><td>{hdd_lab_systems}</td><td>{hdd_income_tax}</td>'
            
            if re.search(pattern1, html_content):
                html_content = re.sub(pattern1, replacement, html_content)
            else:
                html_content = re.sub(pattern2, replacement, html_content)
        else:
            # If we have HDD info but no specific capacity, default to 2TB row
            pattern1 = r'(<td style="text-align: center; height: 35px;">2 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            pattern2 = r'(<td style="text-align: center;">2 TB</td>\s*)<td></td>\s*<td></td>\s*<td></td>'
            replacement = f'\\1<td>{hdd_used}</td><td>{hdd_lab_systems}</td><td>{hdd_income_tax}</td>'
            
            if re.search(pattern1, html_content):
                html_content = re.sub(pattern1, replacement, html_content)
            else:
                html_content = re.sub(pattern2, replacement, html_content)
    
    # Fill Total No. of Hard Disk Used - using regex for more reliable replacement
    if hdd_used:
        # Try multiple patterns to be more flexible
        patterns = [
            r'(<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\s*)<td></td>',
            r'(<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>\s*)<td>\s*</td>',
            r'(<td>Total No. of Hard Disk Used</td>\s*)<td></td>',
            r'(Total No. of Hard Disk Used\s*</td>\s*)<td></td>'
        ]
        
        replacement = f'\\1<td>{hdd_used}</td>'
        
        # Try each pattern until one works
        for pattern in patterns:
            if re.search(pattern, html_content):
                html_content = re.sub(pattern, replacement, html_content)
                break
        
        # As a fallback, if none of the patterns worked, add the data at the end of the table
        if all(not re.search(pattern, html_content) for pattern in patterns):
            pattern = r'(<tr>\s*<td style="text-align: center; font-weight: bold;">Total No. of Hard Disk Used</td>)'
            replacement = f'\\1<td>{hdd_used}</td>'
            html_content = re.sub(pattern, replacement, html_content)
    
    # Working Hours Table - Fill forensic examiner info
    examiner1_name = data.get("Digital Forensic Examiner 1 Name", "") or forensic_examiner
    examiner1_hours = data.get("Digital Forensic Examiner 1 Working Hours", "")
    examiner2_name = data.get("Digital Forensic Examiner 2 Name", "")
    examiner2_hours = data.get("Digital Forensic Examiner 2 Working Hours", "")
    overall_hours = data.get("Overall Working Hours", "") or working_hours
    
    # Print debug info for working hours
    print(f"  - Examiner 1: {examiner1_name} ({examiner1_hours})")
    print(f"  - Examiner 2: {examiner2_name} ({examiner2_hours})")
    print(f"  - Overall Hours: {overall_hours}")
    
    # Fill first examiner with regex for more reliable replacement
    if examiner1_name:
        pattern = r'(<td style="text-align: center;">1\.</td>\s*)<td style="height: 45px;"></td>\s*<td></td>'
        replacement = f'\\1<td style="height: 45px;">{examiner1_name}</td><td>{examiner1_hours}</td>'
        html_content = re.sub(pattern, replacement, html_content)
    
    # Fill second examiner if exists
    if examiner2_name:
        pattern = r'(<td style="text-align: center;">2\.</td>\s*)<td style="height: 45px;"></td>\s*<td></td>'
        replacement = f'\\1<td style="height: 45px;">{examiner2_name}</td><td>{examiner2_hours}</td>'
        html_content = re.sub(pattern, replacement, html_content)
    
    # Fill overall working hours
    if overall_hours:
        pattern = r'(<td></td>\s*<td style="text-align: center; font-weight: bold;">Overall Working Hours</td>\s*)<td></td>'
        replacement = f'\\1<td>{overall_hours}</td>'
        html_content = re.sub(pattern, replacement, html_content)
    
    # Signature Section - Leave empty for manual completion
    # Lead Forensic Examiner and Authorised Officer signatures will remain blank
    
    # Create output path
    output_path = os.path.join(output_dir, f'FILLED_job_form_{timestamp}.html')
    
    # Perform a final check for missing data
    # If any of the table data fields is still empty after our replacements, 
    # try one last method - direct row-by-row injection
    if '<td colspan="3"></td>' in html_content or case_name not in html_content or authorized_officer not in html_content:
        print("[WARNING] Still found empty cells or missing data in job form, attempting final direct replacements")
        
        # Try a complete reconstruction of the basic info table as a reliable last resort
        new_basic_table = f'''
        <table>
            <tr>
                <td style="width: 25%; font-weight: bold;">Case Name/No</td>
                <td colspan="3">{case_name}</td>
            </tr>
            <tr>
                <td style="width: 25%; font-weight: bold;">Date & Time in</td>
                <td style="width: 25%;">{start_date} {start_time}</td>
                <td style="width: 25%; font-weight: bold;">Date & Time Out</td>
                <td style="width: 25%;">{end_date} {end_time}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Authorised Officer</td>
                <td colspan="3">{authorized_officer}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Name of the Party</td>
                <td colspan="3">{assessee_name}</td>
            </tr>
            <tr>
                <td style="font-weight: bold;">Premises Address</td>
                <td colspan="3">{premise_address}</td>
            </tr>
        </table>
        '''
        
        # Find the original basic info table and replace it
        basic_table_pattern = r'<table>\s*<tr>\s*<td[^>]*>Case Name/No</td>.*?<td[^>]*>Premises Address</td>.*?</tr>\s*</table>'
        html_content = re.sub(basic_table_pattern, new_basic_table.strip(), html_content, flags=re.DOTALL)
        
        # If that fails, try a simpler pattern
        if '<td colspan="3"></td>' in html_content or case_name not in html_content or authorized_officer not in html_content:
            print("[WARNING] Complete table replacement failed, trying individual rows")
            
            # Find all table rows in the basic info table
            basic_table_pattern = r'<table>\s*<tr>.*?</table>'
            basic_table_match = re.search(basic_table_pattern, html_content, re.DOTALL)
            
            if basic_table_match:
                basic_table = basic_table_match.group(0)
                
                # Manually replace row by row
                rows = re.findall(r'<tr>.*?</tr>', basic_table, re.DOTALL)
                
                if len(rows) >= 5:  # Basic info table has 5 rows
                    # Row 1: Case Name
                    if case_name and '<td colspan="3">' + case_name + '</td>' not in rows[0]:
                        rows[0] = rows[0].replace('<td colspan="3"></td>', f'<td colspan="3">{case_name}</td>')
                    
                    # Row 3: Authorized Officer
                    if authorized_officer and '<td colspan="3">' + authorized_officer + '</td>' not in rows[2]:
                        rows[2] = rows[2].replace('<td colspan="3"></td>', f'<td colspan="3">{authorized_officer}</td>')
                    
                    # Row 4: Name of Party
                    if assessee_name and '<td colspan="3">' + assessee_name + '</td>' not in rows[3]:
                        rows[3] = rows[3].replace('<td colspan="3"></td>', f'<td colspan="3">{assessee_name}</td>')
                    
                    # Row 5: Premises Address
                    if premise_address and '<td colspan="3">' + premise_address + '</td>' not in rows[4]:
                        rows[4] = rows[4].replace('<td colspan="3"></td>', f'<td colspan="3">{premise_address}</td>')
                    
                    # Reconstruct the table
                    new_basic_table = '<table>\n' + '\n'.join(rows) + '\n</table>'
                    html_content = html_content.replace(basic_table_match.group(0), new_basic_table)
    
    # Save the filled HTML form
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    # Verify the final content
    print(f"Job Form generated successfully: {output_path}")
    
    # Verify critical data is in the file
    with open(output_path, 'r') as f:
        verification = f.read()
        if case_name not in verification:
            print(f"[WARNING] Case Name '{case_name}' not found in final HTML")
        if authorized_officer not in verification:
            print(f"[WARNING] Officer Name '{authorized_officer}' not found in final HTML")
    
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
    
    # Fill items list with device type and assessee name
    if device_type and assessee_name:
        # Create the first item with device type and assessee name
        first_item = f"{assessee_name}_{device_type}_01"
        html_content = html_content.replace('<li><!-- Assessee_Name_Laptop_01 --></li>', 
                                         f'<li>{first_item}</li>')
    else:
        # If data is missing, keep the first item empty
        html_content = html_content.replace('<li><!-- Assessee_Name_Laptop_01 --></li>', '<li></li>')
    
    # Clean up remaining item placeholders to leave them empty for manual completion
    remaining_placeholders = [
        '<!--Assessee_Name_Laptop_02 -->',
        '<!--Assessee_Name_Apple_Mobile -->',
        '<!--Assessee_Name_Samsung_Mobile -->',
        '<!--assessee@gmail.com -->'
    ]
    
    for placeholder in remaining_placeholders:
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
    
    # Extract case folder path for PDF generation
    case_folder_path = None
    if 'Results' in questions_file_path and 'CASE_' in questions_file_path:
        parts = questions_file_path.split(os.sep)
        for i, part in enumerate(parts):
            if part.startswith('CASE_'):
                case_folder_path = os.path.join('..', '..', 'Results', part)
                break
    
    # Generate PDFs if case folder is found
    if case_folder_path and os.path.exists(case_folder_path):
        print(f"\n[INFO] Starting PDF generation...")
        pdf_files = convert_all_html_to_pdf(output_dir, case_folder_path)
        
        if pdf_files:
            print(f"\n[SUMMARY] PDF Summary:")
            print(f"  [DIR] PDF Directory: {os.path.join(case_folder_path, 'Reports pdf')}")
            print(f"  [PDF] PDFs Generated: {len(pdf_files)}")
            for pdf_file in pdf_files:
                print(f"    - {os.path.basename(pdf_file)}")
        else:
            print("[WARN] No PDFs were generated")
    else:
        print("[WARN] Could not determine case folder for PDF generation")

if __name__ == "__main__":
    main()