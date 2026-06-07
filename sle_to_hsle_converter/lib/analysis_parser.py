"""
Parse an analysis.md produced by the diff agent into structured file entries.

Expected .md format (written by formatter.py):
  Header table:
    | **SLE path** | `/abs/path/to/ref_sle` |
    | **HSLE path** | `/abs/path/to/ref_hsle` |

  Category tables:
    | Status | File | Description |
    |--------|------|-------------|
    | 🟢 Added    | `rel/path/to/file` | description text |
    | 🟡 Modified | `rel/path/to/file` | description text |
    | 🔴 Removed  | `rel/path/to/file` | description text |
    | ⏭️ Skipped  | `rel/path/to/file` | *[binary]* description |
"""

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import List, Optional

# Map status word (case-insensitive) to canonical name
_STATUS_WORDS = {
    'added':    'ADDED',
    'modified': 'MODIFIED',
    'removed':  'REMOVED',
    'skipped':  'SKIPPED',
}

# Row pattern: | <anything with status word> | `path` | description |
# Uses word-based matching so emoji variations don't affect parsing
_ROW_RE = re.compile(
    r'^\|\s*[^\|]*?\b(Added|Modified|Removed|Skipped)\b[^\|]*?\|\s*`([^`]+)`\s*\|(.*?)\|?\s*$',
    re.IGNORECASE | re.MULTILINE,
)

# Header path pattern: | **SLE path** | `/path` | or | **HSLE path** | `/path` |
_HEADER_RE = re.compile(
    r'\|\s*\*\*(SLE path|HSLE path)\*\*\s*\|\s*`([^`]+)`\s*\|',
    re.IGNORECASE,
)


@dataclass
class FileEntry:
    rel_path: str
    status: str          # ADDED | MODIFIED | REMOVED | SKIPPED
    description: str = ''


@dataclass
class AnalysisResult:
    ref_sle: str
    ref_hsle: str
    entries: List[FileEntry] = field(default_factory=list)


def parse(md_path: str) -> 'AnalysisResult':
    """Parse analysis.md and return reference paths + all file entries."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    ref_sle = ref_hsle = None
    for m in _HEADER_RE.finditer(content):
        label = m.group(1).lower()
        path  = m.group(2).strip()
        if 'sle path' == label:
            ref_sle = path
        elif 'hsle path' == label:
            ref_hsle = path

    if not ref_sle or not ref_hsle:
        raise ValueError(
            "Could not find 'SLE path' / 'HSLE path' in analysis.md header.\n"
            "Expected rows like:  | **SLE path** | `/abs/path` |"
        )

    entries: List[FileEntry] = []
    seen: set = set()

    for m in _ROW_RE.finditer(content):
        status_word = m.group(1).lower()
        raw_path    = m.group(2).strip()
        description = m.group(3).strip()

        status = _STATUS_WORDS.get(status_word)
        if not status:
            continue

        # Safety: reject absolute paths and directory-traversal sequences
        try:
            safe = _validate_rel_path(raw_path)
        except ValueError as exc:
            print(f"  [parser] WARNING: skipping unsafe path ({exc}): {raw_path!r}")
            continue

        if safe in seen:
            continue
        seen.add(safe)
        entries.append(FileEntry(rel_path=safe, status=status, description=description))

    return AnalysisResult(ref_sle=ref_sle, ref_hsle=ref_hsle, entries=entries)


def _validate_rel_path(raw: str) -> str:
    """
    Normalize and validate a relative path extracted from .md.
    Returns the normalized path or raises ValueError.
    """
    # Reject absolute paths
    if raw.startswith('/') or (len(raw) > 1 and raw[1] == ':'):
        raise ValueError("absolute path")

    # Use PurePosixPath to normalize (collapses ., resolves nothing else)
    parts = PurePosixPath(raw).parts

    # Reject any .. component
    if '..' in parts:
        raise ValueError("directory traversal")

    # Reconstruct with forward slashes
    normalized = '/'.join(parts)
    if not normalized:
        raise ValueError("empty path")

    return normalized
