# 09-P116 0/60 boundary diagnostic

Reference anchor: cpk_060_alt_htrans04_h430_aniso_reduce10_01 from P112, phase -72.5522 deg, target 0.8649, leakage 0.1182, ratio 7.3176.

| Candidate | Phase delta from P111 best (deg) | Leakage delta | Ratio delta | Boundary class | Interpretation |
|---|---:|---:|---:|---|---|
| cpk_060_boundary_h435_aniso_reduce10_01 | 6.2181 | 0.0202 | -1.1134 | early_pass_existing_bin | early-pass but still nearest already-covered -60 |
| cpk_060_boundary_h440_aniso_reduce10_01 | 9.5394 | 0.0370 | -1.7723 | near_pass_failure_boundary | near-pass boundary; selectivity below early-pass threshold |
| cpk_060_boundary_h430_aniso_reduce15_01 | 8.3767 | 0.3112 | -5.5160 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |
| cpk_060_boundary_h435_aniso_reduce15_01 | 14.0888 | 0.3510 | -5.6310 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |
| cpk_060_boundary_h430_scale102_aniso_reduce10_01 | 11.0672 | 0.1826 | -4.4942 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |
| cpk_060_boundary_h430_scale103_aniso_reduce10_01 | 15.8966 | 0.3010 | -5.2423 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |
| cpk_060_boundary_h435_scale102_aniso_reduce10_01 | 17.6469 | 0.2246 | -4.7819 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |
| cpk_060_boundary_h430_scale104_aniso_reduce10_01 | 22.9211 | 0.4105 | -5.7420 | failure_boundary | failure boundary; phase moved but leakage or ratio failed |

Diagnostic conclusion: the alt_htrans04 boundary can push phase toward 0/60, but the selectivity boundary is encountered before the nearest bin changes to 0 or 60 with early-pass quality. Do not continue stronger scale or stronger anisotropy trims.
