# APCD K=6 Small-Data Active Learning Plan

## Scope

This report opens stage `09_small_data_active_learning_surrogate` for the 633 nm APCD-inspired spin-selective dimer/metagrating line.

This stage is scaffold only at this point. No model training was performed. No FDTD run was performed. No lumapi call was made. No `.fsp` file was generated. This report is not a `+15 deg` steering result.

`K` means dimer count. Here `K=6` means six dimers, not six nanopillars.

## Why Enter 09

The stage 08 one-factor perturbation subset showed that most selected candidates can preserve the alpha-pass behavior, but the target-channel phase coverage is too narrow. The observed target-channel phase shifts are only a few degrees to about ten degrees, while a K=6 phase-state library needs roughly `60 deg` spacing between adjacent states.

Manual scanning of the multi-parameter combination space is therefore not a controlled route. Length, width, fractional position, and internal dimer offset can interact, so one-factor intuition is not enough to choose the next 12-18 real FDTD jobs.

The next logical step is a small-data active learning surrogate: use the real evaluated candidate rows to rank a bounded candidate pool, then select only a small number of candidates per target phase bin for future FDTD verification.

This is not a deep-learning large-model stage. The current object is a parameterized dimer, not image topology generation.

## 09 Goal

Find a set of dimer states whose target-channel phase covers:

```text
0, 60, 120, 180, 240, 300 deg
```

under the wrapped `[-180, 180)` convention:

```text
0, 60, 120, -180, -120, -60 deg
```

The selected states should have:

- high `target_conversion`;
- low `opposite_spin_leakage`;
- high `conversion_to_leakage_ratio`;
- acceptable `PD`;
- enough phase diversity to serve as future K=6 phase-state library candidates.

## Recommended Variable Space

Default input parameters:

- `p1_length_nm`
- `p1_width_nm`
- `p2_length_nm`
- `p2_width_nm`
- `p1_frac_x`
- `p1_frac_y`
- `p2_frac_x`
- `p2_frac_y`
- `internal_dx_nm`
- `internal_dy_nm`
- `p1_rotation_deg`
- `p2_rotation_deg`

First-stage search bounds:

- `p1_length_nm`: `110-150`
- `p1_width_nm`: `55-90`
- `p2_length_nm`: `70-105`
- `p2_width_nm`: `130-170`
- `internal_dx_nm`: `-40-40`
- `internal_dy_nm`: `-40-40`

First-stage fixed values:

- `p1_rotation_deg = 67.5`
- `p2_rotation_deg = 112.5`
- `period_x_nm = 340`
- `period_y_nm = 340`
- `height_nm = 300`
- `material = c-Si`
- `substrate = Al2O3`

Rotations are deliberately fixed in the first stage because changing `67.5 / 112.5 deg` may change the alpha/beta allowed state rather than only tune the target-channel phase.

## Output Labels

Do not train or rank only on phase. Phase wraps at `+/-180 deg`, so it is a poor sole supervision target.

Recommended labels:

- `t_alpha_star_from_alpha_real`
- `t_alpha_star_from_alpha_imag`
- `target_conversion`
- `opposite_spin_leakage`
- `conversion_to_leakage_ratio`
- `PD`
- `phase_deg`
- `phase_shift_vs_baseline_deg`
- `overall_early_pass`

The real and imaginary parts of `t_alpha_star_from_alpha` are better primary surrogate outputs. Phase can then be reconstructed and wrapped for bin assignment.

## Active Learning Plan

Each future active-learning round should be:

1. Train a small surrogate from the current real FDTD rows.
2. Predict responses for a bounded candidate pool.
3. Rank candidates independently for the six phase bins.
4. Select 2-3 candidates per bin.
5. Run real FDTD verification outside this scaffold step.
6. Append verified results to the dataset.
7. Retrain and repeat.

The selection should balance phase-bin closeness, high target conversion, low leakage, high conversion-to-leakage ratio, and uncertainty or diversity.

## Recommended First Models

Priority models:

- Random Forest
- XGBoost / LightGBM
- Gaussian Process

Deferred models:

- DenseNet
- cVAE
- large deep generative models

Reason: this is a small-data, parameterized dimer problem. It is not yet a topology-image generation problem.

## Relation To Direct Supercell Optimization

The single-dimer route remains the first choice because it can produce a reusable K=6 phase-state library.

If the single-dimer phase-state library still cannot cover the six bins with acceptable conversion and leakage, then the fallback should be direct K=6 supercell optimization. That fallback objective should maximize order `+1` target-channel efficiency while suppressing order `0`, order `-1`, and beta leakage.

That fallback is not part of this 09-P0 scaffold.

## Deliverables

This scaffold defines:

- `src/metasurface/apcd_active_learning.py`
- `scripts/25_define_apcd_k6_active_learning_scaffold.py`
- `outputs/apcd_k6_active_learning/ml_ready_dataset_schema.csv`
- `outputs/apcd_k6_active_learning/candidate_parameter_schema.csv`
- `outputs/apcd_k6_active_learning/phase_bin_targets.csv`
- `outputs/apcd_k6_active_learning/active_learning_scoring_rules.md`

These are schema and ranking artifacts only. They do not prove steering and do not contain new simulation data.
