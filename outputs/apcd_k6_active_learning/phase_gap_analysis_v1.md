# APCD K=6 Phase Coverage and Gap Analysis v1

Scope: 09-P14 analysis only. No FDTD was run. No lumapi call was made. No model was trained. This is not a steering result.

All sample phase range deg: 59.3589 to 124.130057004
Early-pass sample phase range deg: 98.550226723 to 118.078751272
Early-pass usable candidates: baseline, p1L_m10, p1L_m5, p1L_p5, p1W_m5, p1W_p5, p2W_m5, p2W_p10, doe_p1w_dx_01, nhood_p1w_dx_05, fine_p1w_dx_08, fine_p1w_dx_03

The new fine candidates have pushed usable phase coverage into the 98-99 deg region.
However, the K=6 phase-state library is still incomplete: 0, 60, -60, -120, and -180 deg bins are not covered by early-pass candidates.
The 60 deg bin currently has phase evidence from `doe_lhs_like_01`, but that row has high leakage and cannot be used directly as a phase state.

Per-bin coverage:

| bin deg | nearest all | error all | nearest early-pass | error early-pass | status |
|---:|---|---:|---|---:|---|
| 0.0 | doe_lhs_like_01 | 59.358900000000006 | fine_p1w_dx_03 | 98.55022672300163 | missing |
| 60.0 | doe_lhs_like_01 | 0.6410999999999945 | fine_p1w_dx_03 | 38.55022672300163 | high_leakage_only |
| 120.0 | p1W_p5 | 1.9212487281864696 | p1W_p5 | 1.9212487281864696 | covered_candidate |
| -180.0 | p1L_p10 | 55.869942995713984 | p1W_p5 | 61.92124872818647 | missing |
| -120.0 | p1L_p10 | 115.86994299571398 | p1W_p5 | 121.92124872818647 | missing |
| -60.0 | doe_lhs_like_01 | 119.3589 | fine_p1w_dx_03 | 158.55022672300163 | missing |

Missing bins: 0.0, -180.0, -120.0, -60.0

This is not a +15 deg steering proof and does not justify K=7 or phase-ramp supercell assembly.
