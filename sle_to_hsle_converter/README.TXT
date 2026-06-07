================================================================================
  SLE -> HSLE CONVERTER AGENT  --  README
  Apply a reference SLE->HSLE model transition to any new SLE model
  Supports multiple projects (NVL-AX, NVL-S, and any future project)
================================================================================

WHAT THIS AGENT DOES
---------------------
Given:
  1. A project name (nvlax, nvls, ...) OR an explicit analysis .md file
  2. A new SLE emulation model directory (any version or variant)

The agent automatically converts the new SLE model to HSLE by applying the
same structural and content changes recorded in the reference transition analysis.

For each changed file in the analysis:
  - ADDED files    -> copied from the reference HSLE model into the output tree
  - REMOVED files  -> deleted from the output tree (with safety checks)
  - MODIFIED files -> merged using git 3-way merge (base=ref_sle, ours=new_sle,
                       theirs=ref_hsle); falls back to GitHub Copilot LLM on conflicts

Project structure:
  sle_to_hsle_converter/
  |-- convert.py               <- CLI entry point and 6-step pipeline
  |-- config.yaml              <- global settings + project registry
  |-- lib/
  |   |-- analysis_parser.py   <- parse analysis_heuristic.md -> ref paths + FileEntry list
  |   |-- model_builder.py     <- copytree, ADDED copy, REMOVED delete with conflict guard
  |   |-- merger.py            <- git merge-file 3-way merge + smart conflict resolver
  |   |-- llm_client.py        <- GitHub Copilot Chat API (diff-guided LLM merge)
  |   `-- reporter.py          <- conversion_report.txt + .md with confidence levels
  `-- .deps/                   <- local PyYAML install (auto-created on first run)


REGISTERED PROJECTS
--------------------
Run this to see all registered projects and their analysis/donor paths:

  python3 convert.py --list-projects

Current projects (defined in config.yaml):

  nvlax   NVL-AX SLE->HSLE hybridization
          Analysis: analysis_nvlax/analysis_heuristic.md  (212 entries)

  nvls    NVL-S SLE->HSLE hybridization (RTL Core PM / IA core stub)
          Analysis: analysis_nvls/analysis_heuristic.md   (66 entries)

To add a new project, add an entry under `projects:` in config.yaml.


HOW TO RUN
----------
Prerequisites:
  - Python 3.9+
  - git (for 3-way merge; detected automatically)
  - PyYAML (installed automatically into .deps/ on first run, or manually:
      python3 -m pip install pyyaml --target .deps/)
  - `gh` CLI authenticated -- only needed for --patch-mode llm or auto with conflicts:
      gh auth login

Step 1: Dry-run (always start here -- preview without writing anything):

  # Using project shorthand (recommended):
  python3 convert.py --project nvlax \
    --sle-model /path/to/new_sle_model \
    --output    /path/to/output_hsle

  # Using project shorthand for NVL-S:
  python3 convert.py --project nvls \
    --sle-model /path/to/new_sle_model \
    --output    /path/to/output_hsle

  # Explicit (backward-compatible -- works exactly as before):
  python3 convert.py \
    --sle-model /path/to/new_sle_model \
    --analysis  /path/to/analysis_heuristic.md \
    --output    /path/to/output_hsle

Step 2: Apply (when dry-run shows acceptable results):

  python3 convert.py --project nvlax \
    --sle-model /path/to/new_sle_model \
    --output    /path/to/output_hsle \
    --mode apply

All available flags:
  --project     nvlax | nvls | ...     Project shorthand (resolves --analysis + donor)
  --list-projects                      Show registered projects and exit
  --sle-model   /path/to/new_sle       (required) New SLE model to convert
  --analysis    /path/to/analysis.md   Override analysis path (or set when no --project)
  --output      /path/to/output_hsle   (required) Destination HSLE model path
  --config      config.yaml            Override config file (default: auto-discovered)
  --mode        dry-run | apply        Default: dry-run
  --patch-mode  3way | llm | auto      Default: from config (auto)
  --donor       /path/to/donor_hsle    Override donor HSLE model (default: from project)
  --force                              Remove existing output directory first
  --ref-sle     /override/path         Override SLE reference path from analysis header
  --ref-hsle    /override/path         Override HSLE reference path from analysis header

Project name aliases: dashes, underscores, and spaces are ignored during lookup.
  "nvl-ax", "nvl_ax", "NVL AX" -> all resolve to "nvlax"
  "nvl-s",  "nvl_s",  "NVL S"  -> all resolve to "nvls"


