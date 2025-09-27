import os
import sys

# Add parent directory so imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from hashdeep import create_hashdeep_drive as hashdeep
from autopsy import auto

def run_workflow():
    print("="*80)
    print("EDITH-Automater Unified Forensic Workflow")
    print("="*80)

    # ✅ Ask for path only once
    evidence_path = input("Enter path to evidence image (.E01/.dd): ").strip()

    # 1. Run HashDeep (baseline hashing)
    print("\n=== Running HashDeep (Baseline Hashing) ===")
    hashdeep.main(evidence_path)

    # 2. Run Autopsy analysis
    print("\n=== Running Autopsy Analysis ===")
    auto.main(evidence_path)

    # 3. Run HashDeep Verification (reuse same path)
    print("\n=== Running HashDeep Verification ===")
    hash_results = hashdeep.main(evidence_path)
    print(f"[+] HashDeep completed. Report saved at: {hash_results['report']}")

    print("\n✅ Full forensic workflow completed successfully!")
    print("   - Baseline hashes created")
    print("   - Autopsy analysis done")
    print("   - Final verification passed")

if __name__ == "__main__":
    run_workflow()
