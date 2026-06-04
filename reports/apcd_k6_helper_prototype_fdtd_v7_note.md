# APCD K=6 Helper Prototype FDTD v7 Note

## Scope

This is 09-P42/P44. It tests four physics-guided helper prototype records with fabrication-friendly dielectric pillar helpers.

The helper is a third standalone weak auxiliary phase shifter. It is not another APCD dimer and not half of another APCD pair. APCD core pillar1/pillar2 remains responsible for spin-selective conversion; pillar3 helper only probes weak dielectric loading, phase pulling, or phase-delay behavior.

No full 48-row helper v2 pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper shape, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## Geometry Validation

Prototype records: 4
Geometry pass: 3/4

| candidate | target | same-cell gap | periodic gap | recommended | notes |
|---|---:|---:|---:|---|---|
| `h2_square_load_01` | 0 | 75.6248394357237 | 75.6248394357237 | True | geometry/gap/sanity validation passed; optical response unknown |
| `h2_nearsquare_load_02` | 0 | 68.28791499243114 | 68.28791499243114 | True | geometry/gap/sanity validation passed; optical response unknown |
| `h2_weak_aniso_03` | -60 | 52.26564326784529 | 52.26564326784528 | True | geometry/gap/sanity validation passed; optical response unknown |
| `h2_phase_delay_04` | -180 | 47.81855425478244 | 47.818554254782434 | False | same-cell gap below 50 nm prototype threshold; periodic-image gap below 50 nm prototype threshold |

YAML configs were generated only for geometry-passing candidates.

## FDTD Results

Actual run candidates: h2_square_load_01, h2_nearsquare_load_02, h2_weak_aniso_03
Geometry-failed not-run candidates: h2_phase_delay_04

| candidate | helper type | target | phase | leakage | ratio | early pass | target status |
|---|---|---:|---:|---:|---:|---|---|
| `h2_square_load_01` | `low-leakage loading helper` | 0 | 115.7231380707874 | 0.040077604335282485 | 24.239301126374972 | True | usable_but_not_target |
| `h2_nearsquare_load_02` | `near-square loading helper` | 0 | 120.7343925288726 | 0.04310696211211005 | 22.377148545287728 | True | usable_but_not_target |
| `h2_weak_aniso_03` | `weak anisotropic nanofin helper` | -60 | 128.67545189753866 | 0.053721931132566875 | 17.923653091325708 | True | usable_but_not_target |
| `h2_phase_delay_04` | `phase-delay nanofin helper` | -180 |  |  |  | False | not_run_geometry_failed |

Interpretation: the three geometry-passing prototypes preserved low leakage and early-pass quality, but they pulled the phase to positive 115-129 deg rather than filling 0 deg or -60 deg. This expands the high-positive usable phase evidence beyond v6, but it does not close the remaining major target gaps.

## Dataset and Coverage v7

Dataset v7 rows: 33

| bin deg | status |
|---:|---|
| 0.0 | evidence_only |
| 60.0 | early_covered |
| 120.0 | strong_covered |
| -180.0 | evidence_only |
| -120.0 | open_gap |
| -60.0 | open_gap |

## Next Step

Use these prototype results to decide whether weak helper loading is worth a small neighborhood follow-up. Do not assemble a phase-ramp supercell until all K=6 bins have usable phase states.
