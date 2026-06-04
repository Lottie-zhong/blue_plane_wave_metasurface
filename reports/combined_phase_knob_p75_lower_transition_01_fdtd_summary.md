# 09-P75 lower_transition_01 FDTD summary

## Scope

This is a stage 09 single-dimer lower-transition result summary from the compact SSH remote runner. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

No K=7, 450 nm/TiO2, Micro-LED integration, or ML claim is made.

## Run provenance

Candidate run on server:

```text
cpk_mbin_lower_transition_01
```

Server GitHub pull was blocked by a TLS handshake failure, so the required runner/config files were synced over SSH before the run. The real FDTD run was still executed on the server with `configs/runtime.yaml`.

## Compact metrics

| candidate | phase deg | nearest bin | best missing bin | target conversion | leakage | ratio | PD | early pass | near pass | opens missing bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_mbin_lower_transition_01` | 179.4676618610021 | -180 | 60 | 0.9151477133673995 | 0.0846264722112817 | 10.813965056617185 | 0.830708827188383 | True | False | False |

## Interpretation

`cpk_mbin_lower_transition_01` is an early-pass result, but its nearest K=6 target bin is `-180`, which was already covered before this run. It does not open any remaining missing bin from `[-60, 0, 60]`.

Per the P75/P76 decision rule, `cpk_mbin_lower_transition_02` should be run next and then the task should stop after that candidate.

Raw server `results.csv`, `summary.md`, `.fsp`, `pre_run` files, `.npy`, and large outputs are not committed.
