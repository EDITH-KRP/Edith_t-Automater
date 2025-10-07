#!/usr/bin/env python3

"""
Quick test to verify bulk-extractor integration fix
"""

import os
import sys

# Test just the bulk-extractor part
def test_bulk_extractor_output():
    print("🧪 Testing Bulk-Extractor Output Generation")
    print("="*50)
    
    # Create a test image file with some content
    test_image = "/tmp/test_evidence.dd"
    test_output = "/tmp/test_bulk_output"
    
    # Create sample data file
    with open(test_image, 'w') as f:
        f.write("test@example.com\n")
        f.write("https://www.google.com\n") 
        f.write("password123\n")
        f.write("admin@company.org\n")
        f.write("192.168.1.1\n")
    
    print(f"📁 Created test image: {test_image}")
    print(f"📏 Size: {os.path.getsize(test_image)} bytes")
    
    # Import our function
    sys.path.append('/home/shirish/Project/Zetpeak/Edith_t-Automater/tools/Scripts')
    from script_3 import run_bulk_extractor_with_custom_output
    
    # Test the function
    print(f"\n🚀 Running bulk-extractor on test image...")
    try:
        success = run_bulk_extractor_with_custom_output(test_image, test_output)
        
        if success:
            print("✅ Bulk-extractor completed successfully!")
            
            # Check what files were created
            if os.path.exists(test_output):
                files = os.listdir(test_output)
                print(f"📁 Files created: {len(files)}")
                for f in files:
                    file_path = os.path.join(test_output, f)
                    size = os.path.getsize(file_path)
                    print(f"   📄 {f}: {size} bytes")
            else:
                print("❌ Output directory not created")
        else:
            print("❌ Bulk-extractor failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Cleanup
    if os.path.exists(test_image):
        os.remove(test_image)
    print(f"\n🧹 Cleaned up test files")

if __name__ == "__main__":
    test_bulk_extractor_output()