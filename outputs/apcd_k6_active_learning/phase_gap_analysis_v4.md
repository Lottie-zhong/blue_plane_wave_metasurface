# APCD K=6 Phase Gap Analysis v4

Scope: 09-P27 phase coverage update only. No FDTD was run in this stage. No phase-ramp supercell was built.

60 deg bin status: `early_covered`.
120 deg bin status: `strong_covered`.
0 deg bin status: `evidence_only`.
-60 deg bin status: `open_gap`.
-120 deg bin status: `open_gap`.
-180 deg bin status: `open_gap`.

`focus_neg60_geom_04` is a high-quality positive-phase candidate, not a -60 deg phase-state candidate.

| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |
|---:|---|---:|---|---:|---|
| 0.0 | aggr_lhs_retention_dy_05 | 72.24132809604521 | next_zero_rot_anchor_03 | 20.788972844777305 | evidence_only |
| 60.0 | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 | early_covered |
| 120.0 | p1W_p5 | 1.9212487281864696 | doe_lhs_like_01 | 60.641099999999994 | strong_covered |
| -180.0 | p1W_p5 | 61.92124872818647 | doe_lhs_like_01 | 120.6411 | open_gap |
| -120.0 | p1W_p5 | 121.92124872818647 | next_zero_rot_anchor_03 | 140.78897284477728 | open_gap |
| -60.0 | aggr_lhs_retention_dy_05 | 132.2413280960452 | next_zero_rot_anchor_03 | 80.78897284477728 | open_gap |

The K=6 phase-state library is still incomplete. This is not a +15 deg steering proof.
