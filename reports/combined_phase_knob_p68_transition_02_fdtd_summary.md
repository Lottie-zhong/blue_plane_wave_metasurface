# 09-P68 transition_02 FDTD summary

## Scope

This records the completed single-dimer `cpk_mbin_transition_02` real FDTD result. This is still stage 09 phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not 450 nm / Micro-LED integration, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Result

`cpk_mbin_transition_02` is an early-pass candidate:

- phase: -176.389 deg
- nearest target bin: -180 deg
- phase error to -180 deg: 3.611 deg
- target_conversion: 0.906719
- opposite_spin_leakage: 0.129664
- conversion_to_leakage_ratio: 6.992842
- PD: 0.749776
- early-pass: True

## Interpretation

This result opens the -180 deg missing bin with early-pass quality.

It does not open the 60 deg or 0 deg bins. The previous quick `opens_missing_bin=False` interpretation was caused by checking only `[60, 0]`; the correct missing-bin set before P68 was `[-180, -60, 0, 60]`, so `cpk_mbin_transition_02` is a positive -180 deg result.

Do not enter the K=6 phase-ramp supercell yet. The -60, 0, and 60 deg bins remain missing, so the K=6 phase-state library is not complete.
