# Model Transition Analysis: `SLE` → `HSLE`

**Generated:** 2026-06-07 00:28:52  |  **Description mode:** heuristic

| | |
|---|---|
| **SLE path** | `/nfs/site/disks/ive_nvl_efs_pgesyuk_001/hybridization/src_donor_models/pkg-nvlpkg-a0-1p0-c.14d_h.14g_p.07_p.11_sle_hsle.8_s7z24_co` |
| **HSLE path** | `/nfs/site/disks/ive_nvl_efs_pgesyuk_001/hybridization/src_donor_models/pkg-nvlpkg-a0-1p0-c.14d_h.14g_p.07_p.11_sle_hsle.8_rtl_core_pm_co` |
| **Total differences** | 66 (10 added · 55 modified · 1 removed) |
| **Note** | Entries from §0 (RTL Core PM) are sourced from developer notes + `.ref` intra-model diffs; they are identical in both snapshots but capture the compile-time IA-core hybridization contract. Seven additional `par_pm`-internal signal paths (IOSF payload buses, IOSF GP packet creation, Fuse Puller FSM, C6Entry/C6Exit FSMs) are not yet represented in any donor-snapshot file — see §0 gap table. |

---

## Table of Contents
- [0. RTL Core PM / IA Core Hybridization (Compile-Time)](#0-rtl-core-pm-ia-core-hybridization-compile-time)
- [1. IOSF SB Transactors](#1-iosf-sb-transactors)
- [2. HSLE Register Lists](#2-hsle-register-lists)
- [3. HSLE Emulation Scripts](#3-hsle-emulation-scripts)
- [4. Testbench / TB Changes](#4-testbench-tb-changes)
- [5. Platform Config](#5-platform-config)
- [6. Offline DPI Trackers](#6-offline-dpi-trackers)
- [7. Integration / RTL Hotfixes](#7-integration-rtl-hotfixes)
- [8. RTL Core PM Runtime Changes](#8-rtl-core-pm-runtime-changes)
- [9. Key Themes](#9-key-themes)

---

## 0. RTL Core PM / IA Core Hybridization (Compile-Time)

> **Source:** Developer notes (rtl_core_pm feature). Files in this section are either:
> - **Captured via `.ref` pattern** — both snapshot models contain the same HSLE-modified file;
>   the `.ref` sibling inside the HSLE model stores the SLE (pre-HSLE) version and is the
>   authoritative "before" state for the converter.
> - **Not yet present in either snapshot** — files the developer has identified as required
>   additions when converting a clean SLE model; marked `*[developer-noted addition]*`.
>
> The converter must treat these files as part of the SLE→HSLE contract even when the
> snapshot-level `diff -rq` shows them as identical.

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/src/val/emu/testbench/rtl/cdie_emu_tb.sv` | **Core TB restructured for HSLE.** `.ref`→HSLE diff: adds `CDIE0_TB_ENABLE`/`CDIE1_TB_ENABLE` parameters; wraps `cdie0_emu_iosf_sb_xtor_ccp`, `cdie0_emu_idi_xtor_ccp`, `cdie0_emu_fuse_tb` and the cdie1 equivalents inside `generate if (CDIEХ_TB_ENABLE)` guards; removes the generic single-die `cdie_emu_idi_xtor_ccp`; adds `cdie_emu_hybrid_mux_xtor` instantiation (hybrid mux for IOSF SB steering); passes `.CDIE_ID(CDIE1_TB_ENABLE)` to `core_uri_connect` and `santa_uri_maker`; comments out `cdie_emu_pydoh_xtors` for fast PyDoh mode. |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/src/val/emu/testbench/rtl/cdie_pwr_jem_tracker.sv` | **D2D disabled + bind path fixed for HSLE.** `.ref`→HSLE diff: `CDIE_D2D_ENABLE` parameter changed from `1` → `0` (D2D traffic monitoring disabled in hybrid mode); bind path corrected from `` `EMU_CDIE.cdie_emu_tb `` to `` `CDIE.cdie_emu_tb `` so the power JEM tracker binds to the correct HSLE hierarchy. |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/src/val/emu/testbench/rtl/cdie_emu_tlms.sv` | **TLM bind stubs removed.** Removes `bind` statements targeting `par_mlc` and `icore` modules that are stubbed out in HSLE. *[developer-noted: not yet in snapshot — must be created/patched when converting a clean SLE model]* |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/src/val/emu/testbench/rtl/cdie_pwr_jem_cstate_tracker.sv` | **C-state tracker binds to stubbed logic removed.** Removes bind statements to `par_mlc` / `icore` instantiation points eliminated during IA core stubbing. *[developer-noted: not yet in snapshot]* |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/src/val/emu/rtlchanges/subip/hip/cdie_p1278_core/core/core_te/verif/tb/ti/core_top_ti.v` | **Remove binds to stubbed par_mlc / icore.** Test-interface file that had `bind` statements directly into `par_mlc` and `icore` submodule hierarchy; all such binds are removed since those modules are stubbed to empty shells in HSLE compile. *[developer-noted: not yet in snapshot]* |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/subip/hip/cdie_p1278_core/target/core/gen/tlm/rtl/txte_tlm_top/txte_tlm_top_collectors_binds.vs` | **TLM collector binds to stubbed modules removed.** `txte_tlm_top` collector bind file removes the `par_mlc` and `icore` bind entries, keeping only the `par_pm` and surviving subsystem collectors active. *[developer-noted: not yet in snapshot]* |
| 🟡 Modified | `verif/emu/rtl_cfg/global_emu_common_elab_opts.f` | **UPF error downgraded to warning for stubbed logic.** SLE had `-ignore initializer_driver_checks` (FA workaround for 24.03-1); HSLE drops that line, effectively exposing UPF initializer-driver warnings from the newly stubbed `par_mlc`/`icore` hierarchy rather than silencing them. |
| 🟡 Modified | `verif/emu/rtl_cfg/PKG_IP_CHANGES.cfg` | **RTL override manifest.** Already contains HSLE-aware entries for `cdie_emu_tb.sv`, `cdie_pwr_jem_tracker.sv`, `txte_tlm_top` bind files (cdie0 + cdie1 paths via `${DUT}` variable), and `+incdir` for TLM-top generated output. Identical in both snapshots because the manifest was aligned before branching; no further change needed when porting to a new SLE model that uses the same directory layout. |
| 🟡 Modified | `src/val/emu/build_cfg/probes_pkg/cdie_hsle.py` | **Hybrid-mux force/probe list for par_pm preservation.** Forces `hyb_sel`, `hyb_sel_idi`, `hyb_sel_iosf_sb` on each Big Core and Atom Core mux instance (`cdie_emu_hybrid_mux_xtor.cdieN_coreX_xtors_mux`). Forces `par_pm.gp_side_pok` and `par_pm.pm_side_pok` on each `sfc_bcslice0.par_bsX.coreX_wrap.coreX` path — this is the **key mechanism by which par_pm is kept alive while par_mlc/icore are stubbed**: forcing the PM side-pok signals keeps PM state-machine inputs valid without needing the real IA core hierarchy. Also monitors `CcfBlocked` at `par_santa.sbo_pma.ccfpmcs.pmc_pmu`. Identical in both snapshots. |
| 🟡 Modified | `src/val/emu/build_cfg/fwc/fwc_top.v` | **FWC top already includes par_pm and IOSF SB FWC modules.** References `pythonsv_iosf_sb_xtors_fwc.v` and all PM-related FWC sub-files. Identical in both snapshots — the par_pm FWC infrastructure was already in place; `par_pm_fwc.v` must be added alongside it (see ADDED entry below). |
| 🟡 Modified | `verif/emu/buildit/EmuGen.py` | **Gen-stage probe removal for par_mlc / icore.** Developer-noted as removing probe generation for stubbed modules. Identical in both snapshots — the relevant par_mlc/icore probe exclusions may not yet be committed to either branch. *[developer-noted: must be updated in clean SLE conversion]* |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7/cdie1/subip/hip/cdie_p1278_core/target/core/dft_insert/client_1278p6/core_client/rtl_out/core_client.v` | **Compile-time IA core stub.** RTL stub that replaces the real `cdie_p1278_core` compile: stubs out `par_mlc` (MLC cache) and `icore` (IA core execute pipeline) while preserving `par_pm` (power management) as a live RTL hierarchy. This is the **primary compile-time hybridization change** — with this stub the emulator compiles only PM logic, reducing compile time and enabling mixed-mode operation. *[developer-noted: not yet in snapshot — must be added when converting a clean SLE model]* |
| 🟢 Added | `src/val/emu/build_cfg/fwc/par_pm_fwc.v` | **FWC for par_pm signals.** Force-write collateral that drives the par_pm PM state-machine inputs (power-on, clock-gate, etc.) to their functional defaults when the real IA core driver logic (`par_mlc`/`icore`) is absent. Without this FWC, par_pm would stall waiting for inputs that the stubbed modules no longer drive. *[developer-noted: not yet in snapshot — must be created alongside core_client.v stub]* |

### §0 Gap Table — par_pm internal signal paths (developer-reviewed 2026-06-07)

> Seven specific `par_pm`-internal RTL paths were reviewed against all files in both donor
> snapshots. Paths 2 and 3 are **partially covered** by existing `cdie_pwr_jem_tracker.sv`
> monitoring. Paths 1, 4, 5, 6, and 7 are **absent** from every file in both snapshots
> and represent required work items when converting a clean SLE model to HSLE.

| # | Signal path (within `sfc_bcslice0.par_bsl.corel_wrap.corel`) | Developer label | Coverage in current snapshot | Required action |
|---|---|---|---|---|
| 1 | `par_pm.core_<pm/gp>_<m/t>payload[15:0]` | IOSF data buses | ❌ Not referenced anywhere | These 16-bit PM-side and GP-side IOSF payload buses are driven by `icore` in SLE; must be forced to valid values in `par_pm_fwc.v` when icore is stubbed, to prevent par_pm from stalling on undriven inputs |
| 2 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.pma_pmsb_crs.core_pma_pmsb_registers` | PM_HW register interface | ✅ Partially — `cdie_pwr_jem_tracker.sv` monitors `.nbl_voltage_threshold`, `.control_temp` (Acode Tjmax), and `core_pma_pmsb_regs.config_ctrl`, `.rcsm_phase_command`, etc. via `PWR_FLOW_EVENT` | Monitoring adequate for PM register state visibility; verify that register reset/init values are set correctly with par_mlc absent; no FWC forcing currently — add to `par_pm_fwc.v` if init depends on icore reset sequencing |
| 3 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.pma_iosf_pmsb` | PM_HW IOSF SB Packet Creation | ✅ Partially — `cdie_pwr_jem_tracker.sv` monitors `pma_iosf_pmsb.pmsb_pma_ep.side_rst_b` for each per-core IOSF PMSB endpoint | Reset deassertion monitored; packet-creation FSM state (idle/sending/done) not tracked — add FSM state probe to `cdie_pwr_jem_cstate_tracker.sv` for full SB packet visibility |
| 4 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.pma_iosf_gpsb` | PM_HW IOSF GP Packet Creation | ❌ Not referenced in any file in either snapshot | GP packet creation module entirely unmonitored; add `PWR_FLOW_EVENT` for `pma_iosf_gpsb` endpoint reset (parallel to path 3) in `cdie_pwr_jem_tracker.sv`; also add GP-bus input forcing in `par_pm_fwc.v` |
| 5 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.mlfps.ccp_fuse_puller` | FUSE PULLER FSM | ❌ Not referenced in any file in either snapshot | Fuse-pull FSM completely absent from all monitoring; add FSM state (idle/active/done) as `PWR_FLOW_EVENT` in `cdie_pwr_jem_cstate_tracker.sv`; also ensure fuse input signals are driven in `par_pm_fwc.v` so the puller FSM can complete |
| 6 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.pma_control.pma_rcsm.pma_rcsm_c6entry_fsm` | C6EntryFSM | ⚠️ Indirect only — `cdie_pwr_jem_tracker.sv` monitors `pma_control.pma_cmq_wrapper.pma_mmanager.ModuleInMC6X4H` (C6 occupancy flag) but not the entry FSM state machine itself | Add direct C6 entry FSM state monitoring to `cdie_pwr_jem_cstate_tracker.sv` (the developer-noted file that removes par_mlc/icore binds); pair with path 7 for complete C6 transition visibility |
| 7 | `par_pm.pm.mlbtrs.mlcabs.mlpmas.pma_control.pma_rcsm.pma_rcsm_c6exit_fsm` | C6ExitFSM | ❌ Not referenced anywhere | C6 exit FSM state entirely absent; add to `cdie_pwr_jem_cstate_tracker.sv` alongside path 6; both entry and exit FSM states are needed to verify C6 power-flow sequences in HSLE where icore no longer drives the associated handshakes |

---

## 1. IOSF SB Transactors

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Xtors/IosfSb/IosfSbXtor.py` | Switches the Simics-side IOSF SB device from `libiosf_sb_xtor.so` + adapter init to direct `libiosf_sb_simics.so`, keeping the named IOSF SB endpoints but removing the legacy cpp adapter hook. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/iosf_sb_xtors_configuration_workaround.simics` | Gates the legacy manual IOSF SB xtor creation behind `if ((cmd_line_opt->hsle) == FALSE)` and drops `cpp_tb_fn`; HSLE no longer instantiates the old per-core workaround xtors from this script. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_core_init.py` | Preserves sideband access through hybrid core plumbing: P2SB redirect regs move to `0x41200f90d0/d4/d8`, PCD SBREG monitoring switches to `mb.pcd.pci_mem` + `mb.pcd.p2sb0.bank.sbreg_bank`, and a Funny-I/O SAI callback is added. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/mappings/hybrid_null.smart.switches.os-min.simics` | Adds `nvl_mb_pcd_srm4_port_gpsbSOCPCHPRTID0xc3` and `...srm5...0xc4` with `-use-simics`, explicitly steering those GPSB ports into the Simics hybrid path. |
| 🟡 Modified | `verif/emu/transactors.json` | Retargets IOSF/HSLE runtime modules: keeps `iosf_sb_xtor` but points it at `spark-1.12.9.sem.timer.credit_init.credit_reinit`, adds `jem`/`null_engine`, and bumps `hybrid_core`, `hybrid_xtor_config`, and `transaction_shadower` used to carry SB traffic in HSLE. |

## 2. HSLE Register Lists

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `reglist/common/emu/common_pkg_chppr.list` | Updates the disabled `emu_cut_driver_clock.py` example from scale 60 to 80 (`##+defaults ... --scale 80 ...`), documenting newer CHPPR/ZSE timing collateral. |
| 🟡 Modified | `reglist/common/emu/common_xdie_bkc.list` | Points `BKC_ROOT` to the `...Rev1_nullChanges` collateral tree, aligning HSLE with the null-engine/HSLE xdie package. |
| 🟡 Modified | `reglist/common/emu/hsd_14022935859_credits.simics` | Keeps the credit workaround but converts waits from `bp.cycle.wait-for` to `emu.engine.wait-for-cycle -relative` for newer Simics CLI behavior. |
| 🟡 Modified | `reglist/nvlsi7/emu/hsle/debug/getvalue.simics` | Same debug flow, but all long delays are converted to `emu.engine.wait-for-cycle -relative`. |
| 🟡 Modified | `reglist/nvlsi7/emu/hsle/null/null_fsp_test_end.simics` | Simplifies FSP shell detection from `bp.console_string.wait-for ...` to direct `nvl.serconsole.con.wait-for-string "UEFI Interactive Shell"`. |
| 🟡 Modified | `reglist/nvlsi7/emu/hsle/warm_reset.simics` | Warm-reset delay switches to `emu.engine.wait-for-cycle -relative 10000`. |
| 🟡 Modified | `reglist/nvlsi7/emu/level0_pkg_chppr_model_p4e8_zse.list` | Uncomments `.include $WORKAREA/reglist/common/emu/nvlsi7_p4e8_reset_fetch_pegoste_zse.list`, so reset-fetch collateral is now active in the HSLE level0 list. |

## 3. HSLE Emulation Scripts

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/bios_asserts.simics` | Moves BIOS assert detection to `$uart.wait-for-string` and `emu.engine.wait-for-cycle`, keeping the same PEI/ASSERT checks with updated Simics commands. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/target_setup.simics` | Converts setup milestones to direct serial waits (`$uart.wait-for-string`, `$system.serconsole.con.wait-for-string`) instead of breakpoint console waits. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/testload.simics` | Uses `wait-for-hap X86_HLT_Instr` and newer cycle-wait syntax, but keeps the ACED/DEAD completion check on `cdie[x].ccp[0].module.core[0][0]`. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/init.simics` | Renames the CLI knob from `log_level` to `log-level`, recreates `emu.cfg.runtime_logger`, and swaps several legacy debug/list commands for current Simics equivalents. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/init_before_connect.py` | Re-enables `ctypes.CDLL("x11-support.so", mode=ctypes.RTLD_GLOBAL)` before connect. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/pcd_post_connect.simics` | Re-enables the Xtensa tracker load for non-null engines instead of leaving the whole block commented out. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/xdie_scripts/check_tcss_usb3_port0.simics` | USB3 port0 polling delays are migrated to `emu.engine.wait-for-cycle`. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/xdie_scripts/check_tcss_usb3_port1.simics` | USB3 port1 polling delays are migrated to `emu.engine.wait-for-cycle`. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/xdie_scripts/dis_fast_reset_mode.simics` | Fast-reset disable script now uses `emu.engine.wait-for-cycle 1000000`. |
| 🟡 Modified | `src/val/emu/testbench/py_lib/xdie_scripts/force_soc_dmi_normal.simics` | Updates the commented breakpoint syntax from `bp.wait-for-breakpoint` to `wait-for-breakpoint`. |
| 🟡 Modified | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.04.003_sle_hsle/TlsPyLib/Lib/XtorSysMemory.py` | Drops the obsolete second argument from `image.save_diff(filename_craff)`, matching the active Simics image API. |

## 4. Testbench / TB Changes

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `filelists/val/vip.list` | Refreshes VIP collateral: adds newer entries such as `IOSF_PVC`, `IOSF_SVC`, `axi_jem_tracker`, `bios_ipsd`, and `cbo_jem_tracker` while removing many Simics7/SLES15-era VIP aliases and local placeholders. |
| 🟡 Modified | `filelists/val/vip_config.list` | Applies the same VIP inventory cleanup in the config list, removing stale iosf/uvm/env aliases that were present in the SLE Simics7 bundle. |
| 🟡 Modified | `flows/pydoh/tool.cth` | Moves `pydoh_path` back from a private Simics7 modules tree to the standard `toolversion(pydoh)` lookup. |
| 🟡 Modified | `src/val/emu/build_cfg/probes_pkg/ProbesLib.py` | Probe generation no longer adds `-object_not_found warning`; missing probe objects stop generating warning-only noise. |
| 🟡 Modified | `src/val/emu/build_cfg/sle_dut.utf` | Replaces the commented delayed-trigger workaround with direct `ztopbuild -advanced_command {enable delayed_trigger}`. |
| 🟡 Modified | `src/val/emu/build_cfg/snps_recommended.utf` | Removes the temporary `Compile:DropSelfInvert=true` carry-over workaround block. |
| 🟡 Modified | `src/val/emu/build_cfg/vcserrs_emu.ctrl` | Removes the temporary `-xlrm module_xmr` FA workaround. |
| 🟡 Modified | `src/val/emu/scripts/sle_run_scripts/run_simregress.L0.chppr_zse5.csh` | Updates the two FSDB/TREX capture start timestamps, keeping the same regression flow with shifted debug windows. |
| 🟡 Modified | `src/val/emu/testbench/spark/args.yml` | Renames the spark argument key from `log_level` to `log-level`. |
| 🟡 Modified | `src/val/emu/testbench/spark/options.yml` | Switches the default spark host class from `SLES15` to `SLES12`. |
| 🟡 Modified | `src/val/emu/testbench/spark/sle.simics` | Drops the explicit `@import ...` preamble at the top of the script and relies on the active Simics runtime imports. |

## 5. Platform Config

Git history shows HSLE HEAD = `Platform Config XML updated`, but there is **no net SLE→HSLE tree delta** in the platform-config XML files checked here (`src/val/emu/tests/platfconfig/emu/nvlpkg_A0_p4e8_hsle.xml`, `src/val/emu/tests/platfconfig/emu/nvlpkg_A0_p4e8e4.xml`, and `src/val/emu/tests/platfconfig/nvlpkg_A0_p4e8e4.xml`).

Converter implication: no platform-config file entries are required for this model transition even though the branch history contains that commit.

## 6. Offline DPI Trackers

Git history shows HSLE commit `c4581ad35 Offline DPI Tracker enablement` added large tracker collateral on that branch, but the **net SLE→HSLE tree diff** retains only the visible footprints already captured above (notably refreshed VIP inventory plus `jem` presence in `verif/emu/transactors.json`).

There is no standalone `tracker_wrapper.py`/tracker-file row in the final inter-model diff, so converter action should focus on the surviving collateral references rather than replaying the whole commit.

## 7. Integration / RTL Hotfixes

| Status | File | Description |
|--------|------|-------------|
| 🔴 Removed | `verif/emu/; unset PROMPT_COMMAND` | Stray empty shell-artifact file removed; no model functionality is carried by this file. |
| 🟡 Modified | `verif/emu/Makefile.env` | Simplifies compile-time library setup by removing the explicit `BOOST_PATH` export and trimming `LD_LIBRARY_PATH`/spacing around `SIMICS_PROJECT`. |
| 🟡 Modified | `verif/emu/emuvcs/global_emuvcs_elab_opts.f` | Relaxes elaboration KDB selection from `-kdb=common_elab` to plain `-kdb`. |
| 🟡 Modified | `verif/emu/rtl_cfg/CDIE_IP_CHANGES.cfg` | Matches the KDB simplification in CDIE RTL config (`-kdb` instead of `-kdb=common_elab`). |
| 🟡 Modified | `verif/emu/rtl_cfg/gcd_common_elab_opts.f` | Matches the same KDB simplification in GCD elaboration options. |
| 🟡 Modified | `verif/emu/rtl_cfg/global_emu_common_elab_opts.f` | Removes the temporary `-ignore initializer_driver_checks` FA workaround block. |
| 🟡 Modified | `verif/emu/rtl_cfg/global_emuvcs_elab_opts.f` | Matches the same KDB simplification for global emuvcs elaboration. |
| 🟡 Modified | `verif/emu/rtl_cfg/global_sem_common_elab_opts.f` | Matches the same KDB simplification for SEM elaboration. |
| 🟡 Modified | `verif/emu/tool.cth` | Backs away from the SLE Simics7 tool stack: ZSE/VCS/Verdi versions change, `simics_path` moves off the private Simics7 tree, and the custom DVB override is removed. |
| 🟡 Modified | `verif/emu/zebu/Makefile.cfg` | Retargets the Zebu runtime from the Simics7 NVL-S bundle to the `installed_packages/2025ww16.5.00_24` stack, changes TB classes to `SLES12`, and trims Python/LD path setup. |

---

## 8. RTL Core PM Runtime Changes

> **Source:** Developer notes (rtl_core_pm runtime feature). All entries in this section are
> sourced from developer-provided paths. Files marked *[developer-noted]* do not yet exist in
> either donor snapshot and must be created; files marked *[via .ref diff]* are already in the
> HSLE snapshot with an intra-model `.ref` storing the SLE baseline.
>
> **Key mechanism:** A new command-line switch `-hsle_rtl_core_pm` guards all runtime paths
> that differ when IA cores are stubbed. Invoked via `+options -ms -hsle_rtl_core_pm -ms-` in
> the test list file. Python code checks this at runtime to skip icore/par_mlc workloads and
> activate PM-specific reset/boot sequences.

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_core_init.py` | **Guarded using `hsle_rtl_core_pm`.** Snapshot diff: `empty_components` → `component` for the hybrid hierarchy Simics class creation. Additionally: runtime paths that reference `par_mlc`/`icore` registers or state must be wrapped in `if cmd_line_opt.hsle_rtl_core_pm:` guards so they are skipped when IA cores are absent. *[developer-noted: guard wrappers not yet in either snapshot]* |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_mux.py` | **Guarded using `hsle_rtl_core_pm`.** Identical in both snapshots. Must be updated to skip any mux-setup paths that depend on `icore`/`par_mlc` being live; the `hsle_rtl_core_pm` flag gates those code paths at runtime. *[developer-noted: guard not yet in snapshot]* |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_p1278/Cdie0TlsTb/Reset/ResetCycle0.py` | **Remove par_mlc and icore references; EMU_MODEL_TARGET paths.** Via `.ref` diff: adds `import os`; adds `hdie_rpm_vip_config_yaml_path` using `EMU_MODEL_TARGET` env; guards `force_initial_tsc_value.run_tcm` with `cfg_hub_connected` check; switches hard-coded yaml path to `EMU_MODEL_TARGET/gen_stage/subip_collateral_for_pylib/hdie_rpm_vip_config.yaml`. Additionally: developer-noted `par_mlc`/`icore` signal references (e.g. `icore0`/`icore1` in `enabled_icore` loops for SCR patches, lock_pred, SMC filter, `par_mlc.mlc.mlcctls` paths) must be removed or guarded with `hsle_rtl_core_pm`. |
| 🟢 Added | `src/val/emu/testbench/py_lib_overrides/cdie_p1278/Cdie0TlsTb/Reset/ResetPhase3.py` | **New reset phase for cdie0 null-engine / HSLE mode.** Not in either snapshot; must be created parallel to `Cdie1TlsTb/Reset/ResetPhase3.py`. The Cdie1 `.ref` diff shows: updated to `Cdie1TlsTb` namespace imports; adds `SIM_log_info` calls to log "RESET PHASE3: Ucode Reset Completed!" and "RESET PHASE3: EbxAcedDone_check: ACED achieved!" milestones. Cdie0 version follows same pattern with `Cdie0TlsTb` namespace. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `src/val/emu/testbench/py_lib_overrides/cdie_p1278/Cdie0TlsTb/TB/TBManager.py` | **Icecode load bypass for null_engine (HSLE) mode.** Not in either snapshot; must be created parallel to `Cdie1TlsTb/TB/TBManager.py`. The Cdie1 `.ref` diff shows: adds `from TlsPyLib.Lib.SimicsLibs import conf`; inserts early-return guard `if conf.emu.engine.classname == "null_engine": return` to skip TB manager setup (including icecode firmware load) when running in Simics null-engine / HSLE mode. This is the "bypass icecode load" mechanism. *[developer-noted: not yet in snapshot]* |
| 🟡 Modified | `src/val/emu/testbench/spark/args.yml` | **Add `hsle_rtl_core_pm` switch.** Existing snapshot diff captures `log_level` → `log-level` rename. Additionally must add the new boolean switch: `hsle_rtl_core_pm: { default: false, type: 'b', help: 'Enable RTL Core PM HSLE mode (stubs par_mlc/icore)' }`. This provides the command-line knob consumed by `hybrid_core_init.py`, `hybrid_mux.py`, `ResetCycle0.py`, and the list file `+options` invocation. *[developer-noted: switch not yet in either snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_boot.simics` | **RTL Core PM boot sequence script.** New Simics debug script for boot flow when running with IA cores stubbed. Provides PM-specific boot milestones (ROM init, FW download, PM state machine ready) that replace the normal icore boot tracking. Invoked via `+options -ms -hsle_rtl_core_pm -ms-` in the test list file. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_CR.simics` | **RTL Core PM cold reset (CR) debug script.** HSLE-specific cold reset flow that routes PM state transitions through `par_pm` RTL monitors while icore reset handshakes are bypassed. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_S3.simics` | **RTL Core PM S3 suspend/resume debug script.** Handles the PM IOSF SB and GP sequences for S3 power state entry/exit without icore participation. Monitors `pma_rcsm` FSM transitions tracked in `cdie_pwr_jem_cstate_tracker.sv`. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_S4.simics` | **RTL Core PM S4 hibernate debug script.** S4 power state (hibernate) flow adapted for HSLE; par_pm FSM progresses through C6/C8 states without icore clock-gate handshakes. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_S5.simics` | **RTL Core PM S5 soft-off debug script.** S5 (soft power-off) PM flow for HSLE; icore shutdown handshakes bypassed; par_pm drives the IOSF GP/SB soft-off packet creation path. *[developer-noted: not yet in snapshot]* |
| 🟢 Added | `reglist/nvlsi7/emu/hsle/debug/rtl_core_pm_WR.simics` | **RTL Core PM warm reset debug script.** Warm reset flow for HSLE RTL Core PM mode; skips icore reset-fetch logic and relies on par_pm reset sequencer. Companion to `rtl_core_pm_CR.simics`. *[developer-noted: not yet in snapshot]* |

> **List file integration note:** the entry point for all RTL Core PM runtime changes is a
> `+options -ms -hsle_rtl_core_pm -ms-` line in the test list file (e.g.,
> `reglist/nvlsi7/emu/level0_pkg_chppr_model_p4e8_zse.list` or a project-specific list).
> The six `.simics` scripts above are sourced conditionally on that option flag. When porting to
> a new SLE model, this `+options` line and all six scripts must be added alongside `args.yml`
> and the guarded Python changes.

---

## 9. Key Themes

- **IA core hybridization — compile-time stub (§0 new entries):** the fundamental HSLE compile-time change is `core_client.v` — a stub that replaces `cdie_p1278_core` with an empty `par_mlc` / `icore` while keeping `par_pm` as live RTL. The consequence cascades into five supporting files: `cdie_emu_tlms.sv`, `cdie_pwr_jem_cstate_tracker.sv`, `core_top_ti.v`, and `txte_tlm_top_collectors_binds.vs` each remove `bind` statements that pointed into the now-absent hierarchy; `verif/emu/buildit/EmuGen.py` removes the gen-stage probe generation for those same modules.

- **par_pm preservation is explicit:** `cdie_hsle.py` forces `par_pm.gp_side_pok` and `par_pm.pm_side_pok` on every Big Core and Atom Core path (`sfc_bcslice0.par_bsX.coreX_wrap.coreX`). This keeps PM logic alive while the MLC/IA execute units are stubbed. `par_pm_fwc.v` provides the companion force-write collateral for PM state-machine inputs that are otherwise driven by the missing `par_mlc`/`icore`. **Five of seven par_pm-internal signal paths reviewed by the developer (IOSF payload buses, IOSF GP packet creation, Fuse Puller FSM, C6Entry FSM, C6Exit FSM) are not yet present in any donor-snapshot file** — see §0 gap table for per-path status and required actions.

- **Hybrid mux bridges IOSF SB from RTL to Simics:** `cdie_emu_tb.sv` instantiates `cdie_emu_hybrid_mux_xtor` — the per-core RTL mux that routes IOSF SB traffic either from the real Simics IA model (when core is not hybridized) or from the HSLE transactor path. `hyb_sel_iosf_sb` is forced in `cdie_hsle.py` for every hybridized core, directing SB traffic through the Simics path and away from the stubbed RTL endpoints.

- **IA core removal in this NVL-S diff:** the clearest behavioral change is that `src/val/emu/testbench/py_lib/iosf_sb_xtors_configuration_workaround.simics` now wraps the old manual xtor creation inside `if ((cmd_line_opt->hsle) == FALSE)`. In practice, HSLE stops using that legacy per-core/per-atom workaround path, so the removed IA-core-oriented hookup is the *manual workaround layer*, not the IOSF SB protocol itself.

- **How IOSF SB remains intact:** the replacement path is Simics/hybrid-core based, not RTL-endpoint based. `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_core_init.py` rewires sideband preservation through hybrid-core smart mapping: `mb.pcd.pci_mem`, `mb.pcd.p2sb0.bank.sbreg_bank`, redirect regs at `0x41200f90d0/d4/d8`, and a `sai_change_funny_io` callback. `verif/emu/transactors.json` also keeps the `iosf_sb_xtor` module active and updates the hybrid-core/transactor packages around it.

- **`reglist/common/emu/nvlsi7_p4e8_pythonsv_iosf_sb_xtors_zse.list`:** unchanged between SLE and HSLE. It still explicitly enables the die-specific xtors with `+options PCH_IOSF_SB_XTORS=1 PCD_IOSF_SB_XTORS=1 CDIE1_IOSF_SB_XTORS=1 HUBDIE_IOSF_SB_XTORS=1` and launches `-ms -py_d pysv_iosf_sb_xtors_test.py -ms-`. That means the validation intent for IOSF SB was preserved, not removed.

- **`reglist/common/emu/pysv_iosf_sb_xtors_test.py`:** also unchanged. It waits for each xtor to come out of reset and then uses `s.emu_execute_sbmsg_commands(...)` to write/read real sideband registers: e.g. PCD `mailbox1_interface=0xaced0`, PCH `mailbox1_interface=0xaced1`, CDIE `dmu_boot_config2=0x80EE00AB`, HUB `dmu_event_31=0xaced2`. This is strong evidence that IOSF SB functionality is intentionally preserved across the transition.

- **Integration hotfix IOSF SBC endpoints:** all `integration/hotfix/rtl/*/sip/*/subIP/iosf_sbc_ep/` directories are byte-for-byte identical between SLE and HSLE. IOSF SB preservation is **not** coming from RTL endpoint edits; it is preserved above RTL by keeping the collateral/tests and changing the hybrid-core/transactor hookup.

- **Files not yet in either snapshot (developer-noted):** Compile-time: `core_client.v`, `par_pm_fwc.v`, `cdie_emu_tlms.sv`, `cdie_pwr_jem_cstate_tracker.sv`, `core_top_ti.v`, `txte_tlm_top_collectors_binds.vs`, `EmuGen.py` probe-exclusion changes. Runtime: `ResetPhase3.py` (Cdie0), `TBManager.py` (Cdie0), 6 × `rtl_core_pm_*.simics` scripts, `hsle_rtl_core_pm` switch in `args.yml`, `+options -ms -hsle_rtl_core_pm -ms-` in list file, guard wrappers in `hybrid_core_init.py` and `hybrid_mux.py`. None of these can be auto-applied from the current donor snapshot; they require manual creation guided by §0 and §8 of this analysis. See §0 gap table for 5 par_pm internal signal paths that additionally need to go into `par_pm_fwc.v` and `cdie_pwr_jem_cstate_tracker.sv`.
