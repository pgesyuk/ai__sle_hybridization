#!/usr/bin/env python3
"""
HSLE Converter Agent
====================
Apply a reference SLE→HSLE transition to a new (unseen) SLE model.

Inputs:
  --sle-model   Path to the new SLE model directory to convert.
  --analysis    Path to the analysis .md file produced by the diff agent.
                (Must contain embedded "SLE path" / "HSLE path" header rows.)
  --output      Destination path for the resulting HSLE model.

Pipeline:
  1. Parse analysis.md  → ref_sle, ref_hsle paths + 212-file entry list
  2. Preflight checks   → validate all paths / tools / .md integrity
  3. Create output tree → shutil.copytree(new_sle → output, symlinks=True)
  4. Apply ADDED        → copy ref_hsle/file → output/file  (conflict detection)
  5. Apply REMOVED      → delete output/file                (safety check)
  6. Apply MODIFIED     → git merge-file 3-way merge; LLM fallback on conflict
  7. Write report       → conversion_report.txt + .md

Default mode is --mode dry-run (safe preview). Use --mode apply to commit changes.
"""

import argparse
import os
import shutil
import stat
import sys

# ── local .deps for PyYAML ─────────────────────────────────────────────────
_DEPS = os.path.join(os.path.dirname(__file__), '.deps')
if os.path.isdir(_DEPS):
    sys.path.insert(0, _DEPS)

import yaml  # noqa: E402 (after path fixup)

sys.path.insert(0, os.path.dirname(__file__))

from lib.analysis_parser import parse as parse_analysis
from lib.model_builder    import (create_output, apply_added, apply_removed,
                                  finalize_permissions, _dereference_file_symlinks)
from lib.merger           import three_way_merge, is_binary, get_unified_diff
from lib.llm_client       import llm_merge_file
from lib.reporter         import write_report


# --------------------------------------------------------------------------- #
#  Config loading
# --------------------------------------------------------------------------- #

def _load_config(path: str | None) -> dict:
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


# --------------------------------------------------------------------------- #
#  Preflight validation
# --------------------------------------------------------------------------- #

def _preflight(args, cfg) -> tuple[object, str, str]:
    """Validate paths, tools, and .md integrity. Returns (analysis, ref_sle, ref_hsle)."""
    errors = []

    if not os.path.isfile(args.analysis):
        errors.append(f"analysis file not found: {args.analysis}")
    if not os.path.isdir(args.sle_model):
        errors.append(f"SLE model directory not found: {args.sle_model}")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)

    try:
        analysis = parse_analysis(args.analysis)
    except ValueError as exc:
        print(f"  ERROR parsing analysis.md: {exc}")
        sys.exit(1)

    ref_sle  = args.ref_sle  or analysis.ref_sle
    ref_hsle = args.ref_hsle or analysis.ref_hsle

    if not os.path.isdir(ref_sle):
        errors.append(f"Reference SLE directory not found: {ref_sle}")
    if not os.path.isdir(ref_hsle):
        errors.append(f"Reference HSLE directory not found: {ref_hsle}")

    # Donor is optional — warn but do not abort if path is given but missing
    if getattr(args, 'donor', None) and not os.path.isdir(args.donor):
        print(f"  WARNING: donor directory not found: {args.donor} — ignoring donor")

    if shutil.which('git') is None:
        print("  WARNING: git not found in PATH — 3-way merge unavailable; will use LLM or manual mode")

    if errors:
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)

    return analysis, ref_sle, ref_hsle


# --------------------------------------------------------------------------- #
#  Main pipeline
# --------------------------------------------------------------------------- #