ARGUMENT PRECEDENCE
--------------------
When the same setting can come from multiple sources, the order is:

  CLI flag  >  project config (config.yaml)  >  global config  >  built-in default

Examples:
  --patch-mode 3way overrides config.yaml patch_mode: auto
  --donor /my/path  overrides the project's default donor
  --analysis /my.md overrides the analysis resolved from --project


ADDING A NEW PROJECT
---------------------
1. Create or obtain the SLE->HSLE reference analysis .md file for the new project.
   (Run the diff agent: compare the reference SLE and HSLE models manually or with AI.)

2. Add an entry to the `projects:` section of config.yaml:

   projects:
     myproject:
       description: "My Project SLE->HSLE"
       analysis: /path/to/my_project/analysis_heuristic.md
       donor: /path/to/my_project_donor_hsle     # optional
       output_group: soc                          # optional, overrides global

3. Verify registration:
   python3 convert.py --list-projects

4. Run a dry-run:
   python3 convert.py --project myproject \
     --sle-model /path/to/new_sle --output /path/to/out


UNDERSTANDING THE REPORT
------------------------
Each file gets a confidence label:

  Outcome            Confidence label             Action needed
  -----------------  ---------------------------  -------------------------
  applied            direct copy from ref HSLE    None
  applied_from_donor copied from donor model      None
  removed            deleted (matched ref SLE)    None
  merged_clean       clean 3-way merge            None (verify if critical)
  merged_smart       auto-resolved concurrent     None (verify if critical)
  llm_merged         LLM-assisted merge           Manual spot-check advised
  already_same       already up-to-date           None
  already_absent     already absent               None
  conflicts          CONFLICT -- manual review    Edit output file manually
  conflict           CONFLICT -- manual review    Check ADDED/REMOVED overlap
  missing_ref        MISSING in ref model         File may have moved/renamed
  binary             BINARY -- manual review      Copy or patch manually
  too_large          TOO LARGE for LLM            Merge manually (large file)
  llm_error          LLM ERROR -- manual review   Retry or merge manually


DONOR MODEL  (--donor)
-----------------------
A donor is an already-converted HSLE model from a previous project or earlier version.
It serves two purposes:

  1. Source for ADDED files (higher priority than ref_hsle):
     When the donor has an ADDED file, that file is copied from the donor instead
     of from the reference HSLE. The donor's version is typically more up-to-date.

  2. Context for LLM-assisted merges:
     The donor's version of MODIFIED files is included in the LLM prompt as
     additional reference, improving merge quality.

The project registry sets a default donor per project; use --donor to override.


PATCH-MODE STRATEGIES
-----------------------
  3way  (safest, no LLM)
    Uses git merge-file as a true 3-way merge.
    Clean -> writes result.  Conflicts -> flags for manual review.
    Smart concurrent-insertion conflicts are auto-resolved (keep both sides).

  llm   (no git required)
    Skips 3-way merge. Sends unified diff + new file content to Copilot LLM.
    Size limit: llm_max_chars / llm_max_lines (default 10 000 chars / 300 lines).

  auto  (default, recommended)
    Tries 3-way merge first. Falls back to LLM only if there are conflicts.
    Falls back to manual-review if LLM also fails.


QUICK-START EXAMPLES
---------------------
  # NVL-AX conversion (dry-run then apply):
  python3 convert.py --project nvlax \
    --sle-model /path/to/nvlax_sle --output /path/to/nvlax_hsle
  python3 convert.py --project nvlax \
    --sle-model /path/to/nvlax_sle --output /path/to/nvlax_hsle --mode apply

  # NVL-S conversion:
  python3 convert.py --project nvls \
    --sle-model /path/to/nvls_sle --output /path/to/nvls_hsle
  python3 convert.py --project nvls \
    --sle-model /path/to/nvls_sle --output /path/to/nvls_hsle --mode apply

  # With custom donor (override project default):
  python3 convert.py --project nvlax \
    --sle-model /path/to/sle --output /path/to/out \
    --donor /path/to/my_donor_hsle --mode apply

  # List all projects:
  python3 convert.py --list-projects

  # Force overwrite existing output:
  python3 convert.py --project nvls ... --mode apply --force

  # 3-way only (no LLM, no GitHub auth needed):
  python3 convert.py --project nvls ... --patch-mode 3way


RELATED FILES
--------------
  ../analysis_nvlax/analysis_heuristic.md  -- NVL-AX reference analysis (212 entries)
  ../analysis_nvls/analysis_heuristic.md   -- NVL-S reference analysis (66 entries)
  ../src_donor_models/                     -- Reference SLE and HSLE model snapshots

================================================================================
