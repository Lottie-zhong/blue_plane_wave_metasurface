# APCD K=6 P1-Length Candidate Trend Note

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
- p2W_m5

Missing inputs: none

## P1 Length Trend

| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |
|---|---:|---:|---:|---:|---:|---:|---|
| p1L_m10 | -10.0 | 0.9432781844426418 | 0.08702803074499596 | 10.838785806802145 | 0.8310637566530411 | -7.340966210077795 | True |
| p1L_m5 | -5.0 | 0.9633130891923771 | 0.03274486508525911 | 29.418752731328766 | 0.9342510845978365 | -4.455893498056298 | True |
| baseline | 0.0 | 0.9711541351322045 | 0.0401994772579764 | 24.158377206667513 | 0.9205036166065964 | 0.0 | True |
| p1L_p5 | 5.0 | 0.9445714253434363 | 0.11078078290051971 | 8.526491694720443 | 0.7900591252180209 | 5.275299435810723 | True |
| p1L_p10 | 10.0 | 0.8532489247928811 | 0.2314567251907657 | 3.6864296083293766 | 0.5732358816522403 | 12.813406094096479 | False |

## Interpretation

- The pillar-1 length perturbation now spans `-10, -5, 0, +5, +10 nm`.
- `p1L_m10` is worth retaining: it keeps high target conversion, passes the current early leakage and ratio thresholds, and gives a negative phase shift.
- `p1L_p5` passes the current early thresholds, but its leakage is higher than baseline and should be treated cautiously.
- `p1L_p10` gives the largest positive phase shift in this small set, but fails leakage/ratio and should not be prioritized for the phase-state pool.
- These shifts are far below a full `60 deg` K=6 phase-state separation, so this subset is not enough to form a six-state phase library.
- `p2W_m5` is included as a width-perturbation comparator, not as part of the pillar-1 length trend.

Candidates passing all current early thresholds: p1L_m10, p1L_m5, baseline, p1L_p5, p2W_m5

## Next Step

Next, test only a few width perturbations such as `p1W_m5/p1W_p5` or stronger `p2W_m10/p2W_p10`. Do not launch all 13 candidates as a batch.
