import os

def main():
    print("\n--- Digital Evidence Collection Form ---\n")

    answers = {}

    # Helper function
    def ask(question, condition=True):
        if condition:
            ans = input(f"{question}: ").strip()
            answers[question] = ans

    # General Information
    ask("Case Name / No")
    ask("Authorized Officer")
    ask("Name of Assessee / Party")
    ask("Premise Address")
    ask("Start Date & Time")
    ask("End Date & Time")
    ask("Search Date")
    ask("Examiner’s Name and Details")
    ask("Digital Forensic Examiner")
    ask("Working Hours")

    # Device Info
    ask("Device Owner / In Possession of")
    ask("Device Type (Laptop/Desktop/Server/Other)")
    device_status = input("Device Status at Seizure (On/Off/Sleep): ").strip()
    answers["Device Status at Seizure (On/Off/Sleep)"] = device_status

    if device_status.lower() == "on":
        ask("Screen Visible (if ON)")

    ask("Volatile Memory / RAM Collected (Yes/No)")
    ask("Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)")

    # Email
    ask("Email Service Provider")
    ask("Email ID")
    ask("Software Used to Backup Email")
    email_encrypted = input("Is Email Data Encrypted (Yes/No): ").strip()
    answers["Is Email Data Encrypted (Yes/No)"] = email_encrypted

    if email_encrypted.lower() == "yes":
        ask("Encryption Software")

    ask("Email Data Handling (Previewing/Imaging/Backup)")
    ask("Imaging Software / Version")

    # Integrity Verification
    hash_calc = input("Is Hash Value Calculated (Yes/No): ").strip()
    answers["Is Hash Value Calculated (Yes/No)"] = hash_calc

    if hash_calc.lower() == "yes":
        ask("Algorithm Used (MD5/SHA1/Others)")
        ask("MD5 Hash Value")
        ask("SHA1 Hash Value")

    # Storage Details
    ask("Storage Master Copy Make/Model/Size/Serial No")
    ask("Storage Working Copy Make/Model/Size/Serial No")
    ask("Hard Disk Capacity")
    ask("No. of HDD Used")
    ask("No. of HDD provided by Lab Systems (I) Pvt. Ltd.")
    ask("No. of HDD provided by Income Tax Department")

    # Witness
    ask("Is Witness Signature Taken (Yes/No)")
    ask("Witness Name")
    ask("Witness Father’s Name")

    # Ask destination folder
    save_path = input("\nEnter the destination folder path where the file should be saved: ").strip()
    if not os.path.exists(save_path):
        print("The given path does not exist. Creating it...")
        os.makedirs(save_path)

    # Ask filename
    file_name = input("Enter the filename (without extension): ").strip() + ".txt"
    full_path = os.path.join(save_path, file_name)

    # Write to file
    with open(full_path, "w") as f:
        f.write("Digital Evidence Collection & Chain of Custody Form\n")
        f.write("="*60 + "\n\n")
        for q, a in answers.items():
            f.write(f"{q}: {a}\n")

    print(f"\nFile saved successfully at: {full_path}")

    # Save structured answers for another script (as dictionary)
    return answers


if __name__ == "__main__":
    data = main()
    # Example: in another script, you could import and use like:
    # from evidence_form import main
    # answers = main()
    # print(answers["Device Status at Seizure (On/Off/Sleep)"])
