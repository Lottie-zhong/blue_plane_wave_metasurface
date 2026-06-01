# APCD K=6 P1 Length + Width Candidate Trend Note

## Scope

This report only summarizes existing small-subset real-run results. No new FDTD run was performed by this summary step.

It is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML, and not proof of `+15 deg` steering.

## Inputs

The summary reads existing `results.csv` files for:

- baseline
- p1L_m10
- p1L_m5
- p1L_p5
- p1L_p10
- p1W_m5
- p1W_p5

Missing inputs: none

## P1 Length Trend

| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |
|---|---:|---:|---:|---:|---:|---:|---|
| p1L_m10 | -10.0 | 0.9432781844426418 | 0.08702803074499596 | 10.838785806802145 | 0.8310637566530411 | -7.340966210077795 | True |
| p1L_m5 | -5.0 | 0.9633130891923771 | 0.03274486508525911 | 29.418752731328766 | 0.9342510845978365 | -4.455893498056298 | True |
| baseline | 0.0 | 0.9711541351322045 | 0.0401994772579764 | 24.158377206667513 | 0.9205036166065964 | 0.0 | True |
| p1L_p5 | 5.0 | 0.9445714253434363 | 0.11078078290051971 | 8.526491694720443 | 0.7900591252180209 | 5.275299435810723 | True |
| p1L_p10 | 10.0 | 0.8532489247928811 | 0.2314567251907657 | 3.6864296083293766 | 0.5732358816522403 | 12.813406094096479 | False |

## P1 Width Trend

| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |
|---|---:|---:|---:|---:|---:|---:|---|
| p1W_m5 | -5.0 | 0.9630178978367885 | 0.03327122222380918 | 28.94447012889415 | 0.9332097047847876 | -5.998417282378824 | True |
| p1W_p5 | 5.0 | 0.9472618562179853 | 0.11949113699612182 | 7.927465417303727 | 0.7759722489524304 | 6.762100361623993 | True |

## Interpretation

- The pillar-1 length and pillar-1 width perturbations both provide small intrinsic phase tuning.
- `p1W_m5` and `p1W_p5` both pass the current early thresholds.
- `p1W_m5` has very low leakage and is worth retaining.
- `p1W_p5` still passes, but leakage rises relative to baseline and should be treated cautiously.
- The `p1W` +/-5 nm phase shifts are about +/-6 deg, slightly stronger than the `p1L` +/-5 nm shifts.
- The current pillar-1 perturbations are still far from a `60 deg` K=6 phase-state spacing, so they are not enough to form a six-state phase library.
- This is not proof of `+15 deg` steering.

Candidates passing all current early thresholds: p1L_m10, p1L_m5, baseline, p1L_p5, p1W_m5, p1W_p5

## Next Step

Next, test only a few pillar-2 width perturbations such as `p2W_m10/p2W_p10`. Do not launch all 13 candidates as a batch.
