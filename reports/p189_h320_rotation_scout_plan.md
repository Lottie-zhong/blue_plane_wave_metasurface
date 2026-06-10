# P189 h320 rotation scout plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Rotation scout only.
- No height scan.
- No K=6 supercell.
- No steering claim.
- No Micro-LED claim.

generated_candidates: 18

## Candidate queue

| target | base | variant | candidate | changed fields | purpose |
|---|---|---|---|---:|---|
| m120 | m180_base | crot_p20 | `p189_h320_m120_m180_base_crot_p20` | 2 | common rotation +20 deg: move -180 branch toward -120 |
| m120 | m180_base | crot_p25 | `p189_h320_m120_m180_base_crot_p25` | 2 | common rotation +25 deg |
| m120 | m180_base | crot_p30 | `p189_h320_m120_m180_base_crot_p30` | 2 | common rotation +30 deg |
| m120 | m180_base | crot_p35 | `p189_h320_m120_m180_base_crot_p35` | 2 | common rotation +35 deg |
| m120 | m180_base | crot_p40 | `p189_h320_m120_m180_base_crot_p40` | 2 | common rotation +40 deg |
| m120 | m180_bestlw | bestlw_crot_p20 | `p189_h320_m120_m180_bestlw_bestlw_crot_p20` | 2 | best L/W -180 anchor + common rot +20 |
| m120 | m180_bestlw | bestlw_crot_p25 | `p189_h320_m120_m180_bestlw_bestlw_crot_p25` | 2 | best L/W -180 anchor + common rot +25 |
| m120 | m180_bestlw | bestlw_crot_p30 | `p189_h320_m120_m180_bestlw_bestlw_crot_p30` | 2 | best L/W -180 anchor + common rot +30 |
| p060 | p060_base | crot_m5 | `p189_h320_p060_p060_base_crot_m5` | 2 | baseline 120-ish p060 branch, common rot -5 |
| p060 | p060_base | crot_m10 | `p189_h320_p060_p060_base_crot_m10` | 2 | baseline p060 branch, common rot -10 |
| p060 | p060_base | crot_m15 | `p189_h320_p060_p060_base_crot_m15` | 2 | baseline p060 branch, common rot -15 |
| p060 | p060_scale098 | crot_m2p5 | `p189_h320_p060_p060_scale098_crot_m2p5` | 2 | near-boundary scale098, common rot -2.5 |
| p060 | p060_scale098 | crot_m5 | `p189_h320_p060_p060_scale098_crot_m5` | 2 | near-boundary scale098, common rot -5 |
| p060 | p060_scale098 | rel_p1m2p5_p2p2p5 | `p189_h320_p060_p060_scale098_rel_p1m2p5_p2p2p5` | 2 | relative rotation recovery A |
| p060 | p060_scale098 | rel_p1p2p5_p2m2p5 | `p189_h320_p060_p060_scale098_rel_p1p2p5_p2m2p5` | 2 | relative rotation recovery B |
| p060 | p060_p2Wm4 | crot_m5 | `p189_h320_p060_p060_p2Wm4_crot_m5` | 2 | p2W_m4 borderline leakage, common rot -5 |
| p060 | p060_p2Wm4 | rel_p1m2p5_p2p2p5 | `p189_h320_p060_p060_p2Wm4_rel_p1m2p5_p2p2p5` | 2 | p2W_m4 relative recovery A |
| p060 | p060_p2Wm4 | rel_p1p2p5_p2m2p5 | `p189_h320_p060_p060_p2Wm4_rel_p1p2p5_p2m2p5` | 2 | p2W_m4 relative recovery B |