# APCD K=6 Helper Plateau and Combined Phase-Knob Plan

## Scope

This is 09-P48/P50. It diagnoses the v8 helper phase plateau and plans a combined phase-knob v9 candidate pool.

No FDTD, lumapi, `.fsp`, YAML generation, full old-pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## Plateau Diagnosis

The highest early-pass helper phase is 131.6650 deg. Helper prototype/refinement results show a low-leakage plateau around 120-132 deg.

- Square/near-square helpers keep leakage low but stay near 116-121 deg.
- Weak anisotropic helpers are the best helper-only phase-push family but saturate near 128-132 deg.
- Gap-fixed phase-delay helpers preserve low leakage but did not push phase beyond anisotropic helpers.
- 0 deg, -60 deg, -120 deg, and -180 deg are still not covered by usable phase states.

## Why Combined Knobs

The next step needs coupled phase knobs because helper-only local geometry appears to preserve amplitude but offers limited phase span. Released rotations may perturb the complex amplitude direction; height and period are propagation/material phase scouts rather than supercell or steering tests.

## v9 Pool

Pool rows: 45
Geometry pass: 33/45

## Selected Not Run

| rank | candidate | family | target | priority |
|---:|---|---|---:|---|
| 1 | `cpk_rot_release_02` | `helper_plus_released_rotation` | -180 | top2_next_run |
| 2 | `cpk_height_prop_05` | `helper_plus_height_propagation` | -180 | top2_next_run |
| 3 | `cpk_period_phase_04` | `helper_plus_period_phase` | -180 | backup_selected_not_run |
| 4 | `cpk_position_scout_01` | `helper_position_phase_scout` | -180 | backup_selected_not_run |
| 5 | `cpk_strong_delay_07` | `strong_but_safe_phase_delay_helper` | -180 | backup_selected_not_run |

Recommended next run top-2: `cpk_rot_release_02` and `cpk_height_prop_05`.
