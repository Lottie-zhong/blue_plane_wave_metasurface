# APCD K=6 P2 Width Candidate Trend Note

## Scope

This report only summarizes existing `p2W` small-subset real-run results. No new FDTD run was performed by this summary step.

It is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML, and not proof of `+15 deg` steering.

## Inputs

The summary reads existing `results.csv` files for:

- p2W_m10
- p2W_m5
- baseline
- p2W_p10

Missing inputs: none

## P2 Width Trend

| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | total_transmission | phase_shift_vs_baseline_deg | early pass |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| p2W_m10 | -10.0 | 0.9326477741220178 | 0.3489369565512095 | 2.6728260122927705 | 0.4554601842546334 | 0.6407923653366139 | -3.746100720439358 | False |
| p2W_m5 | -5.0 | 0.9536094363333241 | 0.14331073983793746 | 6.654137976023684 | 0.7387034299277365 | 0.5484600880856311 | -1.9751895845140268 | True |
| baseline | 0.0 | 0.9711541351322045 | 0.0401994772579764 | 24.158377206667513 | 0.9205036166065964 | 0.5056768061950905 | 0.0 | True |
| p2W_p10 | 10.0 | 0.989295647991839 | 0.013538327784482138 | 73.07369592969323 | 0.9729998621666397 | 0.5014169878881605 | 4.201026446414716 | True |

## Interpretation

- This report only organizes the existing `p2W_m10 / p2W_m5 / baseline / p2W_p10` subset; it does not add any new simulation.
- `p2W_m10` has clearly excessive leakage and fails the current early leakage and ratio thresholds, so it should not enter the priority pool.
- `p2W_p10` keeps excellent alpha-pass behavior and is worth retaining.
- Within this small subset, increasing pillar-2 width in the positive direction appears to reduce leakage and improve the target-to-leakage ratio.
- The phase shifts are still only a few degrees, far below a `60 deg` K=6 phase-state spacing.
- This is not proof of `+15 deg` steering.

Candidates passing all current early thresholds: p2W_m5, baseline, p2W_p10

## Next Step

Next, merge the existing `p1L`, `p1W`, and `p2W` small subsets into one comparison table. Then decide whether testing `p2L` is still useful or whether the phase knob needs to be reconsidered.
