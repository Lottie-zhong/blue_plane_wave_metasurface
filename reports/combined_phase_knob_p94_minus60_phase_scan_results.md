# 09-P94 minus60 phase scan results

Real FDTD was run remotely through the compact SSH runner for the six selected P93 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included here.

Definitions used in this report:

- phase_hit: nearest_target_bin_deg is -60.
- useful_hit: phase_hit plus target_conversion >= 0.5 and opposite_spin_leakage <= 0.3.
- early_pass: compact runner early_pass value.

| Candidate | Phase deg | Nearest bin | Target | Leakage | Ratio | PD | Success level | Opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---|---|
| cpk_m60scan_common_m80_01 | -64.3615 | -60 | 0.4740 | 0.6738 | 0.7035 | -0.1740 | phase_hit | False |
| cpk_m60scan_common_m90_01 | -74.1214 | -60 | 0.4401 | 0.6335 | 0.6946 | -0.1802 | phase_hit | False |
| cpk_m60scan_common_m100_01 | -100.6608 | -120 | 0.5007 | 0.6350 | 0.7885 | -0.1182 | no_phase_hit | False |
| cpk_m60scan_relcomp_m80_diff35_01 | -62.9408 | -60 | 0.5524 | 0.5976 | 0.9244 | -0.0393 | phase_hit | False |
| cpk_m60scan_p2geom_m85_90x145_01 | -67.2011 | -60 | 0.3883 | 0.7091 | 0.5477 | -0.2922 | phase_hit | False |
| cpk_m60scan_helper_suppress_m85_40x90_01 | -73.4798 | -60 | 0.4632 | 0.5748 | 0.8059 | -0.1075 | phase_hit | False |

Key result: the controlled scan located a -60 phase branch. Five of six candidates landed nearest to -60, and cpk_m60scan_relcomp_m80_diff35_01 is the best phase-hit tradeoff with phase -62.9408 deg and target_conversion 0.5524. Leakage remains 0.5976, so there is no useful-hit and no early-pass opening yet.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
