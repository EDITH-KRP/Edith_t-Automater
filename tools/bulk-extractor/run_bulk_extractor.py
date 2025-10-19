import subprocess
import os
import sys

# Scanners available in your bulk_extractor build
VALID_SCANNERS = ["email", "base16", "hiberfile", "outlook", "wordlist", "xor"]

def run_bulk_extractor(input_file, output_dir=None):
    if not os.path.exists(input_file):
        print(f" File not found: {input_file}")
        return

    # Use provided output directory or default
    if output_dir is None:
        # Save results in the bulk_extractor directory (current script's parent directory)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bulk_extractor_dir = os.path.join(script_dir, "bulk_extractor")
        output_dir = os.path.join(bulk_extractor_dir, "be_results")
    
    os.makedirs(output_dir, exist_ok=True)

    # Try to use our Python implementation first
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bulk_extractor_py = os.path.join(script_dir, "bulk_extractor.py")
    
    if os.path.exists(bulk_extractor_py):
        print("==> Using Python-based bulk_extractor alternative")
        try:
            # Import and run our bulk extractor alternative
            sys.path.insert(0, script_dir)
            from bulk_extractor import BulkExtractorAlternative
            
            extractor = BulkExtractorAlternative()
            success = extractor.run_extraction(input_file, output_dir)
            if success:
                print(f"\n[SUCCESS] Extraction complete. Results saved in: {output_dir}")
                return
            else:
                print(f"[ERROR] Python bulk_extractor failed")
                return
        except ImportError as e:
            print(f"[ERROR] Could not import bulk_extractor module: {e}")
            print("Falling back to command line version...")
        except Exception as e:
            print(f"[ERROR] Error with Python implementation: {e}")
            print("Falling back to command line version...")

    # Fallback to command line version
    # Build command with all valid scanners
    cmd = ["bulk_extractor", "-o", output_dir]
    for scanner in VALID_SCANNERS:
        cmd.extend(["-E", scanner])
    cmd.append(input_file)

    print(" Running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print(f"\n[SUCCESS] Extraction complete. Results saved in: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(" Error running bulk_extractor:", e)
    except FileNotFoundError:
        print(" Error: bulk_extractor executable not found")
        print("💡 Please install bulk_extractor or use the Python alternative")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        # Called with command line arguments
        input_file = sys.argv[1]
        output_dir = sys.argv[2]
        run_bulk_extractor(input_file, output_dir)
    elif len(sys.argv) == 2:
        # Called with just input file
        input_file = sys.argv[1]
        run_bulk_extractor(input_file)
    else:
        # Interactive mode
        input_file = input("Enter the full path of the forensic image: ").strip()
        run_bulk_extractor(input_file)