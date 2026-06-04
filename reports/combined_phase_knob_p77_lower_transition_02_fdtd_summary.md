# 09-P77 lower_transition_02 FDTD summary

## Scope

This is a stage 09 single-dimer lower-transition result summary from the compact SSH remote runner. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

No K=7, 450 nm/TiO2, Micro-LED integration, or ML claim is made.

## Compact metrics

| candidate | phase deg | nearest bin | best missing bin | target conversion | leakage | ratio | PD | early pass | near pass | opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_mbin_lower_transition_02` | 161.07512957025864 | -180 | 60 | 0.9549044240313563 | 0.03636021546774067 | 26.26234228048785 | 0.926638731940287 | True | False | False |

## Interpretation

`cpk_mbin_lower_transition_02` is an early-pass result, but its nearest K=6 target bin is `-180`, which was already covered before this run. It does not open any remaining missing bin from `[-60, 0, 60]`.

Per the P75/P76 task rule, candidate execution stops after `cpk_mbin_lower_transition_02`. No additional candidates or broader pools were run.

Raw server `results.csv`, `summary.md`, `.fsp`, `pre_run` files, `.npy`, and large outputs are not committed.
