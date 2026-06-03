# APCD K=6 v5 Diagnosis and Next-Generation Redesign Plan

## Scope

This is 09-P33/P35. It summarizes accumulated real FDTD rows through dataset v5, diagnoses phase-span/leakage bottlenecks, and creates a next-generation candidate planning scaffold.

No FDTD, lumapi, `.fsp`, YAML generation, old-pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made in this stage.

## Accumulated Diagnosis

Usable phase span is 72.24132809604521 to 118.07875127181353 deg. The usable set is mainly concentrated in the 60-120 deg region, with no usable negative-phase state.

Main bottleneck: expanding phase away from the 60-120 deg cluster tends to raise leakage or collapse back to positive phase. 0 deg and -180 deg have evidence-only rows, not usable states.

## Next-Generation Strategy

- Release fixed rotations 67.5/112.5 deg in a controlled way.
- Expand internal dx/dy beyond the previous conservative neighborhood.
- Redesign p1/p2 aspect-ratio families and test controlled swap/inversion without using beta-selective p2=150x85 nm.
- Keep height/period as optional future knobs in a small scaffold, not as a broad sweep.
- Separate zero-bin and negative-bin strategies instead of using one bridge pattern for all gaps.

## Candidate Pool v6

Nextgen candidate count: 60
Geometry pass: 60/60

Family counts:
- `controlled_swap_inversion_neg120`: 10
- `expanded_internal_separation_negative_push`: 10
- `height_period_future_knob_scout`: 10
- `pi_wrap_leakage_control`: 10
- `rotation_released_neg60_dxdy`: 10
- `rotation_released_zero_bin`: 10

## Selected Not Run

| rank | candidate | target | family | next priority |
|---:|---|---:|---|---|
| 1 | `ng_zero_rot_release_07` | 0 | `rotation_released_zero_bin` | top2_next_round |
| 2 | `ng_neg60_dxdy_release_08` | -60 | `rotation_released_neg60_dxdy` | top2_next_round |
| 3 | `ng_neg120_swap_asym_05` | -120 | `controlled_swap_inversion_neg120` | backup_selected_not_run |
| 4 | `ng_pi_wrap_lowleak_06` | -180 | `pi_wrap_leakage_control` | backup_selected_not_run |
| 5 | `ng_neg60_bridge_release_04` | -60 | `expanded_internal_separation_negative_push` | backup_selected_not_run |

Next round should run the top-2 only first: `ng_zero_rot_release_07` and `ng_neg60_dxdy_release_08`.
