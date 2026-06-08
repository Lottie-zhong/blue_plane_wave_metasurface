# P181 K=6 supercell dry-run config

## Scope

This is a K=6 supercell dry-run/config generation step only. No K=6 FDTD has been run. No +15 deg beam steering has been verified. This prepares the input for later server-side FDTD validation. It is not a Micro-LED result.

`K` means six dimers, not individual nanopillars.

## Inputs

- P180 phase-ramp plan: `outputs/apcd_k6_active_learning/p180_k6_phase_ramp_supercell_plan.csv`
- P179 frozen phase library: `outputs/apcd_k6_active_learning/p179_stage10_frozen_phase_library.csv`

## Assembly

| index | target_bin_deg | candidate_id | source_config |
| ---: | ---: | --- | --- |
| 0 | 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | `configs/apcd_k6_phase_state_candidates/cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01.yaml` |
| 1 | 60 | `aggr_lhs_retention_dy_05` | `configs/apcd_k6_phase_state_candidates/aggr_lhs_retention_dy_05.yaml` |
| 2 | 120 | `cpk_rot_release_02` | `configs/apcd_k6_phase_state_candidates/cpk_rot_release_02.yaml` |
| 3 | -180 | `cpk_resphase_scale104_nohelper_01` | `configs/apcd_k6_phase_state_candidates/cpk_resphase_scale104_nohelper_01.yaml` |
| 4 | -120 | `cpk_060_anchor_wh03_h425_scale98_01` | `configs/apcd_k6_phase_state_candidates/cpk_060_anchor_wh03_h425_scale98_01.yaml` |
| 5 | -60 | `cpk_060_boundary_h435_aniso_reduce10_01` | `configs/apcd_k6_phase_state_candidates/cpk_060_boundary_h435_aniso_reduce10_01.yaml` |

## Sanity

- K: 6
- six dimers present: True
- six unique target bins present: True
- supercell_period_nm: 2445.724192163921
- dimer_pitch_nm: 407.620698694
- all source anchors early-pass: True
- pillar_count: 15
- min_same_cell_gap_nm: 63.22398681325972
- min_adjacent_dimer_gap_nm: 123.86811339134141
- no pillar crosses supercell boundary: True
- no overlap detected: True
- no steering claim: True
- fdtd_run_performed: False

## Outputs

- dry-run config: `configs/apcd_k6_supercells/p181_k6_phase_ramp_supercell_633nm.yaml`
- geometry plan CSV: `outputs/apcd_k6_active_learning/p181_k6_supercell_geometry_plan.csv`
- sanity CSV: `outputs/apcd_k6_active_learning/p181_k6_supercell_sanity.csv`

## Boundary

This config is an assembly input for later server-side FDTD validation. It is not optical validation.
