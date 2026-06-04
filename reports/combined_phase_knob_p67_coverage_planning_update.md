# 09-P67 coverage and planning update after P66

## Scope

This report updates the single-dimer phase-state coverage after the P66 `cpk_mbin_transition_01` FDTD result.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## P66 input result

`cpk_mbin_transition_01`:

- phase: -145.401 deg
- nearest bin: -120 deg
- phase error to nearest bin: 25.401 deg
- best missing target: -60 deg
- phase error to best missing target: 85.401 deg
- target_conversion: 0.889380
- opposite_spin_leakage: 0.232271
- conversion_to_leakage_ratio: 3.8291
- PD: 0.585841
- early-pass: False
- near-pass: True

Interpretation: P66 avoids the catastrophic leakage collapse of the 440 nm candidate, but it does not open -60 deg or 0 deg. It remains on the negative branch near the -120/-180 region.

## Updated coverage by target bin

| target bin deg | best status | best candidate | phase deg | phase error | target | leakage | ratio | early-pass count | note |
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
- P66 did not open a new missing phase bin.
- `cpk_mbin_transition_01` is useful evidence that 380 nm is safer than 440 nm, but it still stays on the negative branch.

## Decision table

| item | decision | run next | reason |
|---|---|---|---|
| cpk_mbin_transition_01 | record_as_near_pass_negative_branch_evidence | no | It avoids 440 nm leakage collapse but lands at -145 deg, far from -60/0 missing bins. |
| cpk_mbin_transition_02 | optional_but_not_auto | only_if_budget_is_available | P65 allowed it only if transition_01 was informative. It was informative in quality recovery but not promising for missing-bin access, so run only as a limited final check. |
| K6_phase_ramp_supercell | do_not_enter | no | Early-pass coverage remains only -120 and 120 deg; missing bins remain -180, -60, 0, and 60. |
| next_planning_route | if_not_running_transition_02_then_revise_strategy | planning | Height-only transition sampling is not opening new bins; next strategy should consider more explicit phase-offset/library approaches. |


## Recommendation

Do not enter K=6 phase-ramp supercell.

If FDTD budget is available, `cpk_mbin_transition_02` may be run as one limited check of the lower-height transition side, because it was already selected in P65 as top-2. But it should not be treated as guaranteed progress toward new bin coverage.

If budget is tight, skip `transition_02` and move to revised strategy planning.
