"""
reporter.py — Write conversion_report.txt and .md after the conversion run.
"""

import os
from datetime import datetime
from typing import List

# Outcomes that require no human action
_AUTO_OUTCOMES = frozenset({
    'applied', 'applied_from_donor', 'removed',
    'merged_clean', 'merged_smart', 'merged_patch',
    'llm_merged', 'already_same', 'already_absent',
})
# Outcomes that are informational non-changes
_DRY_OUTCOMES = frozenset({
    'would_apply', 'would_apply_donor', 'would_remove',
    'would_merge', 'would_smart_merge', 'would_conflict', 'would_patch',
})
# Outcomes that require manual review
_MANUAL_OUTCOMES = frozenset({
    'conflict', 'conflicts', 'missing_ref', 'missing_current',
    'binary', 'error', 'git_unavailable', 'too_large',
    'llm_error', 'llm_empty', 'merged_patch_partial',
    'copied_from_donor',   # donor used as last-resort — needs project-specific review
})

# Confidence label per outcome
_CONFIDENCE = {
    'merged_clean':          'clean 3-way merge',
    'merged_smart':          'concurrent insertions auto-resolved',
    'merged_patch':          'patch-based merge (verify!)',
    'applied':               'copied from ref_hsle',
    'applied_from_donor':    'copied from donor model',
    'removed':               'deleted (matched ref SLE)',
    'llm_merged':            'LLM-assisted merge (verify!)',
    'already_same':          'already up-to-date',
    'already_absent':        'already absent',
    'would_merge':           'would merge cleanly',
    'would_smart_merge':     'would auto-resolve insertions',
    'would_patch':           'would apply patch',
    'would_apply':           'would copy from ref_hsle',
    'would_apply_donor':     'would copy from donor model',
    'would_remove':          'would delete',
    'would_conflict':        'would have conflicts',
    'merged_patch_partial':  'PARTIAL PATCH -- some hunks rejected',
    'copied_from_donor':     'DONOR COPY -- review project-specific adaptations',
    'conflicts':             'CONFLICT -- manual review',
    'conflict':              'CONFLICT -- manual review',
    'missing_ref':           'MISSING in ref model',
    'missing_current':       'MISSING in output',
    'binary':                'BINARY -- manual review',
    'too_large':             'TOO LARGE for LLM -- manual review',
    'llm_error':             'LLM ERROR -- manual review',
    'llm_empty':             'LLM empty -- manual review',
    'git_unavailable':       'git not found',
    'error':                 'ERROR',
}


