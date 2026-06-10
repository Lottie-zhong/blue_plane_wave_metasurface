# P189 h320 rotation scout results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Rotation scout only.
- No K=6 supercell run.
- No +15 deg steering claim.

## Branch summary

| target | tested | valid | early | target hits | bins seen | early bins | best ratio | best candidate | best target hit |
|---|---:|---:|---:|---:|---|---|---:|---|---|
| m120 | 8 | 8 | 0 | 0 | -180;-120 |  | 5.739678920 | `p189_h320_m120_m180_base_crot_p20` | `` |
| p060 | 10 | 10 | 0 | 0 | 60;120 |  | 4.781829331 | `p189_h320_p060_p060_base_crot_m5` | `` |

## Candidate results

| target | base | variant | status | nearest bin | phase | target conv | leakage | ratio | early | target hit | candidate |
|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| m120 | m180_base | crot_p20 | ok | -180 | -157.460844022 | 0.850888820 | 0.148246763 | 5.739678920 | False | False | `p189_h320_m120_m180_base_crot_p20` |
| m120 | m180_base | crot_p25 | ok | -120 | -149.575847036 | 0.827082647 | 0.180602581 | 4.579572695 | False | False | `p189_h320_m120_m180_base_crot_p25` |
| m120 | m180_base | crot_p30 | ok | -120 | -145.031036390 | 0.844201298 | 0.154918397 | 5.449328892 | False | False | `p189_h320_m120_m180_base_crot_p30` |
| m120 | m180_base | crot_p35 | ok | -120 | -130.568066711 | 0.784075891 | 0.213967668 | 3.664459675 | False | False | `p189_h320_m120_m180_base_crot_p35` |
| m120 | m180_base | crot_p40 | ok | -120 | -130.397066282 | 0.817898342 | 0.181536920 | 4.505410478 | False | False | `p189_h320_m120_m180_base_crot_p40` |
| m120 | m180_bestlw | bestlw_crot_p20 | ok | -180 | -155.911434840 | 0.846423179 | 0.154254867 | 5.487173240 | False | False | `p189_h320_m120_m180_bestlw_bestlw_crot_p20` |
| m120 | m180_bestlw | bestlw_crot_p25 | ok | -120 | -148.038682862 | 0.817689057 | 0.190933856 | 4.282577621 | False | False | `p189_h320_m120_m180_bestlw_bestlw_crot_p25` |
| m120 | m180_bestlw | bestlw_crot_p30 | ok | -120 | -142.376082305 | 0.825222499 | 0.173569938 | 4.754409147 | False | False | `p189_h320_m120_m180_bestlw_bestlw_crot_p30` |
| p060 | p060_base | crot_m5 | ok | 120 | 91.914538426 | 0.884153540 | 0.184898598 | 4.781829331 | False | False | `p189_h320_p060_p060_base_crot_m5` |
| p060 | p060_base | crot_m10 | ok | 60 | 82.309142328 | 0.875182263 | 0.330557312 | 2.647596140 | False | False | `p189_h320_p060_p060_base_crot_m10` |
| p060 | p060_base | crot_m15 | ok | 60 | 77.383620578 | 0.847311469 | 0.301781670 | 2.807696932 | False | False | `p189_h320_p060_p060_base_crot_m15` |
| p060 | p060_scale098 | crot_m2p5 | ok | 60 | 88.171261247 | 0.908136311 | 0.373760887 | 2.429725373 | False | False | `p189_h320_p060_p060_scale098_crot_m2p5` |
| p060 | p060_scale098 | crot_m5 | ok | 60 | 86.549260203 | 0.900340134 | 0.351108570 | 2.564278433 | False | False | `p189_h320_p060_p060_scale098_crot_m5` |
| p060 | p060_scale098 | rel_p1m2p5_p2p2p5 | ok | 120 | 95.613032021 | 0.897233323 | 0.232473893 | 3.859501432 | False | False | `p189_h320_p060_p060_scale098_rel_p1m2p5_p2p2p5` |
| p060 | p060_scale098 | rel_p1p2p5_p2m2p5 | ok | 60 | 88.519649159 | 0.904095808 | 0.416557059 | 2.170400881 | False | False | `p189_h320_p060_p060_scale098_rel_p1p2p5_p2m2p5` |
| p060 | p060_p2Wm4 | crot_m5 | ok | 60 | 88.928188667 | 0.904633005 | 0.341411301 | 2.649686766 | False | False | `p189_h320_p060_p060_p2Wm4_crot_m5` |
| p060 | p060_p2Wm4 | rel_p1m2p5_p2p2p5 | ok | 120 | 98.530760234 | 0.904114057 | 0.209941866 | 4.306497195 | False | False | `p189_h320_p060_p060_p2Wm4_rel_p1m2p5_p2p2p5` |
| p060 | p060_p2Wm4 | rel_p1p2p5_p2m2p5 | ok | 120 | 92.342932535 | 0.911020813 | 0.358711228 | 2.539705316 | False | False | `p189_h320_p060_p060_p2Wm4_rel_p1p2p5_p2m2p5` |

## Decision rule

- If m120 target hit appears, use it as h320 -120 candidate.
- If p060 target hit appears, use it as h320 60 candidate.
- If only phase-hit but leakage fails, next step is helper/notch leakage recovery.
- If rotation destroys selectivity broadly, stop common rotation and use small gap/coupling scan.