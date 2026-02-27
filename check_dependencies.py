#!/usr/bin/env python3
"""
EDITH-Automater Dependency Checker
Validates all required dependencies before running forensic workflows
"""

import sys
import subprocess
import importlib
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.results = {
            'critical': [],
            'recommended': [],
            'optional': []
        }
        
    def check_module(self, module_name, package_name=None, level='critical'):
        """Check if a Python module is available"""
        if package_name is None:
            package_name = module_name
            
        try:
            importlib.import_module(module_name)
            return True, f"✓ {package_name}"
        except ImportError:
            msg = f"✗ {package_name} (pip install {package_name})"
            self.results[level].append((package_name, False, msg))
            return False, msg
        except (OSError, Exception) as e:
            # Handle system-level dependency issues (e.g., WeasyPrint on Windows)
            if 'weasyprint' in module_name.lower():
                msg = f"⚠ {package_name} (installed but needs GTK - use reportlab instead)"
                self.results[level].append((package_name, False, msg))
                return False, msg
            msg = f"✗ {package_name} (error: {str(e)[:50]})"
            self.results[level].append((package_name, False, msg))
            return False, msg
    
    def check_binary(self, binary_path, name, level='optional'):
        """Check if a binary file exists"""
        path = Path(binary_path)
        if path.exists():
            return True, f"✓ {name} found"
        else:
            msg = f"✗ {name} not found at {binary_path}"
            self.results[level].append((name, False, msg))
            return False, msg
    
    def run_full_check(self):
        """Run comprehensive dependency check"""
        print("="*80)
        print("EDITH-Automater Dependency Checker")
        print("="*80)
        print()
        
        # Critical Dependencies
        print("🔴 CRITICAL DEPENDENCIES (Required for basic functionality)")
        print("-"*80)
        
        critical = [
            ('reportlab', 'reportlab'),
            ('jinja2', 'jinja2'),
            ('plotly', 'plotly'),
            ('psutil', 'psutil'),
            ('openpyxl', 'openpyxl'),
        ]
        
        critical_ok = 0
        for module, package in critical:
            ok, msg = self.check_module(module, package, 'critical')
            print(f"  {msg}")
            if ok:
                critical_ok += 1
        
        print(f"\nCritical Status: {critical_ok}/{len(critical)} OK")
        print()
        
        # Recommended Dependencies
        print("🟡 RECOMMENDED DEPENDENCIES (For full functionality)")
        print("-"*80)
        
        recommended = [
            ('weasyprint', 'weasyprint'),
            ('playwright', 'playwright'),
            ('volatility3', 'volatility3'),
            ('beautifulsoup4', 'beautifulsoup4'),
            ('requests', 'requests'),
            ('PIL', 'Pillow'),
        ]
        
        recommended_ok = 0
        for module, package in recommended:
            ok, msg = self.check_module(module, package, 'recommended')
            print(f"  {msg}")
            if ok:
                recommended_ok += 1
        
        print(f"\nRecommended Status: {recommended_ok}/{len(recommended)} OK")
        print()
        
        # Optional Dependencies
        print("🟢 OPTIONAL DEPENDENCIES (For advanced features)")
        print("-"*80)
        
        optional = [
            ('pytsk3', 'pytsk3'),
            ('libewf', 'libewf-python'),
            ('yara', 'yara-python'),
            ('scapy', 'scapy'),
        ]
        
        optional_ok = 0
        for module, package in optional:
            ok, msg = self.check_module(module, package, 'optional')
            print(f"  {msg}")
            if ok:
                optional_ok += 1
        
        print(f"\nOptional Status: {optional_ok}/{len(optional)} OK")
        print()
        
        # Check for forensic tool binaries
        print("🔧 FORENSIC TOOL BINARIES")
        print("-"*80)
        
        project_root = Path(__file__).parent
        
        tools_to_check = [
            (project_root / "tools" / "autopsy" / "sleuthkit-4.12.1-win32" / "bin" / "mmls.exe", "Sleuth Kit (mmls)"),
            (project_root / "tools" / "autopsy" / "sleuthkit-4.12.1-win32" / "bin" / "fls.exe", "Sleuth Kit (fls)"),
            (project_root / "tools" / "exiftool" / "bin" / "exiftool.exe", "ExifTool"),
            (project_root / "tools" / "volatility" / "volatility3" / "vol.py", "Volatility3"),
        ]
        
        tools_ok = 0
        for tool_path, tool_name in tools_to_check:
            ok, msg = self.check_binary(tool_path, tool_name, 'optional')
            print(f"  {msg}")
            if ok:
                tools_ok += 1
        
        print(f"\nTools Status: {tools_ok}/{len(tools_to_check)} OK")
        print()
        
        # Summary and recommendations
        print("="*80)
        print("SUMMARY & RECOMMENDATIONS")
        print("="*80)
        
        # Overall status
        if critical_ok == len(critical):
            print("✅ READY FOR DEMO: All critical dependencies installed!")
            print()
            if recommended_ok < len(recommended):
                print("⚠️  Consider installing recommended packages for full functionality:")
                for name, ok, msg in self.results['recommended']:
                    if not ok:
                        print(f"    pip install {name}")
            return True
        else:
            print("❌ NOT READY: Missing critical dependencies!")
            print()
            print("Install these packages immediately:")
            print()
            missing_critical = [name for name, ok, _ in self.results['critical'] if not ok]
            if missing_critical:
                print(f"    pip install {' '.join(missing_critical)}")
            print()
            return False
    
    def generate_install_script(self):
        """Generate a script to install all missing dependencies"""
        script_path = Path(__file__).parent / "install_missing_deps.bat"
        
        missing_packages = []
        for level in ['critical', 'recommended']:
            for name, ok, _ in self.results[level]:
                if not ok:
                    missing_packages.append(name)
        
        if missing_packages:
            with open(script_path, 'w') as f:
                f.write("@echo off\n")
                f.write("echo Installing missing dependencies for EDITH-Automater...\n")
                f.write("echo.\n")
                f.write(f"pip install {' '.join(missing_packages)}\n")
                f.write("echo.\n")
                f.write("echo Installation complete! Run this script again to verify.\n")
                f.write("pause\n")
            
            print(f"\n📝 Installation script generated: {script_path}")
            print(f"   Run it to install all missing packages at once.\n")
            return str(script_path)
        return None


def main():
    """Main entry point"""
    checker = DependencyChecker()
    ready = checker.run_full_check()
    
    # Generate install script if needed
    if not ready:
        checker.generate_install_script()
        print("\n💡 TIP: Run install_missing_deps.bat to fix all issues automatically\n")
        sys.exit(1)
    else:
        print("\n🚀 System is ready for forensic analysis!\n")
        print("Next steps:")
        print("  1. cd tools\\Scripts")
        print("  2. python q_script.py  (to collect evidence)")
        print("  3. python script_3.py  (to run forensic analysis)")
        print("\nOr use the orchestrator for automated workflows:")
        print("  python orchestrator\\orchestrator.py --help\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
