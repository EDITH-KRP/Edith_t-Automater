#!/usr/bin/env python3
"""
EDITH-Automater — Cross-Tool Timeline Correlator
=================================================
Merges timestamps and events from ALL forensic tools into a single
chronological investigation timeline with severity scoring.

Supported sources:
  • FTK / img_stat   — image acquisition metadata
  • Autopsy / SleuthKit fls — file system MAC(b) timestamps
  • ExifTool          — embedded file metadata timestamps
  • HashDeep          — hash-verification events
  • Volatility        — process creation / network events
  • Bulk Extractor    — email / URL artefact timestamps
"""

import os
import re
import json
import csv
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import html as html_lib

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────

SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}

SOURCE_COLORS = {
    "FTK":           "#e74c3c",   # red
    "AUTOPSY":       "#3498db",   # blue
    "EXIFTOOL":      "#2ecc71",   # green
    "HASHDEEP":      "#9b59b6",   # purple
    "VOLATILITY":    "#e67e22",   # orange
    "BULK_EXTRACTOR":"#1abc9c",   # teal
    "SYSTEM":        "#95a5a6",   # grey
}

@dataclass
class TimelineEvent:
    timestamp: datetime
    source_tool: str          # FTK | AUTOPSY | EXIFTOOL | HASHDEEP | VOLATILITY | BULK_EXTRACTOR
    event_type: str           # CREATED | MODIFIED | ACCESSED | DELETED | ACQUIRED | PROCESS | NETWORK | ARTEFACT | VERIFIED
    subject: str              # file path, process name, URL, etc.
    description: str
    severity: str = "INFO"    # INFO | LOW | MEDIUM | HIGH | CRITICAL
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def ts_iso(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def ts_date(self) -> str:
        return self.timestamp.strftime("%Y-%m-%d")

    @property
    def color(self) -> str:
        return SOURCE_COLORS.get(self.source_tool.upper(), "#95a5a6")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["timestamp"] = self.ts_iso
        d["color"] = self.color
        return d


# ──────────────────────────────────────────────────────────
# Helper parsers
# ──────────────────────────────────────────────────────────

def _parse_dt(raw: str) -> Optional[datetime]:
    """Try multiple timestamp formats and return UTC-naive datetime or None."""
    if not raw:
        return None
    raw = str(raw).strip()

    # Unix epoch integer (e.g. EWF header stores seconds since 1970)
    if re.fullmatch(r'\d{9,10}', raw):
        try:
            epoch = int(raw)
            if 0 < epoch < 2_000_000_000:   # sanity: between 1970 and ~2033
                return datetime.fromtimestamp(epoch)
        except Exception:
            pass

    # Strip timezone suffix for simpler parsing
    raw_tz = re.sub(r'[+-]\d{2}:\d{2}$', '', raw).rstrip('Z').strip()

    fmts = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%a %b %d %H:%M:%S %Y",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        for candidate in (raw_tz, raw):
            try:
                return datetime.strptime(candidate, fmt)
            except Exception:
                pass
            # Also try truncating to first 19 chars for ISO-with-millis variants
            try:
                return datetime.strptime(candidate[:19], fmt)
            except Exception:
                pass
    return None


SUSPICIOUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.vbs', '.ps1', '.psm1', '.psd1',
    '.sh', '.py', '.rb', '.pl', '.php', '.jar', '.class',
    '.scr', '.pif', '.com', '.hta', '.lnk', '.tmp',
}

SUSPICIOUS_PATHS = [
    r'\\temp\\', r'\\tmp\\', r'/tmp/', r'\\appdata\\roaming\\',
    r'\\windows\\system32\\', r'\\recycler\\', r'\$recycle\.bin',
    r'\\startup\\', r'\\run\\',
]

def _score_file(path: str, event_type: str) -> str:
    """Heuristic severity for a file-system event."""
    pl = path.lower()
    ext = Path(path).suffix.lower()
    if event_type == "DELETED" and ext in SUSPICIOUS_EXTENSIONS:
        return "HIGH"
    if event_type == "DELETED":
        return "MEDIUM"
    if ext in SUSPICIOUS_EXTENSIONS:
        return "MEDIUM"
    if any(re.search(p, pl) for p in SUSPICIOUS_PATHS):
        return "LOW"
    return "INFO"


# ──────────────────────────────────────────────────────────
# Main correlator
# ──────────────────────────────────────────────────────────

