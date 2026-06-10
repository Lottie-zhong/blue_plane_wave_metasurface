# P195 h320 -60 mechanism scout results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: find -60 phase-hit first.
- Success criterion for this scout: nearest_bin=-60 and target_conversion>0.5.
- Early-pass is welcome but not required.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- tested: 12
- valid_results: 12
- early_pass: 2
- m60_phase_hit_count: 5
- m60_early_pass_count: 0
- near_m60_45deg_count: 5
- best_ratio_candidate: `p195_h320_m60_C_dynamic_m120_anchor_p2L_m12_p2W_p6`
- best_ratio: 7.508249486
- best_m60_candidate: `p195_h320_m60_D_control_m180_strong_extra_crot_p40`
- best_m60_ratio: 1.685521501
- closest_to_m60_candidate: `p195_h320_m60_A_rot_m120_anchor_extra_crot_p40`
- closest_to_m60_abs_phase_deg: 2.289358712

## Candidate results

| group | base | variant | status | nearest bin | phase | abs phase to -60 | target | leakage | ratio | early | -60 hit | near -60 45 | candidate |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| A_rot | m120_anchor | extra_crot_p10 | ok | -120 | -133.016298117 | 73.016298117 | 0.827390147 | 0.178088175 | 4.645957804 | False | False | False | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p10` |
| A_rot | m120_anchor | extra_crot_p20 | ok | -120 | -116.015903920 | 56.015903920 | 0.717002929 | 0.317813297 | 2.256050759 | False | False | False | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p20` |
| A_rot | m120_anchor | extra_crot_p30 | ok | -60 | -81.726940294 | 21.726940294 | 0.690525780 | 0.436402046 | 1.582315635 | False | True | True | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p30` |
| A_rot | m120_anchor | extra_crot_p40 | ok | -60 | -62.289358712 | 2.289358712 | 0.585525504 | 0.523354179 | 1.118793978 | False | True | True | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p40` |
| B_rot_comp | m120_anchor | extra_crot_p20_p1W_m2_p2W_p2 | ok | -120 | -123.411963521 | 63.411963521 | 0.683076981 | 0.324608076 | 2.104312960 | False | False | False | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p20_p1W_m2_p2W_p2` |
| B_rot_comp | m120_anchor | extra_crot_p20_p1L_m2_p2L_p2 | ok | -120 | -120.783459736 | 60.783459736 | 0.662632945 | 0.394764046 | 1.678554447 | False | False | False | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p20_p1L_m2_p2L_p2` |
| B_rot_comp | m120_anchor | extra_crot_p30_p1W_m2_p2W_p2 | ok | -60 | -87.481206560 | 27.481206560 | 0.654547345 | 0.456878506 | 1.432650774 | False | True | True | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p30_p1W_m2_p2W_p2` |
| B_rot_comp | m120_anchor | extra_crot_p30_p1L_m2_p2L_p2 | ok | -60 | -85.605497743 | 25.605497743 | 0.653459635 | 0.557273570 | 1.172601160 | False | True | True | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p30_p1L_m2_p2L_p2` |
| C_dynamic | m120_anchor | p2L_m8_p2W_p4 | ok | -180 | -154.405817610 | 94.405817610 | 0.885663014 | 0.129391218 | 6.844846435 | True | False | False | `p195_h320_m60_C_dynamic_m120_anchor_p2L_m8_p2W_p4` |
| C_dynamic | m120_anchor | p2L_m12_p2W_p6 | ok | -180 | -157.242193511 | 97.242193511 | 0.887351870 | 0.118183589 | 7.508249486 | True | False | False | `p195_h320_m60_C_dynamic_m120_anchor_p2L_m12_p2W_p6` |
| D_control | m180_strong | extra_crot_p30 | ok | -120 | -105.203534530 | 45.203534530 | 0.703205269 | 0.306511808 | 2.294219182 | False | False | False | `p195_h320_m60_D_control_m180_strong_extra_crot_p30` |
| D_control | m180_strong | extra_crot_p40 | ok | -60 | -81.127370203 | 21.127370203 | 0.655697201 | 0.389017405 | 1.685521501 | False | True | True | `p195_h320_m60_D_control_m180_strong_extra_crot_p40` |

## Decision rule

- If m60_phase_hit_count > 0, use best -60 phase-hit for P196 leakage recovery.
- If m60_early_pass_count > 0, freeze best -60 anchor directly.
- If near_m60_45deg_count > 0 but no -60 hit, refine closest-to--60 mechanism.
- If all candidates remain around -120/-180, stop this rotation-chain route.