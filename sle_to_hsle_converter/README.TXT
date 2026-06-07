================================================================================
  HSLE CONVERTER AGENT  —  README
  Apply a reference SLE→HSLE model transition to any new SLE model
================================================================================

WHAT THIS AGENT DOES
---------------------
Given:
  1. A new SLE emulation model directory (any version or variant)
  2. An analysis .md file describing the reference SLE→HSLE transition
     (produced by the Model Diff Agent in ../nvlax_hybridization_agent/)

The agent automatically converts the new SLE model to HSLE by applying the
same structural and content changes that were recorded in the reference
transition.

For each changed file in the analysis:
  - ADDED files   → copied from the reference HSLE model into the output tree
  - REMOVED files → deleted from the output tree (with safety checks)
  - MODIFIED files→ merged using git's 3-way merge (base=ref_sle, ours=new_sle,
                      theirs=ref_hsle); falls back to GitHub Copilot LLM on conflicts

The reference SLE and HSLE model paths are read directly from the .md file
header — no extra config needed for the common case.

Project structure:
  sle_to_hsle_converter/
  ├── convert.py               ← CLI entry point and 6-step pipeline
  ├── config.yaml              ← tunable settings (conflict policy, LLM limits, etc.)
  ├── lib/
  │   ├── analysis_parser.py   ← parse analysis.md → ref paths + FileEntry list
  │   ├── model_builder.py     ← copytree, ADDED copy, REMOVED delete with conflict guard
  │   ├── merger.py            ← git merge-file 3-way merge + dry-run simulation
  │   ├── llm_client.py        ← GitHub Copilot Chat API (diff-guided LLM merge)
  │   └── reporter.py          ← conversion_report.txt + .md with confidence levels
  └── .deps/                   ← local PyYAML install (auto-created on first run)

Safety features built in:
  - All relative paths validated (rejects absolute paths, directory traversal)
  - ADDED files: skipped if new model already has the path with different content
    (flagged for manual review rather than silently overwritten)
  - REMOVED files: only auto-deleted if content still matches ref_sle exactly
    (protects files that were legitimately updated in the new model)
  - 3-way merge: uses git merge-file --stdout — never corrupts the output file
    on partial apply
  - dry-run mode is the default — nothing is written until you say --mode apply


HOW TO RUN
----------
Prerequisites:
  - Python 3.9+
  - git (for 3-way merge; detected automatically)
  - PyYAML (installed automatically into .deps/ on first run, or manually:
      python3 -m pip install pyyaml --target .deps/)
  - `gh` CLI authenticated — only needed for --patch-mode llm or auto with conflicts:
      gh auth login

Step 1: Dry-run (always start here — preview changes without writing anything):
  python3 convert.py \
    --sle-model /path/to/new_sle_model \
    --analysis  /path/to/analysis.md \
    --output    /path/to/output_hsle \
    --mode      dry-run

  The dry-run:
    - Parses analysis.md and extracts reference model paths
    - Validates all paths exist
    - Simulates 3-way merges to preview clean vs conflict outcomes
    - Writes conversion_report.txt and .md (alongside output, not inside it)
    - Reports: N would auto-apply, M need manual review

Step 2: Apply (when dry-run shows acceptable results):
  python3 convert.py \
    --sle-model /path/to/new_sle_model \
    --analysis  /path/to/analysis.md \
    --output    /path/to/output_hsle \
    --mode      apply

  All available flags:
    --sle-model   /path/to/new_sle         (required) New SLE model to convert
    --analysis    /path/to/analysis.md     (required) Diff agent .md analysis file
    --output      /path/to/output_hsle     (required) Destination HSLE model path
    --config      config.yaml              (optional) Override default config settings
    --mode        dry-run | apply          Default: dry-run
    --patch-mode  3way | llm | auto        Default: auto
    --donor       /path/to/donor_hsle      (optional) Donor HSLE model — see below
    --force                                Remove existing output directory first
    --ref-sle     /override/path           Override SLE path from .md header
    --ref-hsle    /override/path           Override HSLE path from .md header

Examples:
  # Preview with LLM disabled (no GitHub auth needed):
  python3 convert.py \
    --sle-model /path/to/new_sle --analysis /path/to/analysis.md \
    --output /path/to/out --patch-mode 3way --mode dry-run

  # Apply with LLM fallback for conflicts:
  python3 convert.py \
    --sle-model /path/to/new_sle --analysis /path/to/analysis.md \
    --output /path/to/out --mode apply

  # Apply using a donor model from a previous project:
  python3 convert.py \
    --sle-model /path/to/new_sle --analysis /path/to/analysis.md \
    --output /path/to/out --mode apply \
    --donor /path/to/previous_hsle_model

  # Force overwrite of existing output:
  python3 convert.py ... --mode apply --force

Output files (written by both dry-run and apply):
  <output>/conversion_report.txt   ← plain-text report with confidence per file
  <output>/conversion_report.md    ← Markdown report with manual-review table


UNDERSTANDING THE REPORT
------------------------
Each file gets a confidence label:

  Outcome            Confidence label             Action needed
  -----------------  ---------------------------  -------------------------
  applied            direct copy from ref HSLE    None
  removed            deleted (matched ref SLE)    None
  merged_clean       clean 3-way merge            None (verify if critical)
  llm_merged         LLM-assisted merge (verify!) Manual spot-check advised
  already_same       already up-to-date           None
  already_absent     already absent               None
  conflicts          CONFLICT — manual review     Edit output file manually
  conflict           CONFLICT — manual review     Check ADDED/REMOVED overlap
  missing_ref        MISSING in ref model         File may have moved/renamed
  binary             BINARY — manual review       Copy or patch manually
  too_large          TOO LARGE for LLM            Merge manually (large file)
  llm_error          LLM ERROR — manual review    Retry or merge manually

