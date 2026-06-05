# 09-P98 coverage update for resphase_core_preserve

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p95.csv.

P97 did not open a new missing bin. The early-pass bins remain [-180, -120, 120], and the remaining missing bins remain [-60, 0, 60].

Best selectivity result: cpk_resphase_anchor_wh03_h410_trim_m5_01, phase -159.0076 deg, target_conversion 0.9191, leakage 0.0088, ratio 104.8964. This is excellent APCD selectivity but nearest to the already-covered -180 bin.

Best 60-bin comparison: cpk_resphase_60lock_counter_m40_h320_helper35x85_01, phase 82.8349 deg, target_conversion 0.7247, leakage 0.2953, ratio 2.4545. This does not meet the phase-hit window or selectivity thresholds.

Decision: stop after the planned top-4. The evidence supports the new principle that APCD selection can be preserved by core-preserving resonance geometry, but the first batch did not find 60/0/-60 coverage. Do not proceed to K=6 phase-ramp or steering claims from these data.
