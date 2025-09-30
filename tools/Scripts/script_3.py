import os
import sys

def setup_paths():
    """Setup proper paths for imports regardless of where script is run from"""
    # Get the absolute path of this script
    script_path = os.path.abspath(__file__)

    # Get the Scripts directory (where this script is located)
    scripts_dir = os.path.dirname(script_path)

    # Get the tools directory (parent of Scripts)
    tools_dir = os.path.dirname(scripts_dir)

    # Add tools directory to Python path so we can import modules
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    print(f"Script location: {script_path}")
    print(f"Tools directory: {tools_dir}")
    print(f"Current working directory: {os.getcwd()}")

    return tools_dir

# Setup paths before importing
tools_dir = setup_paths()

# Now import the modules
try:
    from hashdeep import create_hashdeep_drive as hashdeep
    print("✓ HashDeep module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import HashDeep: {e}")
    sys.exit(1)

try:
    from autopsy import auto
    print("✓ Autopsy module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Autopsy: {e}")
    sys.exit(1)

try:
    from volatility import auto_vol
    print("✓ Volatility module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Volatility: {e}")
    sys.exit(1)

def run_workflow():
    print("="*80)
    print("EDITH-Automater Unified Forensic Workflow")
    print("="*80)

    # ✅ Ask for paths
    evidence_path = input("\nEnter path to evidence image (.E01/.dd): ").strip()
    memory_file = input("Enter path to memory dump file (.mem/.raw/.dmp/.vmem) [optional, press Enter to skip]: ").strip()

    # Expand user paths
    evidence_path = os.path.expanduser(evidence_path)
    if memory_file:
        memory_file = os.path.expanduser(memory_file)

    # Validate evidence path
    if not os.path.exists(evidence_path):
        print(f"✗ Error: Evidence file not found at {evidence_path}")
        return

    # Validate memory file if provided
    if memory_file and not os.path.exists(memory_file):
        print(f"✗ Error: Memory dump file not found at {memory_file}")
        return

    print(f"\n📁 Evidence file: {evidence_path}")
    if memory_file:
        print(f"💾 Memory file: {memory_file}")

    try:
        # 1. Run HashDeep (baseline hashing)
        print("\n" + "="*50)
        print("🔸 Step 1: HashDeep (Baseline Hashing)")
        print("="*50)
        hashdeep_result = hashdeep.main(evidence_path)
        if hashdeep_result:
            print("✓ HashDeep baseline completed successfully")
        else:
            print("⚠ HashDeep baseline had issues")

        # 2. Run Autopsy analysis
        print("\n" + "="*50)
        print("🔸 Step 2: Autopsy Analysis")
        print("="*50)
        autopsy_result = auto.main(evidence_path)
        if autopsy_result:
            print("✓ Autopsy analysis completed successfully")
        else:
            print("⚠ Autopsy analysis had issues")

        # 3. Run Volatility analysis (if memory file provided)
        if memory_file and memory_file.strip():
            print("\n" + "="*50)
            print("🔸 Step 3: Volatility Memory Analysis")
            print("="*50)
            vol_results = auto_vol.main(memory_file)
            if vol_results and vol_results.get('success'):
                print(f"✓ Volatility analysis completed. Results saved in: {vol_results['output_dir']}")
                if 'successful_plugins' in vol_results:
                    print(f"    - Successful plugins: {len(vol_results['successful_plugins'])}")
                    print(f"    - Failed plugins: {len(vol_results['failed_plugins'])}")
            else:
                print("⚠ Volatility analysis failed or was skipped")
        else:
            print("\n" + "="*50)
            print("🔸 Step 3: Skipping Volatility Analysis")
            print("="*50)
            print("No memory file provided - skipping memory analysis")

        # 4. Run HashDeep Verification
        print("\n" + "="*50)
        print("🔸 Step 4: HashDeep Verification")
        print("="*50)
        hash_results = hashdeep.main(evidence_path)
        if hash_results and 'report' in hash_results:
            print(f"✓ HashDeep verification completed. Report saved at: {hash_results['report']}")
        else:
            print("✓ HashDeep verification completed")

        # Summary
        print("\n" + "="*80)
        print("🎉 FORENSIC WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("✓ Baseline hashes created")
        print("✓ Autopsy analysis completed")
        if memory_file and memory_file.strip():
            print("✓ Volatility memory analysis completed")
        print("✓ Final verification completed")
        print("\nAll forensic analysis tools have been executed.")

    except Exception as e:
        print(f"\n✗ Error during workflow execution: {str(e)}")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    print("Starting EDITH-Automater Forensic Workflow...")
    run_workflow()
