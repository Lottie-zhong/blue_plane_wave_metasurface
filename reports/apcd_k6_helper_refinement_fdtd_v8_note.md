# APCD K=6 Helper Refinement FDTD v8 Note

## Scope

This is 09-P45/P47. It refines physics-guided standalone helper prototypes toward high-positive / pi-near phase while preserving low leakage.

No full helper v2 pool, full helper refinement pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## Starting Point

- Square/near-square helpers stayed low leakage but near 116-121 deg.
- `h2_weak_aniso_03` is the best current helper anchor: phase 128.6755 deg with low leakage.
- `h2_phase_delay_04` failed geometry only, so phase-delay was retried with safer reduced-size/gap-fixed helpers.

## Geometry and Selection

Geometry pass: 16/16

| rank | candidate | family | target | reason |
|---:|---|---|---:|---|
| 1 | `hr_aniso_push_05` | `aniso_helper_phase_push` | -180 | phase-push candidate close to h2_weak_aniso_03 but with stronger helper width and 135 deg rotation. |
| 2 | `hr_aniso_push_08` | `aniso_helper_phase_push` | -180 | second anisotropic phase-push candidate testing larger length with safer 110 nm width. |
| 3 | `hr_phase_delay_03` | `phase_delay_gap_fixed` | -180 | geometry-safe retry of h2_phase_delay_04 phase-delay logic with >=55 nm gaps. |
| 4 | `hr_lowleak_control_02` | `lowleak_anchor_control` | 120 | low-leakage near-square control for comparing phase movement against h2_square/nearsquare prototypes. |

## FDTD Results

| candidate | family | target | phase | leakage | ratio | early pass | status |
|---|---|---:|---:|---:|---:|---|---|
| `hr_aniso_push_05` | `aniso_helper_phase_push` | -180 | 128.72874773442857 | 0.1200857911932035 | 8.045695404886663 | True | usable_but_not_target |
| `hr_aniso_push_08` | `aniso_helper_phase_push` | -180 | 131.6649840315141 | 0.07909108118126469 | 12.158022572100036 | True | usable_but_not_target |
| `hr_phase_delay_03` | `phase_delay_gap_fixed` | -180 | 128.72715476002463 | 0.056781903980201914 | 17.01161162869423 | True | usable_but_not_target |
| `hr_lowleak_control_02` | `lowleak_anchor_control` | 120 | 120.69178549380604 | 0.04396643352483241 | 22.090892311344128 | True | strong_covered |

Most promising helper type: hr_aniso_push_08 (aniso_helper_phase_push), phase=131.6649840315141 deg, leakage=0.07909108118126469

Interpretation: v8 opened a modest high-positive usable extension beyond `h2_weak_aniso_03` (128.6755 deg) to about 131.665 deg, while keeping leakage low. It did not reach the 150-180 deg / pi-near region and does not cover -180 deg.

## Coverage v8

Dataset v8 rows: 37

| bin deg | status |
|---:|---|
| 0.0 | evidence_only |
| 60.0 | early_covered |
| 120.0 | strong_covered |
| -180.0 | evidence_only |
| -120.0 | open_gap |
| -60.0 | open_gap |

Open or incomplete targets remain 0 deg, -60 deg, -120 deg, and possibly -180 deg unless v8 produces an early-pass wrapped phase within threshold.
