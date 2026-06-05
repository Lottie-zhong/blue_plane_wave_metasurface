# 09-P97 resphase_core_preserve FDTD results

Real FDTD was run remotely through the compact SSH runner for the four selected P96 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included.

| Candidate | Phase deg | Nearest bin | Best missing | Target | Leakage | Ratio | PD | Early pass | Opens missing bin | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| cpk_resphase_h380_nohelper_01 | -162.7079 | -180 | -60 | 0.9054 | 0.0469 | 19.3101 | 0.9015 | True | False | early_pass_existing_bin |
| cpk_resphase_scale104_nohelper_01 | -179.8120 | -180 | -60 | 0.9173 | 0.0900 | 10.1903 | 0.8213 | True | False | early_pass_existing_bin |
| cpk_resphase_anchor_wh03_h410_trim_m5_01 | -159.0076 | -180 | -60 | 0.9191 | 0.0088 | 104.8964 | 0.9811 | True | False | early_pass_existing_bin |
| cpk_resphase_60lock_counter_m40_h320_helper35x85_01 | 82.8349 | 60 | 60 | 0.7247 | 0.2953 | 2.4545 | 0.4210 | False | False | fail |

Key result: the core-preserving resonance route preserved APCD selectivity in three candidates, especially cpk_resphase_anchor_wh03_h410_trim_m5_01 with leakage 0.0088 and ratio 104.8964. However, those high-selectivity candidates all reinforced the already-covered -180 bin. The 60deg phase-lock recovery comparison landed nearest 60, but phase error to 60 is 22.8349 deg and leakage is 0.2953, so it is not a phase-hit success and does not open coverage.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
