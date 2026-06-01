# APCD K=6 Bounded Candidate Pool v0 Summary

Scope: 09-P2 candidate pool scaffold only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.

Candidate count: 52
Unique candidate IDs: True
Bounds check: passed
Anchors present: baseline, p1W_m5, p2W_p10, p1L_m10, p1L_m5, p1L_p5

Candidate family distribution:

- `baseline`: 1
- `lhs_like_mixed_combo`: 8
- `p1l_p1w_combo`: 6
- `p1l_p2w_combo`: 6
- `p1w_internal_dx_combo`: 6
- `p1w_p2w_combo`: 8
- `p1w_p2w_internal_dx_combo`: 6
- `p2w_internal_dy_combo`: 6
- `v0_good_anchor`: 5

All rows use fixed rotations `67.5 / 112.5 deg`, `requires_fdtd=true`, and `status=not_evaluated`.

The `predicted_phase_bin` column is intentionally blank because no surrogate prediction was made.

Geometry notes: this scaffold uses conservative bounds and fixed fractional positions. Precise gap validation is deferred to the next validation step before any FDTD job.
