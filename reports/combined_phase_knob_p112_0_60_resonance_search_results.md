# 09-P112 0/60 resonance search FDTD summary

Stage: 09-P112 real FDTD summary for the P111 top-4 core-preserving resonance search.

Scope: stage 09 only. These are single-dimer APCD candidates, not K=6 phase-ramp supercells, not steering results, and not a complete phase-state library claim.

Current target after P110: early-pass bins [-180, -120, -60, 120]; remaining missing bins [0, 60]. The runner prints compact metrics with its historical missing-bin set, so this report recomputes opens_missing_bin against the current P111 missing bins [0, 60].

| Candidate | Phase (deg) | Nearest bin | Best current missing bin | Target | Leakage | Ratio | PD | Early | Near | Opens [0,60] | Note |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| cpk_060_alt_htrans04_h440_01 | -79.6880 | -60 | 0 | 0.8956 | 0.0837 | 10.6943 | 0.8290 | True | False | False | early-pass but still already-covered -60 |
| cpk_060_alt_htrans04_h430_aniso_reduce10_01 | -72.5522 | -60 | 0 | 0.8649 | 0.1182 | 7.3176 | 0.7595 | True | False | False | useful +15.70 deg trend toward 0/60 |
| cpk_060_alt_htrans04_h430_scale104_01 | -62.8043 | -60 | 0 | 0.9489 | 0.2087 | 4.5479 | 0.6395 | False | True | False | closest phase, but leakage/ratio fail early-pass |
| cpk_060_wh03_h430_aniso_reduce10_01 | -89.4202 | -60 | 0 | 0.6724 | 0.0792 | 8.4851 | 0.7891 | True | False | False | alternative anchor remains near -60 boundary |

Result: no P112 candidate opens the current missing bins [0, 60]. The best useful trend is cpk_060_alt_htrans04_h430_aniso_reduce10_01 because it moves from -88.25 deg to -72.55 deg while preserving early-pass selectivity.

Do not claim steering or K=6 phase-ramp readiness from these data.
