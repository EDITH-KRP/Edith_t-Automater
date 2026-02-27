#!/usr/bin/env python3
"""
FTK Integration - Final Verification Report
Confirms all components are properly integrated
"""

import sys
from pathlib import Path

# Add tools to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

def verify_integration():
    """Verify FTK module integration"""
    
    print("\n" + "="*80)
    print("FTK MODULE INTEGRATION VERIFICATION")
    print("="*80)
    
    # Test 1: Module Import
    print("\n[TEST 1] Module Imports")
    print("-" * 80)
    try:
        from ftk_metadata import integrate_ftk_with_case, FTKImageAnalyzer, FTKIntegration
        print("✓ FTK module imports successfully")
    except ImportError as e:
        print(f"✗ FTK module import failed: {e}")
        return False
    
    # Test 2: Orchestrator Integration
    print("\n[TEST 2] Orchestrator Integration")
    print("-" * 80)
    try:
        from orchestrator.orchestrator import EDITHOrchestrator, FTK_AVAILABLE
        print(f"✓ Orchestrator imports successfully")
        print(f"  FTK_AVAILABLE = {FTK_AVAILABLE}")
        
        if not FTK_AVAILABLE:
            print("  WARNING: FTK module detected as unavailable")
    except ImportError as e:
        print(f"✗ Orchestrator import failed: {e}")
        return False
    
    # Test 3: FTK Method Available
    print("\n[TEST 3] FTK Processing Method")
    print("-" * 80)
    try:
        o = EDITHOrchestrator()
        
        if hasattr(o, 'process_ftk_image'):
            print("✓ process_ftk_image method available")
        else:
            print("✗ process_ftk_image method not found")
            return False
            
        if hasattr(o, 'run_sequential_workflow'):
            print("✓ Sequential workflow method available")
        else:
            print("✗ Sequential workflow method not found")
            return False
            
    except Exception as e:
        print(f"✗ Failed to instantiate orchestrator: {e}")
        return False
    
    # Test 4: q_script.py Integration
    print("\n[TEST 4] q_script Integration")
    print("-" * 80)
    try:
        from tools.Scripts.q_script import save_case_info, main
        print("✓ q_script imports successfully")
        
        import inspect
        sig = inspect.signature(save_case_info)
        params = list(sig.parameters.keys())
        
        if 'answers' in params:
            print("✓ save_case_info has 'answers' parameter")
        else:
            print("✗ save_case_info missing 'answers' parameter")
            return False
            
    except ImportError as e:
        print(f"✗ q_script import failed: {e}")
        return False
    
    # Test 5: Directory Structure
    print("\n[TEST 5] Directory Structure")
    print("-" * 80)
    from pathlib import Path
    
    ftk_dir = Path(__file__).parent / "tools" / "ftk_metadata"
    
    required_files = [
        "ftk_image_analyzer.py",
        "ftk_integration.py",
        "__init__.py",
        "README.md",
        "INTEGRATION_GUIDE.md",
        "TEST_RESULTS.md"
    ]
    
    all_files_exist = True
    for file in required_files:
        file_path = ftk_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {file} ({size:,} bytes)")
        else:
            print(f"✗ {file} NOT FOUND")
            all_files_exist = False
    
    if not all_files_exist:
        return False
    
    # Test 6: FTK Module Functionality
    print("\n[TEST 6] FTK Module Functionality")
    print("-" * 80)
    try:
        import tempfile
        import os
        
        # Create test image
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.img")
            with open(test_file, 'wb') as f:
                f.write(b"TEST_DATA" * 1000)
            
            # Test analyzer
            analyzer = FTKImageAnalyzer(test_file)
            metadata = analyzer.extract_all_metadata()
            
            required_fields = ['file_name', 'format', 'file_size_bytes', 'md5_hash']
            missing = [f for f in required_fields if f not in metadata]
            
            if missing:
                print(f"✗ Missing metadata fields: {missing}")
                return False
            else:
                print("✓ Metadata extraction working")
                print(f"  - File: {metadata['file_name']}")
                print(f"  - Size: {metadata['file_size_bytes']} bytes")
                print(f"  - MD5: {metadata['md5_hash'][:16]}...")
        
    except Exception as e:
        print(f"✗ FTK module functionality test failed: {e}")
        return False
    
    return True


if __name__ == '__main__':
    success = verify_integration()
    
    print("\n" + "="*80)
    if success:
        print("✅ FTK INTEGRATION VERIFICATION: PASSED")
        print("="*80)
        print("\nAll components verified successfully!")
        print("\nReady to use:")
        print("  python orchestrator/orchestrator.py sequential")
        print("\nOr for interactive mode:")
        print("  python orchestrator/launcher.ps1")
        print("="*80 + "\n")
        exit(0)
    else:
        print("❌ FTK INTEGRATION VERIFICATION: FAILED")
        print("="*80)
        print("\nPlease check the errors above and resolve dependencies")
        print("="*80 + "\n")
        exit(1)
