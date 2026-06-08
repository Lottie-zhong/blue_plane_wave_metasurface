# P172 fixed h233 resonance-phase note

## Scope

Stage 09 single-dimer zero-bin search only. This note does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering or Micro-LED results.

## Decision Update

- The h232 route reaches the 0-bin, but selection fails because the selectivity ratio falls below the early-pass threshold.
- The h233 `p1geom120x58` anchor preserves APCD selectivity and is only about 6 deg away from the 0-bin boundary.
- The next official search fixes `height_nm = 233` and uses integer in-plane resonance-phase tuning.
- This remains a Stage 09 single-dimer search, not a K=6 phase-ramp supercell and not a steering result.

## Target

Move the phase below 30 deg while keeping `target_conversion >= 0.5`, `opposite_spin_leakage <= 0.2`, and `conversion_to_leakage_ratio >= 6`.

Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
