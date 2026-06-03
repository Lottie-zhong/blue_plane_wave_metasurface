# APCD K=6 Phase Gap Analysis v5

Scope: coverage update after 09-P29/P32 phase-lowering selected real FDTD. This is not a phase-ramp supercell or steering proof.

| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |
|---:|---|---:|---|---:|---|
| 0.0 | aggr_lhs_retention_dy_05 | 72.24132809604521 | next_zero_rot_anchor_03 | 20.788972844777305 | evidence_only |
| 60.0 | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 | early_covered |
| 120.0 | p1W_p5 | 1.9212487281864696 | pl_pi_wrap_04 | 43.39711779606267 | strong_covered |
| -180.0 | p1W_p5 | 61.92124872818647 | pl_pi_wrap_04 | 16.60288220393727 | evidence_only |
| -120.0 | p1W_p5 | 121.92124872818647 | pl_pi_wrap_04 | 76.60288220393733 | open_gap |
| -60.0 | aggr_lhs_retention_dy_05 | 132.2413280960452 | next_zero_rot_anchor_03 | 80.78897284477728 | open_gap |

A bin is not closed unless the candidate is both phase-near and early-pass. The K=6 phase-state library remains incomplete unless all six bins are usable.
