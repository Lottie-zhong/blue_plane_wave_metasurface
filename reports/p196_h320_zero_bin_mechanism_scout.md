# APCD P196 h320 zero-bin mechanism scout

## Scope

This is a Stage 09 fixed-height h320 single-dimer zero-bin mechanism scout. It generates configs, a small candidate table, and geometry sanity validation only.

It does not run FDTD, does not call lumapi, does not export `.fsp`, does not enter K6 phase-ramp supercell, does not use mixed height, and does not claim steering or a complete K6 phase-state library.

## Starting Context

- Current h320 fixed-height coverage from the task context is `[-180, -120, 120]`.
- Missing h320 bins remain `[-60, 0, 60]`.
- P195 -60 scout found phase hits but severe APCD selectivity collapse, so this plan avoids broad common-rotation leakage recovery.
- P195 C_dynamic high-ratio -180 variants are used as diagnostics only, not as a route to keep polishing -180.

## Candidate Strategy

The pool contains 12 integer-nm candidates at `height_nm = 320` targeting the 0 deg phase bin through orthogonal mechanisms:

- dimer gap/coupling offset
- mild notch/slot perturbation using existing notched-rectangle schema
- weak scalar helper, kept standalone and away from the APCD core
- balanced p1/p2 geometry compensation

## Geometry Sanity

- candidate count: 12
- geometry pass: 12/12
- checks: no overlap, minimum same-cell gap, periodic-image gap, boundary containment, fixed height, dimension bounds, duplicate id, duplicate geometry

## Candidate Summary

| candidate | group | anchor | mechanism | status |
|---|---|---|---|---|
| `cpk_p196_zgap_dx_in_01` | dimer_gap_coupling_offset | P190_-120_anchor | change dimer coupling phase without common rotation | not_evaluated |
| `cpk_p196_zgap_dx_out_02` | dimer_gap_coupling_offset | strong_-180_anchor_family | test opposite coupling sign while preserving p1/p2 rotations | not_evaluated |
| `cpk_p196_zgap_dy_in_03` | dimer_gap_coupling_offset | 120_anchor_family | change vertical coupling and retardance balance at fixed h320 | not_evaluated |
| `cpk_p196_zgap_shear_04` | dimer_gap_coupling_offset | P195_C_dynamic_high_ratio_diagnostic | detune coupling asymmetrically without broad rotation recovery | not_evaluated |
| `cpk_p196_znotch_p1r_05` | mild_notch_slot_perturbation | P190_-120_anchor | local scalar phase trimming on p1 while keeping APCD dimer orientation | not_evaluated |
| `cpk_p196_znotch_p2l_06` | mild_notch_slot_perturbation | 120_anchor_family | rebalance p2 phase loading without using beta-selective baseline | not_evaluated |
| `cpk_p196_zslot_bal_07` | mild_notch_slot_perturbation | P195_C_dynamic_high_ratio_diagnostic | weak phase trim with compensated conversion channel | not_evaluated |
| `cpk_p196_zhelper_sq_far_08` | weak_scalar_helper | strong_-180_anchor_family | standalone weak scalar phase loading away from the APCD core | not_evaluated |
| `cpk_p196_zhelper_diag_09` | weak_scalar_helper | 120_anchor_family | weak detour phase perturbation with large core-helper gap | not_evaluated |
| `cpk_p196_zhelper_mid_10` | weak_scalar_helper | P190_-120_anchor | test side-loaded scalar phase without adding a second APCD dimer | not_evaluated |
| `cpk_p196_zbal_geom_a_11` | balanced_p1_p2_geometry_compensation | P190_-120_anchor | balanced aspect-ratio compensation to move phase while preserving selectivity | not_evaluated |
| `cpk_p196_zbal_geom_b_12` | balanced_p1_p2_geometry_compensation | P195_C_dynamic_high_ratio_diagnostic | opposite balanced compensation to probe zero-bin phase crossing | not_evaluated |

## Recommendation

Do not run the whole pool blindly. If a follow-up FDTD task is opened, first review the 12 configs and choose at most a top-2 or top-3 subset from different mechanism groups, with priority on geometry-pass candidates that keep APCD selectivity least disturbed.
