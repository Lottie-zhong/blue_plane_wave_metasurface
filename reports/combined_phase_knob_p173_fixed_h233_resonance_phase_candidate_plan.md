# P173 fixed h233 resonance-phase candidate plan

## Scope

Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering.

## Design Basis

- h232 route reaches the 0-bin but fails selection.
- h233 p1geom120x58 preserves selection and is about 6 deg from the 0-bin boundary.
- official route fixes `height_nm = 233`.
- all official P173 geometry parameters are integer nm values.
- target: move phase below 30 deg while keeping target >= 0.5, leakage <= 0.2, ratio >= 6.

## Candidate Groups

- Group A p2 dynamic-resonance phase scan: 6 candidates
- Group B p1 minor compensation at fixed h233: 3 candidates
- Group C mild notch at fixed h233: 3 candidates

## Notch Schema Check

Existing `notched_rectangle` schema was found in the repo, so Group C was generated using that schema.

## Next Step

Review these YAMLs, then run real FDTD manually on the server if approved. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.
