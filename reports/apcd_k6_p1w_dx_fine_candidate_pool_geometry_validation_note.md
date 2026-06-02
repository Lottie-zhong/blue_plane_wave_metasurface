# APCD K=6 p1w_dx Fine Candidate Pool Geometry Validation Note

This note records stage 09-P11: geometry / gap / sanity validation for
`p1w_dx_fine_candidate_pool_v1.csv`.

## Scope

This round only validates the fine candidate pool geometry. No FDTD run was
performed, no lumapi call was made, no model was trained, and no `.fsp` file was exported. This is geometry only and is not a `+15 deg` steering result.

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
- duplicate geometry is rejected against `doe_p1w_dx_01`,
  `nhood_p1w_dx_05`, and `nhood_p1w_dx_02`.

## Interpretation Boundary

Geometry pass does not represent optical pass, target-channel phase, leakage,
ratio, diffraction efficiency, or steering performance. It only says the row is
eligible for later selection from a geometry/sanity perspective.

## Next Step

The next step should select 2-3 `recommended_for_fdtd=true` rows for real FDTD.
The selection should focus on `p1_width=56-58 nm` and `internal_dx=-32 to -34 nm`
because that region lies between the low-leakage reference and the lower-phase
high-leakage boundary. The active target remains a compromise state with phase
inside 90-100 deg, `opposite_spin_leakage <= 0.2`, and
`conversion_to_leakage_ratio >= 6`.
