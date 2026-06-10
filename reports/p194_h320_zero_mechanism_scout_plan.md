# P194 h320 zero-bin mechanism scout plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: find 0-bin phase-hit first.
- Success criterion for this scout is nearest_bin=0 and target_conversion>0.5.
- Early-pass is welcome but not required in this mechanism scout.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 12
generation_errors: 0

## Candidate queue

| group | variant | status | candidate | changed fields | purpose / error |
|---|---|---|---|---:|---|
| A_dynamic | p2L_m10_p2W_p4 | generated | `p194_h320_zero_A_dynamic_p2L_m10_p2W_p4` | 2 | strong p2 aspect compensation; seek phase drop toward 0 |
| A_dynamic | p2L_m15_p2W_p6 | generated | `p194_h320_zero_A_dynamic_p2L_m15_p2W_p6` | 2 | stronger p2 aspect compensation |
| A_dynamic | p1L_m5_p2L_m10 | generated | `p194_h320_zero_A_dynamic_p1L_m5_p2L_m10` | 2 | both lengths down, stronger p2 |
| A_dynamic | p1W_m4_p2W_p4 | generated | `p194_h320_zero_A_dynamic_p1W_m4_p2W_p4` | 2 | width contrast compensation |
| A_dynamic | scale090_p2W_p4 | generated | `p194_h320_zero_A_dynamic_scale090_p2W_p4` | 5 | global core scale down with p2 width recovery |
| B_gap | gapx_m10 | generated | `p194_h320_zero_B_gap_gapx_m10` | 2 | reduce dimer separation by 10 nm; test hybridized resonance branch |
| B_gap | gapx_p10 | generated | `p194_h320_zero_B_gap_gapx_p10` | 2 | increase dimer separation by 10 nm |
| B_gap | gapx_m20 | generated | `p194_h320_zero_B_gap_gapx_m20` | 2 | reduce dimer separation by 20 nm |
| B_gap | gapx_p20 | generated | `p194_h320_zero_B_gap_gapx_p20` | 2 | increase dimer separation by 20 nm |
| C_rotation | crot_m20 | generated | `p194_h320_zero_C_rotation_crot_m20` | 2 | common rotation -20 deg diagnostic |
| C_rotation | crot_m30 | generated | `p194_h320_zero_C_rotation_crot_m30` | 2 | common rotation -30 deg diagnostic |
| C_rotation | crot_m40 | generated | `p194_h320_zero_C_rotation_crot_m40` | 2 | common rotation -40 deg diagnostic |