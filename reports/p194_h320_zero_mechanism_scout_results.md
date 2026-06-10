# P194 h320 zero-bin mechanism scout results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: find 0-bin phase-hit first.
- Success criterion for this scout: nearest_bin=0 and target_conversion>0.5.
- Early-pass is welcome but not required.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- generated_candidates: 12
- generation_errors: 0
- valid_results: 12
- early_pass: 4
- zero_phase_hit_count: 0
- zero_early_pass_count: 0
- near_zero_45deg_count: 0
- best_ratio_candidate: `p194_h320_zero_B_gap_gapx_p20`
- best_ratio: 10.096479703
- best_zero_candidate: ``
- best_zero_ratio: 
- closest_to_zero_candidate: `p194_h320_zero_C_rotation_crot_m40`
- closest_to_zero_abs_phase_deg: 54.712984079

## Candidate results

| group | variant | status | nearest bin | phase | abs phase to 0 | target | leakage | ratio | early | zero hit | near zero 45 | candidate |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| A_dynamic | p2L_m10_p2W_p4 | ok | 120 | 91.623635397 | 91.623635397 | 0.920780513 | 0.263981129 | 3.488054300 | False | False | False | `p194_h320_zero_A_dynamic_p2L_m10_p2W_p4` |
| A_dynamic | p2L_m15_p2W_p6 | ok | 60 | 87.260238176 | 87.260238176 | 0.957806373 | 0.692876387 | 1.382362555 | False | False | False | `p194_h320_zero_A_dynamic_p2L_m15_p2W_p6` |
| A_dynamic | p1L_m5_p2L_m10 | ok | 60 | 88.165021655 | 88.165021655 | 0.939733699 | 0.552071206 | 1.702196544 | False | False | False | `p194_h320_zero_A_dynamic_p1L_m5_p2L_m10` |
| A_dynamic | p1W_m4_p2W_p4 | ok | 120 | 103.275333043 | 103.275333043 | 0.896740266 | 0.105144423 | 8.528652725 | True | False | False | `p194_h320_zero_A_dynamic_p1W_m4_p2W_p4` |
| A_dynamic | scale090_p2W_p4 | ok | 60 | 81.850492799 | 81.850492799 | 0.955693272 | 0.881108066 | 1.084649329 | False | False | False | `p194_h320_zero_A_dynamic_scale090_p2W_p4` |
| B_gap | gapx_m10 | ok | 120 | 105.602314736 | 105.602314736 | 0.896812963 | 0.133000602 | 6.742924085 | True | False | False | `p194_h320_zero_B_gap_gapx_m10` |
| B_gap | gapx_p10 | ok | 120 | 100.983505109 | 100.983505109 | 0.905561220 | 0.114701416 | 7.894943690 | True | False | False | `p194_h320_zero_B_gap_gapx_p10` |
| B_gap | gapx_m20 | ok | 120 | 108.549917005 | 108.549917005 | 0.908834589 | 0.207829580 | 4.372979959 | False | False | False | `p194_h320_zero_B_gap_gapx_m20` |
| B_gap | gapx_p20 | ok | 120 | 104.076705560 | 104.076705560 | 0.911442283 | 0.090273274 | 10.096479703 | True | False | False | `p194_h320_zero_B_gap_gapx_p20` |
| C_rotation | crot_m20 | ok | 60 | 84.073076374 | 84.073076374 | 0.817372328 | 0.170318327 | 4.799086175 | False | False | False | `p194_h320_zero_C_rotation_crot_m20` |
| C_rotation | crot_m30 | ok | 60 | 66.887520415 | 66.887520415 | 0.759113121 | 0.275365187 | 2.756750512 | False | False | False | `p194_h320_zero_C_rotation_crot_m30` |
| C_rotation | crot_m40 | ok | 60 | 54.712984079 | 54.712984079 | 0.612877291 | 0.366598268 | 1.671795380 | False | False | False | `p194_h320_zero_C_rotation_crot_m40` |

## Decision rule

- If zero_phase_hit_count > 0, use best zero phase-hit for P195 leakage recovery.
- If near_zero_45deg_count > 0 but zero_phase_hit_count = 0, refine the closest-to-zero mechanism.
- If all candidates remain in 60/120 bins, stop h320 zero small-modification route and consider a new geometry family.