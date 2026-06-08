# P169 integer zero-recovery candidate plan

## Scope

Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering.

## Fabrication-Aware Rule

- Official P169 candidates use `height_nm = 232`.
- Official P169 geometry parameters are integer nm values only.
- The h232.49 to h232.48 cliff remains diagnostic history only.
- Further sub-nm cliff scans are stopped for the main route.

## Candidate Groups

- integer p1 length/width compensation: 6 candidates
- integer mild p1 notch compensation: 3 candidates

## Notch Schema Check

Existing `notched_rectangle` schema was found in the repo, so integer notch candidates were generated using that schema.

## Next Step

Review these YAMLs, then run real FDTD manually on the server if approved. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.
