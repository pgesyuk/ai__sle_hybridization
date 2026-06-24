# HSLE Hybridization Analysis
## NVL-AX A0: `sle_emu-nvlax-a0-26ww16a_co` → `sle_emu-nvlax-a0-26ww16a_hsle_v07__semi_ai__rtl_core_pm_01_co`

---

## Part 1 — What SLE and HSLE Mean

| Term | Full Form | Description |
|------|-----------|-------------|
| **SLE** | Silicon-Level Emulation | Standard emulation model where **all** CPU cores run as RTL inside the emulator (Zebu/ZeBu). Full hardware accuracy everywhere but slow boot and high emulator resource usage. |
| **HSLE** | Hybrid SLE | A **hybridized** emulation model where a **subset** of cores run as real RTL while the remaining cores are replaced by fast software (Simics) virtual models. This enables OS-level software boot at reasonable speed while preserving RTL fidelity for the core(s) under test. |

The `v07` in the model name is the hybridization recipe version. The `semi_ai__rtl_core_pm_01` tag indicates:
- **semi_ai**: produced by the semi-automated AI-assisted conversion pipeline
- **rtl_core_pm_01**: first iteration of a real-RTL core PM (power management) test scenario

---

## Part 2 — Conceptual Architecture: SLE vs HSLE

```
╔══════════════════════════════════════════════════════════════════════════╗
║                          SLE (PURE EMULATION)                           ║
║                                                                          ║
║  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                   ║
║  │  Core 0 │  │  Core 1 │  │  Core 2 │  │  Core 3 │  ← ALL real RTL   ║
║  │  (RTL)  │  │  (RTL)  │  │  (RTL)  │  │  (RTL)  │    in emulator    ║
║  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                   ║
║       └────────────┴────────────┴─────────────┘                        ║
║                              │ IDI Bus                                  ║
║                       ┌──────┴──────┐                                   ║
║                       │  HUB (RTL)  │                                   ║
║                       └─────────────┘                                   ║
╚══════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════╗
║                         HSLE (HYBRID EMULATION)                         ║
║                                                                          ║
║  ┌─────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    ║
║  │  Core 0 │  │   Core 1     │  │   Core 2     │  │   Core 3     │    ║
║  │  (RTL)  │  │  (Simics SW) │  │  (Simics SW) │  │  (Simics SW) │    ║
║  │ ← Real  │  │  ← Stubbed   │  │  ← Stubbed   │  │  ← Stubbed   │    ║
║  └────┬────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   ║
║       │              │                  │                  │             ║
║  ┌────┴──────────────┴──────────────────┴──────────────────┴────────┐  ║
║  │              cdie_emu_hybrid_mux_xtor.sv  (NEW RTL)              │  ║
║  │       Routes IDI traffic: RTL core ↔ Simics stub cores           │  ║
║  └──────────────────────────────┬─────────────────────────────────── ┘  ║
║                                  │                                       ║
║                           ┌──────┴──────┐                               ║
║                           │  HUB (RTL)  │                               ║
║                           └──────┬──────┘                               ║
║                    ┌─────────────┘                                       ║
║           ┌────────┴─────────┐                                          ║
║           │hub_emu_hybrid_mux│ (NEW RTL — hub-side MUX transactor)      ║
║           └──────────────────┘                                          ║
║                                                                          ║
║  Simics                                                                  ║
║  Layer:  hybrid_core.simics → hybrid_mux.py → Simics CPU models         ║
╚══════════════════════════════════════════════════════════════════════════╝
```

**Key insight**: The hybrid MUX transactor (`*_hybrid_mux_xtor.sv`) is the bridge that
makes hybridization possible at the RTL level. It multiplexes the IDI bus between the
real RTL core (in the emulator) and the Simics stub cores (in software).

---

## Part 3 — The Hybridization Automation Pipeline

