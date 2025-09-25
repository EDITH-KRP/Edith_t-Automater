from fpdf import FPDF
import string
import os
import re

parsed_txt_path = "/home/kali/zetpeak/bulk_project/parsed_clean.txt"
pdf_path = "/home/kali/zetpeak/bulk_project/final_report.pdf"
MAX_LINES_PER_FILE = 200
MAX_CHAR_PER_LINE = 150

# Regex to parse winlnk entries
winlnk_pattern = re.compile(
    r'(?P<entry>\d+)NO_LINKINFO<lnk>(<atime>(?P<atime>.*?)</atime>)?(<ctime>(?P<ctime>.*?)</ctime>)?(<mtime>(?P<mtime>.*?)</mtime>)?'
)

def safe_line(line):
    line = ''.join(c for c in line if c in string.printable)
    line = line.replace('\n', ' ').replace('\r', '').strip()
    if not line:
        return None
    if len(line) > MAX_CHAR_PER_LINE:
        line = line[:MAX_CHAR_PER_LINE] + "..."
    return line

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, "=== Bulk Extractor Parsed Report ===\n\n")

if not os.path.exists(parsed_txt_path):
    print(f"[!] Parsed text file not found: {parsed_txt_path}")
    exit(1)

current_file = ""
line_count = 0

with open(parsed_txt_path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = safe_line(line)
        if not line:
            continue

        # File header
        if line.startswith("---") and line.endswith("---"):
            current_file = line
            line_count = 0
            try:
                pdf.multi_cell(0, 10, current_file)
            except:
                continue
            continue

        if line_count >= MAX_LINES_PER_FILE:
            continue

        # Special parsing for winlnk.txt
        if "winlnk.txt" in current_file.lower():
            match = winlnk_pattern.match(line)
            if match:
                entry = match.group('entry') or "N/A"
                atime = match.group('atime') or "N/A"
                ctime = match.group('ctime') or "N/A"
                mtime = match.group('mtime') or "N/A"
                try:
                    pdf.multi_cell(0, 8, f"Entry: {entry}")
                    pdf.multi_cell(0, 8, f"  Access Time: {atime}")
                    pdf.multi_cell(0, 8, f"  Create Time: {ctime}")
                    pdf.multi_cell(0, 8, f"  Modify Time: {mtime}\n")
                except:
                    continue
                line_count += 1
                continue

        # Default: print normal line
        try:
            pdf.multi_cell(0, 8, line)
            line_count += 1
        except:
            continue

pdf.output(pdf_path)
print(f"[+] PDF report generated: {pdf_path}")