def run() -> None:
    parser = argparse.ArgumentParser(
        description='Apply a reference SLE→HSLE transition to a new SLE model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--sle-model',  required=True, help='New SLE model directory to convert')
    parser.add_argument('--analysis',   required=True, help='analysis.md from the diff agent')
    parser.add_argument('--output',     required=True, help='Destination path for the HSLE model')
    parser.add_argument('--config',                    help='Optional config.yaml')
    parser.add_argument('--mode',       choices=['dry-run', 'apply'], default='dry-run',
                        help='dry-run (default): preview only; apply: commit changes')
    parser.add_argument('--patch-mode', choices=['3way', 'llm', 'auto'], default='auto',
                        help='Strategy for MODIFIED files (default: auto = 3way then LLM fallback)')
    parser.add_argument('--force',      action='store_true',
                        help='Overwrite output directory if it already exists')
    parser.add_argument('--ref-sle',    help='Override reference SLE path extracted from analysis.md')
    parser.add_argument('--ref-hsle',   help='Override reference HSLE path extracted from analysis.md')
    parser.add_argument('--donor',      help='Donor HSLE model (previous project or version) — '
                                             'provides up-to-date HSLE files and LLM context')
    parser.add_argument('--scope',      metavar='TEXT',
                        help='Only apply changes whose path contains TEXT (case-insensitive). '
                             'E.g. --scope cdie0 restricts all ADDED/MODIFIED/REMOVED '
                             'operations to files matching that substring.')
    args = parser.parse_args()

    cfg      = _load_config(args.config)
    dry_run  = args.mode == 'dry-run'
    patch_mode          = args.patch_mode or cfg.get('patch_mode', 'auto')
    conflict_policy     = cfg.get('added_conflict_policy', 'manual')
    removed_safety      = cfg.get('removed_safety_check', True)
    llm_max_chars       = cfg.get('llm_max_chars', 10_000)
    llm_max_lines       = cfg.get('llm_max_lines', 300)
    merge_hints         = cfg.get('merge_hints', '')
    report_name         = cfg.get('report_name', 'conversion_report')
    file_overrides      = cfg.get('file_overrides', {})   # {rel_path: abs_src_path}
    _path_remaps        = cfg.get('path_remaps', [])       # [{from: X, to: Y}, ...]

    print("=" * 60)
    print("  HSLE Converter Agent")
    print(f"  Mode: {'DRY-RUN (preview)' if dry_run else 'APPLY (writing files)'}")
    if args.scope:
        print(f"  Scope: {args.scope}  (only paths containing this string)")
    print("=" * 60)

    # ── Step 1: Parse + preflight ───────────────────────────────────────────
    print("\n[1/6] Parsing analysis.md and validating paths...")
    analysis, ref_sle, ref_hsle = _preflight(args, cfg)

    added    = [e for e in analysis.entries if e.status == 'ADDED']
    removed  = [e for e in analysis.entries if e.status == 'REMOVED']
    modified = [e for e in analysis.entries if e.status == 'MODIFIED']
    skipped  = [e for e in analysis.entries if e.status == 'SKIPPED']

    print(f"  Parsed {len(analysis.entries)} entries: "
          f"{len(added)} added, {len(modified)} modified, "
          f"{len(removed)} removed, {len(skipped)} skipped/binary")

    # Auto-generated directories/paths: never touched by the converter.
    # These files are regenerated during compilation and must not be
    # overwritten, deleted, or merged.
    _AUTOGEN_PREFIXES = ('filelists/', 'output/', '.grdlbuild_logs/', 'soc/', 'subip/', 'src/codegen/')
    def _is_autogen(rel_path: str) -> bool:
        if any(rel_path == p.rstrip('/') or rel_path.startswith(p)
               for p in _AUTOGEN_PREFIXES):
            return True
        if 'PCD_WORKAREA/' in rel_path and 'pchlp/output/' in rel_path:
            return True
        return False

    autogen_count = sum(1 for e in added + removed + modified if _is_autogen(e.rel_path))
    if autogen_count:
        added    = [e for e in added    if not _is_autogen(e.rel_path)]
        removed  = [e for e in removed  if not _is_autogen(e.rel_path)]
        modified = [e for e in modified if not _is_autogen(e.rel_path)]
        print(f"  Auto-generated excluded: {autogen_count} entries "
              f"(filelists/ or PCD_WORKAREA pchlp/output/)")

    if args.scope:
        scope_lc = args.scope.lower()
        added    = [e for e in added    if scope_lc in e.rel_path.lower()]
        removed  = [e for e in removed  if scope_lc in e.rel_path.lower()]
        modified = [e for e in modified if scope_lc in e.rel_path.lower()]
        print(f"  Scope filter '{args.scope}': "
              f"{len(added)} added, {len(modified)} modified, {len(removed)} removed")

    # ── Path remapping ────────────────────────────────────────────────────────
    # Remap analysis entry paths to project-specific output destinations.
    # Source lookup always uses entry.rel_path; only the output path is remapped.
    # Configured via path_remaps in config.yaml: [{from: X, to: Y}, ...]
    def _remap_output_path(rel_path: str) -> str | None:
        """Return the remapped output path, or None if no remap applies."""
        for remap in _path_remaps:
            frm = remap.get('from', '')
            if frm and rel_path.startswith(frm):
                return remap.get('to', frm) + rel_path[len(frm):]
        return None

    if _path_remaps:
        remap_count = 0
        dest_seen: dict[str, str] = {}
        for entry in added + modified + removed:
            remapped = _remap_output_path(entry.rel_path)
            if remapped is not None:
                remap_count += 1
                if remapped in dest_seen:
                    print(f"  WARNING: path remap collision: "
                          f"'{entry.rel_path}' and '{dest_seen[remapped]}' "
                          f"both map to '{remapped}'")
                dest_seen[remapped] = entry.rel_path
        if remap_count:
            print(f"  Path remaps: {remap_count} entries will be placed at remapped destinations")

    print(f"  Ref SLE  : {ref_sle}")
    print(f"  Ref HSLE : {ref_hsle}")
    print(f"  New SLE  : {args.sle_model}")
    print(f"  Output   : {args.output}")
    donor = args.donor if (args.donor and os.path.isdir(args.donor)) else None
    if donor:
        print(f"  Donor    : {donor}")

    results = []

    # ── Step 2: Create output tree ──────────────────────────────────────────
    print("\n[2/6] Preparing output directory...")
    if os.path.exists(args.output):
        if not args.force:
            print(f"  ERROR: Output already exists: {args.output}")
            print("  Use --force to remove it and start fresh.")
            sys.exit(1)
        if not dry_run:
            shutil.rmtree(args.output)
            print(f"  Removed existing: {args.output}")

    if dry_run:
        print(f"  [dry-run] Would copy: {args.sle_model} → {args.output}")
    else:
        create_output(args.sle_model, args.output)
        print(f"  Copied: {args.sle_model} → {args.output}")

    # ── Step 3: Apply ADDED ─────────────────────────────────────────────────
    print(f"\n[3/6] Applying {len(added)} ADDED files...")
    for entry in added:
        outcome, detail = apply_added(
            entry,
            ref_hsle=ref_hsle,
            new_sle=args.sle_model,
            output=args.output,
            donor=donor,
            conflict_policy=conflict_policy,
            dry_run=dry_run,
            output_rel_path=_remap_output_path(entry.rel_path),
        )
        icon = '✓' if outcome in ('applied', 'applied_from_donor', 'would_apply', 'would_apply_donor', 'already_same') else '!'
        display_path = _remap_output_path(entry.rel_path) or entry.rel_path
        print(f"  {icon} {outcome:<22} {display_path}")
        if detail and outcome not in ('applied', 'applied_from_donor', 'would_apply', 'would_apply_donor', 'already_same'):
            print(f"      ↳ {detail}")
        results.append({
            'status': 'ADDED', 'rel_path': display_path,
            'outcome': outcome, 'detail': detail,
            'description': entry.description,
        })

    # ── Step 4: Apply REMOVED ───────────────────────────────────────────────
    print(f"\n[4/6] Applying {len(removed)} REMOVED files...")
    for entry in removed:
        outcome, detail = apply_removed(
            entry,
            ref_sle=ref_sle,
            output=args.output,
            safety_check=removed_safety,
            dry_run=dry_run,
            output_rel_path=_remap_output_path(entry.rel_path),
        )
        icon = '✓' if outcome in ('removed', 'would_remove', 'already_absent') else '!'
        display_path = _remap_output_path(entry.rel_path) or entry.rel_path
        print(f"  {icon} {outcome:<18} {display_path}")
        if detail and outcome not in ('removed', 'already_absent'):
            print(f"      ↳ {detail}")
        results.append({
            'status': 'REMOVED', 'rel_path': display_path,
            'outcome': outcome, 'detail': detail,
            'description': entry.description,
        })

    # ── Step 5: Apply MODIFIED ──────────────────────────────────────────────
    print(f"\n[5/6] Applying {len(modified)} MODIFIED files (patch_mode={patch_mode})...")
    for entry in modified:
        outcome = detail = ''
        _out_rel = _remap_output_path(entry.rel_path)  # None if no remap

        # 3-way merge attempt
        if patch_mode in ('3way', 'auto'):
            # In dry-run mode the output tree hasn't been created yet;
            # point the merger at new_sle so it can simulate the merge.
            dry_run_current = (
                os.path.join(args.sle_model, entry.rel_path) if dry_run else None
            )
            outcome, detail = three_way_merge(
                entry, ref_sle=ref_sle, ref_hsle=ref_hsle,
                output=args.output, dry_run=dry_run,
                current_path=dry_run_current,
                output_rel_path=_out_rel,
            )

        # Fallback A: missing file -> copy from ref_hsle/donor
        if outcome in ('missing_current', 'missing_ref'):
            fb_outcome, fb_detail = apply_added(
                entry,
                ref_hsle=ref_hsle, new_sle=args.sle_model, output=args.output,
                donor=donor, conflict_policy='auto', dry_run=dry_run,
                output_rel_path=_out_rel,
            )
            if fb_outcome not in ('missing_ref', 'error'):
                outcome = fb_outcome
                detail  = fb_detail or 'file absent from new SLE -- copied from ref_hsle'

        # LLM fallback — only in apply mode, only on conflict/error
        dst_file = os.path.join(args.output, _out_rel or entry.rel_path)
        if patch_mode in ('llm', 'auto') and not dry_run:
            if outcome in ('conflicts', 'error', 'git_unavailable', ''):
                current_path = dst_file
                base_path    = os.path.join(ref_sle,  entry.rel_path)
                theirs_path  = os.path.join(ref_hsle, entry.rel_path)

                if (os.path.exists(current_path)
                        and not is_binary(current_path)
                        and os.path.exists(base_path)
                        and os.path.exists(theirs_path)):
                    diff_text = get_unified_diff(base_path, theirs_path)
                    outcome, detail = llm_merge_file(
                        current_path=current_path,
                        base_path=base_path,
                        theirs_path=theirs_path,
                        diff_text=diff_text,
                        description=entry.description,
                        donor_path   = os.path.join(donor, entry.rel_path) if donor else None,
                        merge_hints=merge_hints,
                        max_chars=llm_max_chars,
                        max_lines=llm_max_lines,
                    )

        display_path = _out_rel or entry.rel_path
        icon = '✓' if outcome in (
            'merged_clean', 'merged_smart', 'llm_merged',
            'would_merge',  'would_smart_merge',
            'applied', 'applied_from_donor', 'would_apply', 'would_apply_donor',
        ) else '!'
        print(f"  {icon} {outcome:<22} {display_path}")
        if detail:
            print(f"      ↳ {detail}")
        results.append({
            'status': 'MODIFIED', 'rel_path': display_path,
            'outcome': outcome, 'detail': detail,
            'description': entry.description,
        })

    # Skipped/binary — record but don't touch
    for entry in skipped:
        results.append({
            'status': 'SKIPPED', 'rel_path': entry.rel_path,
            'outcome': 'binary', 'detail': 'Binary file — manual review required',
            'description': entry.description,
        })

    # ── Step 5b (overrides): config file_overrides + built-in assets overlay ──
    # Part 1: project-specific overrides from config.yaml file_overrides dict
    if file_overrides and not dry_run and os.path.isdir(args.output):
        print(f"\n[5b/6] Applying {len(file_overrides)} config file override(s)...")
        for rel_path, src_path in file_overrides.items():
            dst = os.path.join(args.output, rel_path)
            if not os.path.isfile(src_path):
                print(f"  ! override_missing     {rel_path}")
                print(f"      ↳ source not found: {src_path}")
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src_path, dst)
            os.chmod(dst, os.stat(dst).st_mode | stat.S_IWUSR)
            print(f"  ✓ override_applied     {rel_path}")
            print(f"      ↳ from: {src_path}")

    # Part 2: built-in assets overlay — files under assets/ ship WITH the
    # converter and are always applied to the output model using the same
    # relative path (assets/scripts/foo -> output/scripts/foo).
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
    if os.path.isdir(assets_dir) and not dry_run and os.path.isdir(args.output):
        asset_files = []
        for dirpath, _, files in os.walk(assets_dir):
            for fname in files:
                asset_files.append(os.path.join(dirpath, fname))
        if asset_files:
            print(f"\n[5b/6] Applying {len(asset_files)} built-in asset(s) from assets/...")
        for src_path in asset_files:
            rel_path = os.path.relpath(src_path, assets_dir)
            dst = os.path.join(args.output, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src_path, dst)
            os.chmod(dst, os.stat(dst).st_mode | stat.S_IWUSR)
            print(f"  ✓ asset_applied        {rel_path}")

    # ── Step 5c: Finalize permissions ───────────────────────────────────────
    if not dry_run and os.path.isdir(args.output):
        output_group = cfg.get('output_group', 'soc')
        _dereference_file_symlinks(args.output)
        perm_warnings = finalize_permissions(args.output, group=output_group)
        if perm_warnings:
            for w in perm_warnings:
                print(f"  [warn] {w}")
        else:
            print(f"  ✓ Permissions set: group={output_group}, u+w g+w on all files")

    # ── Step 6: Write reports ────────────────────────────────────────────────
    print("\n[6/6] Writing reports...")
    report_dir = args.output if (not dry_run and os.path.isdir(args.output)) \
                 else os.path.dirname(os.path.abspath(args.output))
    os.makedirs(report_dir, exist_ok=True)

    write_report(
        results, report_dir,
        sle_model=args.sle_model, ref_sle=ref_sle, ref_hsle=ref_hsle,
        donor=donor or '',
        dry_run=dry_run, name=report_name,
    )

    # Emit MERGE_TODO.md for files that need manual attention
    manual_items = [
        r for r in results if r['outcome'] in (
            'conflicts', 'conflict',
            'llm_error', 'llm_empty', 'too_large',
            'missing_ref', 'missing_current',
            'error', 'git_unavailable',
        )
    ]
    if manual_items and not dry_run:
        _write_merge_todo(manual_items, report_dir, ref_sle=ref_sle, ref_hsle=ref_hsle)
        print(f"  ⚠ Manual review needed for {len(manual_items)} file(s).")
        print(f"    See: {report_dir}/MERGE_TODO.md")

    # ── Final summary ────────────────────────────────────────────────────────
    auto_count   = sum(1 for r in results if r['outcome'] in
                       ('applied', 'applied_from_donor', 'removed',
                        'merged_clean', 'merged_smart', 'llm_merged',
                        'already_same', 'already_absent',
                        'would_apply', 'would_apply_donor', 'would_remove',
                        'would_merge', 'would_smart_merge'))
    manual_count = sum(1 for r in results if r['outcome'] in
                       ('conflict', 'conflicts', 'would_conflict',
                        'missing_ref', 'missing_current',
                        'binary', 'error', 'git_unavailable', 'too_large',
                        'llm_error', 'llm_empty'))

    print()
    print("=" * 60)
    if dry_run:
        print("  DRY-RUN COMPLETE — no files written")
        print(f"  {len(results)} files analysed: "
              f"{auto_count} would auto-apply, {manual_count} need manual review")
        print()
        print("  To commit the conversion:")
        print(f"    python3 convert.py --sle-model {args.sle_model} \\")
        print(f"      --analysis {args.analysis} \\")
        print(f"      --output {args.output} \\")
        print(f"      --mode apply")
    else:
        print("  ✓ CONVERSION COMPLETE")
        print(f"  {len(results)} files processed: "
              f"{auto_count} auto-applied, {manual_count} need manual review")
        if manual_count:
            print(f"\n  ⚠  {manual_count} file(s) need manual attention:")
            print(f"     {report_dir}/MERGE_TODO.md")
    print("=" * 60)


