# 09-P124 0/60 geometry-family FDTD results

Stage: 09-P124 real FDTD compact summary for the P123 top-6 geometry-family candidates.

Scope: stage 09 only. These are single-dimer APCD candidates, not K=6 phase-ramp supercells, not steering results, and not a complete phase-state library claim.

Implementation evidence: non-rectangular APCD cores use polygon vertices through shape-aware `addpoly`, not rectangular aliases. Current missing bins are [0, 60].

| Candidate | Core shape | Phase (deg) | Nearest bin | Best current missing bin | Target | Leakage | Ratio | PD | Early | Near | Opens [0,60] | Useful anchor | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| cpk_060_geom_round_h420_r12_01 | rounded_rectangle | -135.0904 | -120 | 0 | 0.8919 | 0.3703 | 2.4084 | 0.4132 | False | False | False | False | fail_covered_bin |
| cpk_060_geom_ellipse_h420_01 | ellipse | 176.3725 | -180 | 60 | 0.9166 | 0.6869 | 1.3344 | 0.1433 | False | False | False | False | fail_covered_bin |
| cpk_060_geom_capsule_h420_01 | capsule | -162.1028 | -180 | 60 | 0.9097 | 0.0241 | 37.7278 | 0.9484 | True | False | False | False | early_pass_covered_bin |
| cpk_060_geom_chamfer_h425_c10_01 | chamfered_rectangle | -131.6039 | -120 | 0 | 0.8881 | 0.4510 | 1.9690 | 0.3264 | False | False | False | False | fail_covered_bin |
| cpk_060_geom_round_h430_r16_01 | rounded_rectangle | -127.4800 | -120 | 0 | 0.8919 | 0.4977 | 1.7920 | 0.2837 | False | False | False | False | fail_covered_bin |
| cpk_060_geom_ellipse_h425_scalar55_01 | ellipse_plus_scalar | -173.9952 | -180 | 60 | 0.9032 | 0.6133 | 1.4728 | 0.1912 | False | False | False | False | fail_covered_bin |

Result: no P124 candidate opens [0, 60] or qualifies as a useful 0/60 anchor. Capsule h420 is the strongest APCD-selective new-geometry point, but it reinforces the covered -180 bin.
