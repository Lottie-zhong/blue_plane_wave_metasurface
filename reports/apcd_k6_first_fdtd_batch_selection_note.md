# APCD K=6 First FDTD Batch Selection Note

## Scope

This is 09-P4 for `09_small_data_active_learning_surrogate`.

This step only selects the first small batch of FDTD candidates from the geometry-passing candidate pool. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a `+15 deg` steering result.

`K` means dimer count. Here `K=6` means six dimers, not six nanopillars.

## Input Basis

Input candidate pool:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv
```

Geometry validation:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0_geometry_validation.csv
```

The geometry validation found 52 candidates with `overall_geometry_pass=true` and `recommended_for_fdtd=true`. Baseline is excluded from this first batch because it already has a real result.

## Selection Policy

Because there is no trained surrogate and no surrogate prediction, this is rule-based diversity selection.

Selection rules:

- choose only `recommended_for_fdtd=true` candidates;
- exclude `baseline`;
- prioritize multi-parameter combinations over repeated one-factor anchors;
- cover multiple candidate families;
- include both positive and negative geometry/displacement directions where possible;
- keep the first batch small, within 6-10 candidates.

## Selected Batch

Output CSV:

```text
outputs/apcd_k6_active_learning/first_fdtd_batch_v0.csv
```

Output summary:

```text
outputs/apcd_k6_active_learning/first_fdtd_batch_v0_summary.md
```

Selected count: `8`

Selected candidates:

- `doe_p1w_p2w_02`
- `doe_p1l_p1w_04`
- `doe_p1w_dx_01`
- `doe_p2w_dy_04`
- `doe_p1l_p2w_01`
- `doe_p1w_p2w_dx_02`
- `doe_lhs_like_01`
- `doe_lhs_like_02`

These rows are marked:

```text
status = selected_not_run
```

## Interpretation

This batch is only a small real-FDTD candidate list for the next stage. It does not prove phase coverage, target conversion, leakage suppression, diffraction-order behavior, or steering.

The next step is to prepare these selected candidates for a controlled real FDTD evaluation, still avoiding a full sweep.
