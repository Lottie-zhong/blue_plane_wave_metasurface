# APCD K=6 v6 Pilot Failure Diagnosis Summary

Scope: 09-P39/P41 diagnosis only. No FDTD/lumapi/.fsp/YAML/training.

Current usable phase span: 72.24132809604521 to 118.07875127181353 deg.
Weak-helper v1 geometry pass: 4/10.

Failure modes:
- `ng_zero_rot_release_07`: released_rotation_zero_failed_leakage_and_phase_far
- `ng_neg60_dxdy_release_08`: released_dxdy_neg60_failed_leakage_and_phase_far
- `wh_zero_aux_phase_01`: weak_helper_failed_leakage_ratio_and_insufficient_phase_shift

Conclusion: released rotations, released dx/dy, and the first weak-helper pilot did not open a new usable phase region. The helper v1 pool failed mainly because center/near-core helper positions caused same-cell overlap or too-small gaps.
