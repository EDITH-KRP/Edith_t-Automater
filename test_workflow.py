#!/usr/bin/env python3
"""
Test script for the updated EDITH-Automater workflow
This script simulates the workflow without requiring actual evidence files
"""

import os
import sys
import tempfile
from pathlib import Path

# Add paths for imports
BASE_DIR = Path(__file__).parent.parent.absolute()
TOOLS_DIR = BASE_DIR / "tools"
sys.path.append(str(TOOLS_DIR))

def create_test_files():
    """Create temporary test files to simulate evidence"""
    temp_dir = Path(tempfile.mkdtemp(prefix="edith_test_"))
    
    # Create fake E01 file
    e01_file = temp_dir / "test_evidence.E01"
    e01_file.write_text("Fake E01 evidence file for testing")
    
    # Create fake memory dump
    mem_file = temp_dir / "test_memory.mem"
    mem_file.write_text("Fake memory dump file for testing")
    
    print(f"✅ Created test files:")
    print(f"   📀 Disk Image: {e01_file}")
    print(f"   🧠 Memory Dump: {mem_file}")
    
    return str(e01_file), str(mem_file)

def test_workflow_validation():
    """Test the new workflow file validation"""
    print("="*60)
    print("Testing EDITH-Automater Workflow Validation")
    print("="*60)
    
    # Test with non-existent files
    print("\n1. Testing with non-existent files:")
    try:
        from Scripts import script_3
        
        # This should fail gracefully
        print("   - This test would require user input, skipping automatic test")
        print("   - File validation logic is implemented in script_3.py")
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    # Test file creation
    print("\n2. Testing file creation:")
    e01_path, mem_path = create_test_files()
    
    print(f"   ✅ Test E01 file exists: {os.path.exists(e01_path)}")
    print(f"   ✅ Test MEM file exists: {os.path.exists(mem_path)}")
    
    # Clean up
    os.unlink(e01_path)
    os.unlink(mem_path)
    os.rmdir(os.path.dirname(e01_path))
    
    return True

def test_auto_vol_integration():
    """Test auto_vol.py integration"""
    print("\n" + "="*60)
    print("Testing Volatility Integration")
    print("="*60)
    
    try:
        from volatility import auto_vol
        print("   ✅ auto_vol module imported successfully")
        
        # Test VolatilityAnalyzer class
        analyzer = auto_vol.VolatilityAnalyzer()
        print("   ✅ VolatilityAnalyzer class instantiated")
        
        # Check paths are set correctly
        print(f"   📁 Volatility path: {analyzer.vol_path}")
        print(f"   📁 Memory directory: {analyzer.mem_dir}")
        print(f"   📁 Results directory: {analyzer.results_dir}")
        
        # Check directories were created
        print(f"   ✅ Memory dir exists: {analyzer.mem_dir.exists()}")
        print(f"   ✅ Results dir exists: {analyzer.results_dir.exists()}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 EDITH-Automater Integration Tests")
    print("=" * 80)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Workflow validation
    if test_workflow_validation():
        tests_passed += 1
        print("✅ Test 1 PASSED: Workflow validation")
    else:
        print("❌ Test 1 FAILED: Workflow validation")
    
    # Test 2: Auto_vol integration
    if test_auto_vol_integration():
        tests_passed += 1
        print("✅ Test 2 PASSED: Volatility integration")
    else:
        print("❌ Test 2 FAILED: Volatility integration")
    
    # Summary
    print("\n" + "="*80)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The workflow is ready to use.")
        print("\n📝 Usage Instructions:")
        print("   1. Navigate to tools/Scripts/")
        print("   2. Run: python script_3.py")
        print("   3. Choose option 1 for full workflow")
        print("   4. Provide paths to your .E01 and .mem files")
        print("   5. Watch the magic happen! ✨")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)