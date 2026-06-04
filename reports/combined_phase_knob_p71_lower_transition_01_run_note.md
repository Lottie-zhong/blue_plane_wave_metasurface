# 09-P71 lower_transition_01 run note

## Scope

This note prepares only `cpk_mbin_lower_transition_01` for manual real FDTD. It remains stage 09 single-dimer phase-state refinement.

This is not a K=6 phase-ramp supercell, not a steering result, and not a complete K=6 phase-state library claim.

## Why selected

P70 selected `cpk_mbin_lower_transition_01` because it directly probes the lower-height interval between the 300 nm 120 deg plateau and the 360 nm branch that opened the -180 deg bin. The geometry keeps the period fixed and uses the conservative 70 x 120 nm weak helper at rotation 135 deg.

## Expected target bins

The intended missing-bin targets are `60 / 0`.

## Coverage before run

Current early-pass bins before this run are `[-180, -120, 120]`.

Remaining missing bins are `[-60, 0, 60]`.

## Next action

Run real FDTD manually on the server using:

```text
configs/apcd_k6_phase_state_candidates/cpk_mbin_lower_transition_01.yaml
```

Do not claim any result yet. Update coverage only after the real FDTD `results.csv` has been inspected and summarized into small committed report artifacts.
