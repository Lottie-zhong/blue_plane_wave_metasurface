# P165 zero-cliff recovery candidate plan

## Scope

Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim steering.

## Design Basis

- current early-pass rule: target >= 0.5, leakage <= 0.2, ratio >= 6
- bins: [-180, -120, -60, 0, 60, 120]
- current coverage: [-180, -120, -60, 60, 120]
- missing bin: [0]
- zero branch: `aggr_lhs_retention_dy_05 -> p1geom120x58`
- cliff: h232.5 remains 60-bin early-pass; h232.4 enters 0-bin but fails selectivity

## Candidate Groups

- Group A ultra-fine height scan: 6 candidates
- Group B mild p1 notch check: 3 candidates
- Group C p1 minor compensation: 3 candidates

## Notch Schema Check

Existing `notched_rectangle` schema was found in the repo, so Group B was generated using that schema.

## Next Step

Run real FDTD manually on the server only after reviewing the YAMLs. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.
