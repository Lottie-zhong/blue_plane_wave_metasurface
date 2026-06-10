# P188 h320 lateral compensation scout results

## Scope

- Fixed-height h320 single-dimer candidates only.
- L/W/aspect compensation only.
- No K=6 supercell run.
- No +15 deg steering claim.

## Branch summary

| branch | tested | valid | early | bins seen | early bins | best ratio | best candidate |
|---|---:|---:|---:|---|---|---:|---|
| p060 | 6 | 6 | 0 | 60;120 |  | 3.971097174 | `p188_h320_p060_p2W_m4` |
| p000 | 6 | 6 | 1 | 60;120 | 120 | 7.021174658 | `p188_h320_p000_p1p2W_m4` |
| m180 | 6 | 6 | 4 | -180 | -180 | 25.833195670 | `p188_h320_m180_p2W_p4` |

## Candidate results

| branch | variant | status | nearest bin | phase | target | leakage | ratio | early | candidate |
|---|---|---|---:|---:|---:|---:|---:|---|---|
| p060 | scale098 | ok | 120 | 93.384087636 | 0.895174924 | 0.266028858 | 3.364954210 | False | `p188_h320_p060_scale098` |
| p060 | scale096 | ok | 60 | 86.636240342 | 0.931637316 | 0.633330839 | 1.471012080 | False | `p188_h320_p060_scale096` |
| p060 | p2L_m4 | ok | 120 | 91.772866651 | 0.915741032 | 0.322192989 | 2.842212778 | False | `p188_h320_p060_p2L_m4` |
| p060 | p2W_m4 | ok | 120 | 96.487933499 | 0.904285342 | 0.227716750 | 3.971097174 | False | `p188_h320_p060_p2W_m4` |
| p060 | p1p2L_m4 | ok | 120 | 90.120742542 | 0.907111273 | 0.353844025 | 2.563590761 | False | `p188_h320_p060_p1p2L_m4` |
| p060 | p2L_m4_W_p2 | ok | 120 | 93.058774377 | 0.905098695 | 0.228753730 | 3.956651096 | False | `p188_h320_p060_p2L_m4_W_p2` |
| p000 | scale096 | ok | 120 | 92.307155066 | 0.926429399 | 0.405732419 | 2.283350693 | False | `p188_h320_p000_scale096` |
| p000 | scale094 | ok | 60 | 87.255368213 | 0.944703197 | 0.711073934 | 1.328558328 | False | `p188_h320_p000_scale094` |
| p000 | p2L_m6 | ok | 120 | 94.354054783 | 0.920444819 | 0.215236386 | 4.276436870 | False | `p188_h320_p000_p2L_m6` |
| p000 | p1p2L_m6 | ok | 120 | 92.747770298 | 0.912130651 | 0.261804818 | 3.484010174 | False | `p188_h320_p000_p1p2L_m6` |
| p000 | p1p2W_m4 | ok | 120 | 99.818384991 | 0.899086829 | 0.128053620 | 7.021174658 | True | `p188_h320_p000_p1p2W_m4` |
| p000 | p2L_m8_W_p2 | ok | 120 | 92.895832673 | 0.918891593 | 0.227910350 | 4.031811607 | False | `p188_h320_p000_p2L_m8_W_p2` |
| m180 | scale102 | ok | -180 | 174.283179758 | 0.886663403 | 0.111378819 | 7.960790120 | True | `p188_h320_m180_scale102` |
| m180 | scale104 | ok | -180 | -176.826383781 | 0.861703317 | 0.156843257 | 5.494041219 | False | `p188_h320_m180_scale104` |
| m180 | p2L_p4 | ok | -180 | 169.281623888 | 0.984541640 | 0.100357862 | 9.810309036 | True | `p188_h320_m180_p2L_p4` |
| m180 | p2W_p4 | ok | -180 | 163.249684807 | 0.959874344 | 0.037156624 | 25.833195670 | True | `p188_h320_m180_p2W_p4` |
| m180 | p1p2L_p4 | ok | -180 | 175.645442618 | 0.933549482 | 0.123880767 | 7.535871027 | True | `p188_h320_m180_p1p2L_p4` |
| m180 | p2L_p6_W_m2 | ok | -180 | 173.493231260 | 0.979684746 | 0.250680105 | 3.908107286 | False | `p188_h320_m180_p2L_p6_W_m2` |

## Decision rule

- If p060 branch recovers early-pass 60 at h320, keep it as h320 60 anchor.
- If p000 branch moves toward 0 but ratio fails, use helper/notch recovery later.
- If m180 branch opens -120 at h320, keep h320 as primary fixed-height platform.
- Do not proceed to K=6 until h320 fixed-height single-dimer coverage is sufficient.