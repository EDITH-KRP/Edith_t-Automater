import q_script
import script_2
import script_3

def main():
    print("="*50)
    print("      Welcome to the EDITH Automation Main Menu")
    print("="*50)
    print("Choose an option to run:")
    print("1. Answer Questions for Digital Evidence Collection")
    print("2. Run Digital Evidence Collection")
    print("3. Run Tools for Forensic Analysis")
    print("0. Exit")

    while True:
        choice = input("\nEnter option number: ").strip()
        if choice == "1":
            print("\nRunning...\n")
            result = q_script.main()
            print("\nResult:", result)
        elif choice == "2":
            print("\nRunning...\n")
            result = script_2.main()
            print("\nResult:", result)    
        elif choice == "3":
            print("\nRunning...\n")
            result = script_3.main()
            print("\nResult:", result)
        elif choice == "0":
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid option. Please enter 1, 2, or 0.")

if __name__ == "__main__":
    main()