The report summary section lists:
  - Auto-applied count
  - Files needing manual review (listed with file path + reason + description)
  - Full file list with outcome and confidence for every file


DONOR MODEL  (--donor)
---------------------
A donor is an already-converted HSLE model from a previous project or an earlier
version of the same project. It serves two purposes:

  1. Source for ADDED files  (higher priority than ref_hsle)
     When the donor has a file that the analysis marks as ADDED, that file is
     copied from the donor instead of from the reference HSLE model.

     Why this matters: the donor's version of hybridization files is typically
     more up-to-date than the original reference HSLE used to create the analysis.
     For example, if you previously converted NVLax-A0 (that HSLE model is your
     donor), its `hsle_core_files/` and `reglist/hsle/` files may be newer than
     the reference HSLE recorded in the analysis.md.

     Report outcomes when donor is used:
       applied_from_donor   — ADDED file was copied from the donor
       would_apply_donor    — dry-run: would copy from donor

     Fall-back: if a file is NOT in the donor, ref_hsle is used automatically.

  2. Context for LLM-assisted merges  (MODIFIED files only)
     When a MODIFIED file cannot be merged cleanly with 3-way merge AND the LLM
     fallback is used, the donor's version of that file is included in the LLM
     prompt as an additional reference:

       "Donor HSLE file (from a similar/previous project — for reference only):
        <donor file content>"

     This helps the LLM understand the real-world HSLE style for that file type,
     improving merge quality beyond what the diff alone provides.
     The donor content is capped at 6 000 chars in the prompt to avoid token bloat.

Use cases:
  - Same project, newer SLE version:
      donor = your last converted HSLE model (e.g. 26ww12 HSLE → converting 26ww15 SLE)
  - Different project, same IP family:
      donor = another project's HSLE model that shares the same hybridization scripts
  - Bootstrapping a new project:
      donor = the closest existing HSLE model from a related project

Example:
  python3 convert.py \
    --sle-model /path/to/nvlax_b0_sle \
    --analysis  /path/to/analysis_heuristic.md \
    --output    /path/to/nvlax_b0_hsle \
    --donor     /path/to/nvlax_a0_hsle \
    --mode      apply



---------------------
  3way  (safest, no LLM)
    Uses `git merge-file` as a true 3-way merge:
      base   = ref_sle/file   (common ancestor — what the reference SLE had)
      ours   = output/file    (what the new model has — we want to preserve this)
      theirs = ref_hsle/file  (changes to apply — what HSLE adds)
    If there are no conflicts → writes merged result.
    If there are conflicts   → flags for manual review.

  llm  (no git required)
    Skips 3-way merge entirely. Sends to Copilot:
      - A unified diff of ref_sle → ref_hsle (what changed in the reference)
      - The full new SLE file content
      - A description of the change (from analysis.md)
    LLM applies an analogous change to the new file.
    Size limit: llm_max_chars / llm_max_lines (default 10 000 chars / 300 lines).

  auto  (default, recommended)
    Tries 3-way merge first. Falls back to LLM only if there are conflicts.
    Falls back to manual-review if LLM also fails.


ADAPTING THE ANALYSIS.MD FORMAT
--------------------------------
The analysis.md must contain these lines in its header table for the agent to
find the reference model paths:

  | **SLE path**  | `/abs/path/to/reference_sle_model`  |
  | **HSLE path** | `/abs/path/to/reference_hsle_model` |

This format is written automatically by the diff agent (formatter.py).
If you produce the .md by hand, ensure these rows are present.

The file table rows must follow this format:
  | 🟢 Added    | `rel/path/to/file` | description |
  | 🟡 Modified | `rel/path/to/file` | description |
  | 🔴 Removed  | `rel/path/to/file` | description |

Status word (Added/Modified/Removed/Skipped) is matched case-insensitively.
Emoji variants are handled automatically.


CONFIG REFERENCE (config.yaml)
--------------------------------
  added_conflict_policy: manual | auto
    manual (default): flag ADDED files for review if path already exists in new model
    auto: overwrite if content differs from ref_hsle

  removed_safety_check: true | false
    true (default): only auto-delete REMOVED files if content matches ref_sle
    false: always delete regardless of content

  patch_mode: 3way | llm | auto
    See "Patch-mode strategies" section above.

  llm_max_chars: 10000
    Files larger than this (in characters) skip LLM and go to manual review.

  llm_max_lines: 300
    Files longer than this skip LLM and go to manual review.

  report_name: conversion_report
    Stem name for the output report files.


QUICK-START FOR A NEW PROJECT
-------------------------------
  1. Run the diff agent to compare your reference SLE and HSLE models:
       cd ../nvlax_hybridization_agent
       python3 run.py --config my_project_config.yaml --mode heuristic

  2. Take the analysis.md output to this converter and do a dry-run:
       python3 convert.py \
         --sle-model /path/to/new_sle_model \
         --analysis  /path/to/analysis.md \
         --output    /path/to/output_hsle \
         --mode      dry-run

  3. Review the conversion_report.txt. If the dry-run looks good, apply:
       python3 convert.py ... --mode apply

  4. Spot-check a few LLM-merged files (if any) before taping out.


CONTACT / ORIGIN
----------------
Created as part of the NVLax hybridization automation project.
Companion tool: ../nvlax_hybridization_agent/ (SLE/HSLE diff analyzer)
Reference analysis: ../analysis_nvlax/analysis.txt

================================================================================
