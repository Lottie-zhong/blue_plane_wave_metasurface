# APCD K=6 Next Phase-Gap Top-2 FDTD Result Note

## Scope

This is 09-P23. Only two next phase-gap candidates were run with real FDTD:

- `next_zero_rot_anchor_03`, targeting the 0 deg major gap.
- `next_rot_anchor_04`, targeting the -60 deg major gap.

The ranks 3-4 selected candidates, `next_mixed_bridge_03` and `next_pi_mixed_bridge_03`, were not run. The full 38-row next candidate pool was not run. No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, DenseNet, or cVAE work was done. This is not a +15 deg steering result and does not complete the K=6 phase-state library.

## Results

| candidate | target bin | phase deg | error deg | target conversion | leakage | ratio | PD | early pass | target bin status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `next_zero_rot_anchor_03` | 0 | 20.788972844777305 | 20.788972844777305 | 0.5125041298645276 | 0.45007533270235894 | 1.1387074399016555 | 0.06485573356783089 | False | evidence_only |
| `next_rot_anchor_04` | -60 | 157.83382648796396 | 142.16617351203604 | 0.4526296212631516 | 0.544645601389285 | 0.8310534779106825 | -0.09226738821536919 | False | open_gap |

## Interpretation

`next_zero_rot_anchor_03` reached phase 20.788972844777305 deg for target 0 deg, with wrapped error 20.788972844777305 deg. It is phase-near evidence, but leakage 0.45007533270235894 and ratio 1.1387074399016555 fail the early-pass criteria, so the 0 deg gap is not filled.

`next_rot_anchor_04` reached phase 157.83382648796396 deg for target -60 deg, with wrapped error 142.16617351203604 deg. It is not close to the target and also fails target conversion, leakage, and ratio thresholds, so the -60 deg gap remains open.

The rotation-assisted hypothesis did not fill either tested major gap in this top-2 run. The 0 deg candidate provides evidence that the phase can be pulled toward 0 deg, but leakage control is currently inadequate.

## Next Step

Do not run the full next pool. A reasonable next small step is to use the `next_zero_rot_anchor_03` evidence to design a leakage-controlled 0-deg neighborhood, or run one lower-risk bridge candidate only after explicitly deciding that the high-risk rotation-assisted path is still worth probing.
