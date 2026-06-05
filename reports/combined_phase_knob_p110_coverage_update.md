# 09-P110 coverage update after alt_htrans04 continuation

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p107.csv.

P109 opens the -60 missing bin with early-pass quality. Updated early-pass bins are [-180, -120, -60, 120]. Remaining missing bins are [0, 60].

Best tradeoff: cpk_alt_htrans04_h430_01, phase -88.2507 deg, nearest -60, target_conversion 0.8841, leakage 0.0506, ratio 17.4799.

Independent confirmation: cpk_alt_htrans04_h420_aniso_reduce10_01 also opens -60 with target_conversion 0.8270, leakage 0.0844, ratio 9.7978.

Decision: record the -60 opening and stop before extra candidates. Do not proceed to K=6 phase-ramp or steering claims from these data.
