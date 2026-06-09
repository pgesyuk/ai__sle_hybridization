# Model Transition Analysis: `SLE` → `HSLE`

**Generated:** 2026-06-02 23:39  |  **Description mode:** heuristic

| | |
|---|---|
| **SLE path** | `/nfs/site/disks/ive_nvl_efs_pgesyuk_001/hybridization/src_donor_models/sle_emu-nvlax-a0-26ww12a_co` |
| **HSLE path** | `/nfs/site/disks/ive_nvl_efs_pgesyuk_001/hybridization/src_donor_models/sle_emu-nvlax-a0-26ww12a_hsle_v07_cores__msr_co` |
| **Total differences** | 212 (144 added · 65 modified · 3 removed) |

---

## Table of Contents

1. [HSLE Hybrid Core Files](#1-hsle-hybrid-core-files)
2. [Register Lists / Run Configs](#2-register-lists-run-configs)
3. [Build Config / Probes](#3-build-config-probes)
4. [PCD Workarea](#4-pcd-workarea)
5. [RTL Changes](#5-rtl-changes)
6. [Testbench Core Library](#6-testbench-core-library)
7. [Tool Overrides](#7-tool-overrides)
8. [Tests / Workarounds](#8-tests-workarounds)
9. [Emulation TREX Config](#9-emulation-trex-config)
10. [Flow Tool Configs](#10-flow-tool-configs)
11. [Scripts / Trackers](#11-scripts-trackers)
12. [Testbench Overrides](#12-testbench-overrides)
13. [Spark / Run Scripts](#13-spark-run-scripts)
14. [tool.cth](#14-toolcth)
15. [Emulation Build Infrastructure](#15-emulation-build-infrastructure)
16. [RTL Config](#16-rtl-config)
17. [Zebu Build](#17-zebu-build)
18. [Key Themes](#key-themes-of-this-transition)

---

## 1. HSLE Hybrid Core Files

| Status | File | Description |
|--------|------|-------------|
| 🔴 Removed | `src/val/emu/testbench/py_lib/hsle_core_files/config/hybrid_cdie0p1e1_config.yml` | Testbench file removed |
| 🔴 Removed | `src/val/emu/testbench/py_lib/hsle_core_files/config/hybrid_cdie0p4e8_cdie1p4e8_hube4_config.yml` | Testbench file removed |
| 🔴 Removed | `src/val/emu/testbench/py_lib/hsle_core_files/config/hybrid_cdie0p4e8_hube4_config.yml` | Testbench file removed |
| 🟢 Added | `src/val/emu/testbench/py_lib/hsle_core_files/read_hybrid_msrs.simics` | New testbench file added |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/bios_asserts.simics` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/config/hybrid_cdie0p4e8_config.yml` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/debug.simics` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/debug_logs.simics` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hsle_target_setup.simics` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_core.simics` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_core_init.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_mux.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/hybrid_xtors_bypass_x86.py` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/mappings/hybrid_48.smart.switches.os-min.simics` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/remap_pci.py` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/hsle_core_files/target_setup.simics` | Code commented out |

## 2. Register Lists / Run Configs

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `reglist/common/emu/common_hsle.list` | New register list file added |
| 🟢 Added | `reglist/common/emu/common_hsle.null.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/efficiency_defaults.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/NVL_SV01_NNNN-XXXPCDP_CPRF_SEP0_0073001B_2024WW32.2.02.bin` | *[binary]* New binary register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/PEFWC.32.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/PEFWC.lst` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/bsp_rip.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/README.md` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/build.csh` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.16.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.16mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.32.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.64.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.64mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.asm` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.lst` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/nop_hlt.32.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/nop/obj2mem.pm` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/README.md` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/build.csh` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/hlt.16mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/hlt.64mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/hlt.asm` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/hlt.lst` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/nop_hlt.32.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/core_switch/pefw_CTM_10/obj2mem.pm` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/debug/getvalue.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/debug/log_level.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/debug/manual_stop.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/fuses/fuse_default_ovrd_pcd.txt` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hlt/hlt.32.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hlt/hlt.obj` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hlt/hlt.spi_xtor_16mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hlt/hlt.spi_xtor_4mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hlt/hlt.spi_xtor_64mb.mem` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hsle_mem_overlap_fix.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/hsle_workarounds.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/load_pefw.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/load_pefw_null.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/null/manual_stop.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/null/null_fsp_test_end.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/null_engine_mappings.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/null_engine_mappings_1.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/pre_setup.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/set_16bit_ids.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/assert_check_and_quit.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/cpuportin.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/debug.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/kbd_dxe_mapping.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/metric_efi.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/pci_sideband.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/pkgch_memory_map.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/pm_mapping.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/ppr_log_level.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/sata_mapping.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/single_core.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/spi_mapping.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/svos_key_map.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/svos_wa_2.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/simics_post/ts_attributes.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/start_trackers.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/test_hsle_fsp_bios_fail2pass.tcsh` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/hsle/vmxloading.simics` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle_mbx_spacex.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle_mbx_spacex_null.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle_memory_test.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle_null.list` | New register list file added |
| 🟢 Added | `reglist/nvlsi7_n2p/emu/level0_pkg_chpr_model_p4e8_hsle_trk.list` | New register list file added |
| 🟡 Modified | `reglist/common/emu/common_defaults.list` | Register list file updated |
| 🟡 Modified | `reglist/common/emu/common_defaults_zse.list` | Significant additions to register list file |
| 🟡 Modified | `reglist/nvlax/emu/doa_pkg_chp_p2e4_model_zse5.list` | Register list file updated |
| 🟡 Modified | `reglist/nvlsi7_n2p/emu/doa_pkg_chp_model_p2e4_fast_zse5.list` | Code commented out |
| 🟡 Modified | `reglist/nvlsi7_n2p/emu/test_doa.list` | Register list file updated |

## 3. Build Config / Probes

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/build_cfg/probes_pkg/cdie_hsle.py` | New probe config file added |
| 🟢 Added | `src/val/emu/build_cfg/probes_pkg/hub_hsle.py` | New probe config file added |
| 🟡 Modified | `src/val/emu/build_cfg/probes_pkg/all_probes.py` | Import changes; Code commented out |

## 4. PCD Workarea

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/common_py_files/common_utils.py` | New file added |
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/common_py_files/common_utils.py.ref` | New file added |
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/pcd_thc.simics` | New Simics script file added |
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/pcd_thc.simics.ref` | New Simics script file added |
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/spi_xtor.simics` | New transactor file added |
| 🟢 Added | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/spi_xtor.simics.ref` | New transactor file added |
| 🟡 Modified | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_run_dir/run_files/pcd_py_files/pcd_main.py` | Code commented out |
| 🟡 Modified | `src/val/emu/pchlp/PCD_WORKAREA/emu/pchlp/pcd_tb/f_files/emu.f` | Code commented out |
| 🟡 Modified | `src/val/emu/pchlp/PCD_WORKAREA/subsystems/dfx/filelists/val/rtl_opts.f` | Code commented out |
| 🟡 Modified | `src/val/emu/pchlp/PCD_WORKAREA/verif/emu/PCD_ZSE4_UPF/Makefile.cfg` | Code commented out |

## 5. RTL Changes

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/cdie0/src/val/emu/testbench/rtl/cdie_emu_hybrid_mux_xtor.sv` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/cdie0/src/val/emu/testbench/rtl/cdie_emu_hybrid_mux_xtor.sv.ref` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/cdie0/src/val/emu/testbench/rtl/cdie_emu_hybrid_mux_xtor.vh` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/cdie0/src/val/emu/testbench/rtl/cdie_emu_hybrid_mux_xtor.vh.ref` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/hub/src/val/emu/testbench/rtl/hub_emu_hybrid_mux_xtor.sv` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/hub/src/val/emu/testbench/rtl/hub_emu_hybrid_mux_xtor.sv.ref` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/hub/src/val/emu/testbench/rtl/hub_emu_hybrid_mux_xtor.vh` | New RTL file added |
| 🟢 Added | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/hub/src/val/emu/testbench/rtl/hub_emu_hybrid_mux_xtor.vh.ref` | New RTL file added |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/cdie0/src/val/emu/testbench/rtl/cdie_emu_tb.sv` | Significant removals from RTL file |
| 🟡 Modified | `src/val/emu/rtlchanges/soc/nvlsi7_n2p/hub/src/val/emu/testbench/rtl/hub_emu_tb.sv` | Rtl file updated |

## 6. Testbench Core Library

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/testbench/py_lib/disable_stub_core_idi_xtors.01.simics` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/py_lib/disable_stub_core_idi_xtors.0123.simics` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/py_lib/disable_stub_core_idi_xtors.23.simics` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/py_lib/iosf_sb_xtors_configuration_workaround.simics` | New testbench file added |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/PkgTbTop.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Reset/ResetConfig.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Reset/ResetManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Xtors/Clocking/Clocking.py` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Xtors/DirectWires/direct_wires.config.xml` | Significant removals from testbench file |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Xtors/IosfSb/IosfSbXtor.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/PkgTlsTb/Xtors/XtorManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib/disable_stub_core_idi_xtors.simics` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib/init.simics` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib/init_before_connect.py` | New function(s) added; Code commented out |

## 7. Tool Overrides

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/.complete` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/.crt.metadata` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/Makefile` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/README.md` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Callback.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Config.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/ConfigFile.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Debug.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/DutConfigCommon.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/ForceFile.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/GetTimeFromScope.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Logger.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/ManipLogger.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Memory.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/PowerRail.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/RunControl.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/RunFlow.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SigDump.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Signal.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SignalCollection.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibs.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/__init__.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/mock_cli.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/mock_conf.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/mock_simics.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/mock_simmod.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SimicsLibsMock/mock_yaml.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/SvaControl.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/Trackers.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/XtorSysMemory.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Lib/__init__.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/__init__.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/create_vcs_memory_links.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/design_features_scaling.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/load_obj.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/memories.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/Setup/register_width.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/CollagePaths.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/ConfigApplyInputFiles.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/FuseManager.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/ImportModulePrinter.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/LoadUserPythonFiles.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/LogScanner.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/PyDohCallback.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/PyDohLaunch.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/PyDohRunControl.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/PyDohSignal.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/PyDohSignalCollection.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/SVDefine.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/TimePrinter.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/TB/__init__.py` | New testbench file added |
| 🟢 Added | `src/val/emu/testbench/tool_overrides/tlspylib/NVL_24.03.013_sle_hsle/TlsPyLib/__init__.py` | New testbench file added |
| 🟡 Modified | `src/val/emu/testbench/tool_overrides/pydoh_nvl/25.02.001.pkg_patch_ax/Models/Cdie/CdieStubbedCoreResponse.py` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/tool_overrides/pydoh_nvl/25.02.001.pkg_patch_ax/Models/Pkg/PydohMain.py` | Code commented out |

## 8. Tests / Workarounds

| Status | File | Description |
|--------|------|-------------|
| 🟢 Added | `src/val/emu/tests/sle_workarounds/nvlax_efficiency_boost.simics` | New Simics script file added |
| 🟡 Modified | `src/val/emu/tests/sle_workarounds/sle_verify_trackers.py` | Tracker file updated |

## 9. Emulation TREX Config

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `cfg/trex/emulation_TREX.pm` | Code commented out |

## 10. Flow Tool Configs

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `flows/pydoh/tool.cth` | Code commented out |
| 🟡 Modified | `flows/tlspylib/tool.cth` | Code commented out |

## 11. Scripts / Trackers

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/scripts/fc_trackers/fc_cpuid.py` | Tracker file updated |

## 12. Testbench Overrides

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/Reset/ResetConfig.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/Reset/ResetManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/TB/TBManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/Xtors/Ddr/LpddrXtor.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/Xtors/SystemMemory/SystemMemory.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/HubTlsTb/Xtors/XtorManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/Reset/ResetConfig.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/Reset/ResetManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/TB/DutConfig.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/TB/TBManager.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/Xtors/EmuPowerMgmt/PowerRailBfm.py` | Import changes |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/Xtors/Idi/IdiXtor.py` | Code commented out |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_n2p/Cdie0TlsTb/Xtors/XtorManager.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_p1278/Cdie0TlsTb/TB/DutConfig.py` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/py_lib_overrides/cdie_p1278/Cdie0TlsTb/Xtors/EmuPowerMgmt/PowerRailBfm.py` | Import changes |

## 13. Spark / Run Scripts

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `src/val/emu/testbench/spark/args.yml` | Testbench file updated |
| 🟡 Modified | `src/val/emu/testbench/spark/sle.simics` | Significant additions to testbench file |

## 14. tool.cth

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `tool.cth` | Code commented out |

## 15. Emulation Build Infrastructure

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `verif/emu/Makefile.env` | Code commented out |
| 🟡 Modified | `verif/emu/tool.cth` | Code commented out |
| 🟡 Modified | `verif/emu/transactors.json` | file updated |

## 16. RTL Config

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `verif/emu/rtl_cfg/PKG_IP_CHANGES.cfg` | Significant additions to file |

## 17. Zebu Build

| Status | File | Description |
|--------|------|-------------|
| 🟡 Modified | `verif/emu/zebu/Makefile` | Significant additions to build config file |
| 🟡 Modified | `verif/emu/zebu/Makefile.cfg` | Significant additions to build config file |

---

## Key Themes of This Transition

| Theme | Description |
|-------|-------------|
| **Heavy changes in 'Register Lists / Run Configs'** | 75 files changed — the most active area in this transition |
| **Predominantly new files** | 144 new files vs 65 modifications — transition adds significant new capability |
| **Files removed** | 3 files removed from base model |
| **Hybrid MUX infrastructure** | New hybrid MUX transactor files introduced for HSLE connectivity |
| **HSLE-specific additions** | New HSLE-dedicated files added across multiple subsystems |
| **RTL testbench updates** | RTL testbench files modified or added |
| **Simics scripting updates** | Multiple Simics scripts added or updated |
| **New run lists** | New test/run list configurations added for HSLE scenarios |
| **Build infrastructure** | Build system and transactor configs updated |

---
*Generated by model-diff-agent — mode: heuristic*
