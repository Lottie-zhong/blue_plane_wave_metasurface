# APCD K=6 Phase-Gap Driven Next Candidate Decision

This report records the 09-P13 to 09-P15 planning step.

No new FDTD was run. No lumapi call was made. No `.fsp` file was exported. No model was trained. This is not a steering result.

## Dataset v1 Progress

Dataset v1 combines the 10-row v0 dataset with seven recorded real-FDTD summary rows:

- `doe_p1w_p2w_02`
- `doe_p1w_dx_01`
- `doe_lhs_like_01`
- `nhood_p1w_dx_05`
- `nhood_p1w_dx_02`
- `fine_p1w_dx_08`
- `fine_p1w_dx_03`

The important progress is that `fine_p1w_dx_08` and `fine_p1w_dx_03` are both usable early-pass points in the 98-99 deg region. They extend the low-phase edge beyond `doe_p1w_dx_01` while keeping leakage below 0.2 and ratio above 6.

## Meaning of the Fine p1w_dx Points

`fine_p1w_dx_08` and `fine_p1w_dx_03` show that narrow p1 width plus controlled negative internal_dx can create a lower target-channel phase while keeping leakage acceptable. This confirms that the p1w_dx direction is a useful low-leakage anchor.

However, the two points do not solve the K=6 library. They only improve one local phase region near 100 deg. Continuing to optimize only around 98-99 deg would add redundant local evidence while leaving the 0, 60, -60, -120, and -180 deg bins unresolved.

## Next Phase Region

The next priority should be the 60-90 deg region.

`doe_lhs_like_01` reached about 59.36 deg, so it provides phase-coverage evidence near the 60 deg bin. Its leakage is too high and its ratio is too low, so it cannot be used directly. The correct next step is not to run it as a phase state, but to design leakage-reduced lhs-like and bridge-to-p1w_dx candidates that try to preserve part of the large phase shift while moving back toward low-leakage geometry.

## Lhs-Like and Bridge Candidates

The project should re-open the `lhs_like_leakage_reduction` and `bridge_dx_lhs` directions in a controlled way. This does not mean running the full neighborhood pool. It means selecting a few conservative candidates that interpolate between:

- `doe_lhs_like_01`: strong 60 deg phase evidence but high leakage.
- `fine_p1w_dx_08` / `fine_p1w_dx_03`: 98-99 deg usable low-leakage anchors.

`nhood_lhs_leakred_06` remains a reasonable reference candidate, but this step should not run it. The safer route is to generate a small new 60-90 deg leakage-controlled pool, validate geometry, then select 2-4 candidates for a later real-FDTD batch.

## Boundary Decisions

This stage should still not move to K=7, phase-ramp supercell assembly, or ML training.

- K=6 six-phase coverage is not complete.
- The dataset is still too small and too phase-clustered for reliable surrogate training.
- A phase-ramp supercell would be premature without a usable six-state single-dimer library.
- K means dimer count in this project; changing K would change the library objective rather than solve the current gap.

## Recommended Next Step

Generate a small 18-30 row 60-90 deg leakage-controlled candidate pool, validate geometry/gap/sanity, and choose 2-4 selected_not_run candidates. Those selected candidates can become the next small real-FDTD batch only after this planning step is reviewed.
