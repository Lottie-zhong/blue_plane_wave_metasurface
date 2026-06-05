# 09-P103 h420 resonance continuation results

Real FDTD was run remotely through the compact SSH runner for the four selected P102 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included.

Anchor phase: -137.5023 deg from cpk_rescont_h420_anchor_wh03_01.

| Candidate | Phase deg | Shift from h420 | Nearest bin | Best missing | Target | Leakage | Ratio | Early pass | Useful trend | Opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| cpk_rescont_h425_h420anchor_01 | -132.8836 | 4.6187 | -120 | -60 | 0.9069 | 0.0983 | 9.2287 | True | False | False |
| cpk_rescont_h430_h420anchor_01 | -128.1467 | 9.3556 | -120 | -60 | 0.9077 | 0.1474 | 6.1561 | True | False | False |
| cpk_rescont_h420_scale102_01 | -129.7586 | 7.7437 | -120 | -60 | 0.9073 | 0.1103 | 8.2233 | True | False | False |
| cpk_rescont_h420_aniso_reduce5_01 | -126.6809 | 10.8214 | -120 | -60 | 0.9133 | 0.1147 | 7.9642 | True | False | False |

Key result: all four P103 candidates remain early-pass, confirming APCD selectivity survives h425/h430 and h420 size/anisotropy trims. However, all remain nearest to the already-covered -120 bin. No candidate meets the useful-trend threshold of more than 15 deg shift from -137.5 while early-pass, and no missing bin opens.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
