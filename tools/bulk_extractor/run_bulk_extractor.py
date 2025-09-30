import subprocess
import os

def run_bulk_extractor(input_file, output_dir, features=None):
    """
    Run bulk_extractor on a given forensic image.

    :param input_file: Path to evidence file (.E01, .dd, etc.)
    :param output_dir: Directory where results will be saved
    :param features: List of features (e.g., ["email", "url", "ccnd"])
    """
    if features is None:
        features = ["email", "url", "ccnd"]  # default features
    
    # Build the command
    cmd = ["bulk_extractor", "-o", output_dir]
    for f in features:
        cmd.extend(["-E", f])
    cmd.append(input_file)

    print("Running:", " ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Extraction complete. Results saved in: {output_dir}")
    except subprocess.CalledProcessError as e:
        print("❌ Error running bulk_extractor:", e)


if __name__ == "__main__":
    # Get the current folder where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Input forensic image (must be placed in the same folder as this script)
    input_file = os.path.join(script_dir, "nps-2010-emails.E01")

    # Output results directory (inside the same folder)
    output_dir = os.path.join(script_dir, "be_results")

    os.makedirs(output_dir, exist_ok=True)
    run_bulk_extractor(input_file, output_dir)
