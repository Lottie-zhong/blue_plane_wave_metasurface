# 09-P134 Coverage and Decision Update

Coverage source: `outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p130.csv`.

P132 ran exactly six selected P131 orthogonal phase-knob candidates. No candidate opened [0, 60], no useful 0/60 anchor was found, and no phase-hit failed case occurred because all phases stayed far from 0/60.

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best selective new knob: `cpk_orth_notch_p1_right_h425_01`, phase -149.2261 deg, target_conversion 0.8670, leakage 0.0771, ratio 11.2431. This is an early-pass covered -120 result.

Best phase-motion but failed selectivity point: `cpk_orth_mixed_rect_round_h430_01`, phase -123.9242 deg, target_conversion 0.8992, leakage 0.3525, ratio 2.5510. This is not near [0, 60].

Decision: mixed-shape and weak-scalar co-design knobs move phase toward the covered -120 basin and usually break selectivity. Mild notch preserves selectivity but remains far from 0/60. Do not claim hollow/ring results until internal-hole support is implemented and tested.