def _write_merge_todo(
    items: list[dict],
    report_dir: str,
    *,
    ref_sle: str,
    ref_hsle: str,
) -> None:
    """
    Write MERGE_TODO.md — a human-readable checklist of files that the
    converter could not fully auto-resolve.  Each entry explains what
    HSLE change was intended and how to apply it manually.
    """
    path = os.path.join(report_dir, 'MERGE_TODO.md')
    lines = [
        "# MERGE_TODO — Manual Merge Required",
        "",
        "The converter left the following files in an unresolved state.",
        "For each file, the intended HSLE change is described below.",
        "Files tagged `conflicts` contain `# TODO:` markers at the conflict",
        "locations — search for those markers and resolve them.",
        "",
        f"| # | File | Outcome | Notes |",
        f"|---|------|---------|-------|",
    ]
    for idx, item in enumerate(items, 1):
        lines.append(
            f"| {idx} | `{item['rel_path']}` "
            f"| `{item['outcome']}` "
            f"| {item.get('detail','') or item.get('description','')} |"
        )

    lines += [
        "",
        "---",
        "",
        "## How to resolve each file",
        "",
    ]
    for idx, item in enumerate(items, 1):
        rel = item['rel_path']
        desc = item.get('description', '(no description)')
        outcome = item['outcome']
        detail  = item.get('detail', '')
        lines += [
            f"### {idx}. `{rel}`",
            "",
            f"**Intended HSLE change:** {desc}",
            "",
            f"**Outcome:** `{outcome}`  ",
            f"{'**Detail:** ' + detail if detail else ''}",
            "",
            "**Steps:**",
            f"1. Open the output file:  ",
            f"   `{report_dir}/{rel}`",
        ]
        if outcome in ('conflicts', 'conflict'):
            lines += [
                "2. Search for `# TODO: MANUAL MERGE CONFLICT` blocks.",
                "3. For each block, apply the HSLE change shown in the",
                "   `==== HSLE change` section while keeping the new-SLE",
                "   content from the `<<<< new_sle` section.",
                "4. Remove the TODO comment lines.",
                f"5. Reference: diff of ref_sle → ref_hsle:",
                f"   `diff {ref_sle}/{rel} {ref_hsle}/{rel}`",
            ]
        elif outcome in ('llm_error', 'llm_empty', 'too_large'):
            lines += [
                "2. LLM was unavailable; the file still needs HSLE changes.",
                f"3. Compare ref versions to understand what changed:",
                f"   `diff {ref_sle}/{rel} {ref_hsle}/{rel}`",
                "4. Apply the analogous changes to the output file.",
            ]
        elif outcome in ('missing_ref',):
            lines += [
                "2. The file was not found in one of the reference models.",
                "3. Check if the path changed and apply the change manually.",
            ]
        else:
            lines += [
                f"2. Detail: {detail or 'see conversion_report.md for context'}",
                f"3. Reference diff: `diff {ref_sle}/{rel} {ref_hsle}/{rel}`",
            ]
        lines.append("")

    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
if __name__ == '__main__':
    run()
