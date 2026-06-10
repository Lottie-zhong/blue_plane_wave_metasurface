# P190 h320 m120 leakage recovery plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass -120 from P189 rotation phase hits.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 12

## Candidate queue

| base | variant | candidate | changed fields | purpose |
|---|---|---|---:|---|
| crot_p30 | p2W_p2 | `p190_h320_m120_crot_p30_p2W_p2` | 1 | reduce leakage by p2 width +2 |
| crot_p30 | p2W_p4 | `p190_h320_m120_crot_p30_p2W_p4` | 1 | reduce leakage by p2 width +4 |
| crot_p30 | p2L_p2 | `p190_h320_m120_crot_p30_p2L_p2` | 1 | p2 length +2 |
| crot_p30 | p2L_p4 | `p190_h320_m120_crot_p30_p2L_p4` | 1 | p2 length +4 |
| crot_p30 | p1W_m2_p2W_p2 | `p190_h320_m120_crot_p30_p1W_m2_p2W_p2` | 2 | width contrast compensation |
| crot_p30 | p1L_m2_p2L_p2 | `p190_h320_m120_crot_p30_p1L_m2_p2L_p2` | 2 | length contrast compensation |
| crot_p25 | p2W_p2 | `p190_h320_m120_crot_p25_p2W_p2` | 1 | c25 p2 width +2 |
| crot_p25 | p2W_p4 | `p190_h320_m120_crot_p25_p2W_p4` | 1 | c25 p2 width +4 |
| crot_p25 | p2L_p2 | `p190_h320_m120_crot_p25_p2L_p2` | 1 | c25 p2 length +2 |
| crot_p25 | p1W_m2_p2W_p2 | `p190_h320_m120_crot_p25_p1W_m2_p2W_p2` | 2 | c25 width contrast compensation |
| crot_p20 | p2L_p4 | `p190_h320_m120_crot_p20_p2L_p4` | 1 | c20 push phase toward -120 with p2 length +4 |
| crot_p20 | p2W_p4 | `p190_h320_m120_crot_p20_p2W_p4` | 1 | c20 selectivity recovery with p2 width +4 |