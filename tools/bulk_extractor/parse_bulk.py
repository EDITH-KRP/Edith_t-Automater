import os
import string

be_out_path = "/home/kali/zetpeak/bulk_project/be_out"
parsed_txt_path = "/home/kali/zetpeak/bulk_project/parsed_clean.txt"
MAX_LINES = 50
MAX_CHAR = 80

parsed_data = {}

def clean_line(s):
    printable = set(string.printable)
    s = ''.join(filter(lambda x: x in printable, s))
    s = s.replace('\n', ' ').replace('\r', '').strip()
    if not s:
        return None
    if len(s) > MAX_CHAR:
        s = s[:MAX_CHAR] + "..."
    return s

for filename in os.listdir(be_out_path):
    if filename.endswith(".txt"):
        filepath = os.path.join(be_out_path, filename)
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [clean_line(line) for line in f]
            lines = [line for line in lines if line]
            lines = list(dict.fromkeys(lines))
            if lines:
                parsed_data[filename] = lines[:MAX_LINES]

with open(parsed_txt_path, "w") as out:
    for k, v in parsed_data.items():
        out.write(f"--- {k} ({len(v)} entries, max {MAX_LINES}) ---\n")
        for item in v:
            out.write(item + "\n")
        out.write("\n")

print(f"[+] Clean text saved: {parsed_txt_path}")
