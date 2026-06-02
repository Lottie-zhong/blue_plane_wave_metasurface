# APCD K=6 First FDTD Batch v0 Result Note

This note records stage 09-P5: first small-batch real FDTD validation for the
small-data active-learning surrogate workflow.

## Scope

Only three candidates from `first_fdtd_batch_v0.csv` were evaluated:

- `doe_p1w_p2w_02`
- `doe_p1w_dx_01`
- `doe_lhs_like_01`

This round did not run all 8 first-batch candidates and did not run the 52-row
bounded candidate pool. No model was trained, no surrogate prediction was made,
and no `.fsp` export task was added for reporting. It is not a `+15 deg` steering proof or a steering-efficiency result.

## Early-Pass Rule

The early-pass rule used here is:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

The baseline phase is `111.31665091018952 deg`. The previous dataset-v0 phase
range was `103.97568470011174 deg` to `124.13005700428602 deg`.

## Result Summary

| candidate | target_conversion | leakage | ratio | PD | total_T | phase_deg | shift_vs_baseline_deg | early pass | outside v0 phase range |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `doe_p1w_p2w_02` | 0.9541 | 0.2038 | 4.6819 | 0.6480 | 0.5789 | 105.2930 | -6.0236 | no | no |
| `doe_p1w_dx_01` | 0.9472 | 0.0915 | 10.3506 | 0.8238 | 0.5194 | 100.8199 | -10.4967 | yes | yes |
| `doe_lhs_like_01` | 0.9188 | 0.6715 | 1.3684 | 0.1555 | 0.7951 | 59.3589 | -51.9578 | no | yes |

## Interpretation

`doe_p1w_dx_01` is the most valuable new point from this small batch. It passes
the early target/leakage/ratio filters and moves the target-channel phase below
the dataset-v0 low end.

`doe_lhs_like_01` pulls the target-channel phase to about `59.36 deg`, close to a
60-degree phase bin. However, its opposite-spin leakage is high and its
conversion-to-leakage ratio is low, so it cannot be used directly as a phase
state.

`doe_p1w_p2w_02` keeps high target conversion, but its leakage and ratio fail the
early-pass rule. It is recorded for completeness but is not a priority for the
next neighborhood.

These results support the 09-stage premise that multi-parameter and
internal-displacement DOE can expand phase coverage beyond the one-factor
dataset-v0 range. They do not yet provide six usable K=6 phase states.

## Next Step

The next small-data step should prioritize a low-leakage neighborhood around
`doe_p1w_dx_01`, while using `doe_lhs_like_01` as phase-coverage evidence for
designing lower-leakage variants near the 60-degree region.
