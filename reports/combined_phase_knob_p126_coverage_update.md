# 09-P126 coverage and decision update

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p122.csv.

P124 ran exactly six selected P123 geometry-family candidates. No candidate opened [0, 60], and no candidate qualified as a useful 0/60 anchor.

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best new geometry-family point: cpk_060_geom_capsule_h420_01, phase -162.1028 deg, target_conversion 0.9097, leakage 0.0241, ratio 37.7278. This is a covered -180 anchor, not a 0/60 anchor.

Decision: P123 shape families did not discover a new 0/60 APCD-compatible geometry family. Do not continue forcing alt_htrans04, lower-transition repeats, pure helper-shape sweeps, stronger common rotation, K=6 phase-ramp, stage 10, or steering claims. Capsule/racetrack may be retained as high-selectivity evidence, but not as a path to 0/60 without a new phase knob.
