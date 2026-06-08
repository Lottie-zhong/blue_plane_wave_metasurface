# P170 integer zero-recovery results

## Scope

Stage 09 only. This summary reads existing local `results.csv` files from the P169 integer candidate list and does not run FDTD or call lumapi.

No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.

## Fabrication-Aware Rule

The official route fixes `height_nm = 232` and uses integer-nm geometry. Sub-nm cliff scans remain diagnostic history only.

## Summary

- P169 candidates summarized: 9
- existing result CSVs found: 0
- zero-bin early-pass openings: 0

## Decision

- stage: 09-P171 (Stage 09 integer zero-recovery summary only; no K=6 phase-ramp or steering claim.)
- official_height_nm: 232 (Fabrication-aware official route fixes integer height.)
- existing_results_count: 0 (Candidates with a local result CSV available.)
- opens_0_count: 0 (Counts only nearest_bin=0 with early_pass=true.)
- early_pass_count: 0 (Uses target>=0.5, leakage<=0.2, ratio>=6.)
- best_available_candidate:  (Best among existing results by opens_0, early_pass, phase error to 0, and ratio.)
- next_action: run_missing_real_fdtd_on_server (Missing results are not fabricated by this workflow.)

Missing results are retained as `missing_result`; run real FDTD on the server before claiming any recovery result.
Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
