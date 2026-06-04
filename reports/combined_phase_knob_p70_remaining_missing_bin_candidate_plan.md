# 09-P70 remaining missing-bin candidate plan

## Scope

This is a revised stage 09 single-dimer planning note after P68/P69. It does not run FDTD, does not call lumapi, does not generate `.fsp`, and does not enter a K=6 phase-ramp supercell.

## Current coverage

After P68/P69, early-pass bins are `[-180, -120, 120]`.

Remaining missing bins are `[-60, 0, 60]`.

Do not enter K=6 phase-ramp supercell yet because only 3 of 6 target phase bins are early-pass covered.

## Evidence guiding the next plan

- 300 nm / released rotation route tends toward the 120 deg plateau.
- 360 nm `cpk_mbin_transition_02` gives -176 deg early-pass.
- 380 nm `cpk_mbin_transition_01` gives -145 deg near-pass.
- 400-410 nm height-transition candidates give roughly -128/-131 deg early-pass.
- 440 nm height propagation failed badly with leakage around 0.62.
- Height >= 440 nm should not be used now.
- Period/gap expansion should not be the main route yet because `pos_gap` worsened leakage.

## Next real FDTD selection

Run at most two candidates next:

1. `cpk_mbin_lower_transition_01`
2. `cpk_mbin_lower_transition_02`

These directly test the lower-height interval between the 120 deg plateau and the newly opened -180 deg state while keeping period fixed and geometry conservative.

Stop after those two candidates and update coverage again. Do not run a broader pool, do not move to stage 10, and do not claim a complete K=6 phase-state library.
