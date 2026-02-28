#!/usr/bin/env python3
"""
EDITH-Automater  --  Ask the Evidence (AI Q&A)
================================================
Interactive natural language Q&A about a completed forensic case.
Powered by your local Ollama LLM -- no internet required.

Usage:
    python ask_case.py                    # uses the most recent case
    python ask_case.py Results\CASE_XXX   # specify a case directory

Example questions:
    What files did the suspect access?
    What email addresses were found?
    Was the evidence integrity verified?
    Summarise the timeline in plain English.
    What is the most suspicious finding?
"""

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "tools"))

from ai_analyst.ai_analyst import ask_question, get_available_model, generate_narrative


def pick_case(results_dir: Path) -> Path:
    """Return the most recently created case directory."""
    cases = sorted(results_dir.glob("CASE_*"), reverse=True)
    if not cases:
        print(f"[ERROR] No cases found in {results_dir}")
        sys.exit(1)
    return cases[0]


def main():
    results_dir = _HERE / "Results"

    # Case from argument or latest
    if len(sys.argv) > 1:
        case_dir = Path(sys.argv[1]).resolve()
        if not case_dir.exists():
            # Try as relative to Results/
            case_dir = results_dir / sys.argv[1]
        if not case_dir.exists():
            print(f"[ERROR] Case not found: {sys.argv[1]}")
            sys.exit(1)
    else:
        case_dir = pick_case(results_dir)

    timeline_json = case_dir / "Timeline" / "timeline_events.json"

    print()
    print("=" * 60)
    print("  EDITH  --  AI Case Analyst")
    print("=" * 60)
    print(f"  Case    : {case_dir.name}")
    print(f"  Timeline: {timeline_json.name if timeline_json.exists() else 'NOT FOUND'}")

    model = get_available_model()
    if model:
        print(f"  Model   : {model}")
    else:
        print("  Model   : [NOT AVAILABLE -- is Ollama running?]")
        print()
        print("  Start Ollama:  ollama serve")
        print("  Pull a model:  ollama pull llama3.2")
        print()
        input("Press Enter to exit...")
        sys.exit(1)

    print()
    print("  Type your question, or:")
    print("    'summary'  -- generate full forensic narrative")
    print("    'quit'     -- exit")
    print("=" * 60)
    print()

    while True:
        try:
            question = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye.")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q", "bye"):
            print("  Goodbye.")
            break

        if question.lower() in ("summary", "narrate", "narrative"):
            print("\n  [AI] Generating forensic narrative...\n")
            result = generate_narrative(case_dir, timeline_json, model=model)
            if result:
                # Word-wrap at ~70 chars
                for line in result.split("\n"):
                    print(f"  {line}")
            else:
                print("  [AI] Could not generate narrative.")
        else:
            print("\n  [AI] Thinking...\n")
            answer = ask_question(case_dir, timeline_json, question, model=model)
            for line in answer.split("\n"):
                print(f"  {line}")

        print()


if __name__ == "__main__":
    main()
