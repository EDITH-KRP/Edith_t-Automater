import subprocess
import os

def run_volatility():
    memory_file = os.path.expanduser("/home/kali/zetpeak/volatility/memory.mem")
    vol_path = os.path.expanduser("/home/kali/zetpeak/volatility/volatility3/vol.py")
    output_dir = os.path.expanduser("/home/kali/zetpeak/volatility/results")
    os.makedirs(output_dir, exist_ok=True)

    plugins = [
        ("windows.pslist", "processes.json"),
        ("windows.dlllist", "dlls.json"),
        ("windows.cmdline", "cmdline.json"),
        ("windows.netscan", "netscan.json"),
        ("windows.handles", "handles.json"),
        ("windows.malfind", "malfind.json"),
        ("windows.registry.printkey", "registry_keys.json"),
    ]

    for plugin, outfile in plugins:
        print(f"[+] Running {plugin}...")
        with open(os.path.join(output_dir, outfile), "w") as f:
            subprocess.run(
                ["python3", vol_path, "-f", memory_file, plugin],
                stdout=f
            )

    print(f"\nAnalysis complete. Results saved in {output_dir}")

if __name__ == "__main__":
    run_volatility()

