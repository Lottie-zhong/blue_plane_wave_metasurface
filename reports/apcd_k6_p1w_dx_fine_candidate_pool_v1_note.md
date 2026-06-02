# APCD K=6 p1w_dx Fine Candidate Pool v1 Note

This note records stage 09-P10: p1w_dx leakage-controlled fine neighborhood
candidate scaffold.

## Scope

This round only generates a p1w_dx fine neighborhood candidate pool. No FDTD run
was performed, no lumapi call was made, no model was trained, and no `.fsp` file was exported. This is candidate pool only and is not a `+15 deg` steering result.

## Why This Region

The current real-FDTD trend is:

- `doe_p1w_dx_01`: phase `100.8199 deg`, leakage `0.0915`, ratio `10.3506`, early pass.
- `nhood_p1w_dx_05`: phase `100.9514 deg`, leakage `0.0869`, ratio `10.8860`, early pass.
- `nhood_p1w_dx_02`: phase `98.3086 deg`, leakage `0.2153`, ratio `4.3150`, not early pass.

This indicates a phase/leakage tradeoff. Narrowing `p1_width` can lower phase
into the 90-100 degree region, but leakage rises. Making `internal_dx` more
negative can preserve leakage, but did not lower phase enough in the tested
point.

The fine pool therefore focuses on:

- `p1_width_nm = 56-59`
- `internal_dx_nm = -31 to -34`

This region sits between the low-leakage reference and the lower-phase
high-leakage boundary.

## Candidate Intent

The main family, `p1w_dx_fine_leakage_control`, samples small p1_width and
internal_dx steps without changing p2 geometry. A small
`p1w_dx_p2w_leakage_trim` family adds minor p2_width corrections to test whether
leakage can be reduced without a large geometry jump.

No phase, leakage, ratio, or surrogate prediction is assigned to these rows.

## Target For Later FDTD

The goal is to find a compromise candidate with:

- phase inside 90-100 deg,
- `opposite_spin_leakage <= 0.2`,
- `conversion_to_leakage_ratio >= 6`.

The current pool is only a scaffold. The next step should be geometry validation,
then selection of 2-3 candidates for real FDTD.
