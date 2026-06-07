# 09-P122 coverage and decision update

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p117.csv.

P120 ran exactly six selected P119 anchor-discovery candidates. No candidate opened [0, 60], and no candidate qualified as a useful 0/60 anchor.

Updated early-pass bins remain [-180, -120, -60, 120]. Remaining missing bins remain [0, 60].

Best selectivity anchor: cpk_060_anchor_wh03_h425_scale98_01, phase -120.0309 deg, target_conversion 0.9142, leakage 0.0886, ratio 10.3229. This is a covered-bin reference, not a 0/60 anchor.

Decision: P119 did not discover a new 0/60 core-preserving resonance anchor. Do not continue alt_htrans04 stronger h/scale/aniso, lower-transition repeats, pure helper-shape sweeps, K=6 phase-ramp, stage 10, or steering claims. Pivot within stage 09 to a different physics knob or new core-preserving geometry family.
