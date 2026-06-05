# 09-P115 0/60 boundary-value FDTD results

Stage: 09-P115 real FDTD compact summary for the P114 sparse boundary map.

Scope: stage 09 only. These are single-dimer APCD candidates, not K=6 phase-ramp supercells, not steering results, and not a complete phase-state library claim.

Current missing bins are [0, 60]. The compact runner uses a historical missing-bin set that includes -60, so this report recomputes opens_missing_bin against [0, 60].

| Candidate | Phase (deg) | Nearest bin | Best current missing bin | Target | Leakage | Ratio | PD | Early | Near | Opens [0,60] | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| cpk_060_boundary_h435_aniso_reduce10_01 | -66.3341 | -60 | 0 | 0.8589 | 0.1384 | 6.2042 | 0.7224 | True | False | False | early_pass_existing_bin |
| cpk_060_boundary_h440_aniso_reduce10_01 | -63.0128 | -60 | 0 | 0.8608 | 0.1552 | 5.5453 | 0.6944 | False | True | False | near_pass_failure_boundary |
| cpk_060_boundary_h430_aniso_reduce15_01 | -64.1755 | -60 | 0 | 0.7736 | 0.4294 | 1.8016 | 0.2861 | False | False | False | failure_boundary |
| cpk_060_boundary_h435_aniso_reduce15_01 | -58.4635 | -60 | 0 | 0.7914 | 0.4692 | 1.6867 | 0.2556 | False | False | False | failure_boundary |
| cpk_060_boundary_h430_scale102_aniso_reduce10_01 | -61.4850 | -60 | 0 | 0.8493 | 0.3008 | 2.8234 | 0.4769 | False | False | False | failure_boundary |
| cpk_060_boundary_h430_scale103_aniso_reduce10_01 | -56.6557 | -60 | 0 | 0.8700 | 0.4192 | 2.0753 | 0.3497 | False | False | False | failure_boundary |
| cpk_060_boundary_h435_scale102_aniso_reduce10_01 | -54.9054 | -60 | 0 | 0.8692 | 0.3428 | 2.5357 | 0.4343 | False | False | False | failure_boundary |
| cpk_060_boundary_h430_scale104_aniso_reduce10_01 | -49.6312 | -60 | 0 | 0.8330 | 0.5287 | 1.5756 | 0.2235 | False | False | False | failure_boundary |

Result: no P115 candidate opens [0, 60]. The best selectivity-preserving boundary is cpk_060_boundary_h435_aniso_reduce10_01, which stays early-pass at phase -66.3341 deg but remains nearest -60.

Failure boundary: stronger anisotropy and scale values move phase toward less-negative values, but leakage rises above 0.2 or ratio falls below 6.
