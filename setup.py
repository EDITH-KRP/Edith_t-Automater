from cx_Freeze import setup, Executable
import sys

# Include any additional modules your script uses here
build_exe_options = {
    "packages": ["os", "random", "_sha512"],  # add any other packages your script uses
    "includes": ["_sha512"],  # include hidden imports
    "include_files": [],      # add any extra files/folders your program needs
}

# Decide the base: Console for CLI apps, None for GUI apps
base = "Console" if sys.platform == "win32" else None

setup(
    name="YourAppName",
    version="1.0",
    description="My Python Application",
    options={"build_exe": build_exe_options},
    executables=[Executable("orchestrator.py", base=base)]
)