def write_report(
    results: List[dict],
    output_dir: str,
    *,
    sle_model: str = '',
    ref_sle: str = '',
    ref_hsle: str = '',
    donor: str = '',
    dry_run: bool = False,
    name: str = 'conversion_report',
) -> None:
    """Write conversion_report.txt and conversion_report.md to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    manual  = [r for r in results if r['outcome'] in _MANUAL_OUTCOMES]
    auto    = [r for r in results if r['outcome'] in _AUTO_OUTCOMES]
    dry     = [r for r in results if r['outcome'] in _DRY_OUTCOMES]

    counts: dict = {}
    for r in results:
        counts[r['outcome']] = counts.get(r['outcome'], 0) + 1

    _write_txt(
        results, manual, auto, dry, counts,
        os.path.join(output_dir, f'{name}.txt'),
        sle_model=sle_model, ref_sle=ref_sle, ref_hsle=ref_hsle,
        donor=donor, dry_run=dry_run,
    )
    _write_md(
        results, manual, auto, dry, counts,
        os.path.join(output_dir, f'{name}.md'),
        sle_model=sle_model, ref_sle=ref_sle, ref_hsle=ref_hsle,
        donor=donor, dry_run=dry_run,
    )


# --------------------------------------------------------------------------- #
#  Plain-text report
# --------------------------------------------------------------------------- #

def _write_txt(results, manual, auto, dry, counts, path, **meta):
    with open(path, 'w', encoding='utf-8') as f:
        w = f.write

        w("=" * 72 + "\n")
        w("  HSLE CONVERSION REPORT\n")
        w(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        w(f"  Mode      : {'DRY-RUN' if meta['dry_run'] else 'APPLY'}\n")
        if meta.get('sle_model'):
            w(f"  Input SLE : {meta['sle_model']}\n")
        if meta.get('ref_sle'):
            w(f"  Ref SLE   : {meta['ref_sle']}\n")
        if meta.get('ref_hsle'):
            w(f"  Ref HSLE  : {meta['ref_hsle']}\n")
        if meta.get('donor'):
            w(f"  Donor     : {meta['donor']}\n")
        w("=" * 72 + "\n\n")

        w("SUMMARY\n")
        w("-" * 40 + "\n")
        for outcome in sorted(counts):
            label = _CONFIDENCE.get(outcome, outcome)
            w(f"  {label:<36} {counts[outcome]:>4}\n")
        w("\n")
        w(f"  Total files processed : {len(results)}\n")
        w(f"  Auto-applied          : {len(auto)}\n")
        if dry:
            w(f"  Would be applied      : {len(dry)}\n")
        w(f"  Need manual review    : {len(manual)}\n\n")

        if manual:
            w("FILES NEEDING MANUAL REVIEW\n")
            w("-" * 72 + "\n")
            for r in manual:
                w(f"\n  [{r['status']:<8}] {r['rel_path']}\n")
                w(f"    Outcome : {r['outcome']}\n")
                if r.get('detail'):
                    w(f"    Detail  : {r['detail']}\n")
                if r.get('description'):
                    w(f"    Context : {r['description']}\n")
            w("\n")

        w("FULL FILE LIST\n")
        w("-" * 72 + "\n")
        w(f"  {'ST':<8}  {'OUTCOME':<22}  {'CONFIDENCE':<30}  FILE\n")
        w(f"  {'-'*8}  {'-'*22}  {'-'*30}  {'-'*40}\n")
        for r in results:
            mark = '✓' if r['outcome'] in _AUTO_OUTCOMES else ('~' if r['outcome'] in _DRY_OUTCOMES else '!')
            conf = _CONFIDENCE.get(r['outcome'], r['outcome'])
            w(f"  {mark} {r['status']:<7}  {r['outcome']:<22}  {conf:<30}  {r['rel_path']}\n")

    print(f"  [reporter] Written: {path}")


# --------------------------------------------------------------------------- #
#  Markdown report
# --------------------------------------------------------------------------- #

def _write_md(results, manual, auto, dry, counts, path, **meta):
    with open(path, 'w', encoding='utf-8') as f:
        w = f.write

        mode_badge = '🔵 DRY-RUN' if meta['dry_run'] else '🟢 APPLIED'
        w(f"# HSLE Conversion Report\n\n")
        w(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  **Mode:** {mode_badge}\n\n")

        w("| | |\n|---|---|\n")
        if meta.get('sle_model'):
            w(f"| **Input SLE**  | `{meta['sle_model']}` |\n")
        if meta.get('ref_sle'):
            w(f"| **Ref SLE**    | `{meta['ref_sle']}` |\n")
        if meta.get('ref_hsle'):
            w(f"| **Ref HSLE**   | `{meta['ref_hsle']}` |\n")
        if meta.get('donor'):
            w(f"| **Donor**      | `{meta['donor']}` |\n")
        w(f"| **Total**      | {len(results)} files ({len(auto)} auto · {len(manual)} manual review) |\n\n")
        w("---\n\n")

        w("## Summary\n\n")
        w("| Outcome | Confidence | Count |\n|---------|-----------|-------|\n")
        for outcome in sorted(counts):
            label = _CONFIDENCE.get(outcome, outcome)
            w(f"| `{outcome}` | {label} | {counts[outcome]} |\n")
        w("\n")

        if manual:
            w("## ⚠️ Files Needing Manual Review\n\n")
            w("| Status | File | Reason | Context |\n|--------|------|--------|--------|\n")
            for r in manual:
                detail  = r.get('detail', '') or ''
                context = r.get('description', '') or ''
                w(f"| {r['status']} | `{r['rel_path']}` | {r['outcome']}: {detail} | {context} |\n")
            w("\n")

        w("## Full File List\n\n")
        w("| | Status | Outcome | Confidence | File |\n|--|--------|---------|-----------|------|\n")
        _STATUS_ICON = {'ADDED': '🟢', 'REMOVED': '🔴', 'MODIFIED': '🟡', 'SKIPPED': '⏭️'}
        for r in results:
            icon = '✅' if r['outcome'] in _AUTO_OUTCOMES else ('🔵' if r['outcome'] in _DRY_OUTCOMES else '⚠️')
            conf = _CONFIDENCE.get(r['outcome'], r['outcome'])
            st_icon = _STATUS_ICON.get(r['status'], r['status'])
            w(f"| {icon} | {st_icon} {r['status']} | `{r['outcome']}` | {conf} | `{r['rel_path']}` |\n")
        w("\n")

    print(f"  [reporter] Written: {path}")
