# APCD K=6 Phase-Knob Redesign Decision

## Scope

This is the 08-P9 closure note. It only combines existing `p1L`, `p1W`, and `p2W` small-subset summaries. No FDTD run was performed by this step.

This is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML training, and not a steering result.

## Current 08 Small-Subset Result

| variant_id | changed_parameter | delta_nm | target_conversion | opposite_spin_leakage | ratio | phase_shift_vs_baseline_deg | early pass | priority |
|---|---|---:|---:|---:|---:|---:|---|---|
| p1L_m10 | pillar_1_length_nm | -10.0 | 0.9432781844426418 | 0.08702803074499596 | 10.838785806802145 | -7.340966210077795 | True | keep_candidate |
| p1L_m5 | pillar_1_length_nm | -5.0 | 0.9633130891923771 | 0.03274486508525911 | 29.418752731328766 | -4.455893498056298 | True | keep_candidate |
| baseline | none | 0.0 | 0.9711541351322045 | 0.0401994772579764 | 24.158377206667513 | 0.0 | True | keep_high_priority |
| p1L_p5 | pillar_1_length_nm | 5.0 | 0.9445714253434363 | 0.11078078290051971 | 8.526491694720443 | 5.275299435810723 | True | keep_candidate |
| p1L_p10 | pillar_1_length_nm | 10.0 | 0.8532489247928811 | 0.2314567251907657 | 3.6864296083293766 | 12.813406094096479 | False | record_not_priority |
| p1W_m5 | pillar_1_width_nm | -5.0 | 0.9630178978367885 | 0.03327122222380918 | 28.94447012889415 | -5.998417282378824 | True | keep_high_priority |
| p1W_p5 | pillar_1_width_nm | 5.0 | 0.9472618562179853 | 0.11949113699612182 | 7.927465417303727 | 6.762100361623993 | True | keep_candidate |
| p2W_m10 | pillar_2_width_nm | -10.0 | 0.9326477741220178 | 0.3489369565512095 | 2.6728260122927705 | -3.746100720439358 | False | record_not_priority |
| p2W_m5 | pillar_2_width_nm | -5.0 | 0.9536094363333241 | 0.14331073983793746 | 6.654137976023684 | -1.9751895845140268 | True | keep_candidate |
| p2W_p10 | pillar_2_width_nm | 10.0 | 0.989295647991839 | 0.013538327784482138 | 73.07369592969323 | 4.201026446414716 | True | keep_high_priority |

## Phase Coverage Decision

- K=6 needs adjacent dimer target-channel phase spacing of `60 deg` for the intended six-state library.
- The largest early-passing absolute phase shift in the current one-factor subset is about `7.34 deg`.
- The largest observed absolute phase shift is about `12.81 deg`, but that point fails leakage/ratio.
- Therefore, one-factor perturbations are insufficient to form a `0/60/120/180/240/300 deg` phase-state library.
- The current results are not a `+15 deg` steering proof.
- Blindly running the remaining one-factor candidates is not recommended.

## Priority

- keep_high_priority: baseline, p1W_m5, p2W_p10
- keep_candidate: p1L_m10, p1L_m5, p1L_p5, p1W_p5, p2W_m5
- record_not_priority: p1L_p10, p2W_m10

## 08 Closure

08 can close as a negative-but-useful phase-knob diagnostic: the alpha-pass baseline and several one-factor variants remain strong, but the phase span is far short of the K=6 requirement.

## Next Stage: 09 Small-Data Active Learning Surrogate

09 should not start by training a large model. It should first:

1. Define an ML-ready dataset schema.
2. Define a multi-parameter candidate space.
3. Design about 20-30 DOE combined-geometry candidates.
4. Use a small-data surrogate / active learning loop only after the schema and DOE set are locked.

If the single-dimer phase-state library still fails after combined geometry and hybrid knobs, the project should pivot to direct K=6 supercell optimization.
