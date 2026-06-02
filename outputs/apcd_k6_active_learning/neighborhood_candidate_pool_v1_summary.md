# APCD K=6 Neighborhood Candidate Pool v1 Summary

Scope: 09-P6 candidate pool only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.

Candidate count: 24
Unique candidate IDs: True
Bounds check: passed
Reference candidates: doe_lhs_like_01, doe_p1w_dx_01, doe_p1w_dx_01|doe_lhs_like_01
Status values: not_evaluated
requires_fdtd values: true
requires_geometry_validation values: true

Candidate family distribution:

- `bridge_dx_lhs`: 4
- `lhs_like_leakage_reduction`: 10
- `p1w_dx_neighborhood`: 10

`p1w_dx_neighborhood` explores low-leakage variants around `doe_p1w_dx_01`.
`lhs_like_leakage_reduction` pulls `doe_lhs_like_01` toward lower-leakage anchors while preserving mixed displacement.
`bridge_dx_lhs` interpolates between the low-leakage and large-phase-shift references.

All rows require geometry validation before any real FDTD job.
