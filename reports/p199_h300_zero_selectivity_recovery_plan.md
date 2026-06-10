# P199 h300 zero selectivity recovery plan

## Scope

- Fixed height h300 only.
- Base: next_zero_rot_anchor_03.
- Goal: recover APCD selectivity while keeping nearest_bin=0.
- No FDTD in this generation step.
- No K6 / steering claim.

## Candidate queue

| candidate_id | group | variant_id | purpose | config_path |
|---|---|---|---|---|
| `p199_h300_zero_A_crot_rollback_crot_p2p5` | A_crot_rollback | crot_p2p5 | common rotation rollback +2.5°, try reduce leakage while staying 0-bin | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_A_crot_rollback_crot_p2p5.yaml` |
| `p199_h300_zero_A_crot_rollback_crot_p5` | A_crot_rollback | crot_p5 | common rotation rollback +5°, stronger selectivity recovery, still likely near 0-bin | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_A_crot_rollback_crot_p5.yaml` |
| `p199_h300_zero_A_crot_rollback_crot_p7p5` | A_crot_rollback | crot_p7p5 | common rotation rollback +7.5°, boundary probe before phase returns to 60-bin | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_A_crot_rollback_crot_p7p5.yaml` |
| `p199_h300_zero_B_diff_rot_p1_p5` | B_diff_rot | p1_p5 | rotate p1 +5 only, differential APCD recovery | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p1_p5.yaml` |
| `p199_h300_zero_B_diff_rot_p2_p5` | B_diff_rot | p2_p5 | rotate p2 +5 only, differential APCD recovery | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p2_p5.yaml` |
| `p199_h300_zero_B_diff_rot_p1_p5_p2_m2p5` | B_diff_rot | p1_p5_p2_m2p5 | increase relative-angle asymmetry while keeping phase near 0 | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p1_p5_p2_m2p5.yaml` |
| `p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5` | B_diff_rot | p1_m2p5_p2_p5 | opposite differential rotation recovery | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5.yaml` |
| `p199_h300_zero_C_geom_comp_p1_120x58` | C_geom_comp | p1_120x58 | move p1 geometry toward h300 p000 early-pass shape | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_C_geom_comp_p1_120x58.yaml` |
| `p199_h300_zero_C_geom_comp_p2_76x137` | C_geom_comp | p2_76x137 | move p2 geometry toward h300 p000 early-pass shape | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_C_geom_comp_p2_76x137.yaml` |
| `p199_h300_zero_C_geom_comp_p1_120x58_p2_76x137` | C_geom_comp | p1_120x58_p2_76x137 | move both p1/p2 toward known stronger h300 early-pass geometry | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_C_geom_comp_p1_120x58_p2_76x137.yaml` |
| `p199_h300_zero_D_pos_gap_y_to_101` | D_pos_gap | y_to_101 | restore y-position to h300 early-pass anchor, tiny coupling correction | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_D_pos_gap_y_to_101.yaml` |
| `p199_h300_zero_D_pos_gap_y_to_101_crot_p2p5` | D_pos_gap | y_to_101_crot_p2p5 | position correction plus mild rotation rollback | `configs/apcd_k6_phase_state_candidates/p199_h300_zero_D_pos_gap_y_to_101_crot_p2p5.yaml` |