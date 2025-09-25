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
    # Example usage
    input_file = "/mnt/c/Users/Sabiha Anjum/Downloads/nps-2010-emails.E01"
    output_dir = "/mnt/c/Users/Sabiha Anjum/Downloads/be_results"

    os.makedirs(output_dir, exist_ok=True)
    run_bulk_extractor(input_file, output_dir)
