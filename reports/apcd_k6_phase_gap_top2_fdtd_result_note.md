# APCD K=6 Phase-Gap Top-2 FDTD Result Note

This report records 09-P16: phase-gap selected top-2 real FDTD validation and result recording.

This round only ran:

- `gap_bridge_03`
- `gap_lhs_leakred_06`

This round did not run `gap_p2w_trim_03`, did not run the 24-row phase-gap pool, did not run the 20-row fine pool, did not run the 24-row neighborhood pool, and did not run the 52-row bounded pool.

No model was trained. K=7 was not used. No phase-ramp supercell was built. No TiO2/450 nm branch was opened. This is not a steering result and does not support a +15 deg steering claim.

## Results

| candidate_id | phase deg | target_conversion | leakage | ratio | PD | total T | early pass | inside 60-90 deg |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `gap_bridge_03` | 96.7395 | 0.9258 | 0.0947 | 9.7721 | 0.8143 | 0.5103 | yes | no |
| `gap_lhs_leakred_06` | 96.3206 | 0.9232 | 0.0749 | 12.3197 | 0.8498 | 0.4991 | yes | no |

Both candidates meet the early leakage and ratio thresholds:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

However, neither candidate entered the intended 60-90 deg phase region. Both landed near the existing 90-100 deg usable region.

## Interpretation

The two selected phase-gap candidates successfully reduced leakage compared with the aggressive `doe_lhs_like_01` direction, but they also lost the large phase shift that made `doe_lhs_like_01` valuable as 60 deg phase evidence.

This means the conservative bridge / leakage-reduced design was too conservative for the 60-90 deg objective. It produced good low-leakage states, but not new 60-90 deg usable phase states.

No new 60-90 deg usable phase candidate was found in this top-2 run.

## Next Step

The next candidate design should keep the leakage-controlled features but move more deliberately toward the phase-shifting ingredients in `doe_lhs_like_01`, likely by increasing the controlled `internal_dy` and/or using a slightly more aggressive p1/p2 width/length interpolation. The next batch should still be small and should not move to K=7, phase-ramp supercell assembly, or model training.
