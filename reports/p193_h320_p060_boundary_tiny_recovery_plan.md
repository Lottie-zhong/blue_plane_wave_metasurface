# P193 h320 p060 boundary tiny recovery plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: recover early-pass 60 from P192 near-boundary candidates.
- Tiny changes only.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 8

## Candidate queue

| base | variant | candidate | changed fields | purpose |
|---|---|---|---:|---|
| b_ratio | crot_m0p25 | `p193_h320_p060_b_ratio_crot_m0p25` | 2 | pull 90.18 deg just below 90 |
| b_ratio | crot_m0p5 | `p193_h320_p060_b_ratio_crot_m0p5` | 2 | slightly stronger phase rollback |
| b_ratio | crot_m0p25_p2W_p0p5 | `p193_h320_p060_b_ratio_crot_m0p25_p2W_p0p5` | 3 | phase rollback plus tiny p2 width leakage recovery |
| b_60 | p2W_p0p5 | `p193_h320_p060_b_60_p2W_p0p5` | 1 | tiny p2 width recovery while staying 60-bin |
| b_60 | p2W_p1 | `p193_h320_p060_b_60_p2W_p1` | 1 | p2 width recovery |
| b_60 | p1W_m0p5_p2W_p0p5 | `p193_h320_p060_b_60_p1W_m0p5_p2W_p0p5` | 2 | tiny balanced width contrast |
| b_60 | p1W_m0p5 | `p193_h320_p060_b_60_p1W_m0p5` | 1 | tiny p1 width reduction |
| b_60low | p2W_p1 | `p193_h320_p060_b_60low_p2W_p1` | 1 | lower phase 60-bin candidate plus p2 width recovery |