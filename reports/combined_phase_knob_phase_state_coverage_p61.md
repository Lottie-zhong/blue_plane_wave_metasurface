# 09-P61 phase-state coverage update after P60

## Scope

This report updates the single-dimer phase-state coverage after adding the P60 FDTD results.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Criteria

- early-pass: target_conversion >= 0.5, opposite_spin_leakage <= 0.2, ratio >= 6
- near-pass: target_conversion >= 0.5, opposite_spin_leakage <= 0.25, ratio >= 3, but not early-pass
- target K=6 phase bins: 0, 60, 120, -180, -120, -60 deg

## Coverage by target bin

| target bin deg | best status | best candidate | phase deg | phase error | target | leakage | ratio | early-pass candidate count | note |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| -180 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| -120 | early_pass | cpk_refine_weak_helper_03 | -115.182 | 4.818 | 0.920946 | 0.100133 | 9.1972 | 4 | usable early-pass |
| -60 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 0 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 60 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 120 | early_pass | cpk_rot_release_02 | 120.257 | 0.257 | 0.936498 | 0.067424 | 13.8897 | 2 | usable early-pass |


## Candidate records

| candidate | family | source | phase deg | nearest bin | error | target | leakage | ratio | status | role |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| cpk_refine_weak_helper_03 | weak_helper_leakage_recovery | combined_phase_knob_p60_fdtd_summary.csv | -115.182 | -120 | 4.818 | 0.920946 | 0.100133 | 9.1972 | early_pass | P57 reference; phase-near--120 early-pass comparison |
| cpk_refine_weak_helper_04 | weak_helper_leakage_recovery | combined_phase_knob_p60_fdtd_summary.csv | -113.644 | -120 | 6.356 | 0.932750 | 0.083423 | 11.1810 | early_pass | P60 priority-2; weak-helper local tuning around weak_helper_03 |
| cpk_refine_htrans_03 | height_transition_sweep | combined_phase_knob_p60_fdtd_summary.csv | -128.330 | -120 | 8.330 | 0.952936 | 0.085589 | 11.1339 | early_pass | P60 priority-1; lower-height transition check around htrans_04 |
| cpk_refine_htrans_04 | height_transition_sweep | combined_phase_knob_p60_fdtd_summary.csv | -131.308 | -120 | 11.308 | 0.963606 | 0.019658 | 49.0189 | early_pass | P57 reference; current strongest negative-phase candidate by leakage and ratio |
| cpk_refine_pos_gap_01 | helper_position_gap_recovery | combined_phase_knob_v10_backup_fdtd_summary_p58.csv | -116.536 | -120 | 3.464 | 0.895544 | 0.235317 | 3.8057 | near_pass | backup candidate; phase close to -120 but leakage too high |
| cpk_height_prop_05 | helper_plus_height_propagation | combined_phase_knob_v10_top2_fdtd_summary_p57.csv | -109.638 | -120 | 10.362 | 0.927845 | 0.205773 | 4.5091 | near_pass | negative-phase anchor from P51-P53; opened phase but leakage was too high |
| cpk_rot_release_02 | helper_plus_released_rotation | combined_phase_knob_pilot_fdtd_summary_p51_p53.csv | 120.257 | 120 | 0.257 | 0.936498 | 0.067424 | 13.8897 | early_pass |  |
| cpk_period_phase_04 | helper_plus_period_phase | combined_phase_knob_pilot_fdtd_summary_p51_p53.csv | 122.782 | 120 | 2.782 | 0.750138 | 0.094109 | 7.9710 | early_pass |  |


## Current interpretation

- Best-candidate early-pass bins: [-120, 120]
- Bins with any early-pass candidate: [-120, 120]
- Bins whose best candidate is near-pass: []
- Missing or failed-quality bins: [-180, -60, 0, 60]
- P60 added two new early-pass candidates in the -120 deg bin.
- P60 did not open a new missing phase bin.
- `cpk_refine_htrans_04` remains the strongest negative-phase candidate by leakage and ratio.
- `cpk_refine_weak_helper_03` remains the best phase-near--120 early-pass representative by phase error.
- `cpk_refine_htrans_03` supports height-transition robustness around 400-410 nm.
- `cpk_refine_weak_helper_04` improves leakage/ratio relative to `cpk_refine_weak_helper_03`, but moves slightly farther from -120 deg.

## P62 recommendation

Do not enter K=6 phase-ramp supercell yet.

Current coverage is still insufficient because -180, -60, 0, and 60 deg bins are missing.

Recommended next action: 09-P62 missing-bin candidate planning. The next candidate pool should stop polishing the -120 deg bin and instead target missing bins through controlled changes such as global phase offset, height/period propagation phase, helper strength/position recovery, and possibly a conservative no-helper or weak-helper reference branch.
