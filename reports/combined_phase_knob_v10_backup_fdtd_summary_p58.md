# 09-P58 v10 backup FDTD summary

## Scope

This report summarizes the first v10 backup FDTD run after the 09-P57 top2 summary.

This is still a single-dimer phase-state refinement step. It is not a K=6 phase-ramp supercell, not a K=7 result, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, not a +15 degree steering result, and not a complete K=6 phase-state library.

## Compared candidates

| candidate | family | height nm | period nm | target conversion | leakage | ratio | PD | phase deg | early pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| cpk_refine_htrans_04 | height_transition_sweep | 410.0 | 340.0 | 0.963606 | 0.019658 | 49.0189 | 0.960015 | -131.308 | True |
| cpk_refine_weak_helper_03 | weak_helper_leakage_recovery | 420.0 | 340.0 | 0.920946 | 0.100133 | 9.1972 | 0.803868 | -115.182 | True |
| cpk_refine_pos_gap_01 | helper_position_gap_recovery | 420.0 | 360.0 | 0.895544 | 0.235317 | 3.8057 | 0.583827 | -116.536 | False |


## Interpretation

- `cpk_refine_pos_gap_01` gives a phase close to -120 deg, but it fails early-pass because leakage is above 0.2 and the conversion-to-leakage ratio is below 6.
- This suggests that simply expanding the period / helper-position gap can improve phase placement, but may weaken APCD-like polarization selectivity.
- `cpk_refine_htrans_04` remains the strongest negative-phase candidate by leakage suppression and ratio.
- `cpk_refine_weak_helper_03` remains the better phase-near--120 early-pass comparison candidate.

## Current conclusion

Do not replace the P57 top2 with `cpk_refine_pos_gap_01`. Keep it as negative/contrast evidence for the v10 refinement pool. The next refinement should prioritize height-transition and weak-helper local tuning rather than period/gap expansion alone.
