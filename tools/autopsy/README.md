# 🕵️‍♂️ Forensic Evidence Processing Script

A Python-based automation tool to assist in **digital forensic investigations**.  
It leverages **The Sleuth Kit (TSK)** utilities (`mmls`, `fsstat`, `fls`, `tsk_recover`) to process disk images, compute hashes, extract file listings, recover deleted files, and generate case metadata.

---

## 🚀 Features
- 📂 Creates structured **case folders** for each investigation.
- 🔑 Computes **MD5** and **SHA256** hashes of evidence images.
- 📊 Extracts **partition table** information using `mmls`.
- 📜 Collects detailed **filesystem statistics** via `fsstat`.
- 📑 Generates a **recursive file listing** using `fls`.
- 🗃️ Recovers files (deleted and active) using `tsk_recover`.
- 📝 Saves a comprehensive `case_metadata.json` with examiner info, description, timestamps, and hashes.


### Python Requirements
- Python 3.10+  
- Required Python packages (install via pip):
```bash
pip install -r requirements.txt
```
###Contents of requirements.txt:

rich==13.6.0         # Enhanced console output
tqdm==4.66.1         # Progress bars
python-magic==0.4.27 # Optional: File type detection

###Sleuth Kit Requirements (System Tools)
| Tool          | Purpose                       | Installation (Ubuntu/Debian)     |
| ------------- | ----------------------------- | -------------------------------- |
| `mmls`        | Display partition table       | `sudo apt-get install sleuthkit` |
| `fsstat`      | Show filesystem statistics    | `sudo apt-get install sleuthkit` |
| `fls`         | List files and directories    | `sudo apt-get install sleuthkit` |
| `tsk_recover` | Recover files from partitions | `sudo apt-get install sleuthkit` |

###🖥️ Usage

Run the script:

python auto.py

You will be prompted to enter:

    Case Name
    Examiner Name
    Path to Evidence Image (.E01 / .dd)
    Case Description

###Example Session

Enter Case Name: Case123
Enter Examiner Name: John Doe
Enter path to evidence image (.E01/.dd): /cases/evidence1.E01
Enter Case Description: Analysis of suspected USB drive
