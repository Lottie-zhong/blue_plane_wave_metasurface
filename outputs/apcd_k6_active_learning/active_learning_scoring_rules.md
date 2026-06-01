# APCD K=6 Active Learning Scoring Rules

Scope: scaffold only. No training is performed here. No FDTD run is performed here. No `.fsp` file is exported here. This is not a steering result.

## Candidate score

For each predicted candidate and each K=6 phase bin, compute:

```text
score = 0.40 * phase_score
      + 0.25 * target_score
      + 0.20 * leakage_score
      + 0.10 * ratio_score
      + 0.05 * pd_score
      + 0.10 * surrogate_uncertainty_bonus
```

- `phase_score = max(0, 1 - wrapped_phase_error_deg / 30)`
- `target_score = clip(target_conversion, 0, 1)`
- `leakage_score = 1 - clip(opposite_spin_leakage, 0, 1)`
- `ratio_score = clip(log1p(conversion_to_leakage_ratio) / log1p(20), 0, 1)`
- `pd_score = clip((PD + 1) / 2, 0, 1)`

Higher score is better. The ranking is done per phase bin, then the top 2-3 candidates per bin are selected for future real FDTD verification.

## Active learning loop planned for later

1. Train a small surrogate from the current real FDTD dataset.
2. Predict responses for a bounded candidate pool.
3. Rank candidates separately for the 0/60/120/180/240/300 deg target-channel phase bins.
4. Select 2-3 candidates per bin.
5. Run real FDTD outside this scaffold step.
6. Append verified rows to the dataset and retrain.

Use real/imaginary `t_alpha_star_from_alpha` as primary surrogate outputs because phase wraps at +/-180 deg.
