# 09-P63 top-1 missing-bin FDTD summary

## Scope

This report summarizes the P63 top-1 single-dimer FDTD run for `cpk_mbin_hprop_01`.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Result

| candidate | target missing bin | phase deg | nearest bin | phase error | target | leakage | ratio | PD | early pass | near pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| cpk_mbin_hprop_01 | -180 | -90.135 | -120 | 29.865 | 0.918170 | 0.619701 | 1.4816 | 0.194080 | False | False |

## Interpretation

`cpk_mbin_hprop_01` is a clear negative result.

Increasing the height from the robust 400-410 nm range to 440 nm did not push the phase toward the missing -180 deg bin. Instead, the target-channel phase moved to about -90 deg, while opposite-spin leakage increased sharply to about 0.62. The conversion-to-leakage ratio dropped to about 1.48 and PD dropped to about 0.19.

This means the high-height propagation phase push breaks APCD-like selectivity rather than opening a useful -180 deg phase state.

## Decision

Do not run `cpk_mbin_hprop_02` as the immediate next candidate, because it pushes height even further and is likely to worsen leakage.

Do not immediately jump to K=6 phase-ramp supercell.

Recommended next action: commit this negative evidence, then perform a P64 coverage/planning update before choosing whether `cpk_mbin_period_01` is worth running or whether a new missing-bin strategy is needed.
