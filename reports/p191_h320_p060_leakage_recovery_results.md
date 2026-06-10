# P191 h320 p060 leakage recovery results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass 60 from P189 p060 phase hits.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- tested: 12
- valid: 12
- early_pass: 0
- opens_p060: 0
- best_candidate: `p191_h320_p060_crot_m5_extra_crot_m2p5_p1W_m2_p2W_p2`
- best_ratio: 5.397056452
- best_p060_candidate: ``
- best_p060_ratio: 

## Candidate results

| base | variant | status | nearest bin | phase | target | leakage | ratio | early | opens 60 | candidate |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| crot_m5 | extra_crot_m2p5 | ok | 60 | 89.398616961 | 0.873317679 | 0.175684579 | 4.970941015 | False | False | `p191_h320_p060_crot_m5_extra_crot_m2p5` |
| crot_m5 | extra_crot_m2p5_p1L_m2_p2L_p2 | ok | 120 | 91.430929446 | 0.875001393 | 0.188527217 | 4.641247074 | False | False | `p191_h320_p060_crot_m5_extra_crot_m2p5_p1L_m2_p2L_p2` |
| crot_m5 | extra_crot_m2p5_p1W_m2_p2W_p2 | ok | 60 | 89.671001968 | 0.868014351 | 0.160831068 | 5.397056452 | False | False | `p191_h320_p060_crot_m5_extra_crot_m2p5_p1W_m2_p2W_p2` |
| crot_m10 | p1L_m2_p2L_p2 | ok | 60 | 84.335391693 | 0.865167124 | 0.275884240 | 3.135978782 | False | False | `p191_h320_p060_crot_m10_p1L_m2_p2L_p2` |
| crot_m10 | p1W_m2_p2W_p2 | ok | 60 | 82.486292994 | 0.864839585 | 0.284671531 | 3.038026252 | False | False | `p191_h320_p060_crot_m10_p1W_m2_p2W_p2` |
| crot_m10 | p2W_p2 | ok | 60 | 83.424512821 | 0.866240357 | 0.268580467 | 3.225254485 | False | False | `p191_h320_p060_crot_m10_p2W_p2` |
| crot_m10 | p2W_p4 | ok | 60 | 85.392475191 | 0.858632651 | 0.207114694 | 4.145686789 | False | False | `p191_h320_p060_crot_m10_p2W_p4` |
| crot_m10 | p2L_p2 | ok | 60 | 84.851739766 | 0.866596078 | 0.266372684 | 3.253321869 | False | False | `p191_h320_p060_crot_m10_p2L_p2` |
| crot_m15 | p1L_m2_p2L_p2 | ok | 60 | 79.957633820 | 0.834343836 | 0.272848767 | 3.057898500 | False | False | `p191_h320_p060_crot_m15_p1L_m2_p2L_p2` |
| crot_m15 | p1W_m2_p2W_p2 | ok | 60 | 79.325457106 | 0.834132977 | 0.244222732 | 3.415460027 | False | False | `p191_h320_p060_crot_m15_p1W_m2_p2W_p2` |
| crot_m15 | p2W_p2 | ok | 60 | 80.734296682 | 0.835276927 | 0.221099365 | 3.777835039 | False | False | `p191_h320_p060_crot_m15_p2W_p2` |
| crot_m15 | p2L_p2 | ok | 60 | 80.471081940 | 0.834919751 | 0.260627272 | 3.203501098 | False | False | `p191_h320_p060_crot_m15_p2L_p2` |

## Decision rule

- If opens_p060 > 0, freeze best 60 candidate.
- If no opens_p060 but ratio improves strongly, continue with notch/helper recovery.
- If all candidates remain leakage-failed, stop p060 recovery and test coupling/gap scan.