# 09-P140 Coverage and Decision Update

Coverage source: `outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p134.csv`.

P137 ran exactly twelve selected P136 positive-basin candidates. No candidate opened 60, and no candidate entered the 75-105 deg useful-trend window with early-pass selectivity.

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best positive-basin selective result: `cpk_pos120_period390_h320_01`, phase 153.0397 deg, target_conversion 0.9164, leakage 0.0369, ratio 24.8532. This is still a covered wrapped -180 result.

Best 60 phase-hit failed result: `cpk_pos60_recover_m45weak_notch_p1_01`, phase 62.9936 deg, target_conversion 0.6083, leakage 0.3922, ratio 1.5508. It reaches 60 but fails selectivity.

Decision: positive-basin iso-retardance scans did not open 60 in this batch. Height/period/dynamic phase knobs tend to wrap toward -180 or remain near +120; rot60 recovery reaches the 60 phase window but remains leakage-limited. Do not continue +120 height/period brute force unless a new selectivity-preserving retardance constraint is introduced.