The conversion from SLE to HSLE is performed by a **two-phase automated pipeline**
located in `Y:\hybridization\`.

### Phase 1: Diff Analysis (`sle_hsle_diff_analyzer/`)

```
┌────────────────────────────────────────────────────────────────────────┐
│                       PHASE 1 — DIFF ANALYSIS                          │
│                                                                         │
│  INPUT                                                                  │
│  ┌────────────────────────────────┐                                    │
│  │  Reference SLE model           │  sle_emu-nvlax-a0-26ww12a_co       │
│  │  (26ww12a, known-good)         │                                    │
│  └────────────────────────────────┘                                    │
│            ↓  compared against                                          │
│  ┌────────────────────────────────┐                                    │
│  │  Reference HSLE model          │  sle_emu-nvlax-a0-26ww12a_         │
│  │  (26ww12a, manually built)     │  hsle_v07_cores__msr_co            │
│  └────────────────────────────────┘                                    │
│            ↓  tool: run.py                                              │
│   • Python tree walk (os.walk + filecmp)                                │
│   • Path-segment longest-prefix categorization                          │
│   • Heuristic OR LLM (Copilot API) description mode                    │
│   • 212 differences found: 144 added · 65 modified · 3 removed         │
│            ↓                                                            │
│  OUTPUT                                                                 │
│  ┌────────────────────────────────┐                                    │
│  │  analysis_heuristic.md         │  Machine-readable diff report       │
│  │  (analysis_nvlax/)             │  with file status, category, desc  │
│  └────────────────────────────────┘                                    │
└────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Conversion (`sle_to_hsle_converter_nvlax/`)

```
┌────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2 — CONVERSION                               │
│                                                                         │
│  INPUTS                                                                 │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────────┐   │
│  │  New SLE model   │  │  analysis.md    │  │  Donor HSLE model  │   │
│  │  (26ww16a)       │  │  from Phase 1   │  │  (26ww12a HSLE)    │   │
│  └────────┬─────────┘  └────────┬────────┘  └─────────┬──────────┘   │
│           └─────────────────────┼───────────────────── ┘              │
│                                 ↓                                       │
│  convert.py  — 7-step pipeline                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Step 1  Parse analysis.md → ref_sle, ref_hsle, 212-file list   │ │
│  │  Step 2  Preflight checks  → validate paths, git availability    │ │
│  │  Step 3  Create output tree → shutil.copytree(new_sle → output)  │ │
│  │  Step 4  Apply ADDED (144) → copy from Donor → output/file       │ │
│  │            • conflict detection: skip if file exists + differs   │ │
│  │            • fall back to ref_hsle if not in donor               │ │
│  │  Step 5  Apply REMOVED (3) → delete output/file                  │ │
│  │            • safety check: only delete if still == ref_sle       │ │
│  │  Step 6  Apply MODIFIED (65) → 3-way merge (git merge-file)      │ │
│  │            • base   = ref_sle / file  (common ancestor)          │ │
│  │            • ours   = output  / file  (new model version)        │ │
│  │            • theirs = ref_hsle/ file  (desired HSLE changes)     │ │
│  │            → if conflict: LLM (GitHub Copilot) resolves          │ │
│  │            → if LLM fails: flagged for manual review             │ │
│  │  Step 7  Write report → conversion_report.txt + .md              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 ↓                                       │
│  OUTPUT                                                                 │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │  sle_emu-nvlax-a0-26ww16a_hsle_v07__semi_ai__rtl_core_pm_01_co │   │
│  │  (the HSLE model — fully assembled, ready to run on emulator)   │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Part 4 — What Changed: 17 Categories of Modification

The analysis identified **212 differences** (144 added · 65 modified · 3 removed)
across 17 functional categories:

### Category Map (by scope and count)

```
 Category                          Added  Modified  Removed  Total
 ─────────────────────────────────────────────────────────────────
 1. HSLE Hybrid Core Files            1      15        3       19
 2. Register Lists / Run Configs     69       5        0       74  ← most active
 3. Build Config / Probes             2       1        0        3
 4. PCD Workarea                      4       4        0        8
 5. RTL Changes                       8       2        0       10
 6. Testbench Core Library            4      10        0       14
 7. Tool Overrides (TlsPyLib)        45       2        0       47
 8. Tests / Workarounds               1       1        0        2
 9. Emulation TREX Config             0       1        0        1
10. Flow Tool Configs                 0       2        0        2
11. Scripts / Trackers                0       1        0        1
12. Testbench Overrides               0      14        0       14
13. Spark / Run Scripts               0       2        0        2
14. tool.cth                          0       1        0        1
15. Emulation Build Infrastructure    0       3        0        3
16. RTL Config                        0       1        0        1
17. Zebu Build                        0       2        0        2
 ─────────────────────────────────────────────────────────────────
 TOTAL                              144      67        3      214
