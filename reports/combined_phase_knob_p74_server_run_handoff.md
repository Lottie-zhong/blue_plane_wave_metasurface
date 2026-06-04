# 09-P74 server run handoff

## Scope

This is a stage 09 handoff note only. No FDTD or lumapi run was executed here, and no metrics are claimed.

Do not enter stage 10, do not build a K=6 phase-ramp supercell, and do not make a steering claim.

## Server run order

Run `cpk_mbin_lower_transition_01` first on the server.

Do not run `cpk_mbin_lower_transition_02` until `cpk_mbin_lower_transition_01` has a real `results.csv` and has been summarized.

## Coverage context

Current early-pass bins before the server run:

```text
[-180, -120, 120]
```

Remaining missing bins:

```text
[-60, 0, 60]
```

## Summarizer hook

After the server produces:

```text
outputs/apcd_k6_metagrating_633nm/phase_state_candidates/cpk_mbin_lower_transition_01/results.csv
```

run the P73 summarizer:

```text
py scripts/69_summarize_apcd_lower_transition_result.py --candidate-id cpk_mbin_lower_transition_01 --coverage-base outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p69.csv --stage-label 09-P74
```

The summarizer should create only small summary artifacts. Do not commit raw `results.csv`, `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