class TimelineCorrelator:
    """
    Scans a case results directory, parses every tool output,
    and produces a merged chronological timeline.
    """

    def __init__(self, case_dir: str, case_id: str = "", officer: str = ""):
        self.case_dir = Path(case_dir)
        self.case_id = case_id or self.case_dir.name
        self.officer = officer
        self.events: List[TimelineEvent] = []
        self._errors: List[str] = []

    # ── public API ──────────────────────────────────────────

    def build(self) -> "TimelineCorrelator":
        """Parse all available tool outputs and build the timeline."""
        self._parse_ftk()
        self._parse_autopsy()
        self._parse_exiftool()
        self._parse_hashdeep()
        self._parse_volatility()
        self._parse_bulk_extractor()
        self.events.sort(key=lambda e: e.timestamp)
        logger.info(f"Timeline built: {len(self.events)} events from {self.case_dir}")
        return self

    def save_json(self, out_path: str) -> str:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            "case_id": self.case_id,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_count": len(self.events),
            "events": [e.to_dict() for e in self.events],
            "errors": self._errors,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return out_path

    def save_html(self, out_path: str) -> str:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        html = _render_html(self.events, self.case_id, self.officer)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        return out_path

    def save_dashboard(self, out_path: str, ai_narrative: str = "") -> str:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        dash = _render_dashboard(self.events, self.case_id, self.case_dir,
                                 self.officer, ai_narrative=ai_narrative)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(dash)
        return out_path

    def summary(self) -> Dict:
        from collections import Counter
        sev_counts = Counter(e.severity for e in self.events)
        src_counts = Counter(e.source_tool for e in self.events)
        return {
            "total_events": len(self.events),
            "by_severity": dict(sev_counts),
            "by_source": dict(src_counts),
            "date_range": (
                self.events[0].ts_iso if self.events else "N/A",
                self.events[-1].ts_iso if self.events else "N/A",
            ),
            "high_critical": [e.to_dict() for e in self.events
                               if e.severity in ("HIGH", "CRITICAL")],
        }

    # ── parsers ──────────────────────────────────────────────

    def _add(self, event: TimelineEvent):
        self.events.append(event)

    def _err(self, msg: str):
        logger.warning(msg)
        self._errors.append(msg)

    # ── FTK ──────────────────────────────────────────────────

    def _parse_ftk(self):
        """Parse FTK metadata JSON output."""
        for pattern in ["FTK_Acquisition/image_metadata.json",
                        "FTK_Acquisition/acquisition_summary.json",
                        "autopsy_analysis.json"]:
            p = self.case_dir / pattern
            if not p.exists():
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)

                # acquisition timestamp
                for key in ("file_created", "timestamp", "acquisition_date"):
                    ts = _parse_dt(data.get(key, ""))
                    if ts:
                        self._add(TimelineEvent(
                            timestamp=ts,
                            source_tool="FTK",
                            event_type="ACQUIRED",
                            subject=data.get("file_name", data.get("image_file", "evidence")),
                            description=(
                                f"Forensic image acquired — "
                                f"{data.get('format','EWF')} | "
                                f"{round(data.get('file_size_bytes',0)/1e9,2)} GB | "
                                f"MD5: {data.get('md5_hash','N/A')}"
                            ),
                            severity="INFO",
                            extra=data,
                        ))
                        break

                # modification timestamp
                ts_mod = _parse_dt(data.get("file_modified", ""))
                if ts_mod:
                    self._add(TimelineEvent(
                        timestamp=ts_mod,
                        source_tool="FTK",
                        event_type="MODIFIED",
                        subject=data.get("file_name", "evidence"),
                        description="Evidence image file last modified on source media",
                        severity="LOW",
                        extra={"md5": data.get("md5_hash")},
                    ))
            except Exception as e:
                self._err(f"FTK parse error {p}: {e}")

    # ── Autopsy / SleuthKit ───────────────────────────────────

    def _parse_autopsy(self):
        """
        Parse SleuthKit fls output (files.txt) and autopsy_analysis.json.
        fls line format:  TYPE   inode   DELETED?   size   path   [macb timestamps]
        tsk_gettimes / mactime body format: MD5|path|inode|mode|uid|gid|size|atime|mtime|ctime|crtime
        """
        # Try mactime body format first
        for body_file in self.case_dir.rglob("*.body"):
            self._parse_mactime_body(body_file)
            return

        # fls output — search recursively under Autopsy_output (may be in a nested subdir)
        fls_file = None
        for candidate in self.case_dir.rglob("files.txt"):
            # Prefer the one inside Autopsy_output
            if "autopsy" in str(candidate).lower():
                fls_file = candidate
                break
        if fls_file is None:
            fls_file_plain = self.case_dir / "files.txt"
            if fls_file_plain.exists():
                fls_file = fls_file_plain
        if fls_file and fls_file.exists():
            self._parse_fls_output(fls_file)

        # autopsy JSON
        for json_path in self.case_dir.rglob("autopsy_analysis.json"):
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
                ts = _parse_dt(data.get("timestamp", ""))
                if ts:
                    self._add(TimelineEvent(
                        timestamp=ts,
                        source_tool="AUTOPSY",
                        event_type="VERIFIED",
                        subject=data.get("file_path", "evidence"),
                        description=(
                            f"Autopsy analysis run — "
                            f"MD5: {data.get('hashes',{}).get('md5','N/A')} | "
                            f"Size: {data.get('file_size','N/A')} bytes"
                        ),
                        severity="INFO",
                        extra=data,
                    ))
            except Exception as e:
                self._err(f"Autopsy JSON parse error: {e}")

    def _parse_fls_output(self, path: Path):
        """
        Parse SleuthKit fls -r output for file inventory.
        fls line format: type/type inode[*]: name
          d/d inode:  dirname
          r/r inode:  filename
          d/d * inode: (deleted) dirname
        We emit one CREATED or DELETED event per file/directory entry.
        Timestamp = file's last-modified time (filesystem analysis time) since
        fls -r without -m does not embed per-file timestamps.
        """
        try:
            # Use the analysis JSON timestamp if available for a more meaningful base time
            base_ts = datetime.fromtimestamp(path.stat().st_mtime)
            json_sibling = path.parent / "autopsy_analysis.json"
            if json_sibling.exists():
                try:
                    with open(json_sibling) as jf:
                        jd = json.load(jf)
                    t = _parse_dt(jd.get("timestamp", ""))
                    if t:
                        base_ts = t
                except Exception:
                    pass

            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.rstrip()
                    if not line:
                        continue
                    # Detect deleted entries (fls marks with * before inode)
                    is_deleted = re.search(r'\*', line.split(':', 1)[0] if ':' in line else "") is not None
                    # Extract name: everything after the first colon + optional whitespace
                    if ':' in line:
                        name_part = line.split(':', 1)[1].strip()
                    else:
                        parts = line.split()
                        name_part = parts[-1] if parts else line
                    if not name_part:
                        continue
                    ev_type = "DELETED" if is_deleted else "CREATED"
                    sev = _score_file(name_part, ev_type)
                    self._add(TimelineEvent(
                        timestamp=base_ts,
                        source_tool="AUTOPSY",
                        event_type=ev_type,
                        subject=name_part,
                        description=f"{'[DELETED] ' if is_deleted else ''}[fls] {name_part}",
                        severity=sev,
                        extra={"raw": line},
                    ))
        except Exception as e:
            self._err(f"fls parse error {path}: {e}")

    def _parse_mactime_body(self, path: Path):
        """Parse SleuthKit mactime body file (pipe-delimited)."""
        # format: MD5|path|inode|perms|uid|gid|size|atime|mtime|ctime|crtime
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) < 11:
                        continue
                    file_path = parts[1]
                    is_deleted = "(deleted" in file_path.lower()
                    for idx, label in [(7, "ACCESSED"), (8, "MODIFIED"), (9, "CHANGED"), (10, "CREATED")]:
                        try:
                            epoch = int(parts[idx])
                            if epoch <= 0:
                                continue
                            ts = datetime.fromtimestamp(epoch)
                            ev_type = "DELETED" if is_deleted and label == "MODIFIED" else label
                            sev = _score_file(file_path, ev_type)
                            self._add(TimelineEvent(
                                timestamp=ts,
                                source_tool="AUTOPSY",
                                event_type=ev_type,
                                subject=file_path,
                                description=f"{label} — {file_path}",
                                severity=sev,
                            ))
                        except Exception:
                            pass
        except Exception as e:
            self._err(f"mactime body parse error {path}: {e}")

    # ── ExifTool ──────────────────────────────────────────────

    def _parse_exiftool(self):
        """Parse ExifTool JSON output files."""
        search_dirs = [
            self.case_dir / "ExifTool_output",
            self.case_dir / "Exiftool_output",
            self.case_dir,
        ]
        _skip_dirs = {"timeline", "final_reports", "reports"}
        seen = set()
        found = False
        for d in search_dirs:
            if not d.exists():
                continue
            for json_file in d.rglob("*.json"):
                if json_file.resolve() in seen:
                    continue
                if any(p.lower() in _skip_dirs for p in json_file.parts):
                    continue
                if "metadata" in json_file.name.lower() or "exif" in json_file.name.lower():
                    found = True
                    seen.add(json_file.resolve())
                    self._parse_exiftool_json(json_file)
        if not found:
            for d in search_dirs:
                if d.exists():
                    for json_file in list(d.glob("**/*.json"))[:50]:
                        if json_file.resolve() in seen:
                            continue
                        if any(p.lower() in _skip_dirs for p in json_file.parts):
                            continue
                        seen.add(json_file.resolve())
                        self._parse_exiftool_json(json_file)

    def _parse_exiftool_json(self, path: Path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            # ExifTool output can be a single dict or list of dicts
            records = data if isinstance(data, list) else [data]

            for rec in records:
                if not isinstance(rec, dict):
                    continue
                subj = rec.get("SourceFile") or rec.get("FileName") or str(path)

                # Build a normalized lookup that strips ExifTool namespace prefixes
                # e.g. "File:FileModifyDate" is also accessible as "FileModifyDate"
                # and "EWF:AcquisitionStartDateTime" as "AcquisitionStartDateTime"
                norm: Dict[str, Any] = {}
                for k, v in rec.items():
                    norm[k] = v
                    if ":" in k:
                        short = k.split(":", 1)[1]
                        if short not in norm:
                            norm[short] = v

                timestamp_fields = [
                    # EWF/forensic acquisition timestamps (real historical dates)
                    ("EWF:AcquisitionStartDateTime",  "ACQUIRED",  "Evidence acquired (EWF header)"),
                    ("AcquisitionStartDateTime",       "ACQUIRED",  "Evidence acquired"),
                    ("EWF:AcquisitionEndDateTime",     "VERIFIED",  "Acquisition completed"),
                    ("AcquisitionEndDateTime",         "VERIFIED",  "Acquisition completed"),
                    # Standard ExifTool fields (also checked via normalized names)
                    ("DateTimeOriginal",  "CREATED",  "Image captured"),
                    ("CreateDate",        "CREATED",  "File created"),
                    ("ModifyDate",        "MODIFIED", "File modified"),
                    ("FileModifyDate",    "MODIFIED", "File system modified"),
                    ("FileCreateDate",    "CREATED",  "File system created"),
                    ("FileAccessDate",    "ACCESSED", "File accessed"),
                    ("MetadataDate",      "MODIFIED", "Metadata modified"),
                    ("GPSDateTime",       "CREATED",  "GPS timestamp"),
                ]

                for field_name, ev_type, label in timestamp_fields:
                    # Look up in both original rec and namespace-stripped norm dict
                    raw_ts = rec.get(field_name) or norm.get(field_name, "")
                    ts = _parse_dt(raw_ts)
                    if not ts:
                        continue
                    # Build rich description
                    extras = {}
                    for k in ("Make", "Model", "GPSLatitude", "GPSLongitude",
                              "Software", "Author", "Creator", "ImageSize",
                              "EWF:AcquisitionSoftware", "AcquisitionSoftware",
                              "EWF:OperatingSystem", "EWF:MediaType", "EWF:CompressionType"):
                        v = rec.get(k) or norm.get(k)
                        if v:
                            extras[k] = v
                    # Enrich description with EWF metadata if present
                    acq_sw = norm.get("AcquisitionSoftware", "")
                    media  = norm.get("MediaType", "")
                    os_str = norm.get("OperatingSystem", "")
                    desc_parts = [f"{label}: {subj}"]
                    if extras.get("Make") or extras.get("Model"):
                        desc_parts.append(f"Device: {extras.get('Make','')} {extras.get('Model','')}".strip())
                    if extras.get("GPSLatitude"):
                        desc_parts.append(f"GPS: {extras['GPSLatitude']}, {extras.get('GPSLongitude','')}")
                    if acq_sw:
                        desc_parts.append(f"Acquired with: {acq_sw}")
                    if media:
                        desc_parts.append(f"Media: {media}")
                    if os_str:
                        desc_parts.append(f"Source OS: {os_str}")
                    sev = "MEDIUM" if ev_type == "ACQUIRED" else ("MEDIUM" if extras.get("GPSLatitude") else "INFO")
                    self._add(TimelineEvent(
                        timestamp=ts,
                        source_tool="EXIFTOOL",
                        event_type=ev_type,
                        subject=subj,
                        description=" | ".join(desc_parts),
                        severity=sev,
                        extra=extras,
                    ))
        except Exception as e:
            self._err(f"ExifTool JSON parse error {path}: {e}")

    # ── HashDeep ──────────────────────────────────────────────

    def _parse_hashdeep(self):
        """Parse HashDeep JSON results and text hash reports."""
        search_dirs = [
            self.case_dir / "HashDeep_output",
            self.case_dir,
        ]
        seen: set = set()

        def _once(path: Path, fn):
            rp = path.resolve()
            if rp in seen:
                return
            seen.add(rp)
            fn(path)

        for d in search_dirs:
            if not d.exists():
                continue
            # JSON cache files
            for json_file in d.rglob("hash_results*.json"):
                _once(json_file, self._parse_hashdeep_json)
            for json_file in d.rglob("drive_hash*.json"):
                _once(json_file, self._parse_hashdeep_json)
            # Text report files generated by create_hashdeep_drive.py
            for txt_file in d.rglob("DriveHash_Report_*.txt"):
                _once(txt_file, self._parse_hashdeep_txt)
            # Integrity verification report
            for txt_file in d.rglob("integrity_verification.txt"):
                _once(txt_file, self._parse_integrity_txt)

    def _parse_hashdeep_txt(self, path: Path):
        """Parse DriveHash_Report_*.txt text format."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            ts_raw = re.search(r'(?:Timestamp|Report Generated):\s*([\d\-T:.]+)', content)
            ts = _parse_dt(ts_raw.group(1)) if ts_raw else datetime.fromtimestamp(path.stat().st_mtime)
            if not ts:
                ts = datetime.fromtimestamp(path.stat().st_mtime)
            evidence = re.search(r'Evidence Path:\s*(.+)', content)
            md5 = re.search(r'MD5:\s*([0-9a-f]{32})', content, re.I)
            sha1 = re.search(r'SHA1:\s*([0-9a-f]{40})', content, re.I)
            sha256 = re.search(r'SHA256:\s*([0-9a-f]{64})', content, re.I)
            status = re.search(r'Status:\s*(\w+)', content)
            is_verify = "verification" in str(path).lower()
            desc = (
                f"{'Verification' if is_verify else 'Baseline'} hash computed — "
                f"MD5: {md5.group(1) if md5 else 'N/A'}"
            )
            self._add(TimelineEvent(
                timestamp=ts,
                source_tool="HASHDEEP",
                event_type="VERIFIED" if is_verify else "ACQUIRED",
                subject=evidence.group(1).strip() if evidence else str(path),
                description=desc,
                severity="INFO",
                extra={
                    "md5":    md5.group(1)    if md5    else None,
                    "sha1":   sha1.group(1)   if sha1   else None,
                    "sha256": sha256.group(1) if sha256 else None,
                    "status": status.group(1) if status else "UNKNOWN",
                },
            ))
        except Exception as e:
            self._err(f"HashDeep TXT parse error {path}: {e}")

    def _parse_integrity_txt(self, path: Path):
        """Parse integrity_verification.txt."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            ts = datetime.fromtimestamp(path.stat().st_mtime)
            # Determine pass/fail — actual file format: "OVERALL: INTEGRITY MAINTAINED" / "match: PASS"
            passed = bool(re.search(r'INTEGRITY MAINTAINED|match:\s*PASS', content, re.I))
            failed = bool(re.search(r'MISMATCH|FAIL|integrity.*fail|match:\s*FAIL', content, re.I))
            if failed:
                passed = False
            sev = "CRITICAL" if failed else "INFO"
            status_str = "FAILED" if failed else ("PASSED" if passed else "UNKNOWN")
            self._add(TimelineEvent(
                timestamp=ts,
                source_tool="HASHDEEP",
                event_type="VERIFIED",
                subject=str(path.parent),
                description=f"Integrity verification {status_str}",
                severity=sev,
                extra={"file": str(path), "passed": passed},
            ))
        except Exception as e:
            self._err(f"Integrity TXT parse error {path}: {e}")

    def _parse_hashdeep_json(self, path: Path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            ts = _parse_dt(data.get("timestamp") or data.get("created_at", ""))
            if not ts:
                ts = datetime.fromtimestamp(path.stat().st_mtime)
            target = data.get("target_path") or data.get("drive", str(path))
            status = data.get("status", "SUCCESS")
            integrity = data.get("integrity_maintained", True)
            sev = "CRITICAL" if not integrity else ("INFO" if status == "SUCCESS" else "MEDIUM")
            desc = (
                f"HashDeep integrity {'FAILED ⚠' if not integrity else 'verified ✓'} — "
                f"{target} | MD5: {data.get('md5_hash','N/A')}"
            )
            self._add(TimelineEvent(
                timestamp=ts,
                source_tool="HASHDEEP",
                event_type="VERIFIED",
                subject=target,
                description=desc,
                severity=sev,
                extra=data,
            ))
        except Exception as e:
            self._err(f"HashDeep JSON parse error {path}: {e}")

    # ── Volatility ────────────────────────────────────────────

    def _parse_volatility(self):
        """Parse Volatility output files (JSON, text, and status)."""
        vol_dirs = [
            self.case_dir / "Volatility_output",
            self.case_dir,
        ]
        found_any = False
        for d in vol_dirs:
            if not d.exists():
                continue
            for json_file in d.rglob("volatility_*.json"):
                self._parse_volatility_json(json_file)
                found_any = True
            for txt_file in d.rglob("pslist*.txt"):
                self._parse_volatility_pslist(txt_file)
                found_any = True
            for txt_file in d.rglob("netscan*.txt"):
                self._parse_volatility_netscan(txt_file)
                found_any = True
            # Status file written when no memory image was provided
            status_file = d / "volatility_status.txt"
            if not found_any and status_file.exists():
                try:
                    content = status_file.read_text(encoding="utf-8", errors="ignore")
                    ts = datetime.fromtimestamp(status_file.stat().st_mtime)
                    skipped = "SKIPPED" in content.upper()
                    self._add(TimelineEvent(
                        timestamp=ts,
                        source_tool="VOLATILITY",
                        event_type="SKIPPED",
                        subject="No memory dump provided for this case",
                        description=("Memory analysis was not run because no .mem/.vmem/.dmp file "
                                     "was supplied. To enable Volatility analysis, pass a RAM dump "
                                     "with --memory when running the pipeline."),
                        severity="INFO",
                        extra={"status": "SKIPPED" if skipped else "UNKNOWN",
                               "how_to_enable": "run_pipeline.bat evidence.E01 memory.vmem"},
                    ))
                    found_any = True
                except Exception as e:
                    self._err(f"Volatility status parse error: {e}")

    def _parse_volatility_json(self, path: Path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for entry in data:
                    self._parse_vol_entry(entry)
            elif isinstance(data, dict):
                for entry in data.get("processes", data.get("results", [data])):
                    self._parse_vol_entry(entry)
        except Exception as e:
            self._err(f"Volatility JSON parse error {path}: {e}")

    def _parse_vol_entry(self, entry: dict):
        proc = entry.get("ImageFileName") or entry.get("name") or entry.get("process", "unknown")
        raw_ts = (entry.get("CreateTime") or entry.get("create_time")
                  or entry.get("timestamp") or "")
        ts = _parse_dt(raw_ts)
        if not ts:
            return
        pid = entry.get("PID") or entry.get("pid", "")
        ppid = entry.get("PPID") or entry.get("ppid", "")
        suspicious = proc.lower() in ("cmd.exe", "powershell.exe", "wscript.exe",
                                       "cscript.exe", "mshta.exe", "regsvr32.exe", "rundll32.exe")
        sev = "HIGH" if suspicious else "INFO"
        self._add(TimelineEvent(
            timestamp=ts,
            source_tool="VOLATILITY",
            event_type="PROCESS",
            subject=proc,
            description=f"Process: {proc} (PID:{pid} PPID:{ppid})",
            severity=sev,
            extra=entry,
        ))

    def _parse_volatility_pslist(self, path: Path):
        """Parse text pslist output."""
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    # typical: PROCESS   PID   PPID   ...   CreateTime
                    m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if not m:
                        continue
                    ts = _parse_dt(m.group(1))
                    if not ts:
                        continue
                    parts = line.split()
                    proc = parts[0] if parts else "unknown"
                    suspicious = proc.lower() in ("cmd.exe", "powershell.exe", "wscript.exe")
                    self._add(TimelineEvent(
                        timestamp=ts,
                        source_tool="VOLATILITY",
                        event_type="PROCESS",
                        subject=proc,
                        description=f"Process in memory: {line.strip()}",
                        severity="HIGH" if suspicious else "INFO",
                    ))
        except Exception as e:
            self._err(f"pslist parse error {path}: {e}")

    def _parse_volatility_netscan(self, path: Path):
        """Parse text netscan output."""
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', line)
                    if not m:
                        continue
                    ts_m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    ts = _parse_dt(ts_m.group(1)) if ts_m else datetime.fromtimestamp(path.stat().st_mtime)
                    is_external = not m.group(1).startswith(("10.", "192.168.", "172.", "127."))
                    self._add(TimelineEvent(
                        timestamp=ts,
                        source_tool="VOLATILITY",
                        event_type="NETWORK",
                        subject=m.group(0),
                        description=f"Network connection: {line.strip()}",
                        severity="HIGH" if is_external else "LOW",
                    ))
        except Exception as e:
            self._err(f"netscan parse error {path}: {e}")

    # ── Bulk Extractor ────────────────────────────────────────

    _BE_PHONE_CAP = 10   # max phone-number events to add (noise reduction)

    def _parse_bulk_extractor(self):
        """Parse Bulk Extractor output directory."""
        be_dirs = [
            self.case_dir / "BulkExtractor_output",
            self.case_dir,
        ]
        seen = set()
        for d in be_dirs:
            if not d.exists():
                continue
            for txt_file in d.rglob("email.txt"):
                if txt_file.resolve() in seen: continue
                seen.add(txt_file.resolve())
                self._parse_be_file(txt_file, "email", "ARTEFACT", "LOW")
            for txt_file in d.rglob("url.txt"):
                if txt_file.resolve() in seen: continue
                seen.add(txt_file.resolve())
                self._parse_be_file(txt_file, "url", "ARTEFACT", "LOW", url_mode=True)
            for txt_file in d.rglob("domain.txt"):
                if txt_file.resolve() in seen: continue
                seen.add(txt_file.resolve())
                self._parse_be_file(txt_file, "domain", "ARTEFACT", "LOW")
            for txt_file in d.rglob("ip.txt"):
                if txt_file.resolve() in seen: continue
                seen.add(txt_file.resolve())
                self._parse_be_file(txt_file, "ip", "ARTEFACT", "MEDIUM")
            for txt_file in d.rglob("phone.txt"):
                if txt_file.resolve() in seen: continue
                seen.add(txt_file.resolve())
                self._parse_be_file(txt_file, "phone", "ARTEFACT", "LOW",
                                    cap=self._BE_PHONE_CAP, add_total_note=True)
            # Also parse the summary JSON for an overview event
            for json_file in d.rglob("summary.json"):
                if json_file.resolve() in seen: continue
                seen.add(json_file.resolve())
                self._parse_be_summary(json_file)

    def _parse_be_file(self, path: Path, artifact_type: str, event_type: str,
                       default_sev: str, url_mode: bool = False, cap: int = 200,
                       add_total_note: bool = False):
        """Parse a BulkExtractor tab-separated artifact file.
        Format: offset\tvalue  (offset is decimal byte position in image)
        """
        ts_base = datetime.fromtimestamp(path.stat().st_mtime)
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                lines = [ln.rstrip() for ln in f if ln.strip() and not ln.startswith("#")]
            total_lines = len(lines)
            count = 0
            for ln in lines:
                # Tab-separated: offset \t value
                parts = ln.split("\t", 1)
                value = parts[1].strip() if len(parts) == 2 else parts[0].strip()
                if not value:
                    continue
                if url_mode:
                    sev = "MEDIUM" if any(k in value.lower() for k in
                          ("onion", "paste", "mega.", "dropbox", "anonfile",
                           "rawgit", "pastebin", "temp.sh")) else "LOW"
                else:
                    sev = default_sev
                self._add(TimelineEvent(
                    timestamp=ts_base,
                    source_tool="BULK_EXTRACTOR",
                    event_type=event_type,
                    subject=value[:120],
                    description=f"[{artifact_type.upper()}] {value[:120]}",
                    severity=sev,
                    extra={"artifact_type": artifact_type, "offset": parts[0] if len(parts)==2 else ""},
                ))
                count += 1
                if count >= cap:
                    break
            # If capped, emit one summary note so the count is visible in the timeline
            if add_total_note and total_lines > cap:
                self._add(TimelineEvent(
                    timestamp=ts_base,
                    source_tool="BULK_EXTRACTOR",
                    event_type="SUMMARY",
                    subject=f"{artifact_type.upper()} — {total_lines:,} total carved from raw sectors",
                    description=(f"[{artifact_type.upper()}] {total_lines:,} items carved from raw disk sectors. "
                                 f"Showing first {cap} in timeline to reduce noise."),
                    severity="INFO",
                    extra={"artifact_type": artifact_type, "total_found": total_lines, "shown_in_timeline": cap},
                ))
        except Exception as e:
            self._err(f"Bulk Extractor {artifact_type} parse error {path}: {e}")

    def _parse_be_summary(self, path: Path):
        """Emit a single summary event from BulkExtractor summary.json."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            ts = datetime.fromtimestamp(path.stat().st_mtime)
            total = data.get("patterns_found", 0)
            if total == 0:
                return  # nothing to show
            counts = data.get("pattern_counts", {})
            detail = ", ".join(f"{k}: {v}" for k, v in counts.items() if v > 0)
            self._add(TimelineEvent(
                timestamp=ts,
                source_tool="BULK_EXTRACTOR",
                event_type="ARTEFACT",
                subject="BulkExtractor scan complete",
                description=f"Raw disk scan: {total} artifacts carved ({detail})",
                severity="MEDIUM" if total > 0 else "INFO",
                extra=data,
            ))
        except Exception as e:
            self._err(f"Bulk Extractor summary parse error {path}: {e}")


# ──────────────────────────────────────────────────────────
# HTML Report Generator
# ──────────────────────────────────────────────────────────

def _render_html(events: List[TimelineEvent], case_id: str, officer: str = "") -> str:
    from collections import Counter

    sev_counts = Counter(e.severity for e in events)
    src_counts  = Counter(e.source_tool for e in events)
    total = len(events)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_range_start = events[0].ts_iso if events else ""
    date_range_end   = events[-1].ts_iso if events else ""
    # Date inputs need YYYY-MM-DD format
    date_min = events[0].ts_date if events else ""
    date_max = events[-1].ts_date if events else ""

    # Severity badge colours
    sev_badge = {
        "CRITICAL": "#c0392b", "HIGH": "#e74c3c",
        "MEDIUM":   "#e67e22", "LOW": "#f39c12",
        "INFO":     "#27ae60",
    }

    # Build event rows
    rows_html = []
    for i, e in enumerate(events):
        badge_color = sev_badge.get(e.severity, "#999")
        src_color   = SOURCE_COLORS.get(e.source_tool.upper(), "#95a5a6")
        extra_rows  = ""
        if e.extra:
            for k, v in list(e.extra.items())[:8]:
                extra_rows += f"<tr><td class='ek'>{html_lib.escape(str(k))}</td><td class='ev'>{html_lib.escape(str(v))[:300]}</td></tr>"

        rows_html.append(f"""<div class="event" data-source="{e.source_tool}" data-severity="{e.severity}" data-date="{e.ts_date}" style="border-left:4px solid {src_color}">
  <div class="ev-header">
    <span class="ev-ts">{html_lib.escape(e.ts_iso)}</span>
    <span class="ev-badge" style="background:{src_color}">{html_lib.escape(e.source_tool)}</span>
    <span class="ev-badge" style="background:{badge_color}">{html_lib.escape(e.severity)}</span>
    <span class="ev-type">{html_lib.escape(e.event_type)}</span>
    <span class="ev-subject" title="{html_lib.escape(e.subject)}">{html_lib.escape(e.subject[:90])}</span>
    <button class="toggle-btn" onclick="toggleDetail(this)">&#9660;</button>
  </div>
  <div class="ev-detail">
    <p class="ev-desc">{html_lib.escape(e.description)}</p>
    {'<table class="extra-table">' + extra_rows + '</table>' if extra_rows else ''}
  </div>
</div>""")

    # Source stat cards
    cards_html = ""
    src_max = max(src_counts.values()) if src_counts else 1
    for src, cnt in sorted(src_counts.items()):
        col = SOURCE_COLORS.get(src.upper(), "#95a5a6")
        pct = int(cnt / src_max * 100)
        cards_html += f"""<div class="stat-card" style="border-top:4px solid {col}">
  <div class="stat-val">{cnt}</div>
  <div class="stat-lbl">{src}</div>
  <div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:{col}"></div></div>
</div>"""
    for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        col = sev_badge.get(sev, "#999")
        cnt = sev_counts.get(sev, 0)
        cards_html += f"""<div class="stat-card" style="border-top:4px solid {col}">
  <div class="stat-val">{cnt}</div>
  <div class="stat-lbl">{sev}</div>
</div>"""

    # Alert table (HIGH/CRITICAL only)
    alert_rows = ""
    for e in [x for x in events if x.severity in ("HIGH", "CRITICAL")]:
        col = sev_badge.get(e.severity, "#999")
        alert_rows += f"""<tr>
  <td>{html_lib.escape(e.ts_iso)}</td>
  <td><span class="ev-badge" style="background:{col}">{e.severity}</span></td>
  <td>{html_lib.escape(e.source_tool)}</td>
  <td>{html_lib.escape(e.event_type)}</td>
  <td title="{html_lib.escape(e.description)}">{html_lib.escape(e.subject[:80])}</td>
</tr>"""

    # Source filter options with counts
    src_options = "".join(
        f'<option value="{s}">{s} ({src_counts[s]})</option>'
        for s in sorted(src_counts.keys())
    )
    # Severity filter options with counts
    sev_options = "".join(
        f'<option value="{s}">{s} ({sev_counts.get(s, 0)})</option>'
        for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        if sev_counts.get(s, 0) > 0
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>EDITH Investigation Timeline &mdash; {html_lib.escape(case_id)}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e0e0e0;min-height:100vh}}
a{{color:#e74c3c;text-decoration:none}}
/* ── Top bar ── */
.topbar{{background:linear-gradient(135deg,#1a1d2e,#2c3e50);padding:20px 32px;border-bottom:3px solid #e74c3c;display:flex;align-items:center;gap:16px}}
.topbar h1{{font-size:24px;font-weight:700;color:#fff;letter-spacing:1px}}
.topbar h1 span{{color:#e74c3c}}
.topbar .meta{{font-size:12px;color:#aaa;margin-top:4px}}
.topbar-right{{margin-left:auto;text-align:right;font-size:12px;color:#aaa}}
.topbar-right strong{{color:#fff;font-size:14px;display:block}}
/* ── Layout ── */
.container{{max-width:1360px;margin:0 auto;padding:20px 24px}}
.section-title{{font-size:13px;font-weight:700;color:#e74c3c;margin:22px 0 10px;
  border-bottom:1px solid #2c3e50;padding-bottom:6px;text-transform:uppercase;letter-spacing:1px}}
/* ── Stat grid ── */
.stat-grid{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px}}
.stat-card{{background:#1a1d2e;border-radius:8px;padding:14px 18px;min-width:120px;flex:1}}
.stat-val{{font-size:26px;font-weight:700;color:#fff}}
.stat-lbl{{font-size:10px;color:#888;margin-top:3px;text-transform:uppercase;letter-spacing:1px}}
.bar-wrap{{background:#0f1117;border-radius:2px;height:4px;margin-top:8px;overflow:hidden}}
.bar-fill{{height:4px;border-radius:2px;transition:width .4s}}
/* ── Alert table ── */
.alert-table{{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:13px}}
.alert-table th{{background:#1e222e;color:#aaa;padding:9px 10px;text-align:left;
  font-weight:700;text-transform:uppercase;font-size:10px;letter-spacing:1px}}
.alert-table td{{padding:8px 10px;border-bottom:1px solid #1e222e;vertical-align:top}}
.alert-table tr:hover td{{background:#1e2235}}
/* ── Sticky filter bar ── */
.filter-bar{{position:sticky;top:0;z-index:100;background:#0d1020;border-bottom:1px solid #2c3e50;
  padding:10px 0;margin-bottom:12px}}
.filters{{display:flex;flex-wrap:wrap;gap:8px;align-items:center}}
.filters label{{font-size:11px;color:#7f8c8d;margin-right:2px;font-weight:600;text-transform:uppercase;letter-spacing:.5px}}
.filters select,.filters input[type=text],.filters input[type=date]{{
  background:#1a1d2e;border:1px solid #2c3e50;color:#ccc;
  padding:5px 9px;border-radius:4px;font-size:12px;height:30px}}
.filters select:focus,.filters input:focus{{outline:1px solid #e74c3c;border-color:#e74c3c}}
.btn{{border:none;padding:5px 13px;border-radius:4px;cursor:pointer;font-size:12px;height:30px;font-weight:600}}
.btn-primary{{background:#e74c3c;color:#fff}}
.btn-secondary{{background:#2c3e50;color:#ccc}}
.btn-green{{background:#27ae60;color:#fff}}
#eventCount{{font-size:12px;color:#7f8c8d;margin-bottom:10px;padding:4px 0}}
/* ── Event cards ── */
.event{{background:#1a1d2e;border-radius:6px;margin-bottom:6px;padding:10px 14px;transition:background .1s}}
.event:hover{{background:#1e2235}}
.ev-header{{display:flex;flex-wrap:wrap;align-items:center;gap:7px}}
.ev-ts{{font-size:11px;color:#7f8c8d;min-width:152px;font-family:'Courier New',monospace}}
.ev-badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:9px;color:#fff;
  text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}}
.ev-type{{font-size:10px;color:#95a5a6;text-transform:uppercase;letter-spacing:.5px;min-width:70px}}
.ev-subject{{font-size:13px;color:#ecf0f1;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.toggle-btn{{background:none;border:1px solid #2c3e50;color:#7f8c8d;padding:1px 7px;
  border-radius:3px;cursor:pointer;font-size:11px;margin-left:auto;flex-shrink:0}}
.toggle-btn:hover{{background:#2c3e50;color:#fff}}
.ev-detail{{display:none;margin-top:9px;padding-top:9px;border-top:1px solid #1e2235}}
.ev-desc{{font-size:12px;color:#7f8c8d;margin-bottom:7px;line-height:1.5}}
.extra-table{{font-size:11px;border-collapse:collapse;width:100%}}
.extra-table .ek{{color:#7f8c8d;padding:3px 8px;width:170px;font-weight:600;vertical-align:top}}
.extra-table .ev{{color:#bdc3c7;padding:3px 8px;word-break:break-all}}
.extra-table tr:nth-child(even){{background:#0f1420}}
.no-events{{text-align:center;color:#555;padding:40px;font-size:14px}}
/* ── Dashboard link ── */
.dash-link{{display:inline-block;background:#2c3e50;color:#ccc;padding:6px 16px;
  border-radius:5px;font-size:12px;margin-bottom:12px;font-weight:600}}
.dash-link:hover{{background:#e74c3c;color:#fff}}
/* ── Print ── */
@media print{{
  body{{background:#fff;color:#000}}
  .topbar{{background:#2c3e50;color:#fff;-webkit-print-color-adjust:exact}}
  .filter-bar{{display:none}}
  .toggle-btn{{display:none}}
  .ev-detail{{display:block!important}}
  .event{{page-break-inside:avoid}}
}}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <h1>EDITH <span>Investigation Timeline</span></h1>
    <div class="meta">
      Generated: <strong style="color:#fff">{generated}</strong> &nbsp;|&nbsp;
      Period: <strong style="color:#fff">{html_lib.escape(date_range_start or '—')}</strong> &rarr; <strong style="color:#fff">{html_lib.escape(date_range_end or '—')}</strong>
    </div>
  </div>
  <div class="topbar-right">
    <strong>{html_lib.escape(case_id)}</strong>
    Officer: {html_lib.escape(officer or 'N/A')}
  </div>
</div>

<div class="container">
  <a class="dash-link" href="../case_dashboard.html">&larr; Case Dashboard</a>

  <div class="section-title">Summary</div>
  <div class="stat-grid">
    <div class="stat-card" style="border-top:4px solid #e74c3c">
      <div class="stat-val">{total}</div>
      <div class="stat-lbl">Total Events</div>
    </div>
    {cards_html}
  </div>

  {'<div class="section-title">High / Critical Findings</div><table class="alert-table"><thead><tr><th>Timestamp</th><th>Severity</th><th>Source</th><th>Type</th><th>Subject</th></tr></thead><tbody>' + alert_rows + '</tbody></table>' if alert_rows else ''}

  <div class="section-title">Full Timeline</div>

  <div class="filter-bar">
    <div class="filters">
      <label>Source</label>
      <select id="filterSrc" onchange="applyFilters()">
        <option value="">All Sources</option>
        {src_options}
      </select>
      <label>Severity</label>
      <select id="filterSev" onchange="applyFilters()">
        <option value="">All Severities</option>
        {sev_options}
      </select>
      <label>From</label>
      <input type="date" id="filterFrom" value="{html_lib.escape(date_min)}" onchange="applyFilters()">
      <label>To</label>
      <input type="date" id="filterTo" value="{html_lib.escape(date_max)}" onchange="applyFilters()">
      <label>Search</label>
      <input type="text" id="filterSearch" placeholder="keyword in any field..." oninput="applyFilters()" style="width:180px">
      <button class="btn btn-secondary" onclick="resetFilters()">Reset</button>
      <button class="btn btn-secondary" onclick="expandAll()">Expand All</button>
      <button class="btn btn-secondary" onclick="collapseAll()">Collapse All</button>
      <button class="btn btn-green" onclick="exportCSV()">Export CSV</button>
      <button class="btn btn-primary" onclick="window.print()">Print / PDF</button>
    </div>
  </div>
  <div id="eventCount">{total} of {total} events displayed</div>
  <div id="eventList">
    {''.join(rows_html) if rows_html else '<div class="no-events">No events found in this case directory.</div>'}
  </div>
</div>

<script>
var allEvents = Array.from(document.querySelectorAll('.event'));
var totalEvents = {total};

function toggleDetail(btn){{
  var d = btn.closest('.event').querySelector('.ev-detail');
  var open = d.style.display === 'block';
  d.style.display = open ? 'none' : 'block';
  btn.innerHTML = open ? '&#9660;' : '&#9650;';
}}
function expandAll(){{
  allEvents.forEach(function(e){{
    if(e.style.display !== 'none'){{
      e.querySelector('.ev-detail').style.display = 'block';
      e.querySelector('.toggle-btn').innerHTML = '&#9650;';
    }}
  }});
}}
function collapseAll(){{
  allEvents.forEach(function(e){{
    e.querySelector('.ev-detail').style.display = 'none';
    e.querySelector('.toggle-btn').innerHTML = '&#9660;';
  }});
}}
function applyFilters(){{
  var src = document.getElementById('filterSrc').value;
  var sev = document.getElementById('filterSev').value;
  var kw  = document.getElementById('filterSearch').value.toLowerCase();
  var df  = document.getElementById('filterFrom').value;
  var dt  = document.getElementById('filterTo').value;
  var vis = 0;
  allEvents.forEach(function(ev){{
    var mSrc = !src || ev.dataset.source === src;
    var mSev = !sev || ev.dataset.severity === sev;
    var mKw  = !kw  || ev.innerText.toLowerCase().includes(kw);
    var mDf  = !df  || ev.dataset.date >= df;
    var mDt  = !dt  || ev.dataset.date <= dt;
    var show = mSrc && mSev && mKw && mDf && mDt;
    ev.style.display = show ? '' : 'none';
    if(show) vis++;
  }});
  document.getElementById('eventCount').textContent = vis + ' of ' + totalEvents + ' events displayed';
}}
function resetFilters(){{
  document.getElementById('filterSrc').value   = '';
  document.getElementById('filterSev').value   = '';
  document.getElementById('filterSearch').value = '';
  document.getElementById('filterFrom').value  = '{html_lib.escape(date_min)}';
  document.getElementById('filterTo').value    = '{html_lib.escape(date_max)}';
  applyFilters();
}}
function exportCSV(){{
  var visible = allEvents.filter(function(e){{ return e.style.display !== 'none'; }});
  var rows = [['Timestamp','Source','Severity','Type','Subject']];
  visible.forEach(function(ev){{
    var cells = ev.querySelectorAll('.ev-ts,.ev-badge,.ev-type,.ev-subject');
    if(cells.length >= 5){{
      rows.push([cells[0].textContent.trim(), cells[1].textContent.trim(),
                 cells[2].textContent.trim(), cells[3].textContent.trim(),
                 cells[4].textContent.trim()]);
    }}
  }});
  var csv = rows.map(function(r){{ return r.map(function(c){{ return '"'+c.replace(/"/g,'""')+'"'; }}).join(','); }}).join('\\n');
  var a = document.createElement('a');
  a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  a.download = '{html_lib.escape(case_id)}_timeline.csv';
  a.click();
}}
</script>
</body>
</html>"""


def _render_dashboard(events: List[TimelineEvent], case_id: str,
                      case_dir: Path, officer: str = "",
                      ai_narrative: str = "") -> str:
    """Generate a one-page case summary dashboard HTML."""
    import json as _json
    from collections import Counter

    generated  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    src_counts = Counter(e.source_tool for e in events)
    sev_counts = Counter(e.severity for e in events)
    total      = len(events)

    sev_badge = {
        "CRITICAL": "#c0392b", "HIGH": "#e74c3c",
        "MEDIUM":   "#e67e22", "LOW": "#f39c12",
        "INFO":     "#27ae60",
    }

    # ── Hash integrity ──────────────────────────────────────────────────────
    integrity_passed = None
    hashes: dict = {}
    evidence_path_str = ""
    verified_time = ""
    integ_file = case_dir / "HashDeep_output" / "verification" / "integrity_verification.txt"
    if integ_file.exists():
        content = integ_file.read_text(encoding="utf-8", errors="ignore")
        integrity_passed = bool(re.search(r'INTEGRITY MAINTAINED|match:\s*PASS', content, re.I))
        if re.search(r'MISMATCH|match:\s*FAIL', content, re.I):
            integrity_passed = False
        for algo in ("MD5", "SHA1", "SHA256"):
            m = re.search(rf'{algo}:\s*([a-f0-9]+)', content, re.I)
            if m:
                hashes[algo] = m.group(1)
        m = re.search(r'Evidence:\s*(.+)', content)
        if m:
            evidence_path_str = m.group(1).strip()
        m = re.search(r'Verified:\s*(.+)', content)
        if m:
            verified_time = m.group(1).strip()

    if integrity_passed is None:
        integ_color = "#7f8c8d"; integ_text = "UNKNOWN"; integ_icon = "?"
    elif integrity_passed:
        integ_color = "#27ae60"; integ_text = "INTEGRITY MAINTAINED"; integ_icon = "&#10003;"
    else:
        integ_color = "#c0392b"; integ_text = "INTEGRITY FAILED"; integ_icon = "&#10007;"

    # ── ExifTool / EWF metadata ─────────────────────────────────────────────
    ewf_meta: dict = {}
    for jf in (case_dir / "ExifTool_output").rglob("*.json"):
        try:
            raw = _json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(raw, list) and raw:
                raw = raw[0]
            if isinstance(raw, dict):
                for k, v in raw.items():
                    nk = k.split(":")[-1] if ":" in k else k
                    ewf_meta[nk] = v
            break
        except Exception:
            pass

    interesting_fields = [
        "CaseNumber", "EvidenceNumber", "ExaminerName", "Subject", "Notes",
        "AcquisitionStartDateTime", "MediaType", "Model",
        "AcquisitionSoftwareVersion", "OperatingSystem", "FileSize", "FileType",
    ]
    meta_rows = ""
    for k in interesting_fields:
        v = ewf_meta.get(k)
        if v:
            meta_rows += (f"<tr><td class='hk'>{html_lib.escape(k)}</td>"
                          f"<td class='hv'>{html_lib.escape(str(v))}</td></tr>")

    # ── BulkExtractor artifact counts ───────────────────────────────────────
    be_counts: dict = {}
    be_dir = case_dir / "BulkExtractor_output"
    if be_dir.exists():
        for f in sorted(be_dir.rglob("*.txt")):
            try:
                lines = [ln for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                         if ln.strip() and not ln.startswith("#")]
                if lines:
                    be_counts[f.stem] = len(lines)
            except Exception:
                pass
    be_rows = "".join(
        f"<tr><td class='hk'>{html_lib.escape(k)}</td><td class='hv'>{v:,}</td></tr>"
        for k, v in sorted(be_counts.items(), key=lambda x: -x[1])
    ) or "<tr><td colspan='2' style='color:#555;padding:8px'>No BulkExtractor output</td></tr>"

    # ── Hash rows ────────────────────────────────────────────────────────────
    hash_rows = "".join(
        f"<tr><td class='hk'>{algo}</td><td class='hv' style='font-family:monospace;font-size:11px'>{val}</td></tr>"
        for algo, val in hashes.items()
    ) or "<tr><td colspan='2' style='color:#555;padding:8px'>Not available</td></tr>"

    # ── Tool cards ───────────────────────────────────────────────────────────
    all_tools = ["AUTOPSY", "BULK_EXTRACTOR", "EXIFTOOL", "HASHDEEP", "VOLATILITY"]
    # Check if Volatility was skipped (has a SKIPPED event vs genuinely no output)
    vol_skipped = any(e.source_tool == "VOLATILITY" and e.event_type == "SKIPPED" for e in events)
    tool_cards_html = ""
    for tool in all_tools:
        cnt = src_counts.get(tool, 0)
        col = SOURCE_COLORS.get(tool, "#95a5a6")
        if tool == "VOLATILITY" and vol_skipped:
            status = "SKIPPED"
            status_bg = "#5d4e37"
            sub_label = "no memory image"
            display_cnt = "—"
        elif cnt > 0:
            status = "ACTIVE"
            status_bg = col
            sub_label = "events found"
            display_cnt = cnt
        else:
            status = "NO DATA"
            status_bg = "#333"
            sub_label = "events found"
            display_cnt = 0
        tool_cards_html += f"""<div class="tool-card" style="border-top:4px solid {col}">
  <div class="tool-name">{tool.replace('_', ' ')}</div>
  <div class="tool-count">{display_cnt}</div>
  <div class="tool-label">{sub_label}</div>
  <span class="tool-status" style="background:{status_bg}">{status}</span>
</div>"""

    # ── Top findings ─────────────────────────────────────────────────────────
    top_events = [e for e in events if e.severity in ("CRITICAL", "HIGH", "MEDIUM")][:12]
    top_rows = ""
    for e in top_events:
        col = sev_badge.get(e.severity, "#999")
        top_rows += (f"<tr><td style='color:#7f8c8d;font-size:11px;white-space:nowrap'>{html_lib.escape(e.ts_iso)}</td>"
                     f"<td><span class='sev-badge' style='background:{col}'>{e.severity}</span></td>"
                     f"<td style='color:#bdc3c7'>{html_lib.escape(e.source_tool)}</td>"
                     f"<td style='color:#ecf0f1'>{html_lib.escape(e.description[:120])}</td></tr>")
    if not top_rows:
        top_rows = "<tr><td colspan='4' style='color:#555;padding:12px;text-align:center'>No high-severity findings &mdash; evidence verified clean</td></tr>"

    # ── Severity summary pills ────────────────────────────────────────────────
    sev_pills = " ".join(
        f'<span class="sev-badge" style="background:{sev_badge.get(s,"#999")}">{s}: {sev_counts.get(s,0)}</span>'
        for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
        if sev_counts.get(s, 0) > 0
    )

    # ── PDF links ────────────────────────────────────────────────────────────
    pdf_dir = case_dir / "Reports pdf"
    pdf_links = ""
    if pdf_dir.exists():
        for p in sorted(pdf_dir.glob("*.pdf")):
            pdf_links += f'<a class="navlink secondary" href="Reports pdf/{html_lib.escape(p.name)}">{html_lib.escape(p.stem[:35])}</a>'

    # ── AI narrative card ─────────────────────────────────────────────────────
    if ai_narrative:
        # Escape and preserve paragraphs
        paragraphs = [html_lib.escape(p.strip()) for p in ai_narrative.split("\n\n") if p.strip()]
        narrative_html = "".join(f"<p style='margin-bottom:10px;line-height:1.6'>{p}</p>"
                                 for p in paragraphs)
        ai_card = f"""  <div class="card">
    <div class="card-title" style="display:flex;align-items:center;gap:8px">
      <span style="background:#8e44ad;color:#fff;padding:3px 9px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:.5px">AI</span>
      AI Forensic Narrative &mdash; Generated by Local LLM
    </div>
    <div style="color:#bdc3c7;font-size:13px;margin-top:6px">{narrative_html}</div>
    <div style="color:#555;font-size:11px;margin-top:10px">Powered by Ollama &bull; fully offline &bull; no data leaves this machine</div>
  </div>"""
    else:
        ai_card = """  <div class="card" style="opacity:0.4">
    <div class="card-title" style="display:flex;align-items:center;gap:8px">
      <span style="background:#555;color:#aaa;padding:3px 9px;border-radius:12px;font-size:11px;font-weight:600;letter-spacing:.5px">AI</span>
      AI Narrative &mdash; Not Available
    </div>
    <div style="color:#555;font-size:13px;margin-top:6px">Ollama was not running when this case was analysed.<br>
    Run <code style="background:#2c3e50;padding:2px 6px;border-radius:3px">python ask_case.py</code> to query this case interactively.</div>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>EDITH Case Dashboard &mdash; {html_lib.escape(case_id)}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0f1117;color:#e0e0e0;min-height:100vh}}
a{{text-decoration:none}}
.topbar{{background:linear-gradient(135deg,#1a1d2e,#2c3e50);padding:20px 32px;border-bottom:3px solid #e74c3c;display:flex;align-items:center;gap:16px}}
.topbar h1{{font-size:24px;font-weight:700;color:#fff;letter-spacing:1px}}
.topbar h1 span{{color:#e74c3c}}
.topbar .meta{{font-size:12px;color:#aaa;margin-top:4px}}
.topbar-right{{margin-left:auto;text-align:right}}
.topbar-right strong{{font-size:18px;color:#fff;display:block}}
.topbar-right small{{font-size:11px;color:#aaa}}
.container{{max-width:1360px;margin:0 auto;padding:20px 24px}}
.navlinks{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}}
.navlink{{background:#e74c3c;color:#fff;padding:9px 18px;border-radius:6px;font-size:13px;font-weight:700;letter-spacing:.5px}}
.navlink:hover{{background:#c0392b}}
.navlink.secondary{{background:#2c3e50;color:#ccc;font-weight:600}}
.navlink.secondary:hover{{background:#34495e;color:#fff}}
.integ-banner{{border-radius:10px;padding:18px 24px;margin-bottom:18px;display:flex;align-items:center;gap:18px;
  background:{integ_color}18;border:2px solid {integ_color}}}
.integ-icon{{font-size:42px;color:{integ_color};font-weight:700;line-height:1}}
.integ-title{{font-size:22px;font-weight:700;color:{integ_color}}}
.integ-sub{{font-size:12px;color:#aaa;margin-top:5px}}
.tool-grid{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}}
.tool-card{{background:#1a1d2e;border-radius:8px;padding:16px 20px;min-width:140px;flex:1;text-align:center}}
.tool-name{{font-size:10px;color:#7f8c8d;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}}
.tool-count{{font-size:34px;font-weight:700;color:#fff}}
.tool-label{{font-size:10px;color:#555;margin-bottom:10px}}
.tool-status{{font-size:10px;font-weight:700;padding:3px 10px;border-radius:9px;color:#fff;display:inline-block}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}}
@media(max-width:860px){{.grid-2{{grid-template-columns:1fr}}}}
.card{{background:#1a1d2e;border-radius:10px;padding:18px 20px}}
.card-title{{font-size:10px;font-weight:700;color:#7f8c8d;text-transform:uppercase;letter-spacing:1px;
  margin-bottom:12px;border-bottom:1px solid #2c3e50;padding-bottom:7px}}
.kv-table{{width:100%;border-collapse:collapse;font-size:12px}}
.kv-table .hk{{color:#7f8c8d;padding:5px 8px;width:44%;font-weight:600;vertical-align:top}}
.kv-table .hv{{color:#ecf0f1;padding:5px 8px;word-break:break-all}}
.kv-table tr:nth-child(even){{background:#1e2235}}
.findings-table{{width:100%;border-collapse:collapse;font-size:12px}}
.findings-table th{{background:#1e222e;color:#7f8c8d;padding:9px 10px;text-align:left;
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px}}
.findings-table td{{padding:8px 10px;border-bottom:1px solid #1e222e;vertical-align:top}}
.findings-table tr:hover td{{background:#1e2235}}
.sev-badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:9px;color:#fff;
  text-transform:uppercase;display:inline-block;margin:1px}}
.sev-pills{{margin-top:10px;line-height:2}}
.total-badge{{font-size:42px;font-weight:700;color:#fff}}
</style>
</head>
<body>
<div class="topbar">
  <div>
    <h1>EDITH <span>Case Dashboard</span></h1>
    <div class="meta">Generated: <strong style="color:#fff;font-size:13px">{generated}</strong> &nbsp;|&nbsp; Officer: {html_lib.escape(officer or 'N/A')}</div>
  </div>
  <div class="topbar-right">
    <strong>{html_lib.escape(case_id)}</strong>
    <small>Case ID</small>
  </div>
</div>

<div class="container">
  <div class="navlinks">
    <a class="navlink" href="Timeline/investigation_timeline.html">&#128336; Timeline &mdash; {total} Events</a>
    {pdf_links}
  </div>

  <div class="integ-banner">
    <div class="integ-icon">{integ_icon}</div>
    <div>
      <div class="integ-title">{integ_text}</div>
      <div class="integ-sub">
        Evidence: <strong style="color:#ccc">{html_lib.escape(evidence_path_str or 'N/A')}</strong><br>
        Verified: {html_lib.escape(verified_time or 'N/A')}
      </div>
    </div>
  </div>

  <div class="tool-grid">
    {tool_cards_html}
    <div class="tool-card" style="border-top:4px solid #e74c3c;background:#1e1a2e">
      <div class="tool-name">Timeline Events</div>
      <div class="total-badge">{total}</div>
      <div class="tool-label">correlated across all tools</div>
      <div class="sev-pills">{sev_pills}</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title">Cryptographic Hash Verification</div>
      <table class="kv-table">{hash_rows}</table>
    </div>
    <div class="card">
      <div class="card-title">Evidence Metadata (from EWF/ExifTool)</div>
      <table class="kv-table">{meta_rows if meta_rows else '<tr><td colspan="2" style="color:#555;padding:8px">Not available</td></tr>'}</table>
    </div>
  </div>

  <div class="grid-2">
    <div class="card">
      <div class="card-title">BulkExtractor &mdash; Artifacts Carved from Raw Sectors</div>
      <table class="kv-table">{be_rows}</table>
    </div>
    <div class="card">
      <div class="card-title">Event Severity Breakdown</div>
      <table class="kv-table">
        {''.join(f'<tr><td class="hk" style="color:{sev_badge.get(s,"#999")}">{s}</td><td class="hv">{sev_counts.get(s,0)}</td></tr>' for s in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"])}
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-title">Key Findings &mdash; Medium / High / Critical</div>
    <table class="findings-table">
      <thead><tr><th>Timestamp</th><th>Severity</th><th>Source</th><th>Description</th></tr></thead>
      <tbody>{top_rows}</tbody>
    </table>
  </div>

  {ai_card}
</div>
</body>
</html>"""


# ──────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────

def main():
    import argparse, webbrowser
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(
        description="EDITH Cross-Tool Timeline Correlator"
    )
    parser.add_argument("case_dir", help="Path to case results directory")
    parser.add_argument("--case-id",  default="", help="Case ID label")
    parser.add_argument("--officer",  default="", help="Officer name")
    parser.add_argument("--open",     action="store_true", help="Open report in browser")
    args = parser.parse_args()

    corr = TimelineCorrelator(args.case_dir, args.case_id, args.officer)
    corr.build()

    out_dir = Path(args.case_dir) / "Timeline"
    out_dir.mkdir(exist_ok=True)

    html_path      = str(out_dir / "investigation_timeline.html")
    json_path      = str(out_dir / "timeline_events.json")
    dashboard_path = str(Path(args.case_dir) / "case_dashboard.html")

    corr.save_html(html_path)
    corr.save_json(json_path)
    corr.save_dashboard(dashboard_path)

    s = corr.summary()
    print(f"\n{'='*60}")
    print(f"  EDITH Timeline Correlator - {args.case_dir}")
    print(f"{'='*60}")
    print(f"  Total events   : {s['total_events']}")
    print(f"  Date range     : {s['date_range'][0]}  ->  {s['date_range'][1]}")
    print(f"  By source      : {s['by_source']}")
    print(f"  By severity    : {s['by_severity']}")
    hc = s['high_critical']
    if hc:
        print(f"\n  [!] HIGH/CRITICAL findings ({len(hc)}):")
        for ev in hc[:5]:
            print(f"     [{ev['severity']}] {ev['timestamp']}  {ev['subject'][:60]}")
    print(f"\n  Dashboard      : {dashboard_path}")
    print(f"  HTML report    : {html_path}")
    print(f"  JSON export    : {json_path}")
    print(f"{'='*60}\n")

    if args.open:
        webbrowser.open(f"file:///{dashboard_path}")

    return dashboard_path


if __name__ == "__main__":
    main()
