# APCD K=6 Neighborhood Candidate Pool Geometry Validation Note

This note records stage 09-P7: geometry / gap / sanity validation for
`neighborhood_candidate_pool_v1.csv`.

## Scope

This round only validates the geometry of the neighborhood candidate pool v1.
No FDTD run was performed, no lumapi call was made, no model was trained, and no `.fsp` file was exported. This is geometry only and is not a `+15 deg` steering result.

## Validation Rules

Each candidate is checked against the 09-P0 bounds:

- `p1_length_nm`: 110-150
- `p1_width_nm`: 55-90
- `p2_length_nm`: 70-105
- `p2_width_nm`: 130-170
- `internal_dx_nm`: -40 to 40
- `internal_dy_nm`: -40 to 40

Additional checks:

- `p1_rotation_deg` must remain 67.5.
- `p2_rotation_deg` must remain 112.5.
- beta-selective p2 geometry `150 x 85 nm` is not allowed.
- same-cell gap must be at least 5 nm.
- periodic-image gap must be at least 5 nm.

## Interpretation Boundary

Passing this validation only means the candidate is geometrically sane under the
current conservative polygon-gap estimate. Geometry pass does not represent optical pass, target-channel phase coverage, leakage, ratio, diffraction order efficiency, or any steering result.

## Next Step

The next step should select only 2-4 candidates from `recommended_for_fdtd=true`
rows for real FDTD. Priority should go to low-risk `p1w_dx_neighborhood`
candidates because `doe_p1w_dx_01` already showed low leakage and early pass.
A small number of conservative `lhs_like_leakage_reduction` candidates can also
be selected to test whether the large phase-shift trend from `doe_lhs_like_01`
can be retained while reducing leakage.
