# P200 v3 h300 zero valid-helper plan

## Scope

- Fixed height h300 only.
- Base: `p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5`.
- Helper is written using the validated schema: `geometry.nanopillar_helper`.
- No FDTD in this generation step.

| candidate_id | variant_id | purpose | config_path | pillar_paths |
|---|---|---|---|---|
| `p200v3_h300_zero_validhelper_helper_mid_35x35_r45` | helper_mid_35x35_r45 | valid schema middle helper, test real helper effect | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_mid_35x35_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |
| `p200v3_h300_zero_validhelper_helper_diag_p35_30x40_r45` | helper_diag_p35_30x40_r45 | valid schema diagonal helper near p1 side | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_diag_p35_30x40_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |
| `p200v3_h300_zero_validhelper_helper_diag_m35_30x40_r45` | helper_diag_m35_30x40_r45 | valid schema diagonal helper near p2 side | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_diag_m35_30x40_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |
| `p200v3_h300_zero_validhelper_helper_far_p55_30x40_r45` | helper_far_p55_30x40_r45 | valid schema farther helper near p1 side | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_far_p55_30x40_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |
| `p200v3_h300_zero_validhelper_helper_far_m55_30x40_r45` | helper_far_m55_30x40_r45 | valid schema farther helper near p2 side | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_far_m55_30x40_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |
| `p200v3_h300_zero_validhelper_helper_rect_mid_40x80_r45` | helper_rect_mid_40x80_r45 | valid schema stronger rectangular middle helper | `configs/apcd_k6_phase_state_candidates/p200v3_h300_zero_validhelper_helper_rect_mid_40x80_r45.yaml` | geometry.nanopillar_1 | geometry.nanopillar_2 | geometry.nanopillar_helper |