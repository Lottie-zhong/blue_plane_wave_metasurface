# APCD K=6 Bounded Candidate Pool v0 Note

## Scope

This is 09-P2 for `09_small_data_active_learning_surrogate`.

This step only generates a bounded candidate pool / DOE scaffold. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a `+15 deg` steering result.

`K` means dimer count. Here `K=6` means six dimers, not six nanopillars.

## Input Basis

The scaffold uses:

- `outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv`
- `outputs/apcd_k6_active_learning/candidate_parameter_schema.csv`
- `outputs/apcd_k6_active_learning/phase_bin_targets.csv`
- `outputs/apcd_k6_active_learning/active_learning_scoring_rules.md`

Dataset v0 has only 10 real rows, with phase coverage from `103.97568470011174` to `124.13005700428602 deg`. This is too narrow to form a `60 deg` phase-state library and too small to train a reliable surrogate.

## Candidate Pool Strategy

The pool deliberately avoids a full combination sweep. A full grid over six variables would create many unevaluated candidates before there is enough evidence to justify them.

Instead, the scaffold uses a deterministic mixed DOE:

- baseline reference;
- v0 good anchors: `p1W_m5`, `p2W_p10`, `p1L_m10`, `p1L_m5`, `p1L_p5`;
- multi-parameter width and length combinations;
- internal dimer displacement combinations;
- a small deterministic Latin-hypercube-like mixed block.

The first-stage searched variables are:

- `p1_length_nm`
- `p1_width_nm`
- `p2_length_nm`
- `p2_width_nm`
- `internal_dx_nm`
- `internal_dy_nm`

Rotations remain fixed:

- `p1_rotation_deg = 67.5`
- `p2_rotation_deg = 112.5`

The pool includes multi-parameter combinations such as:

- `p1W + p2W`
- `p1L + p1W`
- `p1W + internal_dx`
- `p2W + internal_dy`
- `p1L + p2W`
- `p1W + p2W + internal_dx`

## Outputs

Candidate pool:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv
```

Summary:

```text
outputs/apcd_k6_active_learning/bounded_candidate_pool_v0_summary.md
```

All candidates are marked:

```text
requires_fdtd = true
status = not_evaluated
predicted_phase_bin = blank
```

The blank `predicted_phase_bin` is intentional because this step does not make surrogate predictions.

## Geometry Boundary

All scaffolded candidates use the 09-P0 bounds and fixed rotations. The beta-selective pillar-2 geometry `150 x 85 nm` is not allowed.

Precise gap validation is not claimed in this report. The current scaffold uses conservative parameter bounds and fixed fractional positions, and marks later geometry/gap validation as required before any real FDTD job.

## Next Step

The next step is to select a small number of candidates from this pool using the active-learning scoring rules and manual review. Only after that should a small real FDTD batch be prepared.
