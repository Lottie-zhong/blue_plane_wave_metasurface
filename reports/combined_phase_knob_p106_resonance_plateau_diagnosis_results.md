# 09-P106 resonance plateau diagnosis results

Real FDTD was run remotely through the compact SSH runner for the four selected P105 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included.

Plateau reference phase: -126.6809 deg from cpk_rescont_h420_aniso_reduce5_01.

| Candidate | Phase deg | Shift from ref | Nearest bin | Best missing | Target | Leakage | Ratio | Early pass | Near pass | Useful trend | Opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| cpk_resplateau_h434_boundary_01 | -124.4571 | 2.2238 | -120 | -60 | 0.9066 | 0.1897 | 4.7792 | False | True | False | False |
| cpk_resplateau_h420_aniso_reduce10_01 | -114.0119 | 12.6690 | -120 | -60 | 0.9069 | 0.1402 | 6.4668 | True | False | False | False |
| cpk_resplateau_h425_scale102_aniso_reduce5_01 | -112.8443 | 13.8365 | -120 | -60 | 0.9128 | 0.1937 | 4.7121 | False | True | False | False |
| cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01 | -99.5115 | 27.1694 | -120 | -60 | 0.9079 | 0.0380 | 23.8942 | True | False | True | False |

Key result: the h420/h430 branch remains a -120 plateau. h434 and h425 combined trims stay nearest -120 but lose early-pass ratio. cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01 is the best pivot candidate: phase -99.5115 deg, target_conversion 0.9079, leakage 0.0380, ratio 23.8942. It is a useful early-pass trend but still nearest -120 and does not open a missing bin.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
