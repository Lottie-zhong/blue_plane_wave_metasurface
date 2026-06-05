# 09-P117 coverage and decision update

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p113.csv.

P115 ran exactly eight selected boundary-value candidates from the P114 plan. No candidate opened the current missing bins [0, 60].

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best selectivity-preserving boundary: cpk_060_boundary_h435_aniso_reduce10_01, phase -66.3341 deg, target_conversion 0.8589, leakage 0.1384, ratio 6.2042. It remains early-pass but nearest -60.

Near-pass ratio boundary: cpk_060_boundary_h440_aniso_reduce10_01, phase -63.0128 deg, target_conversion 0.8608, leakage 0.1552, ratio 5.5453. It fails early-pass by ratio.

Farthest phase push: cpk_060_boundary_h430_scale104_aniso_reduce10_01, phase -49.6312 deg, but leakage 0.5287 and ratio 1.5756. This is a failure boundary, not a success.

Decision: mark the alt_htrans04 boundary as a stable -60 basin for early-pass states. Stronger scale/aniso routes move phase but break APCD selectivity, so do not continue stronger scale, stronger anisotropy, K=6 phase-ramp, stage 10, or steering claims from these data.