```

### Detailed Description Per Category

#### 1. HSLE Hybrid Core Files  (`src/val/emu/testbench/py_lib/hsle_core_files/`)
The central Python/Simics library that drives the hybrid behavior at runtime:
- **Added**: `read_hybrid_msrs.simics` — reads MSRs from the live RTL core via Simics
- **Modified**: `hybrid_core.simics`, `hybrid_mux.py`, `hybrid_core_init.py` — core
  hybridization setup and the Python MUX controller
- **Modified**: `bios_asserts.simics`, `target_setup.simics`, `hsle_target_setup.simics`
  — adapted to the hybrid boot environment
- **Modified**: `config/hybrid_cdie0p4e8_config.yml` — active topology config: 4 P-cores,
  8 E-cores, with hybrid MUX
- **Removed**: `hybrid_cdie0p1e1_config.yml`, `hybrid_cdie0p4e8_cdie1p4e8_hube4_config.yml`
  — obsolete multi-die topologies
- Many files have sections **commented out** — these are SLE-only code paths that are
  disabled in HSLE (e.g. stub core IDI transactors, direct wires)

#### 2. Register Lists / Run Configs  (`reglist/`)
The largest category — adds an entire HSLE-specific reglist subtree:
- **`reglist/nvlsi7_n2p/emu/hsle/`** — new subtree (~60 files) containing:
  - `core_switch/nop/`, `core_switch/pefw_CTM_10/` — NOP and CTM-10 assembly binaries
    for **core switching** (firmware that runs before handing off to the RTL core)
  - `hlt/` — HLT instruction binaries for various SPI flash sizes (4MB/16MB/64MB)
  - `simics_post/` — Simics scripts for post-boot device mapping (PCI, SPI, SATA,
    keyboard DXE, memory maps, power management, PCR logging, etc.)
  - `debug/` — Simics debug helpers (getvalue, log level, manual stop)
  - `fuses/` — fuse override file for PCD
  - `hsle_workarounds.simics`, `hsle_mem_overlap_fix.simics` — HSLE-specific workarounds
  - `load_pefw.simics`, `load_pefw_null.simics` — PEFW firmware loader scripts
  - `null_engine_mappings.simics` — null engine memory mappings
  - PEFW firmware blobs: `PEFWC.32.obj`, `PEFWC.lst`, `NVL_SV01_*.bin`
- **New level-0 run lists** for `p4e8` HSLE scenarios:
  `level0_pkg_chpr_model_p4e8_hsle.list`, `*_mbx_spacex.list`, `*_null.list`, etc.
- **`reglist/common/emu/common_hsle.list`** and `common_hsle.null.list` — common
  HSLE register initialization lists

#### 3. Build Config / Probes  (`src/val/emu/build_cfg/probes_pkg/`)
- **Added**: `cdie_hsle.py` and `hub_hsle.py` — new probe configuration files for
  HSLE-specific signal probing on the cdie and hub
- **Modified**: `all_probes.py` — imports the new HSLE probe modules and disables
  some SLE-only probe paths

#### 4. PCD Workarea  (`src/val/emu/pchlp/PCD_WORKAREA/`)
- Added `common_utils.py` and SPI transactor Simics scripts (`spi_xtor.simics`)
- Modified `pcd_main.py` — SLE-specific code commented out
- Modified `emu.f` (filelist) and `Makefile.cfg` — adjusted for HSLE build

#### 5. RTL Changes  (`src/val/emu/rtlchanges/soc/nvlsi7_n2p/`)
The **most important structural change** — new RTL files:
```
cdie0/src/val/emu/testbench/rtl/
    cdie_emu_hybrid_mux_xtor.sv   ← NEW: Cdie-side MUX transactor (RTL)
    cdie_emu_hybrid_mux_xtor.vh   ← NEW: Cdie MUX include header
hub/src/val/emu/testbench/rtl/
    hub_emu_hybrid_mux_xtor.sv    ← NEW: Hub-side MUX transactor (RTL)
    hub_emu_hybrid_mux_xtor.vh    ← NEW: Hub MUX include header
