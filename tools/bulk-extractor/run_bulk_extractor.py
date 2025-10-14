import subprocess
import os
import sys

# Scanners available in your bulk_extractor build
VALID_SCANNERS = ["email", "base16", "hiberfile", "outlook", "wordlist", "xor"]

def run_bulk_extractor(input_file):
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return

    # Save results in the bulk_extractor directory (current script's parent directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bulk_extractor_dir = os.path.join(script_dir, "bulk_extractor")
    output_dir = os.path.join(bulk_extractor_dir, "be_results")
    os.makedirs(output_dir, exist_ok=True)

    # Try to use our Python implementation first
    bulk_extractor_py = os.path.join(script_dir, "bulk_extractor.py")
    
    if os.path.exists(bulk_extractor_py):
        print("🚀 Using Python-based bulk_extractor alternative")
        try:
            # Import and run our bulk extractor alternative
            sys.path.insert(0, script_dir)
            from bulk_extractor import BulkExtractorAlternative
            
            extractor = BulkExtractorAlternative()
            extractor.run_extraction(input_file, output_dir)
            print(f"\n✅ Extraction complete. Results saved in: {output_dir}")
            return
        except Exception as e:
            print(f"❌ Error with Python implementation: {e}")
            print("Falling back to command line version...")

    # Fallback to command line version with Windows compatibility
    # Check for bulk_extractor executable
    bulk_extractor_exe = None
    
    if os.name == 'nt':  # Windows
        # Check for bulk_extractor.exe in current directory
        local_exe = os.path.join(script_dir, "bulk_extractor.exe")
        if os.path.exists(local_exe):
            bulk_extractor_exe = local_exe
        else:
            # Check for bulk_extractor in PATH
            try:
                result = subprocess.run(['where', 'bulk_extractor'], capture_output=True, text=True)
                if result.returncode == 0:
                    bulk_extractor_exe = 'bulk_extractor'
            except:
                pass
    else:
        # Linux/Mac
        try:
            result = subprocess.run(['which', 'bulk_extractor'], capture_output=True, text=True)
            if result.returncode == 0:
                bulk_extractor_exe = 'bulk_extractor'
        except:
            pass
    
    if not bulk_extractor_exe:
        print("❌ bulk_extractor executable not found")
        print("Please install bulk_extractor or place bulk_extractor.exe in the tools/bulk-extractor directory")
        return

    # Build command with all valid scanners
    cmd = [bulk_extractor_exe, "-o", output_dir]
    for scanner in VALID_SCANNERS:
        cmd.extend(["-E", scanner])
    cmd.append(input_file)

    print("🚀 Running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Extraction complete. Results saved in: {output_dir}")
    except subprocess.CalledProcessError as e:
        print("❌ Error running bulk_extractor:", e)
    except FileNotFoundError:
        print("❌ bulk_extractor executable not found in PATH")
        print("Please install bulk_extractor or add it to your system PATH")
    except FileNotFoundError:
        print("❌ bulk_extractor executable not found")
        print("💡 Please install bulk_extractor or use the Python alternative")

if __name__ == "__main__":
    input_file = input("Enter the full path of the forensic image: ").strip()
    run_bulk_extractor(input_file)