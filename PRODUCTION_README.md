# EDITH-Automater: Digital Evidence Report Generation System

## 🚀 Complete Forensic Documentation Workflow

### Overview
EDITH-Automater is a comprehensive digital evidence documentation system that automates the creation of professional forensic reports from collected evidence data.

### 📋 Workflow Steps

#### Step 1: Data Collection
```bash
python tools/Scripts/q_script.py
```
- Interactive form collection for digital evidence
- Collects case information, device details, examiner data
- Saves to: `evidence/Results/Questions/questions.txt`

#### Step 2: Report Generation  
```bash
python tools/Scripts/simple_html_generator.py
```
- Reads collected data from questions.txt
- Processes HTML templates from `reports/Reports html/`
- Generates filled reports in `evidence/Final_Reports/`

#### Step 3: PDF Conversion
- Manual: Open HTML files in browser → Print → Save as PDF
- Automated: Use wkhtmltopdf or online converters

### 🎯 One-Command Workflow
```bash
python tools/Scripts/edith_workflow.py
```
Runs the complete workflow with guided prompts.

### 📄 Generated Reports

The system generates 6 professional forensic reports:

1. **Digital Evidence Form** - Core evidence documentation
2. **Chain of Custody** - Evidence handling tracking  
3. **Form 65B** - Legal compliance certificate
4. **Email Evidence Form** - Email-specific documentation
5. **Job Form** - Case work details
6. **Master Copy Form** - Storage media documentation

### 🗂️ Project Structure

```
e:/Github-adhi982/Edith_t-Automater/
├── tools/Scripts/
│   ├── edith_workflow.py          # Master workflow controller
│   ├── q_script.py                # Data collection script
│   └── simple_html_generator.py   # Report generation engine
├── reports/Reports html/           # HTML templates
│   ├── digital_evidence_form.html
│   ├── chain_of_custody.html
│   ├── form_65B.html
│   ├── email_digital_evidence_form.html
│   ├── job_form.html
│   └── master_copy.html
├── evidence/
│   ├── Results/Questions/          # Collected form data
│   └── Final_Reports/              # Generated HTML reports
└── logs/                          # System logs
```

### ⚙️ System Requirements

- **Python 3.8+**
- **Web Browser** (for PDF conversion)
- **Windows PowerShell** (current setup)

### 🚦 Quick Start

1. **Clone/Setup the repository**
2. **Run the master workflow:**
   ```bash
   cd e:/Github-adhi982/Edith_t-Automater/tools/Scripts
   python edith_workflow.py
   ```
3. **Follow the guided prompts:**
   - Answer evidence collection questions
   - Review generated HTML reports
   - Convert to PDF using browser

### 📊 Data Fields Supported

The system handles 34+ evidence fields including:

- **Case Information**: Case number, officer, assessee details
- **Device Details**: Type, status, specifications  
- **Examiner Data**: Names, qualifications, working hours
- **Technical Info**: Hash values, imaging software, storage details
- **Legal Info**: Witness signatures, chain of custody
- **Email Evidence**: Service providers, encryption status

### 🔧 Customization

#### Adding New Fields
1. Edit `q_script.py` to add new questions
2. Update field mappings in `simple_html_generator.py`
3. Modify HTML templates as needed

#### New Report Templates
1. Add HTML template to `reports/Reports html/`
2. Update template list in `simple_html_generator.py`
3. Add field mappings for the new template

### 📝 Logging

System logs are saved to `logs/` directory with timestamps:
- Data collection logs
- Report generation logs  
- Error tracking and debugging

### 🛠️ Troubleshooting

#### Common Issues

**1. File Not Found Errors**
- Ensure all paths are correct
- Check file permissions
- Verify directory structure

**2. Empty Fields in Reports**
- Check questions.txt for complete data
- Verify field name mappings
- Review template structure

**3. PDF Conversion Issues**
- Use browser print function
- Install wkhtmltopdf for automation
- Try online conversion tools

#### Support
Contact the forensic team for technical assistance.

### 🔒 Security & Compliance

- All evidence data is stored locally
- No external network dependencies
- Maintains chain of custody integrity
- Generates legally compliant documentation

### 📈 Future Enhancements

- [ ] Automated PDF generation
- [ ] Network evidence templates
- [ ] Batch processing capabilities
- [ ] Digital signature integration
- [ ] Database storage backend

---

**Version**: 1.0  
**Author**: EDITH-Automater Team  
**Date**: September 30, 2025

For technical documentation and API details, see the individual script files.