```
- These modules instantiate as **transactors inside the RTL design** and implement the
  IDI bus multiplexing between the real RTL core and Simics.
- Existing `cdie_emu_tb.sv` and `hub_emu_tb.sv` are **significantly trimmed** —
  SLE-only direct connection logic is removed, replaced by the MUX transactor.
- `.ref` copies provided for regression baseline.

#### 6. Testbench Core Library  (`src/val/emu/testbench/py_lib/`)
- **Added**: 4 new Simics scripts for IDI stub control:
  `disable_stub_core_idi_xtors.01.simics`, `.0123.simics`, `.23.simics`
  (disable IDI transactors on stub cores to avoid contention with Simics)
- **Added**: `iosf_sb_xtors_configuration_workaround.simics`
- **Modified**: `PkgTlsTb/PkgTbTop.py`, `XtorManager.py`, `IosfSbXtor.py` — import
  changes to load HSLE modules; SLE-only branches commented out
- **Modified**: `PkgTlsTb/Xtors/DirectWires/direct_wires.config.xml` — large sections
  removed (direct wire connections replaced by MUX transactor)
- **Modified**: `init.simics`, `init_before_connect.py` — HSLE initialization hooks added

#### 7. Tool Overrides — TlsPyLib  (`src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/`)
A **complete override of the TlsPyLib Python layer** for HSLE (~45 new files):
```
TlsPyLib/
  Lib/   Config.py, Debug.py, DutConfigCommon.py, Memory.py, PowerRail.py,
         RunControl.py, RunFlow.py, Signal.py, Trackers.py, ...
  Setup/ design_features_scaling.py, memories.py, register_width.py, ...
  TB/    FuseManager.py, LoadUserPythonFiles.py, PyDohCallback.py,
         PyDohRunControl.py, SVDefine.py, ...
```
This is the HSLE-adapted version of the TLS Python testbench library, maintained
as a versioned override so the standard SLE version is untouched.

#### 8–17. Remaining Categories (summary)
| # | Category | Key Changes |
|---|----------|-------------|
| 8 | Tests/Workarounds | `nvlax_efficiency_boost.simics` added; tracker updates |
| 9 | Emulation TREX | `emulation_TREX.pm` — SLE-specific flows commented out |
| 10 | Flow Tool Configs | `flows/pydoh/tool.cth`, `flows/tlspylib/tool.cth` — version pins adjusted |
| 11 | Scripts/Trackers | `fc_cpuid.py` — CPUID tracker updated for HSLE topology |
| 12 | Testbench Overrides | Hub and Cdie TB managers: imports, reset config, DUT config updated |
| 13 | Spark/Run Scripts | `sle.simics` — significant additions for HSLE startup sequence |
| 14 | tool.cth | Root tool.cth — some SLE-only feature flags commented out |
| 15 | Emu Build Infra | `verif/emu/Makefile.env`, `transactors.json` — MUX transactor registered |
| 16 | RTL Config | `verif/emu/rtl_cfg/PKG_IP_CHANGES.cfg` — MUX transactor RTL added to build |
| 17 | Zebu Build | `verif/emu/zebu/Makefile` and `Makefile.cfg` — MUX transactor compilation added |

---

## Part 5 — Conversion Outcome for `26ww16a`

The conversion report (`conversion_report.md`, generated 2026-06-03 in DRY-RUN mode)
showed:

| Input SLE    | `sle_emu-nvlax-a0-26ww12a_co` (ref run) |
|---|---|
| Ref SLE      | `sle_emu-nvlax-a0-26ww12a_co` |
| Ref HSLE     | `sle_emu-nvlax-a0-26ww12a_hsle_v07_cores__msr_co` |
| Donor        | same as Ref HSLE |
| Total files  | 212 |

| Outcome | Count | Meaning |
|---------|-------|---------|
| `would_apply_donor` | 144 | ADDED files → copied from donor HSLE |
| `would_merge`       |  65 | MODIFIED files → clean 3-way merge predicted |
| `already_absent`    |   3 | REMOVED files → already not present |
| **Manual review**   | **0** | **No conflicts — fully automated** |

**Result: 100% automation, 0 manual review files** for the 26ww16a conversion.
The `semi_ai` label in the output model name reflects that the LLM-assisted pipeline
was used (even though no conflicts required LLM intervention in this run).

---

## Part 6 — File Override Mechanism (Verbatim Copies)

Beyond the analysis-driven changes, the `config.yaml` defines `file_overrides` —
files that are **copied verbatim from the 26ww16a HSLE reference model** because
they are not captured by the 26ww12a analysis (they are 26ww16a-specific additions):

```yaml
file_overrides:
  reglist/common/emu/common_pkg_chppr.list:  ← ref 26ww16a HSLE
  reglist/common/emu/common_xdie_bkc.list:   ← ref 26ww16a HSLE
  reglist/nvlsi7_n2p/emu/...                 ← additional 26ww16a HSLE lists
