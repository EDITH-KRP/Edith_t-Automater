"""
EDITH-Automater Launcher
Portable executable entry point for Windows/Mac/Linux

When double-clicked (no CLI args): shows an interactive menu so the user
can pick a workflow and enter paths without using a terminal.
When run from a terminal with args: passes them straight through to the
orchestrator (same behaviour as before).
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pause(msg="Press Enter to exit..."):
    """Keep the console window open until the user presses Enter."""
    try:
        input(f"\n{msg}")
    except EOFError:
        pass


def _banner():
    print("=" * 70)
    print("  EDITH-Automater  -  Digital Forensic Analysis System")
    print("=" * 70)


def _ask(prompt, required=True, default=None):
    """Prompt the user for input; re-ask if required and blank."""
    while True:
        suffix = f" [{default}]" if default else ""
        val = input(f"{prompt}{suffix}: ").strip()
        if not val and default:
            return default
        if val:
            return val
        if not required:
            return ""
        print("  [!] This field is required.")


def _interactive_menu():
    """
    Full interactive menu shown when the exe is double-clicked.
    Builds sys.argv so the orchestrator's existing main() handles everything.
    """
    _banner()
    print()
    print("  Select a workflow:")
    print()
    print("  [1]  Simultaneous  - Answer questions, then run full forensic analysis")
    print("  [2]  Sequential    - Evidence questionnaire first, then analysis")
    print("  [3]  Evidence only - Fill in the evidence collection form only")
    print("  [4]  Forensic only - Run forensic tools on an existing evidence file")
    print("  [5]  Report only   - Generate reports for an existing case")
    print("  [6]  List cases    - Show all cases in the Results folder")
    print("  [0]  Exit")
    print()

    choice = _ask("Enter choice", required=True)

    if choice == "0":
        print("\nGoodbye.")
        _pause()
        sys.exit(0)

    elif choice == "1":
        evidence = _ask("Path to evidence file (.E01 / .dd / .raw)")
        memory   = _ask("Path to memory dump (optional, press Enter to skip)", required=False)
        sys.argv = [sys.argv[0], "simultaneous", "--evidence", evidence]
        if memory:
            sys.argv += ["--memory", memory]

    elif choice == "2":
        evidence = _ask("Path to evidence file (.E01 / .dd / .raw)")
        memory   = _ask("Path to memory dump (optional, press Enter to skip)", required=False)
        sys.argv = [sys.argv[0], "sequential", "--evidence", evidence]
        if memory:
            sys.argv += ["--memory", memory]

    elif choice == "3":
        sys.argv = [sys.argv[0], "evidence-only"]

    elif choice == "4":
        evidence = _ask("Path to evidence file (.E01 / .dd / .raw)")
        memory   = _ask("Path to memory dump (optional, press Enter to skip)", required=False)
        case_id  = _ask("Case ID to attach results to (leave blank to create new)", required=False)
        sys.argv = [sys.argv[0], "forensic-auto", "--evidence", evidence]
        if memory:
            sys.argv += ["--memory", memory]
        if case_id:
            sys.argv += ["--case", case_id]

    elif choice == "5":
        case_id = _ask("Case ID (e.g. CASE_20260227_154807)")
        sys.argv = [sys.argv[0], "report-only", "--case", case_id]

    elif choice == "6":
        sys.argv = [sys.argv[0], "list-cases"]

    else:
        print(f"\n  [!] Unknown choice '{choice}'. Showing help instead.")
        sys.argv = [sys.argv[0], "help"]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    # Fix stdout/stderr encoding on Windows so Unicode chars don't crash
    if sys.platform.startswith("win"):
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Add the directory that contains this file to sys.path so the
    # 'orchestrator' package can always be imported.
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    # If the exe was double-clicked there will be exactly one entry in
    # sys.argv (the exe path itself) — show the interactive menu.
    double_clicked = len(sys.argv) == 1
    if double_clicked:
        try:
            _interactive_menu()
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            _pause()
            sys.exit(0)

    # Hand off to the orchestrator's async main()
    try:
        from orchestrator import main as orchestrator_main   # orchestrator/orchestrator.py
        asyncio.run(orchestrator_main())
    except ImportError as exc:
        _banner()
        print(f"\n[ERROR] Could not load orchestrator module: {exc}")
        print("\nFull traceback:")
        traceback.print_exc()
        _pause("Press Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Stopped by user.")
        if double_clicked:
            _pause()
        sys.exit(0)
    except SystemExit:
        if double_clicked:
            _pause()
        raise
    except Exception as exc:
        _banner()
        print(f"\n[ERROR] {exc}")
        traceback.print_exc()
        _pause("Press Enter to exit...")
        sys.exit(1)

    if double_clicked:
        _pause("Done. Press Enter to close this window...")


if __name__ == "__main__":
    main()
