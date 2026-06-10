# P192 h320 p060 near-miss refinement results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: push P191 near-miss over early-pass threshold for 60 bin.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- tested: 12
- valid: 12
- early_pass: 0
- opens_p060: 0
- best_candidate: `p192_h320_p060_best_p2W_p1`
- best_ratio: 5.696541805
- best_p060_candidate: ``
- best_p060_ratio: 

## Candidate results

| base | variant | status | nearest bin | phase | target | leakage | ratio | early | opens 60 | candidate |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| best | p1W_m1 | ok | 60 | 89.269248326 | 0.867218398 | 0.165958348 | 5.225518378 | False | False | `p192_h320_p060_best_p1W_m1` |
| best | p2W_p1 | ok | 120 | 90.181523239 | 0.866860332 | 0.152173084 | 5.696541805 | False | False | `p192_h320_p060_best_p2W_p1` |
| best | p1W_m1_p2W_p1 | ok | 60 | 89.783707346 | 0.866060788 | 0.157038338 | 5.514964038 | False | False | `p192_h320_p060_best_p1W_m1_p2W_p1` |
| best | p1W_m2_p2W_p1 | ok | 60 | 89.382181128 | 0.865538751 | 0.161700891 | 5.352714792 | False | False | `p192_h320_p060_best_p1W_m2_p2W_p1` |
| best | p1L_m1_p2L_p1 | ok | 120 | 90.672791103 | 0.873316750 | 0.180690250 | 4.833225639 | False | False | `p192_h320_p060_best_p1L_m1_p2L_p1` |
| best | p1L_m2_p2L_p2 | ok | 120 | 91.733339103 | 0.871364661 | 0.185483242 | 4.697808018 | False | False | `p192_h320_p060_best_p1L_m2_p2L_p2` |
| best | p2L_p1 | ok | 120 | 90.912562443 | 0.874241162 | 0.176873546 | 4.942746840 | False | False | `p192_h320_p060_best_p2L_p1` |
| best | p2L_p2 | ok | 120 | 92.173417492 | 0.873693203 | 0.176938575 | 4.937833372 | False | False | `p192_h320_p060_best_p2L_p2` |
| best | extra_crot_m1_p2W_p2 | ok | 60 | 85.557266273 | 0.868995990 | 0.237339255 | 3.661408611 | False | False | `p192_h320_p060_best_extra_crot_m1_p2W_p2` |
| best | extra_crot_m1_p1W_m1_p2W_p2 | ok | 60 | 85.090645379 | 0.868293114 | 0.244338501 | 3.553648365 | False | False | `p192_h320_p060_best_extra_crot_m1_p1W_m1_p2W_p2` |
| simple | p1W_m3_p2W_p3 | ok | 60 | 89.783707346 | 0.866060788 | 0.157038338 | 5.514964038 | False | False | `p192_h320_p060_simple_p1W_m3_p2W_p3` |
| c10_p2W4 | p1W_m2_p2W_p2 | ok | 60 | 86.272698267 | 0.853640757 | 0.186714908 | 4.571893951 | False | False | `p192_h320_p060_c10_p2W4_p1W_m2_p2W_p2` |

## Decision rule

- If opens_p060 > 0, freeze best 60 candidate.
- If best ratio is still 5-6, use one final tiny recovery around best candidate.
- If phase crosses into 120, do not keep it as 60 anchor.
- Do not proceed to K=6 until fixed-height six-bin coverage exists.