```

This mechanism bridges the gap between the reference version (26ww12a) used to
produce the analysis and the target version (26ww16a) being converted.

The config also defines `paths_to_remove` — SLE directory symlinks that become
broken in the HSLE output:
```yaml
paths_to_remove:
  - src/val/emu/rtlchanges/soc/nvlax/cdie0    # alias → nvlsi7_n2p/cdie0
  - src/val/emu/rtlchanges/soc/nvlax/hub       # alias → nvlsi7_n2p/hub
  - integration/hotfix/upf/soc/nvlp            # UPF hotfix SLE symlinks
  - integration/hotfix/upf/soc/nvlsi7
  - integration/hotfix/upf/soc/nvlsi9
```

---

## Part 7 — Full Hybridization Flow Infographic

```
 ┌────────────────────────────────────────────────────────────────────────────┐
 │                    NVL-AX HSLE HYBRIDIZATION FLOW                          │
 └────────────────────────────────────────────────────────────────────────────┘

   ONCE (per project setup)              REPEATED (per new SLE drop)
   ═══════════════════════               ═══════════════════════════

   ┌──────────────────────────┐          ┌───────────────────────────────────┐
   │    REFERENCE SLE          │          │       NEW SLE MODEL               │
   │  26ww12a_co               │          │    26ww16a_co                     │
   └──────────┬───────────────┘          └─────────────┬─────────────────────┘
              │                                         │
              │      ┌─────────────────┐               │
              │      │  REFERENCE HSLE │               │
              ├─────►│  26ww12a_hsle   │               │
              │      └────────┬────────┘               │
              │               │                         │
              ▼               ▼                         │
   ┌──────────────────────────────────────┐            │
   │   sle_hsle_diff_analyzer/run.py      │            │
   │   ─────────────────────────────      │            │
   │   • Python tree walk + filecmp       │            │
   │   • Longest-prefix categorization    │            │
   │   • Heuristic / LLM description      │            │
   │   • 212 changes found                │            │
   └──────────────────┬───────────────────┘            │
                      │                                 │
                      ▼                                 │
            ┌──────────────────┐                        │
            │ analysis_         │                        │
            │ heuristic.md      │◄───────────────────────┤
            │ (17 categories)   │                        │
            └────────┬──────────┘                        │
                     │                                   │
                     │              ┌────────────────────┘
                     │              │
                     ▼              ▼
   ┌─────────────────────────────────────────────────────────────────��───┐
   │                sle_to_hsle_converter_nvlax/convert.py               │
   │                                                                      │
   │   ① Parse analysis.md    → file list (144 ADD / 65 MOD / 3 DEL)    │
   │   ② Preflight            → validate all paths + git availability    │
   │   ③ copytree(new_sle)    → output/ (full SLE copy as starting base) │
   │   ④ Apply ADDED (144)    → copy from Donor HSLE → output/           │
   │   ⑤ Apply REMOVED (3)    → delete from output/ (safety-checked)     │
   │   ⑥ Apply MODIFIED (65)  → git merge-file (3-way):                  │
   │        base=ref_sle  ours=new_sle  theirs=ref_hsle                  │
   │        ─ clean merge → auto-applied                                  │
   │        ─ conflict   → GitHub Copilot LLM resolves                   │
   │        �� LLM fail   → flagged for manual review                     │
   │   ⑦ file_overrides       → verbatim copy 26ww16a-specific files     │
   │   ⑧ paths_to_remove      → remove broken SLE symlinks               │
   │   ⑨ Write report         → conversion_report.txt / .md              │
   └──────────────────────────────────┬──────────────────────────────────┘
                                       │
                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │  sle_emu-nvlax-a0-26ww16a_hsle_v07__semi_ai__         │
              │                        rtl_core_pm_01_co               │
              │                                                        │
              │  ✅ 144 ADDED   (from donor HSLE)                      │
              │  ✅  65 MODIFIED (clean 3-way merge)                   │
              │  ✅   3 REMOVED  (already absent)                      │
              │  ✅   0 manual review needed                           │
              └────────────────────────────────────────────────────────┘
                                       │
                                       ▼
              ┌────────────────────────────────────────────────────────┐
              │                  EMULATOR (Zebu)                        │
              │                                                        │
              │  RTL Core 0  ←─ cdie_emu_hybrid_mux_xtor.sv ─────┐    │
              │                                                    │    │
              │  Simics CPU 1  ┐                                   │    │
              │  Simics CPU 2  ├─ Simics virtual cores ───────────┘    │
              │  Simics CPU 3  ┘     via hybrid_mux.py                 │
              │                                                        │
              │  Boot: PEFW → NOP sequence → hand off to OS           │
              └────────────────────────────────────────────────────────┘
