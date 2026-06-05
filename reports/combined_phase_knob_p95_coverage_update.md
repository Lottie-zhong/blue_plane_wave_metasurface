# 09-P95 coverage update after minus60 phase scan

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p92.csv.

P94 found phase-hit candidates for the missing -60 bin, but none reached useful-hit or early-pass criteria. Coverage therefore does not change.

Current early-pass bins after P95: [-180, -120, 120].

Remaining missing bins after P95: [-60, 0, 60].

Best tradeoff: cpk_m60scan_relcomp_m80_diff35_01. It is the best -60 phase-hit, but leakage remains 0.5976 and ratio remains 0.9244, far below the selectivity target.

Decision: stop after the planned max-6 P93 scan. The next stage should treat -60 as a located but leakage-dominated branch; it should not proceed to K=6 phase-ramp or steering claims.
