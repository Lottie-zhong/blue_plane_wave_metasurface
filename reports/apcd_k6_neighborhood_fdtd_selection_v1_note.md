# APCD K=6 Neighborhood FDTD Selection v1 Note

This note records stage 09-P8: selecting a small neighborhood candidate subset
for the next real FDTD batch.

## Scope

This round only selects 2-4 neighborhood FDTD candidates. No FDTD run was
performed, no lumapi call was made, no model was trained, and no `.fsp` file was exported. This is selection only and is not a `+15 deg` steering result.

## Selection Logic

The selection uses only candidates with:

- `overall_geometry_pass=True`
- `recommended_for_fdtd=True`
- `requires_fdtd=true`

No phase, leakage, ratio, or surrogate prediction is fabricated for the new
rows.

## Why Prioritize `p1w_dx_neighborhood`

`doe_p1w_dx_01` is the strongest 09-P5 real-FDTD reference: it passed the early
target/leakage/ratio filters and moved phase below the dataset-v0 low end. The
next real-FDTD step should therefore test whether nearby p1-width and
internal_dx perturbations keep leakage low while pulling phase toward the
90-100 degree region.

## Why Select Only One `lhs_like_leakage_reduction`

`doe_lhs_like_01` provided useful phase-coverage evidence near 60 degrees, but
its leakage was too high. The `lhs_like_leakage_reduction` family is therefore
only sampled conservatively in this selection. One candidate is enough to test
whether a small internal_dy perturbation can retain some 60-90 degree trend
without committing a large FDTD budget.

## Why Not Run All 24

The 24-row neighborhood pool is a design scaffold, not a queue to execute
blindly. Running all rows would spend FDTD budget before learning whether the
local p1w_dx trend remains low-leakage. The active-learning loop should run a
very small batch, update the dataset, then decide the next neighborhood.

## Interpretation Boundary

These selected candidates are for the next real-FDTD step only. The selection
does not imply optical performance, target-channel phase, low leakage, high
ratio, diffraction efficiency, or steering performance.
