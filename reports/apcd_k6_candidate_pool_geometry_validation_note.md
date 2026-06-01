# APCD K=6 Candidate Pool Geometry Validation Note

## Scope

This is 09-P3 for `09_small_data_active_learning_surrogate`.

This step only performs candidate pool geometry / gap / sanity validation. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. This is not a `+15 deg` steering result.

`K` means dimer count. Here `K=6` means six dimers, not six nanopillars.

## Input And Output

Input candidate pool:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv
```

Geometry validation output:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0_geometry_validation.csv
```

Validation uses a conservative two-dimensional rotated-rectangle approximation for each pillar. The `internal_dx_nm/internal_dy_nm` fields are interpreted as relative dimer displacement: pillar 1 receives `+dx/2,+dy/2`, and pillar 2 receives `-dx/2,-dy/2`.

## Rules

Validation checks:

- all parameters stay inside 09-P0 bounds;
- `p1_rotation_deg = 67.5`;
- `p2_rotation_deg = 112.5`;
- beta-selective pillar-2 geometry `150 x 85 nm` is rejected;
- same-cell gap is at least `5 nm`;
- nearest periodic-image gap is at least `5 nm`.

## Result

Candidate pool size: `52`

Geometry pass count: `52`

Fail count: `0`

Recommended for FDTD count: `52`

Baseline and anchor status:

- `baseline`: pass
- `p1W_m5`: pass
- `p2W_p10`: pass
- `p1L_m10`: pass
- `p1L_m5`: pass
- `p1L_p5`: pass

Minimum same-cell gap:

```text
55.35345512751108 nm
```

Minimum periodic-image gap:

```text
51.09768861572567 nm
```

No candidate failed the geometry sanity rules under this conservative approximation.

## Interpretation

This validation only indicates that the scaffolded geometries are suitable for later setup review and small-batch FDTD preparation. It does not say anything about target-channel phase, conversion efficiency, leakage, diffraction order behavior, or steering.

The next step is to select a small number of candidates from the geometry-passing pool for real FDTD verification. That selection should use the active-learning scoring plan plus manual review, not a full sweep.
