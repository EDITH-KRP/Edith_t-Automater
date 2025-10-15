import subprocess
import os
import glob
import json
import sys
from datetime import datetime
from pathlib import Path

class VolatilityAnalyzer:
    def __init__(self, custom_results_dir=None):
        # Get current script directory and set relative paths
        self.script_dir = Path(__file__).parent.absolute()
        self.vol_path = self.script_dir / "volatility3" / "vol.py"
        self.mem_dir = self.script_dir / "mem"
        
        # Get the correct Python executable
        self.python_executable = self.get_python_executable()
        
        # Use custom results directory if provided, otherwise use default
        if custom_results_dir:
            self.results_dir = Path(custom_results_dir)
        else:
            self.results_dir = self.script_dir / "results"
        
        # Create necessary directories
        self.mem_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        # Comprehensive plugin list organized by category
        self.plugin_categories = {
            "process_analysis": [
                ("windows.pslist", "Process listing with PID, PPID, threads, handles"),
                ("windows.pstree", "Process tree hierarchy"),
                ("windows.psxview", "Cross-reference process listings"),
                ("windows.cmdline", "Command line arguments for processes"),
                ("windows.dlllist", "DLL modules loaded by processes"),
                ("windows.handles", "Open handles for processes"),
                ("windows.getsids", "Security identifiers for processes")
            ],
            "network_analysis": [
                ("windows.netscan", "Network connections and sockets"),
                ("windows.netstat", "Network statistics")
            ],
            "registry_analysis": [
                ("windows.registry.hivelist", "Registry hive locations"),
                ("windows.registry.printkey", "Registry key contents"),
                ("windows.registry.userassist", "User assist registry entries")
            ],
            "malware_detection": [
                ("windows.malfind", "Malicious code injection detection"),
                ("windows.driverirp", "Driver IRP analysis"),
                ("windows.ssdt", "System Service Descriptor Table"),
                ("windows.callbacks", "Kernel callbacks"),
                ("windows.devicetree", "Device tree analysis")
            ],
            "file_analysis": [
                ("windows.filescan", "File objects in memory"),
                ("windows.dumpfiles", "Extract files from memory")
            ],
            "system_info": [
                ("windows.info", "System information"),
                ("windows.envars", "Environment variables"),
                ("windows.privileges", "Process privileges"),
                ("windows.sessions", "User sessions")
            ]
        }
        
        # Default plugins for quick analysis
        self.default_plugins = [
            "windows.info", "windows.pslist", "windows.pstree", 
            "windows.cmdline", "windows.netscan", "windows.malfind",
            "windows.filescan", "windows.registry.hivelist"
        ]

    def get_python_executable(self):
        """Get the correct Python executable, preferring virtual environment"""
        # Try to find the virtual environment Python
        project_root = self.script_dir.parent.parent
        venv_python = project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            return str(venv_python)
        
        # Fall back to current sys.executable
        return sys.executable

    def find_memory_files(self):
        """Find all memory dump files in the mem directory"""
        memory_extensions = ['*.mem', '*.dmp', '*.raw', '*.vmem', '*.dd', '*.bin', '*.sav']
        memory_files = []
        
        for ext in memory_extensions:
            memory_files.extend(glob.glob(str(self.mem_dir / ext)))
        
        return memory_files

    def detect_os_profile(self, memory_file):
        """Detect the operating system profile of the memory dump"""
        print(f"[+] Detecting OS profile for {os.path.basename(memory_file)}...")
        
        try:
            result = subprocess.run(
                [self.python_executable, str(self.vol_path), "-f", memory_file, "windows.info"],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0 and "windows" in result.stdout.lower():
                return "windows"
            else:
                # Try Linux profile
                result = subprocess.run(
                    [self.python_executable, str(self.vol_path), "-f", memory_file, "linux.info"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    return "linux"
                    
        except subprocess.TimeoutExpired:
            print(f"[-] OS detection timed out for {memory_file}")
        except Exception as e:
            print(f"[-] Error detecting OS: {e}")
            
        return "windows"  # Default to Windows

    def run_plugin(self, memory_file, plugin, output_file, description=""):
        """Run a single Volatility plugin"""
        print(f"[+] Running {plugin}... {description}")
        
        try:
            with open(output_file, "w", encoding='utf-8') as f:
                result = subprocess.run(
                    [self.python_executable, str(self.vol_path), "-f", memory_file, plugin],
                    stdout=f, stderr=subprocess.PIPE, text=True, timeout=300
                )
                
            if result.returncode == 0:
                print(f"    ✓ {plugin} completed successfully")
                return True
            else:
                print(f"    ✗ {plugin} failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"    ⚠ {plugin} timed out (5 minutes)")
            return False
        except Exception as e:
            print(f"    ✗ {plugin} error: {e}")
            return False

    def run_comprehensive_analysis(self, memory_file, quick_mode=False):
        """Run comprehensive memory analysis"""
        print(f"\n{'='*80}")
        print(f"VOLATILITY MEMORY ANALYSIS")
        print(f"File: {os.path.basename(memory_file)}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Create output directory for this memory file
        base_name = Path(memory_file).stem
        output_dir = self.results_dir / f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(exist_ok=True)
        
        # Detect OS profile
        os_profile = self.detect_os_profile(memory_file)
        print(f"[+] Detected OS: {os_profile}")
        
        # Create analysis report
        analysis_report = {
            "memory_file": memory_file,
            "analysis_timestamp": datetime.now().isoformat(),
            "os_profile": os_profile,
            "plugins_run": [],
            "successful_plugins": [],
            "failed_plugins": []
        }
        
        # Choose plugins based on mode
        if quick_mode:
            plugins_to_run = [(plugin, f"Quick analysis plugin") for plugin in self.default_plugins]
        else:
            plugins_to_run = []
            for category, plugins in self.plugin_categories.items():
                print(f"\n[+] Running {category.replace('_', ' ').title()} plugins...")
                for plugin, description in plugins:
                    # Adjust plugin prefix based on OS
                    if os_profile == "linux" and plugin.startswith("windows."):
                        plugin = plugin.replace("windows.", "linux.")
                    plugins_to_run.append((plugin, description))
        
        # Run plugins
        total_plugins = len(plugins_to_run)
        successful_count = 0
        
        for i, (plugin, description) in enumerate(plugins_to_run, 1):
            print(f"\n[{i}/{total_plugins}] ", end="")
            
            output_file = output_dir / f"{plugin.replace('.', '_')}.txt"
            success = self.run_plugin(memory_file, plugin, output_file, description)
            
            analysis_report["plugins_run"].append(plugin)
            if success:
                analysis_report["successful_plugins"].append(plugin)
                successful_count += 1
            else:
                analysis_report["failed_plugins"].append(plugin)
        
        # Save analysis report
        report_file = output_dir / "analysis_report.json"
        with open(report_file, "w") as f:
            json.dump(analysis_report, f, indent=2)
        
        # Print summary
        print(f"\n{'='*80}")
        print(f"ANALYSIS COMPLETE")
        print(f"{'='*80}")
        print(f"Memory file: {os.path.basename(memory_file)}")
        print(f"Total plugins: {total_plugins}")
        print(f"Successful: {successful_count}")
        print(f"Failed: {total_plugins - successful_count}")
        print(f"Results saved in: {output_dir}")
        print(f"Analysis report: {report_file}")
        
        return {
            "output_dir": str(output_dir),
            "report_file": str(report_file),
            "total_plugins": total_plugins,
            "successful_plugins": successful_count,
            "failed_plugins": total_plugins - successful_count
        }

    def run_analysis(self, quick_mode=False, specific_file=None):
        """Main analysis function"""
        if not self.vol_path.exists():
            print(f"[-] Volatility3 not found at {self.vol_path}")
            print("    Please ensure Volatility3 is installed in the volatility3 folder")
            return None
        
        # Find memory files
        if specific_file:
            if os.path.exists(specific_file):
                memory_files = [specific_file]
            else:
                print(f"[-] Specified memory file not found: {specific_file}")
                return None
        else:
            memory_files = self.find_memory_files()
        
        if not memory_files:
            print(f"[-] No memory dump files found in {self.mem_dir}")
            print("    Supported formats: .mem, .dmp, .raw, .vmem, .dd, .bin, .sav")
            return None
        
        print(f"[+] Found {len(memory_files)} memory file(s):")
        for i, mf in enumerate(memory_files, 1):
            print(f"    {i}. {os.path.basename(mf)}")
        
        results = []
        for memory_file in memory_files:
            try:
                result = self.run_comprehensive_analysis(memory_file, quick_mode)
                if result:
                    results.append(result)
            except KeyboardInterrupt:
                print("\n[!] Analysis interrupted by user")
                break
            except Exception as e:
                print(f"[-] Error analyzing {memory_file}: {e}")
        
        return results

def run_volatility(quick_mode=False, memory_file=None, output_dir=None):
    """Main function for external calls"""
    analyzer = VolatilityAnalyzer(custom_results_dir=output_dir)
    return analyzer.run_analysis(quick_mode=quick_mode, specific_file=memory_file)

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Volatility3 Memory Analysis Tool")
    parser.add_argument("-q", "--quick", action="store_true", 
                       help="Run quick analysis with essential plugins only")
    parser.add_argument("-f", "--file", type=str, 
                       help="Specific memory file to analyze")
    
    args = parser.parse_args()
    
    analyzer = VolatilityAnalyzer()
    results = analyzer.run_analysis(quick_mode=args.quick, specific_file=args.file)
    
    if results:
        print(f"\n✅ Analysis completed successfully for {len(results)} file(s)")
    else:
        print("\n❌ Analysis failed or no files processed")
        sys.exit(1)

if __name__ == "__main__":
    main()

