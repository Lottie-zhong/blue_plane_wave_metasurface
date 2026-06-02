# APCD K=6 Aggressive Phase-Gap Candidate Pool v1 Summary

Scope: 09-P17 aggressive candidate pool scaffold only. No FDTD was run. No lumapi call was made. No model was trained. No `.fsp` file was exported. This is not a steering result.

Candidate count: 32
Candidate IDs unique: True
internal_dy range nm: 18 to 36
p1_length range nm: 110 to 130
p2_width range nm: 130 to 145

Family distribution:

- `dy_sweep_near_lhs`: 5
- `lhs_like_leakage_control_p1w`: 6
- `lhs_like_p2w_trim`: 5
- `lhs_like_retention_high_dy`: 6
- `lhs_to_fine_bridge_aggressive`: 5
- `mixed_aggressive_but_safe`: 5

Design target: return closer to `doe_lhs_like_01` phase-shift geometry while retaining selected leakage-control anchors from P16 and p1w_dx fine candidates.
