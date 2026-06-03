# APCD K=6 Focused Next-Gap Redesign v3 Note

## Scope

This is 09-P24/P25. This stage updates the dataset/coverage with the 09-P23 results and designs a focused next-gap candidate pool. No FDTD was run, no lumapi call was made, and no `.fsp` file was generated in this stage.

## 09-P23 Interpretation

`next_zero_rot_anchor_03` did not fill the 0 deg gap: it reached phase 20.788972844777305 deg, but leakage and ratio failed, so it is evidence_only rather than usable.

`next_rot_anchor_04` did not fill the -60 deg gap: its phase stayed far from -60 deg and the optical metrics failed. The -60 deg bin remains open_gap.

The top-2 rotation-assisted hypothesis was therefore not successful as a gap-closing strategy.

## Coverage v3

60 deg remains `early_covered` and 120 deg remains `strong_covered`.
0 deg is `evidence_only` because the nearest phase evidence fails early-pass thresholds.
-60, -120, and -180 deg statuses are `open_gap`, `open_gap`, and `open_gap`.

## Focused Redesign Logic

The next pool splits into zero-bin leakage reduction and negative-phase redesign. The zero branch stays near the 0 deg evidence point while reducing high-risk dy/asymmetry and moving toward low-leakage anchors. The negative branch avoids blind global-rotation continuation and instead varies internal dx/dy coupling, dimer asymmetry, aspect-ratio contrast, and controlled swap-like/pi-bin bridges.

Focused pool count: 40.
Geometry pass: 40.

## Selected Candidates

- `focus_zero_leakred_07` target `0`: Top zero-bin leakage-reduction candidate: close to next_zero evidence while reducing dy and widening p1 for leakage control.
- `focus_neg60_geom_04` target `-60`: -60 deg geometry-driven candidate using coupled dx/dy and asymmetry, not a pure global-rotation offset.
- `focus_neg120_asym_03` target `-120`: -120 deg candidate probing stronger dimer asymmetry and aspect-ratio contrast.
- `focus_pi_wrap_04` target `-180`: -180 deg pi-bin candidate using controlled swap-like bridge without beta-selective p2 geometry.

Recommended next step: generate YAML and run only the top-2 selected candidates first. Do not run the full pool.

## Boundaries

No K=7, no phase-ramp supercell, no TiO2/450 nm, no Micro-LED integration, no DenseNet/cVAE training, no +15 deg steering claim, and no claim that the K=6 phase-state library is complete.
