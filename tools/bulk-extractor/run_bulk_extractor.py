import subprocess
import os

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

    # Build command with all valid scanners
    cmd = ["bulk_extractor", "-o", output_dir]
    for scanner in VALID_SCANNERS:
        cmd.extend(["-E", scanner])
    cmd.append(input_file)

    print("🚀 Running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Extraction complete. Results saved in: {output_dir}")
    except subprocess.CalledProcessError as e:
        print("❌ Error running bulk_extractor:", e)

if __name__ == "__main__":
    input_file = input("Enter the full path of the forensic image: ").strip()
    run_bulk_extractor(input_file)
