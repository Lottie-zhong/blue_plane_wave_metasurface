# P200 h300 zero leakage-cancel mechanism plan

## Scope

- Fixed height h300 only.
- Base: `p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5`.
- Goal: keep nearest_bin=0 while reducing leakage / increasing ratio.
- No FDTD in this generation step.
- No K=6 / steering claim.
- No mixed height.

## Candidate queue

| candidate_id | group | variant_id | purpose | pillars | rough pass | config_path |
|---|---|---|---|---:|---|---|
| `p200_h300_zero_A_helper_cancel_helper_mid_35x35_r45` | A_helper_cancel | helper_mid_35x35_r45 | add weak middle helper, scalar leakage-cancel probe | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_A_helper_cancel_helper_mid_35x35_r45.yaml` |
| `p200_h300_zero_A_helper_cancel_helper_diag_p35_30x40_r45` | A_helper_cancel | helper_diag_p35_30x40_r45 | add weak diagonal helper near p1 side | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_A_helper_cancel_helper_diag_p35_30x40_r45.yaml` |
| `p200_h300_zero_A_helper_cancel_helper_diag_m35_30x40_r45` | A_helper_cancel | helper_diag_m35_30x40_r45 | add weak diagonal helper near p2 side | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_A_helper_cancel_helper_diag_m35_30x40_r45.yaml` |
| `p200_h300_zero_B_p2_aniso_p2L_m2` | B_p2_aniso | p2L_m2 | reduce p2 length slightly, test leakage suppression | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_B_p2_aniso_p2L_m2.yaml` |
| `p200_h300_zero_B_p2_aniso_p2W_p2` | B_p2_aniso | p2W_p2 | increase p2 width slightly, test leakage suppression | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_B_p2_aniso_p2W_p2.yaml` |
| `p200_h300_zero_B_p2_aniso_p2L_m2_W_p2` | B_p2_aniso | p2L_m2_W_p2 | p2 aspect compensation: shorter and wider | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_B_p2_aniso_p2L_m2_W_p2.yaml` |
| `p200_h300_zero_C_gap_coupling_y_in_2` | C_gap_coupling | y_in_2 | bring two pillars closer along y by 2 nm each | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_C_gap_coupling_y_in_2.yaml` |
| `p200_h300_zero_C_gap_coupling_x_in_2` | C_gap_coupling | x_in_2 | bring two pillars closer along x by 2 nm each | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_C_gap_coupling_x_in_2.yaml` |
| `p200_h300_zero_C_gap_coupling_shear_y_p1down_p2up` | C_gap_coupling | shear_y_p1down_p2up | small shear coupling perturbation, preserve 0-bin phase | 2 | False | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_C_gap_coupling_shear_y_p1down_p2up.yaml` |
| `p200_h300_zero_D_helper_p2_combo_helper_mid_p2W_p2` | D_helper_p2_combo | helper_mid_p2W_p2 | middle helper plus p2 width recovery | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_D_helper_p2_combo_helper_mid_p2W_p2.yaml` |
| `p200_h300_zero_D_helper_p2_combo_helper_mid_p2L_m2_W_p2` | D_helper_p2_combo | helper_mid_p2L_m2_W_p2 | middle helper plus p2 aspect compensation | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_D_helper_p2_combo_helper_mid_p2L_m2_W_p2.yaml` |
| `p200_h300_zero_D_helper_p2_combo_helper_diag_p35_p2W_p2` | D_helper_p2_combo | helper_diag_p35_p2W_p2 | diagonal helper plus p2 width recovery | 3 | True | `configs/apcd_k6_phase_state_candidates/p200_h300_zero_D_helper_p2_combo_helper_diag_p35_p2W_p2.yaml` |

## Suggested first batch

1. `p200_h300_zero_A_helper_cancel_helper_mid_35x35_r45`
2. `p200_h300_zero_B_p2_aniso_p2W_p2`
3. `p200_h300_zero_B_p2_aniso_p2L_m2_W_p2`
4. `p200_h300_zero_D_helper_p2_combo_helper_mid_p2W_p2`