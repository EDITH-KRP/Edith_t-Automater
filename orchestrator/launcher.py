"""
EDITH-Automater Launcher
Portable executable entry point for Windows/Mac/Linux
Handles initialization and launches the main orchestrator
"""

import sys
import os
from pathlib import Path

def check_environment():
    """Check and initialize runtime environment"""
    print("=" * 70)
    print("EDITH-Automater - Digital Forensic Analysis System")
    print("=" * 70)
    print("\nInitializing forensic environment...")
    
    # Detect OS
    system = sys.platform.lower()
    if system == "win32":
        os_name = "Windows"
    elif system == "darwin":
        os_name = "macOS"
    elif system == "linux":
        os_name = "Linux"
    else:
        os_name = "Unknown"
    
    print(f"✓ Operating System: {os_name}")
    print(f"✓ Python Version: {sys.version.split()[0]}")
    
    # Check for required directories
    base_dir = Path(__file__).parent
    required_dirs = [
        "tools/analysis_reporter",
        "tools/ftk_metadata",
        "tools/Scripts",
        "reports",
        "case_templates",
    ]
    
    all_present = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - NOT FOUND (may be optional)")
            all_present = False
    
    print("\n" + "=" * 70)
    return all_present

def launch_orchestrator():
    """Launch the main orchestrator"""
    try:
        # Add current directory to path for imports
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import and launch orchestrator
        from orchestrator.orchestrator import ForensicOrchestrator
        from orchestrator.orchestrator import main as orchestrator_main
        
        print("\n🚀 Launching Forensic Orchestrator...\n")
        
        # Run the orchestrator
        orchestrator_main()
        
    except ImportError as e:
        print(f"\n❌ ERROR: Failed to import orchestrator modules")
        print(f"   Details: {str(e)}")
        print(f"\n   This may indicate a corrupted executable.")
        print(f"   Please download a fresh copy from the repository.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        # Check environment
        env_ok = check_environment()
        
        # Launch orchestrator
        launch_orchestrator()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Orchestrator stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
