import os

def main():
    print("\n--- Digital Evidence Collection Form ---\n")

    answers = {}

    # Helper function that forces non-empty input
    def ask(question, condition=True):
        if condition:
            while True:
                ans = input(f"{question}: ").strip()
                if ans:
                    answers[question] = ans
                    break
                else:
                    print("This field cannot be left empty. Please provide an answer.")

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
    while True:
        device_status = input("Device Status at Seizure (On/Off/Sleep): ").strip()
        if device_status:
            answers["Device Status at Seizure (On/Off/Sleep)"] = device_status
            break
        else:
            print("This field cannot be left empty. Please provide an answer.")

    if device_status.lower() == "on":
        ask("Screen Visible (if ON)")

    ask("Volatile Memory / RAM Collected (Yes/No)")
    ask("Shut Down Type (Normal/Power Pulled/Battery Removed/N/A)")

   

    # Integrity Verification
    while True:
        hash_calc = input("Is Hash Value Calculated (Yes/No): ").strip()
        if hash_calc:
            answers["Is Hash Value Calculated (Yes/No)"] = hash_calc
            break
        else:
            print("This field cannot be left empty. Please provide an answer.")

    if hash_calc.lower() == "yes":
        ask("Algorithm Used (MD5/SHA1/Others)")
       

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
    while True:
        base_path = input("\nEnter the destination folder path: ").strip()
        if base_path:
            if not os.path.exists(base_path):
                print("The given path does not exist. Creating it...")
                os.makedirs(base_path)
            break
        else:
            print("This field cannot be left empty. Please provide an answer.")

    # Create Results/Questions inside the destination path
    results_path = os.path.join(base_path, "Results", "Questions")
    if not os.path.exists(results_path):
        os.makedirs(results_path)

    # Ask filename
    while True:
        file_name = input("Enter the filename (without extension): ").strip()
        if file_name:
            file_name += ".txt"
            break
        else:
            print("This field cannot be left empty. Please provide an answer.")

    full_path = os.path.join(results_path, file_name)

    # Write to file
    with open(full_path, "w") as f:
        f.write("Digital Evidence Collection & Chain of Custody Form\n")
        f.write("="*60 + "\n\n")
        for q, a in answers.items():
            f.write(f"{q}: {a}\n")

    print(f"\nFile saved successfully at: {full_path}")

    return answers

if __name__ == "__main__":
    data = main()