# P180 K=6 phase-ramp supercell plan

## Scope

This is a Stage 10 K=6 design plan only. No K=6 FDTD has been run. No +15 deg steering has been verified yet. The result is a supercell assembly input for later FDTD. It is not a Micro-LED result.

`K` means six dimers in the supercell. The target angle is used only to size the design-period input.

## Inputs

- frozen P179 single-dimer phase library: `outputs/apcd_k6_active_learning/p179_stage10_frozen_phase_library.csv`
- wavelength: 633 nm
- target design angle: +15 deg
- K: 6 dimers
- supercell period target Lambda = wavelength / sin(15 deg) = 2445.724192163921 nm
- dimer pitch = Lambda / K = 407.62069869398687 nm

## Phase Ramp

The selected wrapped phase-bin order is `0, 60, 120, -180, -120, -60`, representing a 60 deg step ramp.

| index | target_bin_deg | candidate_id | center_x_nm | cumulative_target_phase_deg |
| ---: | ---: | --- | ---: | ---: |
| 0 | 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | 203.81034934699343 | 0.0 |
| 1 | 60 | `aggr_lhs_retention_dy_05` | 611.4310480409803 | 60.0 |
| 2 | 120 | `cpk_rot_release_02` | 1019.0517467349672 | 120.0 |
| 3 | -180 | `cpk_resphase_scale104_nohelper_01` | 1426.672445428954 | 180.0 |
| 4 | -120 | `cpk_060_anchor_wh03_h425_scale98_01` | 1834.293144122941 | 240.0 |
| 5 | -60 | `cpk_060_boundary_h435_aniso_reduce10_01` | 2241.9138428169276 | 300.0 |

## Sanity

- K: 6
- phase bins complete: True
- all anchors early-pass: True
- expected phase step: 60.0 deg
- max phase error: 23.00999999999999 deg
- no steering claim: True

## Outputs

- plan CSV: `outputs/apcd_k6_active_learning/p180_k6_phase_ramp_supercell_plan.csv`
- sanity CSV: `outputs/apcd_k6_active_learning/p180_k6_phase_ramp_sanity.csv`

## Boundary

This plan should be treated as an assembly input for a later K=6 FDTD run, not as optical validation.
