# 09-P100 resonance continuation results

Real FDTD was run remotely through the compact SSH runner for the four selected P99 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included.

Anchor phase: -159.0076 deg from cpk_resphase_anchor_wh03_h410_trim_m5_01.

| Candidate | Phase deg | Shift from anchor | Nearest bin | Best missing | Target | Leakage | Ratio | Early pass | Useful trend | Opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| cpk_rescont_h420_anchor_wh03_01 | -137.5023 | 21.5053 | -120 | -60 | 0.9063 | 0.0591 | 15.3323 | True | True | False |
| cpk_rescont_scale102_anchor_wh03_01 | -151.2116 | 7.7960 | -180 | -60 | 0.9220 | 0.0196 | 47.0578 | True | False | False |
| cpk_rescont_aniso_reduce5_anchor_wh03_01 | -148.3567 | 10.6508 | -120 | -60 | 0.9160 | 0.0114 | 80.5428 | True | False | False |
| cpk_rescont_ultraweak_helper35x85_anchor_wh03_01 | -171.2473 | 12.2398 | -180 | -60 | 0.9185 | 0.0138 | 66.6800 | True | False | False |

Key result: cpk_rescont_h420_anchor_wh03_01 is a useful trend candidate. It moved phase from -159.0076 deg to -137.5023 deg, a 21.5053 deg shift, while keeping target_conversion 0.9063, leakage 0.0591, and ratio 15.3323. It does not open a missing bin because it is nearest to the already-covered -120 bin.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
