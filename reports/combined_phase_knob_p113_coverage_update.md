# 09-P113 coverage update after 0/60 resonance search

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p110.csv.

P112 ran exactly four selected core-preserving resonance candidates from the P111 plan. No candidate opened the current missing bins [0, 60] because all candidates remained nearest -60, or failed early-pass selectivity.

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best useful trend: cpk_060_alt_htrans04_h430_aniso_reduce10_01, phase -72.5522 deg, target_conversion 0.8649, leakage 0.1182, ratio 7.3176. It moves more than 10 deg from the -88.25 deg anchor toward 0/60 while staying early-pass.

Closest phase but not success: cpk_060_alt_htrans04_h430_scale104_01, phase -62.8043 deg, target_conversion 0.9489, leakage 0.2087, ratio 4.5479. This is near-pass only and does not count as a phase-state success.

Decision: keep the alt_htrans04 resonance branch as useful but not complete. The next search should recover leakage/selectivity around the h430 aniso-reduce10 trend or pivot to another core-preserving resonance anchor. Do not proceed to K=6 phase-ramp, stage 10, or steering claims.
