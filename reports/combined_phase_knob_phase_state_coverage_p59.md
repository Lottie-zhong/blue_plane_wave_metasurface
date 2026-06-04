# 09-P59 phase-state coverage report

## Scope

This report summarizes the current single-dimer phase-state coverage after P51-P58.

This is not a K=6 phase-ramp supercell, not a +15 degree steering result, not a K=7 result, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Criteria

- early-pass: target_conversion >= 0.5, opposite_spin_leakage <= 0.2, ratio >= 6
- near-pass: target_conversion >= 0.5, opposite_spin_leakage <= 0.25, ratio >= 3, but not early-pass
- target K=6 phase bins: 0, 60, 120, -180, -120, -60 deg

## Coverage by target bin

| target bin deg | best status | best candidate | phase deg | phase error | target | leakage | ratio | note |
|---:|---|---|---:|---:|---:|---:|---:|---|
| -180 | missing | - | - | - | - | - | - | no current candidate in this bin |
| -120 | early_pass | cpk_refine_weak_helper_03 | -115.182 | 4.818 | 0.920946 | 0.100133 | 9.1972 | usable early-pass |
| -60 | missing | - | - | - | - | - | - | no current candidate in this bin |
| 0 | missing | - | - | - | - | - | - | no current candidate in this bin |
| 60 | missing | - | - | - | - | - | - | no current candidate in this bin |
| 120 | early_pass | cpk_rot_release_02 | 120.257 | 0.257 | 0.936498 | 0.067424 | 13.8897 | usable early-pass |


## Candidate records

| candidate | family | source | phase deg | nearest bin | error | target | leakage | ratio | status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| cpk_refine_weak_helper_03 | weak_helper_leakage_recovery | combined_phase_knob_v10_backup_fdtd_summary_p58.csv | -115.182 | -120 | 4.818 | 0.920946 | 0.100133 | 9.1972 | early_pass |
| cpk_refine_htrans_04 | height_transition_sweep | combined_phase_knob_v10_backup_fdtd_summary_p58.csv | -131.308 | -120 | 11.308 | 0.963606 | 0.019658 | 49.0189 | early_pass |
| cpk_refine_pos_gap_01 | helper_position_gap_recovery | combined_phase_knob_v10_backup_fdtd_summary_p58.csv | -116.536 | -120 | 3.464 | 0.895544 | 0.235317 | 3.8057 | near_pass |
| cpk_height_prop_05 | helper_plus_height_propagation | combined_phase_knob_v10_top2_fdtd_summary_p57.csv | -109.638 | -120 | 10.362 | 0.927845 | 0.205773 | 4.5091 | near_pass |
| cpk_rot_release_02 | helper_plus_released_rotation | combined_phase_knob_pilot_fdtd_summary_p51_p53.csv | 120.257 | 120 | 0.257 | 0.936498 | 0.067424 | 13.8897 | early_pass |
| cpk_period_phase_04 | helper_plus_period_phase | combined_phase_knob_pilot_fdtd_summary_p51_p53.csv | 122.782 | 120 | 2.782 | 0.750138 | 0.094109 | 7.9710 | early_pass |


## Current interpretation

- Early-pass bins: [-120, 120]
- Bins whose best candidate is near-pass: []
- Near-pass candidates currently exist inside the -120 deg bin, but that bin is already covered by early-pass candidates.
- Missing or failed-quality bins: [-180, -60, 0, 60]
- `cpk_refine_htrans_04` remains the strongest negative-phase candidate by leakage and ratio.
- `cpk_refine_weak_helper_03` remains the better phase-near--120 early-pass comparison.
- `cpk_refine_pos_gap_01` is useful negative/contrast evidence: phase is close to -120 deg, but leakage and ratio fail.

## P60 recommendation

Current coverage is still insufficient for K=6 phase-ramp supercell construction because -180, -60, 0, and 60 deg bins are missing.

Do not enter K=6 phase-ramp supercell yet.

Next FDTD priority should remain:
1. height_transition_sweep
2. weak_helper_leakage_recovery
3. pause pos_gap

P60 should run only 1-2 high-value candidates after checking this coverage table.

