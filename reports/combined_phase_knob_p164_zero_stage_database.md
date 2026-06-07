# P164 zero-stage database

## Scope

Stage 09 only. This manual script reads existing local `results.csv` files for zero-branch candidates and does not run FDTD or call lumapi.

No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.

## Inputs

- active-learning CSV directory: `outputs/apcd_k6_active_learning`
- candidate result root: `outputs/apcd_k6_metagrating_633nm/phase_state_candidates`
- candidate config directory: `configs/apcd_k6_phase_state_candidates`

## Summary

- candidates discovered: 6
- existing result CSVs summarized: 3
- zero-bin early-pass openings found: 0

## Notes

Missing rows are retained as `missing_result` so the workflow can be rerun after server FDTD without inventing data.
Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
