# APCD K=6 Neighborhood Candidate Pool v1 Note

This note records stage 09-P6: second-round active-learning / DOE neighborhood
candidate scaffold.

## Scope

This round only generates a neighborhood candidate pool. No FDTD run was
performed, no lumapi call was made, no surrogate was trained, and no `.fsp` file was exported. The pool is candidate-pool only and is not a `+15 deg` steering result.

## Why Focus on `doe_p1w_dx_01`

`doe_p1w_dx_01` is currently the most useful new real-FDTD point from 09-P5. It
passes the early target/leakage/ratio filters and moves the phase below the
dataset-v0 low end:

- target_conversion = 0.9472
- opposite_spin_leakage = 0.0915
- conversion_to_leakage_ratio = 10.3506
- phase = 100.8199 deg

The `p1w_dx_neighborhood` family therefore keeps p2 geometry close to the known
low-leakage setting and varies p1 width plus internal_dx in small steps. The
goal is to probe whether the low leakage can be retained while the phase moves
toward the 90-100 deg region.

## Why Use `doe_lhs_like_01` Only as Phase-Coverage Evidence

`doe_lhs_like_01` shifted the target-channel phase to about 59.36 deg, close to
a 60-degree phase bin. Its leakage is too high, however:

- opposite_spin_leakage = 0.6715
- conversion_to_leakage_ratio = 1.3684

It is therefore not a usable phase state. The
`lhs_like_leakage_reduction` family pulls this aggressive mixed geometry back
toward lower-leakage anchors such as `p1W_m5`, `p2W_p10`, and
`doe_p1w_dx_01`, while retaining some internal displacement and mixed geometry.

## Why Not Directly Run the Remaining Five First-Batch Candidates

The first 09-P5 results showed that the most informative signal came from a
low-leakage internal_dx neighborhood and from one high-leakage phase-coverage
point. Running the remaining five first-batch candidates blindly would spend
FDTD budget without using this new information. A smaller neighborhood pool is
better aligned with active learning: update the candidate region first, validate
geometry, then select a few real FDTD jobs.

## Candidate Families

- `p1w_dx_neighborhood`: low-leakage neighborhood around `doe_p1w_dx_01`.
- `lhs_like_leakage_reduction`: leakage-reduction variants inspired by
  `doe_lhs_like_01`.
- `bridge_dx_lhs`: interpolation candidates between the low-leakage and
  large-phase-shift references.

All rows keep rotations fixed at 67.5 / 112.5 deg, stay within the 09-P0 bounds,
use `requires_geometry_validation=true`, use `requires_fdtd=true`, and keep
`status=not_evaluated`.

## Next Step

The next step should be geometry validation for the neighborhood pool, followed
by selecting only 2-4 candidates for real FDTD. No surrogate prediction should
be claimed from this scaffold.
