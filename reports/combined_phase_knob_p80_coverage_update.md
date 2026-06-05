# 09-P80 coverage update after remaining-bin batch

## Scope

This is a stage 09 coverage update after the P79 controlled remaining-bin batch. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

The P79 batch ran six candidates targeting the remaining missing bins `[-60, 0, 60]`. Every candidate was early-pass by conversion/leakage/ratio, but every candidate was nearest to `-180`, which was already covered before the run.

Early-pass bins after P80 remain:

```text
[-180, -120, 120]
```

Remaining missing bins after P80 remain:

```text
[-60, 0, 60]
```

## Stop condition

The run stopped after the maximum of six candidates. No two consecutive high-leakage failures occurred, and no candidate opened a missing bin.

## Evidence

The compact P79 summary is `outputs/apcd_k6_active_learning/combined_phase_knob_p79_remaining_bin_batch_results.csv`. No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run files, `.npy`, or large outputs are committed.
