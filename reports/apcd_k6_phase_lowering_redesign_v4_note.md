# APCD K=6 Phase-Lowering Redesign v4 Note

## Scope

This is 09-P27/P28. This stage updates dataset/coverage with 09-P26 results and designs a phase-lowering candidate pool. No FDTD was run, no lumapi call was made, and no `.fsp` file was generated in this stage.

## Why 09-P26 Did Not Fill the Gaps

`focus_zero_leakred_07` did not fill 0 deg: it stayed evidence_only and its leakage did not improve over the previous zero evidence point.

`focus_neg60_geom_04` is valuable because it is low leakage, high ratio, and early-pass, but its phase is 83.13394588891055 deg. It is a high-quality positive-phase candidate, not a -60 deg candidate.

## Coverage v4

0 deg: `evidence_only`; 60 deg: `early_covered`; 120 deg: `strong_covered`.
-60 deg: `open_gap`; -120 deg: `open_gap`; -180 deg: `open_gap`.

## Phase-Lowering Redesign Logic

The new pool uses `focus_neg60_geom_04` as the low-leakage/high-quality anchor and explores geometry-driven phase-lowering: coupled dx/dy, coordinated widths, length asymmetry, aspect-ratio inversion tendency, dimer asymmetry strengthening, pi-wrap probes, and bridges toward existing 0 deg evidence.

Pool count: 42.
Geometry pass: 42.

## Selected Candidates
- `pl_zero_bridge_04` target `0`: 0 deg bridge from focus_neg60 toward the strongest 0 deg evidence, with moderated leakage risk.
- `pl_neg60_focus_push_05` target `-60`: -60 deg phase-lowering candidate using coupled dx/dy and width coordination from the low-leakage focus anchor.
- `pl_neg120_aspect_03` target `-120`: -120 deg candidate probing controlled aspect-ratio inversion without beta-selective p2 geometry.
- `pl_pi_wrap_04` target `-180`: -180 deg pi-wrap hypothesis candidate using stronger dimer asymmetry from the focus anchor.

Recommended next step: generate YAML and run only the top-2 selected candidates first. Do not run the full pool.

## Boundaries

No FDTD, no lumapi, no `.fsp`, no K=7, no phase-ramp supercell, no TiO2/450 nm, no Micro-LED integration, no DenseNet/cVAE training, no +15 deg steering claim, and no claim that the K=6 phase-state library is complete.
