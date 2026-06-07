"""
merger.py — 3-way merge for MODIFIED files using `git merge-file`.

Strategy:
  base   = ref_sle/rel_path   (the common ancestor — what the reference SLE had)
  ours   = output/rel_path    (copy of new_sle/rel_path — what we want to update)
  theirs = ref_hsle/rel_path  (what the reference HSLE has — the change to apply)

`git merge-file --stdout ours base theirs` produces the merged result.
  exit 0  → clean merge, no conflicts
  exit >0 → N conflict hunks (output contains <<<< markers)
  exit <0 → error (missing file, binary, etc.)

On conflict or error the caller may invoke the LLM fallback in llm_client.py.
"""

import os
import stat
import subprocess
import tempfile
from typing import Tuple

from .analysis_parser import FileEntry

_GIT = 'git'


# --------------------------------------------------------------------------- #
#  Public API
# --------------------------------------------------------------------------- #

def is_binary(path: str) -> bool:
    """Heuristic binary detection via null-byte scan (first 8 KB)."""
    try:
        with open(path, 'rb') as f:
            return b'\x00' in f.read(8192)
    except OSError:
        return True


def three_way_merge(
    entry: FileEntry,
    *,
    ref_sle: str,
    ref_hsle: str,
    output: str,
    dry_run: bool = True,
    current_path: str | None = None,
) -> Tuple[str, str]:
    """
    Perform a 3-way merge for one MODIFIED file.

    current_path: override the "ours" file path. In dry-run mode pass the
                  new_sle path so we can simulate without a real output tree.

    Returns (outcome, detail):
      merged_clean    — applied with no conflicts
      would_merge     — dry-run: would apply cleanly
      conflicts       — N conflict hunks remain (not written)
      would_conflict  — dry-run: would have conflicts
      binary          — binary file, cannot merge
      missing_ref     — base or theirs not found
      missing_current — file absent from output (may need ADDED treatment)
      git_unavailable — git not in PATH
      error           — unexpected subprocess error
    """
    current = current_path or os.path.join(output, entry.rel_path)
    base    = os.path.join(ref_sle,  entry.rel_path)
    theirs  = os.path.join(ref_hsle, entry.rel_path)

    # Pre-flight existence checks
    if not os.path.exists(base):
        return ('missing_ref', f"Not found in ref_sle: {entry.rel_path}")
    if not os.path.exists(theirs):
        return ('missing_ref', f"Not found in ref_hsle: {entry.rel_path}")
    if not os.path.exists(current):
        return ('missing_current', f"Not in output tree: {entry.rel_path}")

    # Binary guard
    if is_binary(base) or is_binary(theirs) or is_binary(current):
        return ('binary', 'Binary file — manual review required')

    merged_content, outcome = _run_git_merge(current, base, theirs)

    if outcome == 'git_unavailable':
        return ('git_unavailable', 'git not found in PATH')
    if outcome == 'error':
        return ('error', merged_content)  # merged_content carries the error message here

    has_conflicts = outcome == 'conflicts'
    conflict_detail = ''

    # ── Smart resolution: try to auto-resolve conflict markers ─────────────
    # git merge-file marks concurrent insertions at the same anchor as a
    # conflict even though both sides' additions should be kept.  Resolve
    # those "keep-both" cases deterministically before falling back to LLM.
    if has_conflicts:
        smart_content, n_unresolved = resolve_conflict_markers(merged_content, base)
        if n_unresolved == 0:
            has_conflicts = False
            merged_content = smart_content
            conflict_detail = 'concurrent insertions auto-resolved (keep-both)'
        else:
            # Partially resolved: update merged_content so the LLM (or the
            # user) only sees the remaining hard conflicts with TODO markers.
            merged_content = smart_content
            conflict_detail = (
                f"{n_unresolved} modification conflict(s) remain after "
                f"auto-resolving insertion conflicts — LLM/manual needed"
            )

    # ── Post-merge HSLE-drop check (exit-0 silent drops) ───────────────────
    # git merge-file can silently pick one side when both ours and theirs
    # insert after the same anchor line and exits 0 with no markers.
    if not has_conflicts:
        dropped = _check_hsle_drops(base, theirs, merged_content)
        if dropped:
            has_conflicts = True
            preview = repr(dropped[0])
            extra = f" (+{len(dropped)-1} more)" if len(dropped) > 1 else ""
            conflict_detail = (
                f"git silently dropped {len(dropped)} HSLE-unique line(s): "
                f"{preview}{extra} — escalating to LLM"
            )

    if dry_run:
        if has_conflicts:
            return ('would_conflict', conflict_detail)
        elif conflict_detail:  # smart-resolved
            return ('would_smart_merge', conflict_detail)
        return ('would_merge', '')

    if has_conflicts:
        # Write partially-resolved content (with TODO markers) so the LLM
        # or user gets a useful starting point instead of the raw new-SLE file.
        _write_preserving_endings(current, merged_content)
        return ('conflicts', conflict_detail)

    # Write merged result, preserving original line endings
    _write_preserving_endings(current, merged_content)

    # Preserve executable bit from reference HSLE
    try:
        src_mode = os.stat(theirs).st_mode
        if src_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            cur_mode = os.stat(current).st_mode
            os.chmod(current, cur_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass

    if conflict_detail:  # smart-resolved
        return ('merged_smart', conflict_detail)
    return ('merged_clean', '')


def get_unified_diff(base_path: str, theirs_path: str, max_chars: int = 4000) -> str:
    """
    Return a unified diff of base → theirs (ref_sle → ref_hsle) for LLM prompting.
    Capped at max_chars to stay within token limits.
    """
    try:
        result = subprocess.run(
            ['diff', '-u',
             '--label', 'ref_sle', '--label', 'ref_hsle',
             base_path, theirs_path],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout[:max_chars]
    except Exception:
        return ''


# --------------------------------------------------------------------------- #
#  Internals
# --------------------------------------------------------------------------- #

def _run_git_merge(current: str, base: str, theirs: str) -> Tuple[str, str]:
    """
    Call `git merge-file --stdout` and return (content, outcome).
    outcome: 'clean' | 'conflicts' | 'git_unavailable' | 'error'
    On error, content carries the error message.
    """
    # Write current to a temp file so we can pass it to git without modifying
    # the output file until we're ready to commit.
    try:
        with tempfile.NamedTemporaryFile(
            mode='wb', suffix='.merge_current', delete=False
        ) as tf:
            with open(current, 'rb') as src:
                tf.write(src.read())
            tmp_path = tf.name

        result = subprocess.run(
            [_GIT, 'merge-file', '--stdout',
             '-L', 'new_sle', '-L', 'ref_sle', '-L', 'ref_hsle',
             tmp_path, base, theirs],
            capture_output=True, text=True, timeout=30,
        )

        if result.returncode < 0:
            return (result.stderr.strip(), 'error')

        merged = result.stdout
        outcome = 'conflicts' if result.returncode > 0 else 'clean'
        return (merged, outcome)

    except FileNotFoundError:
        return ('', 'git_unavailable')
    except subprocess.TimeoutExpired:
        return ('', 'error')
    except Exception as exc:
        return (str(exc), 'error')
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _write_preserving_endings(path: str, content: str) -> None:
    """Write text content to path, matching the original file's line-ending style."""
    try:
        with open(path, 'rb') as f:
            original = f.read(4096)
        use_crlf = b'\r\n' in original
    except OSError:
        use_crlf = False

    if use_crlf:
        data = content.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
    else:
        data = content.encode('utf-8')

    with open(path, 'wb') as f:
        f.write(data)


def resolve_conflict_markers(content: str, base_path: str) -> tuple[str, int]:
    """
    Auto-resolve git conflict markers in `content`.

    Strategy per conflict hunk:
    - Pure concurrent insertion (neither ours nor theirs lines existed in base):
        → keep both sides (ours first, then theirs).
    - Modification conflict (at least one side modified lines that were in base):
        → replace with a clearly-labelled TODO block for manual resolution.

    Returns (resolved_content, num_unresolved_hunks).
    num_unresolved_hunks == 0 means the file is fully resolved.
    """
    try:
        with open(base_path, 'r', encoding='utf-8', errors='replace') as f:
            base_set = {l.rstrip() for l in f if l.strip()}
    except OSError:
        base_set = set()

    lines = content.split('\n')
    result_lines: list[str] = []
    n_unresolved = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        if not line.startswith('<<<<<<<'):
            result_lines.append(line)
            i += 1
            continue

        # ── collect the three sections of one conflict hunk ────────────────
        ours_lines: list[str] = []
        sep_lines:  list[str] = []   # lines between ======= variants (rare)
        theirs_lines: list[str] = []
        in_section = 'ours'
        i += 1  # skip <<<<<<< line

        while i < len(lines):
            l = lines[i]
            if l.startswith('======='):
                in_section = 'theirs'
                i += 1
                continue
            if l.startswith('>>>>>>>'):
                i += 1  # skip >>>>>>> line
                break
            if in_section == 'ours':
                ours_lines.append(l)
            else:
                theirs_lines.append(l)
            i += 1

        # ── decide: pure insertion or modification? ─────────────────────────
        ours_stripped   = {l.rstrip() for l in ours_lines   if l.strip()}
        theirs_stripped = {l.rstrip() for l in theirs_lines if l.strip()}

        ours_in_base   = bool(ours_stripped   & base_set)
        theirs_in_base = bool(theirs_stripped & base_set)

        if not ours_in_base and not theirs_in_base:
            # Both sides added new-to-base lines → pure concurrent insertion.
            # Keep both: new-SLE additions first, then HSLE additions.
            result_lines.extend(ours_lines)
            result_lines.extend(theirs_lines)
        else:
            # At least one side modified something that was in the base.
            # Cannot safely auto-resolve; emit a TODO block.
            n_unresolved += 1
            result_lines.append(
                '# TODO: MANUAL MERGE CONFLICT — resolve this block before use'
            )
            result_lines.append('# <<<< new_sle (keep what belongs to new version)')
            result_lines.extend(ours_lines)
            result_lines.append('# ==== HSLE change (apply the HSLE-specific change)')
            result_lines.extend(theirs_lines)
            result_lines.append('# >>>> end conflict')

    return ('\n'.join(result_lines), n_unresolved)


def _check_hsle_drops(base_path: str, theirs_path: str, merged_content: str) -> list[str]:
    """
    Detect HSLE-unique lines that git merge-file silently omitted from the result.

    A line is considered "silently dropped" when:
      - it is present in ref_hsle (theirs) but absent from ref_sle (base)
        → HSLE uniquely added this line
      - it is absent from the merged content
        → git merge-file dropped it without producing a conflict marker

    Lines are compared with trailing whitespace stripped to tolerate minor
    whitespace differences between files.  Empty lines are ignored.

    Returns the list of dropped lines (original form, sorted).
    """
    try:
        with open(base_path, 'r', encoding='utf-8', errors='replace') as f:
            base_set = {l.rstrip() for l in f if l.strip()}
        with open(theirs_path, 'r', encoding='utf-8', errors='replace') as f:
            theirs_lines = [l.rstrip() for l in f if l.strip()]
        theirs_set = set(theirs_lines)

        merged_set = {l.rstrip() for l in merged_content.splitlines() if l.strip()}

        hsle_only = theirs_set - base_set          # lines HSLE uniquely added
        dropped   = sorted(hsle_only - merged_set) # which are missing from merged
        return dropped
    except Exception:
        return []
