"""
model_builder.py — Copy, add, and remove files to create the HSLE model tree.

ADDED files:
  - Copy ref_hsle/rel_path → output/rel_path.
  - Conflict if path already exists in new_sle AND content differs from ref_hsle.

REMOVED files:
  - Delete output/rel_path.
  - Safety check: only auto-delete if file still matches ref_sle content (unchanged
    in the new model); otherwise flag for review.
"""

import filecmp
import grp
import os
import shutil
import stat
from typing import Tuple

from .analysis_parser import FileEntry


# --------------------------------------------------------------------------- #
#  Create output tree
# --------------------------------------------------------------------------- #

def create_output(new_sle: str, output: str) -> None:
    """Copy the entire new SLE model to the output directory, preserving symlinks.

    After copying, ensure every file and directory in the output tree has owner
    write permission.  Source models often contain read-only files/dirs (e.g.
    permissions 555/444), which would cause PermissionError when the converter
    later writes ADDED or MODIFIED files into those paths.
    """
    shutil.copytree(new_sle, output, symlinks=True)
    _chmod_writable_tree(output)


# --------------------------------------------------------------------------- #
#  ADDED
# --------------------------------------------------------------------------- #

def apply_added(
    entry: FileEntry,
    *,
    ref_hsle: str,
    new_sle: str,
    output: str,
    donor: str | None = None,
    conflict_policy: str = 'manual',
    dry_run: bool = True,
) -> Tuple[str, str]:
    """
    Copy a file into output/rel_path, preferring the donor model over ref_hsle
    when the donor has the file (it is typically more up-to-date).

    Source priority: donor → ref_hsle

    Returns (outcome, detail) where outcome is one of:
      applied             — copied from ref_hsle
      applied_from_donor  — copied from donor model
      would_apply         — dry-run: would copy from ref_hsle
      would_apply_donor   — dry-run: would copy from donor
      conflict            — path exists in new model with different content
      already_same        — path exists and is already identical to chosen source
      missing_ref         — file not found in ref_hsle (and not in donor)
    """
    dst          = os.path.join(output,  entry.rel_path)
    new_sle_path = os.path.join(new_sle, entry.rel_path)

    # Resolve the best available source: donor first, then ref_hsle
    src, source_label = _resolve_source(entry.rel_path, ref_hsle=ref_hsle, donor=donor)
    if src is None:
        return ('missing_ref', f"Not found in ref_hsle or donor: {entry.rel_path}")

    # Validate paths stay inside their roots
    if not _is_under(src, source_label) or not _is_under(dst, output):
        return ('error', 'path escapes model root')

    # Conflict check — does new model already have this path?
    if os.path.exists(new_sle_path) and not os.path.islink(new_sle_path):
        if os.path.islink(src):
            tgt_src = os.readlink(src)
            tgt_new = os.readlink(new_sle_path) if os.path.islink(new_sle_path) else None
            if tgt_src == tgt_new:
                return ('already_same', f'symlink target matches ({_source_name(source_label, donor, ref_hsle)})')
        elif filecmp.cmp(new_sle_path, src, shallow=False):
            return ('already_same', f'content already identical to {_source_name(source_label, donor, ref_hsle)}')
        else:
            if conflict_policy == 'manual':
                return ('conflict', 'path exists in new model with different content (manual review)')
            # auto: overwrite — fall through to copy below

    is_donor = (donor and source_label == donor)

    if dry_run:
        return ('would_apply_donor' if is_donor else 'would_apply', '')

    os.makedirs(os.path.dirname(dst), exist_ok=True)

    if os.path.islink(src):
        link_target = os.readlink(src)
        if os.path.exists(dst) or os.path.islink(dst):
            os.unlink(dst)
        os.symlink(link_target, dst)
    else:
        shutil.copy2(src, dst)
        src_mode = os.stat(src, follow_symlinks=False).st_mode
        if src_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            current_mode = os.stat(dst).st_mode
            os.chmod(dst, current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return ('applied_from_donor' if is_donor else 'applied', '')


# --------------------------------------------------------------------------- #
#  REMOVED
# --------------------------------------------------------------------------- #

def apply_removed(
    entry: FileEntry,
    *,
    ref_sle: str,
    output: str,
    safety_check: bool = True,
    dry_run: bool = True,
) -> Tuple[str, str]:
    """
    Delete output/rel_path.

    Returns (outcome, detail) where outcome is one of:
      removed         — deleted successfully
      would_remove    — dry-run: would delete
      already_absent  — file not present in output (may have been removed already)
      conflict        — safety check failed: file differs from ref_sle in new model
    """
    target    = os.path.join(output,  entry.rel_path)
    ref_orig  = os.path.join(ref_sle, entry.rel_path)

    if not _is_under(target, output):
        return ('error', 'path escapes output root')

    if not os.path.exists(target) and not os.path.islink(target):
        return ('already_absent', 'file not present in new model')

    if safety_check and os.path.exists(ref_orig) and not os.path.islink(target):
        # Only auto-remove if still matches the ref SLE content (unchanged in new model)
        if not filecmp.cmp(target, ref_orig, shallow=False):
            return (
                'conflict',
                'file differs from ref_sle — may have been updated in new model; verify before deleting',
            )

    if dry_run:
        return ('would_remove', '')

    if os.path.islink(target) or os.path.isfile(target):
        os.unlink(target)
    elif os.path.isdir(target):
        shutil.rmtree(target)

    return ('removed', '')


# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

def _is_under(path: str, root: str) -> bool:
    """Return True if path is strictly under (or equal to) root after resolution."""
    try:
        real_path = os.path.realpath(os.path.abspath(path))
        real_root = os.path.realpath(os.path.abspath(root))
        return real_path.startswith(real_root + os.sep) or real_path == real_root
    except OSError:
        return False


def _resolve_source(
    rel_path: str,
    *,
    ref_hsle: str,
    donor: str | None,
) -> tuple[str | None, str]:
    """
    Return (absolute_src_path, root_dir) for the best available source of rel_path.
    Priority: donor > ref_hsle.

    Path variations tried:
      - Exact path
      - Cdie0TlsTb -> Cdie1TlsTb substitution (when Cdie0 not in donor/ref_hsle
        but Cdie1 exists; both are equivalent for most files in py_lib_overrides)

    Returns (None, '') if no variation is found.
    """
    candidates = [rel_path]
    if 'Cdie0TlsTb' in rel_path:
        candidates.append(rel_path.replace('Cdie0TlsTb', 'Cdie1TlsTb'))

    if donor:
        for rp in candidates:
            c = os.path.join(donor, rp)
            if os.path.exists(c) or os.path.islink(c):
                return c, donor
    for rp in candidates:
        c = os.path.join(ref_hsle, rp)
        if os.path.exists(c) or os.path.islink(c):
            return c, ref_hsle
    return None, ''


def _source_name(source_root: str, donor: str | None, ref_hsle: str) -> str:
    """Human-readable label for the source root."""
    if donor and source_root == donor:
        return 'donor'
    return 'ref_hsle'


# --------------------------------------------------------------------------- #
#  Permission & ownership helpers
# --------------------------------------------------------------------------- #

def finalize_permissions(output: str, group: str = 'soc') -> list[str]:
    """Walk output tree and apply group ownership + write permissions.

    For every non-symlink file and directory under *output*:
      - Set group to *group* (e.g. 'soc') via chown.
      - Add u+w and g+w so the model is writable by owner and group members.

    Symlinks are skipped — their target permissions are not changed.

    Returns a list of warning strings for any paths where chown/chmod failed
    (logged by the caller; never raises).
    """
    try:
        gid = grp.getgrnam(group).gr_gid
    except KeyError:
        return [f"Group '{group}' not found on this system — skipping chown"]

    warnings: list[str] = []
    for root, dirs, files in os.walk(output):
        for name in dirs + files:
            p = os.path.join(root, name)
            if os.path.islink(p):
                continue
            _apply_perms(p, gid, warnings)
    # Also fix the root output directory itself
    if not os.path.islink(output):
        _apply_perms(output, gid, warnings)
    return warnings


def _apply_perms(path: str, gid: int, warnings: list[str]) -> None:
    """Set group ownership and add u+w g+w to a single path."""
    try:
        st = os.stat(path)
        if st.st_gid != gid:
            os.chown(path, -1, gid)          # -1 = keep existing uid
        new_mode = st.st_mode | stat.S_IWUSR | stat.S_IWGRP
        if stat.S_IMODE(st.st_mode) != stat.S_IMODE(new_mode):
            os.chmod(path, new_mode)
    except OSError as exc:
        warnings.append(f"{path}: {exc}")


def _chmod_writable_tree(root: str) -> None:
    """Add u+w to every non-symlink file and directory under root (including root)."""
    for dirpath, dirs, files in os.walk(root):
        for name in dirs + files:
            p = os.path.join(dirpath, name)
            if not os.path.islink(p):
                try:
                    os.chmod(p, os.stat(p).st_mode | stat.S_IWUSR)
                except OSError:
                    pass
    if not os.path.islink(root):
        try:
            os.chmod(root, os.stat(root).st_mode | stat.S_IWUSR)
        except OSError:
            pass
