# P192 h320 p060 near-miss refinement plan

## Scope

- Fixed-height h320 single-dimer candidates only.
- Target: push P191 near-miss over early-pass threshold for 60 bin.
- No height scan.
- No K=6 supercell.
- No steering claim.

generated_candidates: 12

## Candidate queue

| base | variant | candidate | changed fields | purpose |
|---|---|---|---:|---|
| best | p1W_m1 | `p192_h320_p060_best_p1W_m1` | 1 | slightly increase width contrast without pushing phase too much |
| best | p2W_p1 | `p192_h320_p060_best_p2W_p1` | 1 | slightly increase p2 width; may reduce leakage but phase risk |
| best | p1W_m1_p2W_p1 | `p192_h320_p060_best_p1W_m1_p2W_p1` | 2 | balanced extra width contrast |
| best | p1W_m2_p2W_p1 | `p192_h320_p060_best_p1W_m2_p2W_p1` | 2 | stronger p1 width reduction, mild p2 width up |
| best | p1L_m1_p2L_p1 | `p192_h320_p060_best_p1L_m1_p2L_p1` | 2 | tiny length contrast compensation |
| best | p1L_m2_p2L_p2 | `p192_h320_p060_best_p1L_m2_p2L_p2` | 2 | stronger length contrast compensation |
| best | p2L_p1 | `p192_h320_p060_best_p2L_p1` | 1 | tiny p2 length up |
| best | p2L_p2 | `p192_h320_p060_best_p2L_p2` | 1 | p2 length up |
| best | extra_crot_m1_p2W_p2 | `p192_h320_p060_best_extra_crot_m1_p2W_p2` | 3 | phase safety rotation plus p2 width recovery |
| best | extra_crot_m1_p1W_m1_p2W_p2 | `p192_h320_p060_best_extra_crot_m1_p1W_m1_p2W_p2` | 4 | phase safety rotation plus width contrast |
| simple | p1W_m3_p2W_p3 | `p192_h320_p060_simple_p1W_m3_p2W_p3` | 2 | same direction as best but slightly stronger |
| c10_p2W4 | p1W_m2_p2W_p2 | `p192_h320_p060_c10_p2W4_p1W_m2_p2W_p2` | 2 | more phase margin; try width contrast |