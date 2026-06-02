# APCD K=6 Aggressive Phase-Gap Top-2 FDTD Result Note

This report records 09-P18: aggressive phase-gap selected top-2 real FDTD validation and result recording.

This round only ran:

- `aggr_lhs_retention_dy_05`
- `aggr_p1w_leakctrl_04`

This round did not run `aggr_bridge_lhs_fine_05`, the full 32-row aggressive pool, the 24-row phase-gap pool, the 20-row fine pool, the 24-row neighborhood pool, the 52-row bounded pool, or `gap_p2w_trim_03`.

No model was trained. K=7 was not used. No phase-ramp supercell was built. No TiO2/450 nm or Micro-LED branch was opened. This is not a steering result and does not support a +15 deg steering claim. The K=6 phase-state library is still incomplete.

## Results

| candidate_id | phase deg | target_conversion | leakage | ratio | PD | total T | early pass | inside 60-90 deg |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `aggr_lhs_retention_dy_05` | 72.2413 | 0.8570 | 0.1029 | 8.3297 | 0.7856 | 0.4800 | yes | yes |
| `aggr_p1w_leakctrl_04` | 81.1374 | 0.8719 | 0.0991 | 8.7964 | 0.7958 | 0.4855 | yes | yes |

Both candidates satisfy the early pass thresholds:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

Both candidates also enter the intended 60-90 deg phase region. `aggr_lhs_retention_dy_05` is the more phase-aggressive result and is near the 60 deg bin by the current 15 deg neighborhood criterion.

## Interpretation

The 09-P17 aggressive strategy worked better than the 09-P16 conservative bridge. Retaining more lhs-like phase-shift factors and using larger `internal_dy` moved the phase away from the 96 deg conservative region while keeping leakage acceptable.

This produces new usable 60-90 deg single-dimer phase candidates:

- `aggr_lhs_retention_dy_05`
- `aggr_p1w_leakctrl_04`

This does not mean the full K=6 phase-state library is complete. The result only improves the single-dimer candidate set for the 60-90 deg gap.

## Next Step

The next step should update the ML-ready dataset with these two summary rows and re-run phase coverage analysis. If the 60 deg bin is now considered near-covered by `aggr_lhs_retention_dy_05`, the project should next target the remaining large gaps rather than continue over-optimizing the 60-90 deg region.
