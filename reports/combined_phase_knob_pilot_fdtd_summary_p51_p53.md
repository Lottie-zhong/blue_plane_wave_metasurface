# Combined phase-knob pilot FDTD summary, 09-P51/P53

## Scope

- Stage: 633 nm c-Si/Al2O3 plane-wave single APCD dimer phase-state search.
- These are single periodic unit-cell FDTD results, not K=6 phase-ramp supercell results.
- No K7, no 450 nm scaling, no Micro-LED integration, no +15 deg steering claim, no complete K=6 library claim.

## Results

| candidate | family | h nm | period nm | target conv. | leakage | ratio | PD | phase deg | early-pass | interpretation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| cpk_rot_release_02 | helper_plus_released_rotation | 300 | 340 | 0.9365 | 0.0674 | 13.8897 | 0.8657 | 120.26 | True | strong early-pass but still near 120 deg plateau; rotation release did not open negative phase |
| cpk_height_prop_05 | helper_plus_height_propagation | 420 | 340 | 0.9278 | 0.2058 | 4.5091 | 0.6370 | -109.64 | False | negative-phase evidence; leakage slightly too high; refine height/helper for -120-like state |
| cpk_period_phase_04 | helper_plus_period_phase | 300 | 430 | 0.7501 | 0.0941 | 7.9710 | 0.7771 | 122.78 | True | early-pass but still near 120 deg plateau; period knob did not open negative phase |

## Main conclusions

1. `cpk_rot_release_02` is a strong early-pass candidate but remains near the 120 deg plateau.
2. `cpk_period_phase_04` is also early-pass, but period expansion to 430 nm did not open a negative-phase state.
3. `cpk_height_prop_05` is the most physically informative result: it moves the target-channel phase to about -110 deg, but leakage is slightly above the early-pass threshold and the ratio is below 6.
4. The next v10 design should focus on height/material propagation phase with leakage recovery, rather than simply expanding period or small released rotations.

## Recommended next design direction

- Use `cpk_height_prop_05` as the anchor for a local refinement around height/material propagation phase.
- Sweep height around the negative-phase transition region while weakening or repositioning the helper to reduce leakage.
- Treat the current result as evidence toward a possible -120 deg phase state, not as a solved -180 deg state.
- Keep the claims limited to single-cell phase-state search until a K=6 phase-ramp supercell is actually simulated.
