# P193 h320 p060 boundary tiny recovery results

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass 60 from P192 near-boundary candidates.
- No K=6 supercell run.
- No +15 deg steering claim.

## Summary

- tested: 8
- valid: 8
- early_pass: 0
- opens_p060: 0
- best_candidate: `p193_h320_p060_b_ratio_crot_m0p25_p2W_p0p5`
- best_ratio: 5.784397715
- best_p060_candidate: ``
- best_p060_ratio: 

## Candidate results

| base | variant | status | nearest bin | phase | target | leakage | ratio | early | opens 60 | candidate |
|---|---|---|---:|---:|---:|---:|---:|---|---|---|
| b_ratio | crot_m0p25 | ok | 60 | 89.987099518 | 0.866073780 | 0.152960405 | 5.662078247 | False | False | `p193_h320_p060_b_ratio_crot_m0p25` |
| b_ratio | crot_m0p5 | ok | 60 | 89.797030100 | 0.865269473 | 0.153856828 | 5.623861382 | False | False | `p193_h320_p060_b_ratio_crot_m0p5` |
| b_ratio | crot_m0p25_p2W_p0p5 | ok | 120 | 90.226732929 | 0.865662050 | 0.149654656 | 5.784397715 | False | False | `p193_h320_p060_b_ratio_crot_m0p25_p2W_p0p5` |
| b_60 | p2W_p0p5 | ok | 120 | 90.023058874 | 0.865636757 | 0.153600551 | 5.635635741 | False | False | `p193_h320_p060_b_60_p2W_p0p5` |
| b_60 | p2W_p1 | ok | 120 | 90.247762931 | 0.865295087 | 0.150798321 | 5.738094954 | False | False | `p193_h320_p060_b_60_p2W_p1` |
| b_60 | p1W_m0p5_p2W_p0p5 | ok | 60 | 89.801751614 | 0.865636514 | 0.155680396 | 5.560343723 | False | False | `p193_h320_p060_b_60_p1W_m0p5_p2W_p0p5` |
| b_60 | p1W_m0p5 | ok | 60 | 89.562088142 | 0.866051233 | 0.159207006 | 5.439780912 | False | False | `p193_h320_p060_b_60_p1W_m0p5` |
| b_60low | p2W_p1 | ok | 60 | 89.783707346 | 0.866060788 | 0.157038338 | 5.514964038 | False | False | `p193_h320_p060_b_60low_p2W_p1` |

## Decision rule

- If opens_p060 > 0, freeze best 60 candidate.
- If no opens_p060, stop p060 tiny recovery for now.
- Then switch to 0-bin or -60-bin mechanism search at h320.
- Do not proceed to K=6 until fixed-height six-bin coverage exists.