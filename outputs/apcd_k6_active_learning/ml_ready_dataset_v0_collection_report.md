# APCD K=6 ML-Ready Dataset v0 Collection Report

Scope: 09-P1 collection only. No new FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No new candidate pool was generated. This is not a steering result.

Dataset rows: 10
Included variants: baseline, p1L_m10, p1L_m5, p1L_p5, p1L_p10, p1W_m5, p1W_p5, p2W_m10, p2W_m5, p2W_p10
Missing variants: p2L_m5, p2L_p5, p2W_p5
Phase range deg: 103.9756847 to 124.130057004
Overall early pass count: 8
Overall early pass variants: baseline, p1L_m10, p1L_m5, p1L_p5, p1W_m5, p1W_p5, p2W_m5, p2W_p10

Early pass thresholds:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

This dataset is only suitable for initial surrogate/data plumbing. It is too small to train a reliable model.
