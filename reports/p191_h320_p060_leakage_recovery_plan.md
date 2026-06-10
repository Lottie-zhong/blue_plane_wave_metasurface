# P191 h320 p060 leakage recovery plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass 60 from P189 p060 phase hits.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 12

## Candidate queue

| base | variant | candidate | changed fields | purpose |
|---|---|---|---:|---|
| crot_m5 | extra_crot_m2p5 | `p191_h320_p060_crot_m5_extra_crot_m2p5` | 2 | small extra rotation: push phase into 60-bin |
| crot_m5 | extra_crot_m2p5_p1L_m2_p2L_p2 | `p191_h320_p060_crot_m5_extra_crot_m2p5_p1L_m2_p2L_p2` | 4 | extra rot plus length contrast recovery |
| crot_m5 | extra_crot_m2p5_p1W_m2_p2W_p2 | `p191_h320_p060_crot_m5_extra_crot_m2p5_p1W_m2_p2W_p2` | 4 | extra rot plus width contrast recovery |
| crot_m10 | p1L_m2_p2L_p2 | `p191_h320_p060_crot_m10_p1L_m2_p2L_p2` | 2 | 60-bin phase-hit, length contrast recovery |
| crot_m10 | p1W_m2_p2W_p2 | `p191_h320_p060_crot_m10_p1W_m2_p2W_p2` | 2 | 60-bin phase-hit, width contrast recovery |
| crot_m10 | p2W_p2 | `p191_h320_p060_crot_m10_p2W_p2` | 1 | 60-bin phase-hit, p2 width +2 |
| crot_m10 | p2W_p4 | `p191_h320_p060_crot_m10_p2W_p4` | 1 | 60-bin phase-hit, p2 width +4 |
| crot_m10 | p2L_p2 | `p191_h320_p060_crot_m10_p2L_p2` | 1 | 60-bin phase-hit, p2 length +2 |
| crot_m15 | p1L_m2_p2L_p2 | `p191_h320_p060_crot_m15_p1L_m2_p2L_p2` | 2 | deeper 60-bin, length contrast recovery |
| crot_m15 | p1W_m2_p2W_p2 | `p191_h320_p060_crot_m15_p1W_m2_p2W_p2` | 2 | deeper 60-bin, width contrast recovery |
| crot_m15 | p2W_p2 | `p191_h320_p060_crot_m15_p2W_p2` | 1 | deeper 60-bin, p2 width +2 |
| crot_m15 | p2L_p2 | `p191_h320_p060_crot_m15_p2L_p2` | 1 | deeper 60-bin, p2 length +2 |