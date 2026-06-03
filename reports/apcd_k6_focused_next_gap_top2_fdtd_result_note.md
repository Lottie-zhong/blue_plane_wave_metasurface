# APCD K=6 Focused Next-Gap Top-2 FDTD Result Note

## Scope

This is 09-P26. Only `focus_zero_leakred_07` and `focus_neg60_geom_04` were prepared and run with real FDTD.

`focus_neg120_asym_03`, `focus_pi_wrap_04`, the full 40-row focused pool, and all old pools were not run. No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, DenseNet, or cVAE work was done. This is not a +15 deg steering result and does not complete the K=6 phase-state library.

## Results

| candidate | target bin | phase deg | error deg | target conversion | leakage | ratio | PD | early pass | target bin status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `focus_zero_leakred_07` | 0 | 30.534894730576525 | 30.534894730576525 | 0.5327046775079014 | 0.469513841744978 | 1.1345878015607294 | 0.0630509560030551 | False | evidence_only |
| `focus_neg60_geom_04` | -60 | 83.13394588891055 | 143.13394588891055 | 0.8929435782636037 | 0.08113267089413602 | 11.00596798321521 | 0.8334161807872716 | True | open_gap |

## Interpretation

`focus_zero_leakred_07` target-bin success: False. Its leakage should be compared with `next_zero_rot_anchor_03` leakage 0.45007533270235894 to judge whether zero-bin leakage reduction worked.

`focus_neg60_geom_04` target-bin success: False. This tests whether geometry-driven negative-phase redesign improves over the failed rotation-assisted `next_rot_anchor_04` result.

If a candidate is phase-near but fails leakage/ratio, it is only evidence_only. If it is early-pass but far from target, it is usable-but-not-target and does not close the major gap.

## Next Step

Update dataset/coverage with these two rows before running any backup. Do not run the full focused pool.
