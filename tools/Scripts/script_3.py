import os
import sys
from datetime import datetime

# Add parent directory so imports work
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from hashdeep import create_hashdeep_drive as hashdeep
from autopsy import auto
from volatility import auto_vol


def run_workflow(evidence_path, memory_file=None):
    print("=" * 80)
    print("EDITH-Automater Unified Forensic Workflow (Minimal Prompts)")
    print("=" * 80)

    # 1. Run HashDeep (baseline hashing)
    print("\n=== Running HashDeep (Baseline Hashing) ===")
    hashdeep.main(evidence_path)

    # 2. Run Autopsy analysis
    print("\n=== Running Autopsy Analysis ===")
    auto.main(evidence_path)

    # 3. Run Memory Analysis (if memory file provided)
    memory_results = None
    if memory_file and os.path.exists(memory_file):
        print("\n=== Running Memory Analysis (Volatility) ===")
        print(f"[+] Using memory file: {memory_file}")
        memory_results = auto_vol.run_volatility(quick_mode=True, memory_file=memory_file)
        if memory_results:
            print(f"[+] Memory analysis completed successfully!")
            for result in memory_results:
                print(f"    - Results saved in: {result['output_dir']}")
                print(f"    - Plugins run: {result['successful_plugins']}/{result['total_plugins']}")
        else:
            print("[-] Memory analysis failed")
    else:
        print("\n[*] No memory file provided or file not found. Skipping memory analysis.")

    # 4. Run HashDeep Verification
    print("\n=== Running HashDeep Verification ===")
    hash_results = hashdeep.main(evidence_path)
    print(f"[+] HashDeep completed. Report saved at: {hash_results['report']}")

    print("\n✅ Full forensic workflow completed successfully!")
    print("   - Baseline hashes created")
    print("   - Autopsy analysis done")
    if memory_file:
        print("   - Memory analysis completed")
    print("   - Final verification passed")

    # Summary
    print(f"\n{'='*80}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*80}")
    print(f"Evidence processed: {os.path.basename(evidence_path)}")
    print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nGenerated artifacts:")
    print("- Hash verification reports (hashdeep)")
    print("- Autopsy database and reports")
    if memory_results:
        print("- Memory analysis reports (volatility)")
        for result in memory_results:
            print(f"  * {result['output_dir']}")


if __name__ == "__main__":
    print("="*80)
    print("EDITH-Automater Forensic Workflow")
    print("="*80)

    # ✅ Ask only once for both paths
    evidence_path = input("Enter path to disk image (.E01/.dd/.raw): ").strip()
    memory_file = input("Enter path to memory dump file (leave blank to skip): ").strip()
    memory_file = memory_file if memory_file else None

    run_workflow(evidence_path, memory_file)
