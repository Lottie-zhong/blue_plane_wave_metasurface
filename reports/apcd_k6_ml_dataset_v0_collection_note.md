# APCD K=6 ML Dataset v0 Collection Note

## Scope

This is 09-P1 for `09_small_data_active_learning_surrogate`.

This step only collects existing real FDTD candidate rows into the first ML-ready dataset. No new FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No new candidate pool was generated. This is not a `+15 deg` steering result.

`K` means dimer count. Here `K=6` means six dimers, not six nanopillars.

## Inputs

The collection script reads:

- `outputs/apcd_k6_active_learning/ml_ready_dataset_schema.csv`
- `outputs/apcd_k6_metagrating_633nm/phase_state_candidate_config_index.csv`
- existing `outputs/apcd_k6_metagrating_633nm/phase_state_candidates/<variant_id>/results.csv`

The baseline phase used for wrapped phase shift is:

```text
111.31665091018952 deg
```

Early pass thresholds:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

## Dataset v0 Summary

Output dataset:

```text
outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv
```

Collection report:

```text
outputs/apcd_k6_active_learning/ml_ready_dataset_v0_collection_report.md
```

Sample count: `10`

Included variants:

- `baseline`
- `p1L_m10`
- `p1L_m5`
- `p1L_p5`
- `p1L_p10`
- `p1W_m5`
- `p1W_p5`
- `p2W_m10`
- `p2W_m5`
- `p2W_p10`

Missing variants:

- `p2L_m5`
- `p2L_p5`
- `p2W_p5`

Phase range:

```text
103.9756847 to 124.130057004 deg
```

Overall early pass count: `8`

Overall early pass variants:

- `baseline`
- `p1L_m10`
- `p1L_m5`
- `p1L_p5`
- `p1W_m5`
- `p1W_p5`
- `p2W_m5`
- `p2W_p10`

## Interpretation

Dataset v0 now aligns the existing real FDTD rows to the 09-P0 ML-ready schema. It keeps both `t_alpha_star_from_alpha_real` and `t_alpha_star_from_alpha_imag`, so the future surrogate is not forced to learn wrapped phase as the only target.

The current phase span remains narrow. The dataset v0 is useful for initial surrogate/data plumbing, schema validation, and candidate ranking code tests, but it is not enough to train a reliable model.

## Next Step

The next stage should be bounded candidate pool / DOE scaffold. That should still remain scaffold-only until the candidate pool is reviewed.
