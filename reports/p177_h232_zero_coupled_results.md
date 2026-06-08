# P177 h232 zero coupled recovery results

## Scope

Stage 09 only. This summary reads existing local `results.csv` files from the P176 candidate list and does not run FDTD or call lumapi.

No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.

## H232 Coupled Recovery Rule

The workflow starts from the h232 0-bin phase-hit and uses integer p2 coupled compensation to recover leakage/ratio.

## Summary

- P176 candidates summarized: 6
- existing result CSVs found: 0
- zero-bin early-pass openings: 0

## Decision

- stage: 09-P178 (Stage 09 h232 zero coupled summary only; no K=6 phase-ramp or steering claim.)
- baseline_phase_deg: 19.94 (h232 p1geom120x58 baseline supplied by current decision context.)
- baseline_leakage: 0.179 (Leakage improvement is measured against this baseline.)
- existing_results_count: 0 (Candidates with a local result CSV available.)
- opens_0_count: 0 (Counts only nearest_bin=0 with early_pass=true.)
- zero_bin_leakage_improved_count: 0 (Counts nearest_bin=0 candidates with leakage below the h232 baseline.)
- final_decision: run_missing_real_fdtd_on_server (No real result CSVs are present, so no mechanism decision is claimed.)

Missing results are retained as `missing_result`; run real FDTD on the server before claiming any recovery result.
Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
