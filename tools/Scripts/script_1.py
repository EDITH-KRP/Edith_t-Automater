import os
import q_script
import script_2
import script_3

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear_screen()
        print("="*50)
        print("      Welcome to the EDITH Automation Main Menu")
        print("="*50)
        print("Choose an option to run:")
        print("1. Answer Questions for Digital Evidence Collection")
        print("2. Run Digital Evidence Collection (Image Creation)")
        print("3. Run Tools for Forensic Analysis")
        print("0. Exit")

        choice = input("\nEnter option number: ").strip()
        if choice == "1":
            print("\nRunning...\n")
            q_script.main()
        elif choice == "2":
            print("\nRunning...\n")
            script_2.main()
        elif choice == "3":
            print("\nRunning...\n")
            script_3.main()
        elif choice == "0":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1, 2, or 0.")

if __name__ == "__main__":
    main()