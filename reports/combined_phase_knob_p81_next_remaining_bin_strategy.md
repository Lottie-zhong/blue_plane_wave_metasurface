# 09-P81 next remaining-bin strategy

## Evidence base

The current stage 09 early-pass bins are `[-180, -120, 120]`. The remaining missing bins are `[-60, 0, 60]`.

P75-P78 showed both lower-transition probes were early-pass duplicates near `-180`. P79 then tested six controlled variants across helper rotation, weak helper, no helper, and guarded x-period changes. All six P79 candidates also remained nearest to `-180`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Interpretation

The lower-transition branch is stable around the already covered `-180` bin under these small helper/period perturbations. The useful part of the batch is not a new phase state; it is negative evidence that the current lower-transition geometry family is unlikely to open `-60`, `0`, or `60` with small helper weakening or rotation changes.

## Recommended next step

Priority 1: stop extending this lower-transition helper-tuning family for now. It has produced eight consecutive early-pass duplicates near `-180` across P75-P79.

Priority 2: plan the next stage 09 candidate family from a different phase mechanism, using the existing coverage table as the base. The next family should explicitly target `[-60, 0, 60]` and should be limited before any real FDTD run.

Priority 3: keep the phase-state library marked incomplete. Do not enter a K=6 phase-ramp supercell or make any steering claim until all required phase bins have evidence.
