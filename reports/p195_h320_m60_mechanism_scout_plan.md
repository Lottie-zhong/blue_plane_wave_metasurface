# P195 h320 -60 mechanism scout plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: find -60 phase-hit first.
- Success criterion for this scout: nearest_bin=-60 and target_conversion>0.5.
- Early-pass is welcome but not required.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 12

## Candidate queue

| group | base | variant | candidate | changed fields | purpose |
|---|---|---|---|---:|---|
| A_rot | m120_anchor | extra_crot_p10 | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p10` | 2 | continue rotation +10 from -120 anchor |
| A_rot | m120_anchor | extra_crot_p20 | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p20` | 2 | continue rotation +20 from -120 anchor |
| A_rot | m120_anchor | extra_crot_p30 | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p30` | 2 | continue rotation +30 from -120 anchor |
| A_rot | m120_anchor | extra_crot_p40 | `p195_h320_m60_A_rot_m120_anchor_extra_crot_p40` | 2 | continue rotation +40 from -120 anchor |
| B_rot_comp | m120_anchor | extra_crot_p20_p1W_m2_p2W_p2 | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p20_p1W_m2_p2W_p2` | 4 | rotation + width selectivity recovery |
| B_rot_comp | m120_anchor | extra_crot_p20_p1L_m2_p2L_p2 | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p20_p1L_m2_p2L_p2` | 4 | rotation + length selectivity recovery |
| B_rot_comp | m120_anchor | extra_crot_p30_p1W_m2_p2W_p2 | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p30_p1W_m2_p2W_p2` | 4 | stronger rotation + width recovery |
| B_rot_comp | m120_anchor | extra_crot_p30_p1L_m2_p2L_p2 | `p195_h320_m60_B_rot_comp_m120_anchor_extra_crot_p30_p1L_m2_p2L_p2` | 4 | stronger rotation + length recovery |
| C_dynamic | m120_anchor | p2L_m8_p2W_p4 | `p195_h320_m60_C_dynamic_m120_anchor_p2L_m8_p2W_p4` | 2 | p2 aspect dynamic-phase probe |
| C_dynamic | m120_anchor | p2L_m12_p2W_p6 | `p195_h320_m60_C_dynamic_m120_anchor_p2L_m12_p2W_p6` | 2 | stronger p2 aspect dynamic-phase probe |
| D_control | m180_strong | extra_crot_p30 | `p195_h320_m60_D_control_m180_strong_extra_crot_p30` | 2 | strong -180 control with extra +30 rotation |
| D_control | m180_strong | extra_crot_p40 | `p195_h320_m60_D_control_m180_strong_extra_crot_p40` | 2 | strong -180 control with extra +40 rotation |