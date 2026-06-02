# APCD K=6 Dataset v2 Phase Coverage and Next-Gap Plan

## Scope

This is 09-P19/P20/P21. It updates the ML-ready dataset to v2, analyzes phase coverage after the 09-P18 aggressive phase-gap top-2 results, and plans the next major phase-gap candidates.

No FDTD was run in this stage. No lumapi call was made. No `.fsp` file was generated. No model was trained. No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, DenseNet, or cVAE work was done. This is not a +15 deg steering proof, and the K=6 phase-state library is still incomplete.

## Current Status After 09-P18

The 09-P18 results added two important early-pass candidates:

- `aggr_lhs_retention_dy_05`: phase 72.24132809604521 deg, leakage 0.1028870531101224, ratio 8.329738837977422.
- `aggr_p1w_leakctrl_04`: phase 81.13742146297955 deg, leakage 0.09911912635679705, ratio 8.796387407857752.

Both candidates are inside the 60-90 deg region and satisfy the early-pass thresholds. They are useful new 60-90 deg phase candidates, but they do not close the remaining 0, -60, -120, or -180 deg major gaps.

## Dataset v2 Update

`ml_ready_dataset_v2.csv` appends the two 09-P18 result rows to dataset v1 and keeps the ML-ready real/imaginary complex response labels.

- Dataset v2 rows: 19.
- Early-pass rows: 14.
- New phase-region label: `phase_region`.
- New 60-90 usable rows: `aggr_lhs_retention_dy_05`, `aggr_p1w_leakctrl_04`.

This update is dataset plumbing and phase-coverage accounting only. It is not model training.

## Phase Coverage v2

| K=6 bin deg | nearest early-pass candidate | nearest early-pass phase deg | error deg | status |
|---:|---|---:|---:|---|
| 0 | `aggr_lhs_retention_dy_05` | 72.24132809604521 | 72.24132809604521 | open_gap |
| 60 | `aggr_lhs_retention_dy_05` | 72.24132809604521 | 12.241328096045208 | early_covered |
| 120 | `p1W_p5` | 118.07875127181353 | 1.9212487281864696 | strong_covered |
| -180 | `p1W_p5` | 118.07875127181353 | 61.92124872818647 | open_gap |
| -120 | `p1W_p5` | 118.07875127181353 | 121.92124872818647 | open_gap |
| -60 | `aggr_lhs_retention_dy_05` | 72.24132809604521 | 132.2413280960452 | open_gap |

The main improvement is that the 60 deg bin is now early-covered by a usable 60-90 deg candidate. The 120 deg bin remains strong-covered. The major open gaps are 0, -60, -120, and -180 deg.

## Why Not Keep Optimizing 60-90 Now

The 60-90 region now has two early-pass examples. More local tuning there may improve margins, but it will not solve the K=6 library bottleneck. The next planning step should therefore target the unfilled bins rather than over-optimizing an already useful 60-90 region.

## Next-Gap Pool Logic

`next_phase_gap_candidate_pool_v2.csv` contains 38 candidate scaffold rows. It is not a full sweep and does not include surrogate predictions. Candidate families:

- `rotation_assisted_anchor_probe`: 12.
- `zero_bin_probe`: 6.
- `negative_bin_rotation_probe`: 8.
- `pi_bin_probe`: 6.
- `mixed_safe_bridge`: 6.

The pool prioritizes the remaining gaps using controlled hypotheses:

- 0 deg: rotation-assisted and high-dy probes from the usable 60-90 anchors.
- -60 and -120 deg: global-rotation-assisted candidates and lower-risk mixed bridges.
- -180 deg: pi-bin rotation/mixed probes.

These are optical hypotheses only; real FDTD is required before any performance claim.

## Geometry Validation

`next_phase_gap_candidate_pool_v2_geometry_validation.csv` validates the pool geometry and gap sanity.

- Candidate count: 38.
- Geometry pass: 29.
- Fail: 9.
- Fail reason: duplicate geometry within the scaffold.
- Recommended for FDTD: 29.

The failed rows should stay out of follow-up FDTD. Geometry pass only means the structure is geometrically acceptable; it does not indicate optical performance.

## Selected Next FDTD Candidates

`next_phase_gap_fdtd_selection_v2.csv` selects 4 `selected_not_run` candidates from the geometry-passing rows:

- `next_zero_rot_anchor_03`: target 0 deg, high-risk 0-bin probe.
- `next_rot_anchor_04`: target -60 deg, high-risk rotation-assisted probe.
- `next_mixed_bridge_03`: target -120 deg, moderate-risk mixed bridge.
- `next_pi_mixed_bridge_03`: target -180 deg, moderate-to-high-risk pi-bin bridge.

No YAML configs were generated in this stage. No FDTD was run.

## Recommended Next Action

Generate YAML configs and run only the top two selected candidates first, likely `next_zero_rot_anchor_03` and `next_rot_anchor_04`. Do not run the full 38-row pool. Keep `next_mixed_bridge_03` and `next_pi_mixed_bridge_03` as follow-up candidates if the top two produce useful phase movement or clarify failure modes.
