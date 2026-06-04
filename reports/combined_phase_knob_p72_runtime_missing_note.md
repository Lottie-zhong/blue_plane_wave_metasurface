# 09-P72 runtime missing note

## Scope

This is stage 09 only. No stage 10, K=6 phase-ramp supercell, steering claim, K=7, 450 nm/TiO2, Micro-LED integration, or ML claim is made.

## Runtime check

`configs/runtime.yaml` was not found in this local workspace.

Because the runtime file is missing, `cpk_mbin_lower_transition_01` was not run with FDTD here. No `results.csv` was parsed, and no phase, leakage, ratio, early-pass, near-pass, or missing-bin-opening result is claimed.

## Candidate waiting for server run

Prepared candidate config:

```text
configs/apcd_k6_phase_state_candidates/cpk_mbin_lower_transition_01.yaml
```

Current coverage before the run:

```text
early-pass bins: [-180, -120, 120]
remaining missing bins: [-60, 0, 60]
```

## Required next action

Run real FDTD manually on the server after providing a valid `configs/runtime.yaml`:

```text
py scripts/13_run_apcd_single_dimer.py --config configs/apcd_k6_phase_state_candidates/cpk_mbin_lower_transition_01.yaml --runtime configs/runtime.yaml
```

After the server run, inspect the raw candidate `results.csv` and summarize it into small committed artifacts only. Do not commit raw `phase_state_candidates/results.csv`, `summary.md`, `.fsp`, `pre_run` files, `.npy`, or other large outputs.
