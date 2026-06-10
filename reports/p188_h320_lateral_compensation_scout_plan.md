# P188 h320 lateral compensation scout plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- L/W/aspect compensation only.
- No height scan.
- No K=6 supercell.
- No steering claim.
- No Micro-LED claim.

generated_candidates: 18

## Candidate queue

| branch | variant | candidate | changed fields | purpose |
|---|---|---|---:|---|
| p060 | scale098 | `p188_h320_p060_scale098` | 4 | pull 99deg toward 60 by weakening resonance |
| p060 | scale096 | `p188_h320_p060_scale096` | 4 | stronger pull 99deg toward 60 |
| p060 | p2L_m4 | `p188_h320_p060_p2L_m4` | 1 | p2 length down |
| p060 | p2W_m4 | `p188_h320_p060_p2W_m4` | 1 | p2 width down |
| p060 | p1p2L_m4 | `p188_h320_p060_p1p2L_m4` | 2 | both core lengths down |
| p060 | p2L_m4_W_p2 | `p188_h320_p060_p2L_m4_W_p2` | 2 | p2 length down with width compensation |
| p000 | scale096 | `p188_h320_p000_scale096` | 4 | pull zero-family 104deg downward |
| p000 | scale094 | `p188_h320_p000_scale094` | 4 | stronger zero-family downward pull |
| p000 | p2L_m6 | `p188_h320_p000_p2L_m6` | 1 | zero-family p2 length down |
| p000 | p1p2L_m6 | `p188_h320_p000_p1p2L_m6` | 2 | zero-family both lengths down |
| p000 | p1p2W_m4 | `p188_h320_p000_p1p2W_m4` | 2 | zero-family both widths down |
| p000 | p2L_m8_W_p2 | `p188_h320_p000_p2L_m8_W_p2` | 2 | strong p2 length down with width compensation |
| m180 | scale102 | `p188_h320_m180_scale102` | 4 | push -180 branch toward -120 |
| m180 | scale104 | `p188_h320_m180_scale104` | 4 | stronger push toward -120 |
| m180 | p2L_p4 | `p188_h320_m180_p2L_p4` | 1 | p2 length up |
| m180 | p2W_p4 | `p188_h320_m180_p2W_p4` | 1 | p2 width up |
| m180 | p1p2L_p4 | `p188_h320_m180_p1p2L_p4` | 2 | both core lengths up |
| m180 | p2L_p6_W_m2 | `p188_h320_m180_p2L_p6_W_m2` | 2 | p2 length up with width compensation |