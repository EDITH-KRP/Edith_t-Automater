import subprocess
import os
import sys

def run_volatility():
    # Get the current directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Prompt user for memory dump file path
    print("=== Volatility Memory Analysis Automation ===")
    memory_file = input("Enter the path to the memory dump file (.mem, .raw, .dmp, .vmem): ").strip()
    
    # Expand user path if needed
    memory_file = os.path.expanduser(memory_file)
    
    # Check if the file exists
    if not os.path.exists(memory_file):
        print(f"Error: Memory dump file not found at {memory_file}")
        return
    
    # Check if it's a valid memory dump file
    valid_extensions = ('.mem', '.raw', '.dmp', '.vmem')
    if not memory_file.lower().endswith(valid_extensions):
        print(f"Warning: File doesn't have a typical memory dump extension {valid_extensions}")
        proceed = input("Do you want to proceed anyway? (y/n): ").strip().lower()
        if proceed != 'y':
            return
    
    print(f"Using memory file: {memory_file}")
    
    vol_path = os.path.join(script_dir, "volatility3", "vol.py")
    if not os.path.exists(vol_path):
        print(f"Error: vol.py not found at {vol_path}")
        return
    
    output_dir = os.path.join(script_dir, "results")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    plugins = [
        ("windows.pslist", "processes.json"),
        ("windows.dlllist", "dlls.json"),
        ("windows.cmdline", "cmdline.json"),
        ("windows.netstat", "netstat.json"),  # Changed from netscan to netstat
        ("windows.handles", "handles.json"),
        ("windows.malfind", "malfind.json"),
        ("windows.registry.printkey", "registry_keys.json"),
        ("windows.filescan", "filescan.json"),  # Added file scanning
        ("windows.info", "system_info.json"),  # Added system info
    ]

    for plugin, outfile in plugins:
        print(f"[+] Running {plugin}...")
        output_file = os.path.join(output_dir, outfile)
        try:
            with open(output_file, "w") as f:
                result = subprocess.run(
                    ["python3", vol_path, "-f", memory_file, plugin],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    print(f"    Warning: {plugin} failed with error: {result.stderr.strip()}")
                else:
                    print(f"    ✓ {plugin} completed successfully")
        except Exception as e:
            print(f"    Error running {plugin}: {str(e)}")

    print(f"\nAnalysis complete. Results saved in {output_dir}")
    return {"success": True, "output_dir": output_dir}

def run_volatility_with_path(memory_file_path):
    """
    Run volatility analysis with a provided memory file path.
    This function is designed to be called from other scripts.
    """
    # Get the current directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Expand user path if needed
    memory_file = os.path.expanduser(memory_file_path)
    
    # Check if the file exists
    if not os.path.exists(memory_file):
        print(f"Error: Memory dump file not found at {memory_file}")
        return {"success": False, "error": "File not found"}
    
    # Check if it's a valid memory dump file
    valid_extensions = ('.mem', '.raw', '.dmp', '.vmem')
    if not memory_file.lower().endswith(valid_extensions):
        print(f"Warning: File doesn't have a typical memory dump extension {valid_extensions}")
        print("Proceeding with analysis anyway...")
    
    print(f"Using memory file: {memory_file}")
    
    vol_path = os.path.join(script_dir, "volatility3", "vol.py")
    if not os.path.exists(vol_path):
        print(f"Error: vol.py not found at {vol_path}")
        return {"success": False, "error": "Volatility3 not found"}
    
    output_dir = os.path.join(script_dir, "results")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    plugins = [
        ("windows.pslist", "processes.json"),
        ("windows.dlllist", "dlls.json"),
        ("windows.cmdline", "cmdline.json"),
        ("windows.netstat", "netstat.json"),  # Changed from netscan to netstat
        ("windows.handles", "handles.json"),
        ("windows.malfind", "malfind.json"),
        ("windows.registry.printkey", "registry_keys.json"),
        ("windows.filescan", "filescan.json"),  # Added file scanning
        ("windows.info", "system_info.json"),  # Added system info
    ]

    successful_plugins = []
    failed_plugins = []

    for plugin, outfile in plugins:
        print(f"[+] Running {plugin}...")
        output_file = os.path.join(output_dir, outfile)
        try:
            with open(output_file, "w") as f:
                result = subprocess.run(
                    ["python3", vol_path, "-f", memory_file, plugin],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    print(f"    Warning: {plugin} failed with error: {result.stderr.strip()}")
                    failed_plugins.append(plugin)
                else:
                    print(f"    ✓ {plugin} completed successfully")
                    successful_plugins.append(plugin)
        except Exception as e:
            print(f"    Error running {plugin}: {str(e)}")
            failed_plugins.append(plugin)

    print(f"\nAnalysis complete. Results saved in {output_dir}")
    
    return {
        "success": True, 
        "output_dir": output_dir,
        "successful_plugins": successful_plugins,
        "failed_plugins": failed_plugins,
        "total_plugins": len(plugins)
    }

def main(memory_file_path=None):
    """
    Main function that can be called from other scripts.
    If no path is provided, it will prompt for input.
    """
    if memory_file_path:
        return run_volatility_with_path(memory_file_path)
    else:
        return run_volatility()

    plugins = [
        ("windows.pslist", "processes.json"),
        ("windows.dlllist", "dlls.json"),
        ("windows.cmdline", "cmdline.json"),
        ("windows.netstat", "netstat.json"),  # Changed from netscan to netstat
        ("windows.handles", "handles.json"),
        ("windows.malfind", "malfind.json"),
        ("windows.registry.printkey", "registry_keys.json"),
        ("windows.filescan", "filescan.json"),  # Added file scanning
        ("windows.info", "system_info.json"),  # Added system info
    ]

    for plugin, outfile in plugins:
        print(f"[+] Running {plugin}...")
        output_file = os.path.join(output_dir, outfile)
        try:
            with open(output_file, "w") as f:
                result = subprocess.run(
                    ["python3", vol_path, "-f", memory_file, plugin],
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode != 0:
                    print(f"    Warning: {plugin} failed with error: {result.stderr.strip()}")
                else:
                    print(f"    ✓ {plugin} completed successfully")
        except Exception as e:
            print(f"    Error running {plugin}: {str(e)}")

    print(f"\nAnalysis complete. Results saved in {output_dir}")

if __name__ == "__main__":
    run_volatility()