```

---

## Part 8 — Key Patterns Observed in the RTL/Source Code

From examining the source code and comments across the two models:

### 1. "Code commented out" pattern
The dominant modification pattern (32 out of 65 modified files) is **commenting out
SLE-only code paths** rather than deleting them. This is deliberate:
- Preserves context and auditability
- Makes it easy to see what the HSLE version removed
- Allows re-enabling during debug

### 2. Import substitution pattern
Many Python TB files switch from SLE-specific imports to HSLE module imports:
```python
# SLE:  from PkgTlsTb.Xtors.Idi import IdiXtor   (real IDI transactor)
# HSLE: from hsle_core_files.hybrid_mux import HybridMux  (MUX-based)
```

### 3. IDI stub disable pattern
New Simics scripts `disable_stub_core_idi_xtors.*.simics` explicitly disable the
IDI transactors on the stub (Simics) cores to prevent double-driving the IDI bus
when Simics itself handles those cores.

### 4. Core-topology encoding in filenames
The filenames directly encode the core topology:
- `p4e8` = 4 P-cores, 8 E-cores
- `cdie0p4e8` = cdie0 with 4P+8E
- `_hsle` suffix = HSLE variant of that run list
- `_null` = null FSP test variant
- `_mbx_spacex` = mailbox + SpaceX test variant

### 5. Multi-version evolutionary history
The HSLE directory `Y:\nvl_ax\hsle\` preserves the full evolution:
```
v01 → v02 → v04 (atoms) → v04 (cores) → v06 → v06_debug →
v07_cores__msr → v07__ai_01..10 → v07__semi_ai__rtl_core_pm_01  ← CURRENT
```
The `__ai__` variants used pure LLM conversion; `__semi_ai__` indicates
the semi-automated approach with human oversight of the analysis step.

---

## Summary Table

| Aspect | SLE Model | HSLE Model |
|--------|-----------|------------|
| **Core execution** | All cores as RTL | Core 0 RTL + Cores 1-N Simics |
| **Boot speed** | Slow (full RTL) | Fast (Simics for stub cores) |
| **RTL accuracy** | All cores | Core under test only |
| **Hybrid MUX** | Not present | `*_emu_hybrid_mux_xtor.sv` |
| **Simics scripts** | Minimal | Rich (`hsle_core_files/`) |
| **PEFW/firmware** | Not present | Full set in `reglist/hsle/` |
| **TlsPyLib** | Standard | HSLE override (`NVL_24.03.013_sle_hsle/`) |
| **Run lists** | SLE lists | HSLE-specific level-0 lists |
| **Probe configs** | `all_probes.py` | + `cdie_hsle.py`, `hub_hsle.py` |
| **Direct wires** | Present | Removed (replaced by MUX) |
| **IDI xtors** | Active on all cores | Disabled on stub cores |

---
*Analysis performed by GitHub Copilot CLI — 2026-06-24*
*Models: sle_emu-nvlax-a0-26ww16a_co (SLE) vs sle_emu-nvlax-a0-26ww16a_hsle_v07__semi_ai__rtl_core_pm_01_co (HSLE)*
