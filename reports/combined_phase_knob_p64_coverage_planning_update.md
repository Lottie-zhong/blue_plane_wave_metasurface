# 09-P64 coverage and planning update after P63

## Scope

This report updates the single-dimer phase-state coverage and planning status after the P63 top-1 missing-bin FDTD run.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## P63 input result

`cpk_mbin_hprop_01` was intended to target the missing -180 deg bin by increasing height to 440 nm.

Observed result:

- phase: -90.135 deg
- nearest bin: -120 deg
- target_conversion: 0.918170
- opposite_spin_leakage: 0.619701
- conversion_to_leakage_ratio: 1.4816
- PD: 0.194080
- early-pass: False
- near-pass: False

Interpretation: this is negative evidence. The 440 nm height push did not move the high-quality negative branch toward -180 deg; instead it moved the phase near -90 deg and collapsed APCD selectivity.

## Updated coverage by target bin

| target bin deg | best status | best candidate | phase deg | phase error | target | leakage | ratio | early-pass candidate count | note |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| -180 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| -120 | early_pass | cpk_refine_weak_helper_03 | -115.182 | 4.818 | 0.920946 | 0.100133 | 9.1972 | 4 | usable early-pass |
| -60 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 0 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 60 | missing | - | - | - | - | - | - | 0 | no current candidate in this bin |
| 120 | early_pass | cpk_rot_release_02 | 120.257 | 0.257 | 0.936498 | 0.067424 | 13.8897 | 2 | usable early-pass |


## Current interpretation

- Best-candidate early-pass bins: [-120, 120]
- Bins with any early-pass candidate: [-120, 120]
- Bins whose best candidate is near-pass: []
- Missing or failed-quality bins: [-180, -60, 0, 60]
- P63 did not open a new missing phase bin.
- P63 provides negative evidence against continuing the high-height propagation-phase push toward -180 deg.
- `cpk_refine_htrans_04` remains the strongest negative-phase candidate, but the safe height window appears closer to 400-410 nm rather than 440 nm.

## P64 strategy update

| route | candidate/family | target bin | decision | next action | rationale |
|---|---|---:|---|---|---|
| high_height_hprop | cpk_mbin_hprop_01 | -180 | negative_evidence_recorded | do_not_continue_same_push | 440 nm moved phase to about -90 deg and collapsed selectivity with leakage about 0.62. |
| high_height_hprop_backup | cpk_mbin_hprop_02 | -180 | disable_for_now | do_not_run_as_immediate_next_candidate | It pushes height even higher than failed hprop_01, so leakage risk is likely worse. |
| period_position_push | cpk_mbin_period_01 | -60 | hold_not_immediate | reconsider only after revised missing-bin planning | Previous pos_gap evidence showed period/gap expansion can increase leakage; avoid running without updated guardrails. |
| missing_bin_planning_v2 | P65 revised missing-bin candidate plan | all_missing | recommended_next | generate revised controlled candidate pool before more FDTD | P63 shows missing-bin search needs a new controlled strategy rather than stronger height push. |


## P65 recommendation

Do not run `cpk_mbin_hprop_02`.

Do not immediately run `cpk_mbin_period_01`.

Recommended next action: perform 09-P65 revised missing-bin candidate planning. The revised plan should avoid stronger height pushes and instead design a more controlled candidate pool with explicit leakage-risk guardrails, focusing on routes that can target -180, -60, 0, and 60 deg without destroying the APCD projection selectivity.
