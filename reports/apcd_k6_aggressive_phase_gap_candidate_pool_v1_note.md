# APCD K=6 Aggressive Phase-Gap Candidate Pool v1 Note

This report records 09-P17: aggressive 60-90 deg phase-gap candidate pool scaffold, geometry validation, and selected_not_run candidate selection.

No FDTD was run. No lumapi call was made. No `.fsp` file was generated. No config YAML was generated. No model was trained. This is not a steering result and does not claim +15 deg steering. K=7, phase-ramp supercell, TiO2/450 nm, and Micro-LED integration were not used.

## Motivation

09-P16 showed that `gap_bridge_03` and `gap_lhs_leakred_06` both early-pass, but their phases landed at about 96 deg. That means the conservative bridge / leakage-reduced direction can suppress leakage, but it pulls the phase back toward the existing 90-100 deg region.

The new candidate pool is deliberately more aggressive. It moves closer to `doe_lhs_like_01`, which produced about 59.36 deg phase and therefore remains the main phase-shift anchor. Because `doe_lhs_like_01` had high leakage, the new pool keeps leakage-control anchors from:

- `gap_lhs_leakred_06`
- `gap_bridge_03`
- `fine_p1w_dx_03`
- `fine_p1w_dx_08`

## Candidate Design

The pool contains 32 candidates across six families:

- `lhs_like_retention_high_dy`: 6
- `lhs_like_leakage_control_p1w`: 6
- `lhs_like_p2w_trim`: 5
- `lhs_to_fine_bridge_aggressive`: 5
- `dy_sweep_near_lhs`: 5
- `mixed_aggressive_but_safe`: 5

The design keeps rotations fixed at 67.5 / 112.5 deg. It explores larger `internal_dy`, retains more lhs-like length/width factors, and uses limited p1_width / p2_width changes for leakage control. It does not use the beta-selective p2 geometry.

## Geometry Validation

All 32 candidates pass geometry validation.

- Geometry pass: 32/32
- Recommended for FDTD: 32
- Minimum same-cell gap: 88.26958309667273 nm
- Minimum periodic-image gap: 75.72476807342596 nm

Geometry pass only means the structures are geometrically feasible under this conservative checker. It does not imply optical performance.

## Selected Candidates

Three candidates were selected as selected_not_run:

- `aggr_lhs_retention_dy_05`: most aggressive selected row; keeps short lhs-like p1/p2 geometry and high `internal_dy`.
- `aggr_p1w_leakctrl_04`: leakage-control row; keeps high `internal_dy` while relaxing p1/p2 widths.
- `aggr_bridge_lhs_fine_05`: bridge row; interpolates between `doe_lhs_like_01`, fine p1w_dx anchors, and `gap_lhs_leakred_06`.

These are not run in 09-P17. They are only candidates for a future small real-FDTD batch.

## Next Step

The next step should review the three selected_not_run candidates and decide whether to run 2 of them as a small real-FDTD batch. The goal remains finding a new 60-90 deg usable phase candidate with lower leakage than `doe_lhs_like_01`. The K=6 phase-state library is still incomplete.
