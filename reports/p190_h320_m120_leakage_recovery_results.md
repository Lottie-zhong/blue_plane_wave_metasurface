# P190 h320 m120 leakage recovery results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass -120 from P189 phase hits.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- tested: 12
- valid: 12
- early_pass: 3
- opens_m120: 1
- best_candidate: `p190_h320_m120_crot_p25_p1W_m2_p2W_p2`
- best_ratio: 8.086518530
- best_m120_candidate: `p190_h320_m120_crot_p30_p1L_m2_p2L_p2`
- best_m120_ratio: 6.717066978

## Candidate results

| base | variant | status | nearest bin | phase | target | leakage | ratio | early | opens -120 | candidate |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| crot_p30 | p2W_p2 | ok | -120 | -144.302676862 | 0.836420835 | 0.162587650 | 5.144430326 | False | False | `p190_h320_m120_crot_p30_p2W_p2` |
| crot_p30 | p2W_p4 | ok | -120 | -142.376082305 | 0.825222499 | 0.173569938 | 4.754409147 | False | False | `p190_h320_m120_crot_p30_p2W_p4` |
| crot_p30 | p2L_p2 | ok | -120 | -142.330744095 | 0.837347740 | 0.186814543 | 4.482240661 | False | False | `p190_h320_m120_crot_p30_p2L_p2` |
| crot_p30 | p2L_p4 | ok | -120 | -140.266465979 | 0.852438493 | 0.266262078 | 3.201501688 | False | False | `p190_h320_m120_crot_p30_p2L_p4` |
| crot_p30 | p1W_m2_p2W_p2 | ok | -180 | -150.584515498 | 0.882739196 | 0.115382988 | 7.650514293 | True | False | `p190_h320_m120_crot_p30_p1W_m2_p2W_p2` |
| crot_p30 | p1L_m2_p2L_p2 | ok | -120 | -146.920426947 | 0.880731314 | 0.131118436 | 6.717066978 | True | True | `p190_h320_m120_crot_p30_p1L_m2_p2L_p2` |
| crot_p25 | p2W_p2 | ok | -120 | -148.813545168 | 0.822084554 | 0.186531204 | 4.407222689 | False | False | `p190_h320_m120_crot_p25_p2W_p2` |
| crot_p25 | p2W_p4 | ok | -120 | -148.038682862 | 0.817689057 | 0.190933856 | 4.282577621 | False | False | `p190_h320_m120_crot_p25_p2W_p4` |
| crot_p25 | p2L_p2 | ok | -120 | -147.835780424 | 0.826411864 | 0.169855116 | 4.865392837 | False | False | `p190_h320_m120_crot_p25_p2L_p2` |
| crot_p25 | p1W_m2_p2W_p2 | ok | -180 | -156.023487273 | 0.891352079 | 0.110226926 | 8.086518530 | True | False | `p190_h320_m120_crot_p25_p1W_m2_p2W_p2` |
| crot_p20 | p2L_p4 | ok | -180 | -153.389680966 | 0.877243583 | 0.174146025 | 5.037402277 | False | False | `p190_h320_m120_crot_p20_p2L_p4` |
| crot_p20 | p2W_p4 | ok | -180 | -155.911434840 | 0.846423179 | 0.154254867 | 5.487173240 | False | False | `p190_h320_m120_crot_p20_p2W_p4` |

## Decision rule

- If opens_m120 > 0, freeze best -120 candidate.
- If no opens_m120 but ratio improves above P189, continue with notch/helper recovery.
- If ratio worsens, stop this branch and test coupling/gap scan.