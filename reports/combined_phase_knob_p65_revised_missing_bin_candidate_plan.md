# 09-P65 revised missing-bin candidate planning

## Scope

This report revises the missing-bin candidate plan after the P64 coverage/planning update.

This is a planning report only. It does not include new FDTD results.

The work is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## P64 input status

- Early-pass bins from P64: [-120, 120]
- Missing bins still targeted: [-180, -60, 0, 60]

P63/P64 showed that the 440 nm high-height propagation push failed: it moved the phase near -90 deg and caused very high leakage. Therefore P65 changes the strategy from stronger height push to guarded transition sampling.

## Guardrails

| guardrail | rule | reason |
|---|---|---|
| do_not_push_height_above_safe_window | avoid height >= 440 nm for immediate next FDTD | P63 hprop_01 at 440 nm moved phase near -90 deg and caused leakage about 0.62. |
| pause_hprop_02 | do not run cpk_mbin_hprop_02 as immediate next candidate | It increases height further than the failed P63 top-1 candidate. |
| hold_period_gap_expansion | do not immediately run cpk_mbin_period_01 without a revised guarded plan | Previous pos_gap evidence showed period/gap expansion can place phase near -120 but worsens leakage and ratio. |
| prefer_safe_transition_sampling | sample the transition region between the 120 deg plateau and the robust -120 deg branch with period fixed at 340 nm | This may open 60/0/-60 bins while avoiding the high-height leakage collapse. |


## Revised candidate plan

| priority | candidate | family | primary target | secondary target | base reference | height | period x/y | helper LxW rot | risk | recommendation |
|---:|---|---|---:|---:|---|---:|---|---|---|---|
| 1 | cpk_mbin_transition_01 | safe_height_transition_backoff | -60 | 0 | between cpk_rot_release_02 and cpk_refine_htrans_03 | 380 | 340/340 | 70x120, 135 deg | medium | top1_for_p66 |
| 2 | cpk_mbin_transition_02 | safe_height_transition_backoff | 60 | 0 | between cpk_rot_release_02 and cpk_refine_htrans_03 | 360 | 340/340 | 70x120, 135 deg | medium | top2_only_if_transition_01_is_informative |
| 3 | cpk_mbin_weaksize_01 | weak_helper_strength_guarded | -180 | -60 | cpk_refine_htrans_03 | 400 | 340/340 | 55x105, 135 deg | medium | planning_backup |
| 4 | cpk_mbin_weakrot_01 | weak_helper_rotation_guarded | 0 | 60 | cpk_refine_weak_helper_04 | 400 | 340/340 | 65x115, 105 deg | medium | planning_backup |
| 5 | cpk_mbin_nohelper_transition_01 | apcd_core_reference | 0 | 60 | baseline_apcd_dimer | 380 | 340/340 | none | low | reference_only |
| 6 | cpk_mbin_period_guarded_01 | guarded_period_position_push | -60 | 0 | cpk_refine_weak_helper_04 | 400 | 350/340 | 65x115, 135 deg | medium_high | hold_until_transition_results |


## Recommended P66 FDTD order

1. `cpk_mbin_transition_01`
   - Run this first.
   - Main goal: test a safer 380 nm transition point between the 120 deg plateau and the -120 deg branch.
   - Desired outcome: open or approach -60 or 0 deg while keeping leakage under control.

2. `cpk_mbin_transition_02`
   - Run only if `cpk_mbin_transition_01` is informative and FDTD budget remains.
   - Main goal: test the lower-height side of the same transition route, with possible access to 60 or 0 deg.

## Hold for now

- `cpk_mbin_hprop_02`: disabled for now.
- `cpk_mbin_period_01`: do not run immediately.
- `cpk_mbin_period_guarded_01`: hold until transition candidates show whether safe height sampling can open a missing bin.
- `cpk_mbin_nohelper_transition_01`: reference only.

## Interpretation

P65 does not claim that the phase-state library is complete. The current library still only has reliable early-pass bins at -120 and 120 deg.

The next FDTD should be a single guarded transition candidate, not a K=6 phase-ramp supercell and not a high-height -180 push.
