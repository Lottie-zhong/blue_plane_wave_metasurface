# P176 h232 zero coupled recovery plan

## Scope

Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering or Micro-LED results.

## Design Basis

- coverage before this planning step: [-180, -120, -60, 60, 120]; missing [0]
- h232 p1geom120x58 is already a 0-bin phase-hit but fails selectivity ratio
- target: recover leakage/ratio while keeping phase within +/-30 deg
- p2 width/size-up is the primary selection-recovery knob using the h232 phase budget
- p2 74x136 is the length-down plus width-up compensation control
- p1 119x58 is a weak secondary trim, not the primary phase knob
- no notch candidates are generated in the first P176 batch
- all official candidates use integer-nm geometry and `height_nm = 232`

## Candidate Count

- planned YAML candidates: 6
- minimum same-cell gap nm: 100.712
- minimum periodic-image gap nm: 78.5907
- minimum gap threshold nm: 50

## Next Step

Review these YAMLs, then run real FDTD manually on the server if approved. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.
