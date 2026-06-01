# APCD K=6 First FDTD Batch v0 Summary

Scope: 09-P4 rule-based selection only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.

Selected count: 8
Unique candidate IDs: True
Status values: selected_not_run

Selected candidates:

- `doe_p1w_p2w_02`: width-width combined perturbation to test p1/p2 width interaction
- `doe_p1l_p1w_04`: p1 length-width interaction with positive length and negative width perturbation
- `doe_p1w_dx_01`: p1 width plus negative internal_dx displacement
- `doe_p2w_dy_04`: p2 width plus positive internal_dy displacement
- `doe_p1l_p2w_01`: p1 length plus p2 width interaction
- `doe_p1w_p2w_dx_02`: three-knob width-width-internal_dx interaction
- `doe_lhs_like_01`: LHS-like mixed geometry/displacement diversity point
- `doe_lhs_like_02`: LHS-like mixed geometry/displacement diversity point

Candidate family distribution:

- `lhs_like_mixed_combo`: 2
- `p1l_p1w_combo`: 1
- `p1l_p2w_combo`: 1
- `p1w_internal_dx_combo`: 1
- `p1w_p2w_combo`: 1
- `p1w_p2w_internal_dx_combo`: 1
- `p2w_internal_dy_combo`: 1

Diversity checks:

- negative internal_dx covered: True
- positive internal_dx covered: True
- negative internal_dy covered: True
- positive internal_dy covered: True

All selected rows came from geometry-passing `recommended_for_fdtd=true` candidates. Baseline is excluded because it already has a real result.
