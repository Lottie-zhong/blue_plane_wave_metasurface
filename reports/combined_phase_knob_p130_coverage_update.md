# 09-P130 Coverage and Decision Update

Coverage source: `outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p126.csv`.

P128 ran exactly six selected P127 capsule/racetrack branch candidates. All six were early-pass, but all landed in already-covered -180 or -120 bins. No candidate opened [0, 60].

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best selectivity point: `cpk_capsule_res_h425_01`, phase -157.6913 deg, target_conversion 0.9125, leakage 0.0149, ratio 61.124. This is a covered -180 result.

Largest phase-motion point: `cpk_capsule_res_h435_01`, phase -148.7845 deg, motion 13.3183 deg from the h420 capsule anchor, target_conversion 0.9170, leakage 0.0698, ratio 13.1346. This is still a covered -120 result and does not meet the useful-trend threshold.

Decision: capsule/racetrack branch validates a high-selectivity covered-bin geometry family, but this first continuation is too phase-stiff for [0, 60]. Do not continue stronger common rotation, alt_htrans04 forcing, lower-transition repeats, pure helper-shape sweeps, K=6 phase-ramp, stage 10, or steering claims.
