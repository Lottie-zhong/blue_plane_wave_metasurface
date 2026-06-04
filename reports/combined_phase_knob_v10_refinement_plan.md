# 09-P54/P56 combined phase-knob v10 refinement planning

## Scope

This remains within the 09 stage. The `v10 refinement pool` is only the candidate-pool version following v9 planning.

This step is planning only: no FDTD, no lumapi, no `.fsp`, no YAML generation, no K=6 phase-ramp supercell, no K=7 run, no TiO2/450 nm scaling, no Micro-LED integration, no ML/DenseNet/cVAE training, no +15 deg steering claim, and no complete K=6 phase-state library claim.

## Anchor from 09-P51-P53

`cpk_height_prop_05` is the key negative-phase anchor: target_conversion = 0.9278, leakage = 0.2058, ratio = 4.5091, PD = 0.6370, phase = -109.64 deg, early_pass = False.

Interpretation: height/material propagation phase opened a useful negative phase, but leakage is slightly too high and the conversion-to-leakage ratio needs recovery.

## v10 refinement pool

Candidate count: 26
Geometry-pass count: 26/26

Family distribution:
- `conservative_height_comparison`: 5
- `height_transition_sweep`: 6
- `helper_position_gap_recovery`: 5
- `helper_rotation_recovery`: 5
- `weak_helper_leakage_recovery`: 5

The pool deliberately stays small and controlled. It focuses on height transition, weak-helper leakage recovery, helper-position gap recovery, helper-rotation recovery, and conservative height comparison.

## Selected candidates

| rank | candidate | family | target | priority |
|---:|---|---|---:|---|
| 1 | `cpk_refine_htrans_04` | `height_transition_sweep` | -120 | top2_next_run |
| 2 | `cpk_refine_weak_helper_03` | `weak_helper_leakage_recovery` | -120 | top2_next_run |
| 3 | `cpk_refine_pos_gap_01` | `helper_position_gap_recovery` | -120 | backup_selected_not_run |
| 4 | `cpk_refine_helper_rot_04` | `helper_rotation_recovery` | -120 | backup_selected_not_run |
| 5 | `cpk_refine_htrans_05` | `height_transition_sweep` | -120 | comparison_selected_not_run |
| 6 | `cpk_refine_conservative_03` | `conservative_height_comparison` | -120 | comparison_selected_not_run |

Recommended first manual FDTD candidates after review: `cpk_refine_htrans_04` and `cpk_refine_weak_helper_03`.

Do not describe this as completed steering or a completed phase-state library. It is a phase-state library refinement plan around the negative-phase anchor.
