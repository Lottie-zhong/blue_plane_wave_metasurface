# APCD K=6 Phase Gap Analysis v2

Scope: 09-P20 analysis only. No FDTD was run. No lumapi call was made. No model was trained. This is not a steering result.

60 deg bin status: `early_covered` using nearest early-pass `aggr_lhs_retention_dy_05` at `72.24132809604521` deg.
120 deg bin best early-pass candidate: `p1W_p5` at `118.07875127181353` deg.
Major open gaps: 0.0, -180.0, -120.0, -60.0

Per-bin coverage:

| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |
|---:|---|---:|---|---:|---|
| 0.0 | aggr_lhs_retention_dy_05 | 72.24132809604521 | doe_lhs_like_01 | 59.358900000000006 | open_gap |
| 60.0 | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 | early_covered |
| 120.0 | p1W_p5 | 1.9212487281864696 | p1L_p10 | 4.130057004286016 | strong_covered |
| -180.0 | p1W_p5 | 61.92124872818647 | p1L_p10 | 55.869942995713984 | open_gap |
| -120.0 | p1W_p5 | 121.92124872818647 | p1L_p10 | 115.86994299571398 | open_gap |
| -60.0 | aggr_lhs_retention_dy_05 | 132.2413280960452 | doe_lhs_like_01 | 119.3589 | open_gap |

The K=6 phase-state library is still incomplete. No phase-ramp supercell has been built, and this is not a +15 deg steering proof.
