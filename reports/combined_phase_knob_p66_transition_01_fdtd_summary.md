# 09-P66 transition_01 FDTD summary

## Scope

This report summarizes the P66 top-1 single-dimer FDTD run for `cpk_mbin_transition_01`.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Result

| candidate | target missing bins | phase deg | nearest bin | phase error | best missing target | missing error | target | leakage | ratio | PD | early pass | near pass | informative |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| cpk_mbin_transition_01 | -60 / 0 | -145.401 | -120 | 25.401 | -60 | 85.401 | 0.889380 | 0.232271 | 3.8291 | 0.585841 | False | True | True |

## Interpretation

`cpk_mbin_transition_01` is informative but does not open a new missing phase bin.

Compared with the P63 high-height candidate `cpk_mbin_hprop_01`, the 380 nm transition candidate avoids the catastrophic leakage collapse. The opposite-spin leakage is about 0.232 rather than about 0.620, and the conversion-to-leakage ratio recovers to about 3.83.

However, the phase lands at about -145.4 deg. Its nearest K=6 target bin is still -120 deg, with about 25.4 deg phase error. It is far from the intended missing -60 / 0 deg targets.

Therefore, this result should be recorded as near-pass transition evidence, not as new bin coverage.

## Decision

Do not claim that -60 deg or 0 deg has been opened.

Do not enter K=6 phase-ramp supercell yet.

Recommended next action: commit this P66 top-1 result, then decide whether to run `cpk_mbin_transition_02` or first perform a small P67 coverage/planning update. If FDTD budget is tight, prefer a coverage/planning update before running the second transition candidate.
