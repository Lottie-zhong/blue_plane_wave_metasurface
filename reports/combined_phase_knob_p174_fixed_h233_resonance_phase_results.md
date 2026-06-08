# P174 fixed h233 resonance-phase results

## Scope

Stage 09 only. This summary reads existing local `results.csv` files from the P173 fixed-h233 candidate list and does not run FDTD or call lumapi.

No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.

## Fixed-Height Rule

The official route fixes `height_nm = 233` and uses integer in-plane resonance-phase tuning.

## Summary

- P173 candidates summarized: 12
- existing result CSVs found: 0
- zero-bin early-pass openings: 0

## Decision

- stage: 09-P175 (Stage 09 fixed-h233 resonance-phase summary only; no K=6 phase-ramp or steering claim.)
- official_height_nm: 233 (Fabrication-aware official route fixes integer height.)
- baseline_phase_deg: 36.27 (h233 p1geom120x58 baseline supplied by current decision context.)
- existing_results_count: 0 (Candidates with a local result CSV available.)
- opens_0_count: 0 (Counts only nearest_bin=0 with early_pass=true.)
- best_early_candidate:  (Best early-pass result by distance to 30 deg boundary.)
- final_decision: run_missing_real_fdtd_on_server (No real result CSVs are present, so no mechanism decision is claimed.)

Missing results are retained as `missing_result`; run real FDTD on the server before claiming any recovery result.
Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
