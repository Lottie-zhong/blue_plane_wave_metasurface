# APCD K=6 Neighborhood FDTD Selection v1 Summary

Scope: 09-P8 selection only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.

Selected count: 3
Selected candidate IDs: nhood_p1w_dx_05, nhood_p1w_dx_02, nhood_lhs_leakred_06
Unique candidate IDs: True
Contains p1w_dx_neighborhood: True
lhs_like_leakage_reduction count: 1
Status values: selected_not_run

Family distribution:

- `lhs_like_leakage_reduction`: 1
- `p1w_dx_neighborhood`: 2

Selection reasons:

- `nhood_p1w_dx_05`: Closest low-risk dx-neighborhood probe: keep p1_width=60 nm from doe_p1w_dx_01 and move internal_dx from -30 to -35 nm.
- `nhood_p1w_dx_02`: Low-risk p1-width probe: keep internal_dx=-30 nm from doe_p1w_dx_01 and narrow p1_width from 60 to 55 nm.
- `nhood_lhs_leakred_06`: Conservative lhs-like leakage-reduction probe: retain p1w_dx geometry and add only small internal_dy=5 nm to test lower-leakage 60-90 deg trend.

These candidates are selected for the next real-FDTD step only. The selection does not imply optical pass, phase coverage, leakage, ratio, or steering performance.
