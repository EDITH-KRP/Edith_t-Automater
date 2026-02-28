"""
EDITH-Automater  --  AI Analyst (Ollama-powered)
=================================================
Generates forensic narratives and answers case questions using a local LLM.
Requires Ollama (https://ollama.com) running on localhost.

All calls degrade gracefully -- if Ollama is not running or no model is
installed the functions return None / empty strings instead of crashing.
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional, List, Dict

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Preferred model order -- first one found wins
# ---------------------------------------------------------------------------
_PREFERRED_MODELS = [
    "llama3.2", "llama3", "llama3.1", "llama3:latest",
    "mistral", "phi4", "phi3", "phi3:medium",
    "gemma2", "gemma", "qwen2.5", "qwen2",
    "deepseek-r1", "deepseek-coder",
]


def _get_ollama():
    """Return the ollama module, or None if not importable."""
    try:
        import ollama
        return ollama
    except ImportError:
        return None


def get_available_model() -> Optional[str]:
    """Return the best available Ollama model name, or None."""
    ol = _get_ollama()
    if ol is None:
        return None
    try:
        models_resp = ol.list()
        available = [m.model.split(":")[0] for m in models_resp.models]
        available_full = [m.model for m in models_resp.models]

        # Try preferred order first
        for pref in _PREFERRED_MODELS:
            if pref in available or pref in available_full:
                # Return full name if available
                for full in available_full:
                    if full.startswith(pref):
                        return full
        # Otherwise just return the first available model
        if available_full:
            return available_full[0]
    except Exception as exc:
        log.debug("Ollama model list failed: %s", exc)
    return None


def _build_case_context(case_dir: Path, events: List[Dict]) -> str:
    """Build a compact text summary of the case to feed to the LLM."""
    lines = []

    # Case metadata
    case_id = case_dir.name
    lines.append(f"CASE ID: {case_id}")

    # Integrity
    integ_file = case_dir / "HashDeep_output" / "verification" / "integrity_verification.txt"
    if integ_file.exists():
        txt = integ_file.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'INTEGRITY MAINTAINED|match:\s*PASS', txt, re.I):
            lines.append("INTEGRITY: PASSED (evidence hash verified)")
        else:
            lines.append("INTEGRITY: UNKNOWN")
        m = re.search(r'Evidence:\s*(.+)', txt)
        if m:
            lines.append(f"EVIDENCE FILE: {m.group(1).strip()}")

    # EWF metadata (case info from the image)
    ewf_dir = case_dir / "FTK_output"
    for f in ewf_dir.rglob("*.txt") if ewf_dir.exists() else []:
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for key in ("Case Number", "Subject", "Examiner", "Description",
                    "Operating System", "Computer Name"):
            m = re.search(rf'{key}[:\s]+(.+)', txt, re.I)
            if m:
                lines.append(f"{key.upper()}: {m.group(1).strip()}")
        break

    lines.append("")
    lines.append(f"TOTAL TIMELINE EVENTS: {len(events)}")

    # Severity breakdown
    from collections import Counter
    sev = Counter(e.get("severity", "INFO") for e in events)
    lines.append(f"SEVERITY BREAKDOWN: {dict(sev)}")

    # Tool breakdown
    tools = Counter(e.get("source_tool", "?") for e in events)
    lines.append(f"TOOLS THAT PRODUCED DATA: {dict(tools)}")
    lines.append("")

    # High/Critical events (most important for the narrative)
    high_events = [e for e in events if e.get("severity") in ("CRITICAL", "HIGH")]
    if high_events:
        lines.append(f"HIGH/CRITICAL EVENTS ({len(high_events)}):")
        for e in high_events[:20]:
            lines.append(f"  [{e.get('severity')}] {e.get('timestamp','')} | "
                         f"{e.get('source_tool','')} | {e.get('subject','')}")
        lines.append("")

    # Sample of INFO events to give timeline breadth
    info_events = [e for e in events if e.get("severity") == "INFO"]
    if info_events:
        lines.append(f"SAMPLE EVENTS (first 25 of {len(info_events)} INFO):")
        for e in info_events[:25]:
            lines.append(f"  {e.get('timestamp','')} | {e.get('source_tool','')} | "
                         f"{e.get('subject','')}")

    return "\n".join(lines)


def generate_narrative(case_dir: Path, timeline_json_path: Path,
                       model: Optional[str] = None) -> Optional[str]:
    """
    Generate a forensic analyst narrative from the case timeline.
    Returns a plain-text narrative string, or None if Ollama is unavailable.
    """
    ol = _get_ollama()
    if ol is None:
        log.debug("ollama package not installed")
        return None

    chosen_model = model or get_available_model()
    if not chosen_model:
        log.debug("No Ollama models available")
        return None

    # Load timeline events
    events: List[Dict] = []
    try:
        if Path(timeline_json_path).exists():
            data = json.loads(Path(timeline_json_path).read_text(encoding="utf-8"))
            events = data.get("events", [])
    except Exception as exc:
        log.debug("Could not read timeline JSON: %s", exc)

    if not events:
        return None

    context = _build_case_context(Path(case_dir), events)

    prompt = f"""You are a senior digital forensics examiner writing a professional case summary.
Based on the following forensic analysis output, write a concise 3-4 paragraph narrative that:
1. Describes what type of system was analysed and the case context
2. Summarises the key timeline of events discovered
3. Highlights the most significant findings (file activity, artefacts, suspicious indicators)
4. States the integrity status and any caveats

Write in formal forensic report language. Be specific about dates, file names, and findings where available.
Do NOT invent details not present in the data. Keep to 200-250 words maximum.

--- FORENSIC DATA ---
{context}
--- END DATA ---

FORENSIC NARRATIVE:"""

    try:
        log.info("[AI] Generating narrative with model: %s", chosen_model)
        response = ol.chat(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 400},
        )
        narrative = response.message.content.strip()
        log.info("[AI] Narrative generated (%d chars)", len(narrative))
        return narrative
    except Exception as exc:
        log.warning("[AI] Narrative generation failed: %s", exc)
        return None


def ask_question(case_dir: Path, timeline_json_path: Path,
                 question: str, model: Optional[str] = None) -> str:
    """
    Answer a natural language question about the case evidence.
    Returns an answer string, or an error message if Ollama is unavailable.
    """
    ol = _get_ollama()
    if ol is None:
        return "[AI] ollama Python package not installed. Run: pip install ollama"

    chosen_model = model or get_available_model()
    if not chosen_model:
        return "[AI] No Ollama models found. Run: ollama pull llama3.2"

    events: List[Dict] = []
    try:
        if Path(timeline_json_path).exists():
            data = json.loads(Path(timeline_json_path).read_text(encoding="utf-8"))
            events = data.get("events", [])
    except Exception:
        pass

    context = _build_case_context(Path(case_dir), events)

    prompt = f"""You are a digital forensics expert assistant.
Answer the following question based ONLY on the forensic case data provided.
If the answer is not in the data, say so clearly. Keep the answer concise (2-5 sentences).

--- CASE DATA ---
{context}
--- END DATA ---

QUESTION: {question}

ANSWER:"""

    try:
        response = ol.chat(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 300},
        )
        return response.message.content.strip()
    except Exception as exc:
        return f"[AI] Error: {exc}"
