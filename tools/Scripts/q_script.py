import os
from datetime import datetime

def create_case_directory():
    """
    Create a new case directory structure for the forensic workflow
    """
    # Get the base directory (two levels up from Scripts folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(script_dir))
    results_base = os.path.join(base_dir, "Results")

    # Create case ID with timestamp
    case_id = datetime.now().strftime("CASE_%Y%m%d_%H%M%S")
    case_dir = os.path.join(results_base, case_id)

    # Create directory structure
    subdirs = {
        'questions': os.path.join(case_dir, "Questions"),
        'hashdeep': os.path.join(case_dir, "HashDeep_output"),
        'autopsy': os.path.join(case_dir, "Autopsy_output"),
        'volatility': os.path.join(case_dir, "Volatility_output"),
        'exiftool': os.path.join(case_dir, "ExifTool_output"),
        'bulk_extractor': os.path.join(case_dir, "BulkExtractor_output"),
        'reports': os.path.join(case_dir, "Final_Reports")
    }

    # Create all directories
    for subdir_name, subdir_path in subdirs.items():
        os.makedirs(subdir_path, exist_ok=True)
        print(f" Created: {subdir_path}")

    return case_dir, case_id, subdirs

def save_case_info(case_dir, case_id):
    """
    Save case information for script_3.py to use
    """
    case_info_file = os.path.join(case_dir, ".case_info")
    with open(case_info_file, "w") as f:
        f.write(f"CASE_ID={case_id}\n")
        f.write(f"CASE_DIR={case_dir}\n")
        f.write(f"CREATED={datetime.now().isoformat()}\n")

    print(f" Case info saved: {case_info_file}")
    return case_info_file

