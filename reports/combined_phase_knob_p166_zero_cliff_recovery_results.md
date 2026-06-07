# P166 zero-cliff recovery results

## Scope

Stage 09 only. This summary reads existing local `results.csv` files from the P165 candidate list and does not run FDTD or call lumapi.

No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.

## Summary

- P165 candidates summarized: 12
- existing result CSVs found: 0
- zero-bin early-pass openings: 0

## Decision

- stage: 09-P167 (Stage 09 zero-cliff recovery summary only; no K=6 phase-ramp or steering claim.)
- existing_results_count: 0 (Candidates with a local result CSV available.)
- opens_0_count: 0 (Counts only nearest_bin=0 with early_pass=true.)
- early_pass_count: 0 (Uses target>=0.5, leakage<=0.2, ratio>=6.)
- best_available_candidate:  (Best among existing results by opens_0, early_pass, phase error to 0, and ratio.)
- next_action: run_missing_real_fdtd_on_server (Missing results are not fabricated by this workflow.)

Missing results are retained as `missing_result`; run real FDTD on the server before claiming any recovery result.
Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
