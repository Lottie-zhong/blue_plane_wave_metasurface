# APCD K=6 Phase Gap Analysis v7

Scope: helper prototype v7 update. Only completed valid prototype FDTD rows were added to dataset v7.

| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |
|---:|---|---|---:|---|---:|
| 0.0 | evidence_only | aggr_lhs_retention_dy_05 | 72.24132809604521 | next_zero_rot_anchor_03 | 20.788972844777305 |
| 60.0 | early_covered | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 |
| 120.0 | strong_covered | h2_nearsquare_load_02 | 0.7343925288726041 | pl_pi_wrap_04 | 43.39711779606267 |
| -180.0 | evidence_only | h2_weak_aniso_03 | 51.324548102461335 | pl_pi_wrap_04 | 16.60288220393727 |
| -120.0 | open_gap | h2_weak_aniso_03 | 111.32454810246134 | pl_pi_wrap_04 | 76.60288220393733 |
| -60.0 | open_gap | aggr_lhs_retention_dy_05 | 132.2413280960452 | next_zero_rot_anchor_03 | 80.78897284477728 |

Prototype result statuses:
- `h2_square_load_01`: run_status=completed, phase=115.7231380707874, leakage=0.040077604335282485, ratio=24.239301126374972, target_bin_status=usable_but_not_target
- `h2_nearsquare_load_02`: run_status=completed, phase=120.7343925288726, leakage=0.04310696211211005, ratio=22.377148545287728, target_bin_status=usable_but_not_target
- `h2_weak_aniso_03`: run_status=completed, phase=128.67545189753866, leakage=0.053721931132566875, ratio=17.923653091325708, target_bin_status=usable_but_not_target
- `h2_phase_delay_04`: run_status=not_run_geometry_failed, phase=, leakage=, ratio=, target_bin_status=not_run_geometry_failed

Do not claim a complete K=6 phase-state library or +15 deg steering from these prototype results.