def main():
    print("\n" + "="*80)
    print("EDITH-Automater: Digital Evidence Collection & Forensic Workflow")
    print("="*80)
    print("Step 1: Evidence Collection Form")
    print("Step 2: Forensic Analysis (run script_3.py after this)")
    print("="*80)

    # Create case directory structure first
    case_dir, case_id, subdirs = create_case_directory()

    print(f"\n  Case ID: {case_id}")
    print(f" Case Directory: {case_dir}")

    answers = {}

    def ask(question, condition=True):
        if condition:
            while True:
                ans = input(f"{question}: ").strip()
                if ans:
                    answers[question] = ans
                    break
                else:
                    print("This field cannot be left empty. Please provide an answer.")

    def ask_choice(question, choices, key):
        """Ask a multiple choice question with clear options"""
        print(f"\n{question}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")

        while True:
            try:
                choice_num = input(f"Enter your choice (1-{len(choices)}): ").strip()
                choice_index = int(choice_num) - 1
                if 0 <= choice_index < len(choices):
                    answers[key] = choices[choice_index]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(choices)}")
            except ValueError:
                print("Please enter a valid number")

    def ask_yes_no(question, key):
        """Ask a yes/no question"""
        print(f"\n{question}")
        print("  1. Yes")
        print("  2. No")

        while True:
            choice = input("Enter your choice (1 for Yes, 2 for No): ").strip()
            if choice == "1":
                answers[key] = "Yes"
                break
            elif choice == "2":
                answers[key] = "No"
                break
            else:
                print("Please enter 1 for Yes or 2 for No")

    # General Information
    print("\n" + "="*50)
    print("GENERAL INFORMATION")
    print("="*50)

    ask("Case Name / No")
    ask("Authorized Officer")
    ask("Name of Assessee / Party")
    ask("Premise Address")
    ask("Start Date & Time (Example: 12-09-2025 2:00PM)")
    ask("End Date & Time (Example: 13-09-2025 2:00AM)")
    ask("Search Date (Example: 12-09-2025)")
    ask("Examiner's Name and Details")

    # Forensic Examiners and Working Hours
    print("\n" + "="*50)
    print("FORENSIC EXAMINERS & WORKING HOURS")
    print("="*50)

    def ask_hours(prompt):
        """Ask for working hours and extract numeric value"""
        while True:
            hours_str = input(f"{prompt} (Example: 8hr, 10, 15hr): ").strip()
            if hours_str:
                # Extract numeric value from input (handle formats like "8hr", "8", "8.5hr")
                import re
                numeric_match = re.search(r'(\d+(?:\.\d+)?)', hours_str)
                if numeric_match:
                    return hours_str, float(numeric_match.group(1))
                else:
                    print("Please enter a valid number (e.g., 8hr, 10, 15hr)")
            else:
                print("This field cannot be left empty. Please provide an answer.")

    # Ask for first examiner
    ask("Digital Forensic Examiner 1 Name")
    examiner1_hours_str, examiner1_hours_num = ask_hours("Digital Forensic Examiner 1 Working Hours")
    answers["Digital Forensic Examiner 1 Working Hours"] = examiner1_hours_str

    # Ask for second examiner (optional)
    examiner2_name = input("Digital Forensic Examiner 2 Name (optional, press Enter to skip): ").strip()
    if examiner2_name:
        answers["Digital Forensic Examiner 2 Name"] = examiner2_name
        examiner2_hours_str, examiner2_hours_num = ask_hours("Digital Forensic Examiner 2 Working Hours")
        answers["Digital Forensic Examiner 2 Working Hours"] = examiner2_hours_str

        # Calculate overall working hours
        total_hours = examiner1_hours_num + examiner2_hours_num
        overall_hours = f"{total_hours}hr" if total_hours == int(total_hours) else f"{total_hours:.1f}hr"
        answers["Overall Working Hours"] = overall_hours
        print(f"Calculated Overall Working Hours: {overall_hours}")
    else:
        # Only one examiner, so overall hours = examiner 1 hours
        answers["Overall Working Hours"] = examiner1_hours_str
        print(f"Overall Working Hours: {examiner1_hours_str}")

    # For backward compatibility, set the main examiner fields
    answers["Digital Forensic Examiner"] = answers["Digital Forensic Examiner 1 Name"]
    answers["Working Hours"] = answers["Overall Working Hours"]

    # Device Info
    print("\n" + "="*50)
    print("DEVICE INFORMATION")
    print("="*50)

    ask("Device Owner / In Possession of")

    ask_choice(
        "What type of device was seized?",
        ["Laptop", "Desktop", "Server", "Other"],
        "Device Type (Laptop/Desktop/Server/Other)"
    )
    
    print("\nEnter victim device details")
    print("Format: Make/Model/Size/Serial Number")
    print("Example: Dell/Latitude E7450/500GB/XYZ789456123")
    ask("Victim Device Make/Model/Size/Serial No")

    ask_choice(
        "What was the device status when seized?",
        ["On", "Off", "Sleep"],
        "Device Status at Seizure (On/Off/Sleep)"
    )

    device_status = answers["Device Status at Seizure (On/Off/Sleep)"]
    if device_status.lower() == "on":
        ask("Screen Visible (if ON) - What was visible on the screen?")

    # Memory and Shutdown
    print("\n" + "="*50)
    print("MEMORY & SHUTDOWN DETAILS")
    print("="*50)

    ask_yes_no("Was Volatile Memory / RAM collected?", "Volatile Memory / RAM Collected (Yes/No)")

    ask_choice(
        "How was the device shut down?",
        ["Normal", "Power Pulled", "Battery Removed", "N/A"],
        "Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)"
    )

    # Media Encryption
    print("\n" + "="*50)
    print("ENCRYPTION DETAILS")
    print("="*50)

    ask_yes_no("Is the suspected media encrypted?", "Is the suspected media encrypted (Yes/No)")
    encryption_status = answers["Is the suspected media encrypted (Yes/No)"]
    if encryption_status.lower() == "yes":
        ask("Type of encryption Software used (Example: BitLocker, TrueCrypt, etc.)")

    # Hard Disk Handling
    print("\n" + "="*50)
    print("HARD DISK HANDLING")
    print("="*50)

    ask_choice(
        "What type of hard disk handling was performed?",
        ["Seizure", "Forensic Previewing", "Imaging", "Backup"],
        "Hard Disk Handling (Seizure/Forensic Previewing/Imaging/Backup)"
    )

    # Forensic Works Performed
    print("\n" + "="*50)
    print("FORENSIC WORKS PERFORMED")
    print("="*50)

    forensic_works_options = [
        "Data Acquisition", "Data Extraction", "Data Analysis", "Data Duplication",
        "Data Raw Backup", "Email Backup", "Cloud Acquisition", "Other Works"
    ]

    print("Select the forensic works performed:")
    for i, work in enumerate(forensic_works_options, 1):
        print(f"  {i}. {work}")

    print("\nYou can:")
    print("- Enter individual numbers (e.g., 1, then 2, then 3)")
    print("- Enter multiple numbers separated by spaces (e.g., 1 2 3 4)")
    print("- Type 'done' when finished")

    selected_works = []
    while True:
        user_input = input(f"Enter choice(s) (1-{len(forensic_works_options)}) or 'done': ").strip().lower()

        if user_input == 'done':
            if selected_works:
                break
            else:
                print("Please select at least one forensic work.")
                continue

        # Handle multiple numbers separated by spaces
        choices = user_input.split()
        valid_selections = False

        for choice in choices:
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(forensic_works_options):
                    work = forensic_works_options[choice_num - 1]
                    if work not in selected_works:
                        selected_works.append(work)
                        print(f"Added: {work}")
                        valid_selections = True
                    else:
                        print(f"{work} already selected.")
                else:
                    print(f"Invalid choice: {choice_num}. Please enter numbers between 1 and {len(forensic_works_options)}")
            except ValueError:
                print(f"Invalid input: '{choice}'. Please enter valid numbers or 'done'")

        if not valid_selections and user_input != 'done':
            print("No valid selections were made. Please try again.")

        if selected_works:
            print(f"\nCurrently selected: {', '.join(selected_works)}")

    answers["Forensic Works Performed"] = ", ".join(selected_works)

    # Integrity Verification
    print("\n" + "="*50)
    print("HASH VERIFICATION")
    print("="*50)

    ask_yes_no("Is Hash Value Calculated?", "Is Hash Value Calculated (Yes/No)")
    hash_calc = answers["Is Hash Value Calculated (Yes/No)"]

    if hash_calc.lower() == "yes":
        ask_choice(
            "Which algorithm was used for hash calculation?",
            ["MD5", "SHA1", "Others"],
            "Algorithm Used (MD5/SHA1/Others)"
        )

    # Storage Details
    print("\n" + "="*50)
    print("STORAGE DETAILS")
    print("="*50)
    print("Format: Make/Model/Size/Serial Number")
    print("Example: Asus/X550/5TB/ABC123456789")

    ask("Storage Master Copy Make/Model/Size/Serial No")
    ask("Storage Working Copy Make/Model/Size/Serial No")

    # Hard Disk Capacity Details
    print("\n" + "="*50)
    print("HARD DISK CAPACITY & PROVIDER DETAILS")
    print("="*50)

    # Ask for capacity selection
    capacity_options = ["1 TB", "2 TB", "4 TB"]
    ask_choice(
        "Select Hard Disk Capacity:",
        capacity_options,
        "Hard Disk Capacity"
    )

    selected_capacity = answers["Hard Disk Capacity"]
    print(f"\nFor {selected_capacity} capacity:")

    ask("No. of HDD Used (Example: 1, 2, 3)")
    ask("No. of HDD provided by Lab Systems (I) Pvt. Ltd.")
    ask("No. of HDD provided by Income Tax Department")

    # Witness
    print("\n" + "="*50)
    print("WITNESS INFORMATION")
    print("="*50)

    ask_yes_no("Is Witness Signature Taken?", "Is Witness Signature Taken (Yes/No)")
    ask("Witness Name")

    # Save the evidence collection form
    print("\n" + "="*50)
    print("SAVING EVIDENCE COLLECTION FORM")
    print("="*50)

    # Generate simple filename without timestamp
    filename = "questions.txt"
    questions_dir = subdirs['questions']
    full_path = os.path.join(questions_dir, filename)

    # Write the form
    with open(full_path, "w", encoding='utf-8') as f:
        f.write("Digital Evidence Collection & Chain of Custody Form\n")
        f.write("="*60 + "\n")
        f.write(f"Case ID: {case_id}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Case Directory: {case_dir}\n")
        f.write("="*60 + "\n\n")

        for q, a in answers.items():
            f.write(f"{q}: {a}\n")

        # Add metadata section
        f.write(f"\n{'='*60}\n")
        f.write("METADATA\n")
        f.write(f"{'='*60}\n")
        f.write(f"File created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Script version: q_script.py v2.0\n")
        f.write(f"Case ID: {case_id}\n")
        f.write(f"Case directory: {case_dir}\n")

    # Save case info for script_3.py
    save_case_info(case_dir, case_id)

    print(f"\n Evidence Collection Form saved!")
    print(f" Location: {full_path}")
    print(f"️  Case directory: {case_dir}")

    print(f"\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print(f"1.  Evidence collection form completed")
    print(f"2.  Now run: python script_3.py")
    print(f"3.  All forensic analysis will be saved to the same case directory")
    print(f"")
    print(f"Case ID: {case_id}")
    print(f"Directory: {case_dir}")
    print("="*80)

    return answers, case_dir, case_id

if __name__ == "__main__":
    data, case_dir, case_id = main()
