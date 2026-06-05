# 09-P109 alt_htrans04 continuation results

Real FDTD was run remotely through the compact SSH runner for the four selected P108 candidates only. No raw results.csv, summary.md, .fsp, pre_run, .npy, or large outputs are included.

Pivot phase: -99.5115 deg from cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01.

| Candidate | Phase deg | Shift from pivot | Nearest bin | Target | Leakage | Ratio | Early pass | Useful trend | Opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| cpk_alt_htrans04_h425_01 | -93.7256 | 5.7859 | -120 | 0.9030 | 0.0421 | 21.4481 | True | False | False |
| cpk_alt_htrans04_h430_01 | -88.2507 | 11.2608 | -60 | 0.8841 | 0.0506 | 17.4799 | True | True | True |
| cpk_alt_htrans04_h420_aniso_reduce10_01 | -84.8650 | 14.6464 | -60 | 0.8270 | 0.0844 | 9.7978 | True | True | True |
| cpk_alt_htrans04_h420_square_helper50_01 | -115.0518 | 15.5404 | -120 | 0.9086 | 0.2523 | 3.6018 | False | False | False |

Key result: cpk_alt_htrans04_h430_01 opens the -60 missing bin with early-pass selectivity. cpk_alt_htrans04_h420_aniso_reduce10_01 independently opens -60 as well. The square 50x50 isotropic helper check fails leakage and ratio and should not be continued as a helper-shape route.

No stage 10, no K=6 phase-ramp supercell, and no steering claim is made.
