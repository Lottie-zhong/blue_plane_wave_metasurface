# APCD K=6 Helper Prototype FDTD Results v7 Summary

Scope: 09-P42/P44 physics-guided helper prototype batch. Only valid helper prototype YAML configs were run.

Geometry pass: 3/4
Dataset v7 rows: 33

| candidate | target | phase | leakage | ratio | early pass | target status | run status |
|---|---:|---:|---:|---:|---|---|---|
| `h2_square_load_01` | 0 | 115.7231380707874 | 0.040077604335282485 | 24.239301126374972 | True | usable_but_not_target | completed |
| `h2_nearsquare_load_02` | 0 | 120.7343925288726 | 0.04310696211211005 | 22.377148545287728 | True | usable_but_not_target | completed |
| `h2_weak_aniso_03` | -60 | 128.67545189753866 | 0.053721931132566875 | 17.923653091325708 | True | usable_but_not_target | completed |
| `h2_phase_delay_04` | -180 |  |  |  | False | not_run_geometry_failed | not_run_geometry_failed |

Coverage v7:

| bin deg | status |
|---:|---|
| 0.0 | evidence_only |
| 60.0 | early_covered |
| 120.0 | strong_covered |
| -180.0 | evidence_only |
| -120.0 | open_gap |
| -60.0 | open_gap |

No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, ML training, freeform helper, +15 deg steering claim, or complete K=6 library claim.
